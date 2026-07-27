from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from typing import IO, cast
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen
from uuid import UUID

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
API_BASE_URL = "http://127.0.0.1:8003"
PRODUCTION_API_BASE_URL = "http://127.0.0.1:8001"
FRONTEND_BASE_URL = (
    "http://127.0.0.1:4173/my-personal-website"
)
OWNER_ID = UUID("61c2f4ca-2fab-4b50-a0cf-12aac0ec0b24")
OWNER_EMAIL = "owner@diary.test"
NON_OWNER_ID = UUID("0c97345c-50ac-4fcb-9664-bf796b854a92")
NON_OWNER_EMAIL = "not-owner@diary.test"
MAGIC_LINK_PATTERN = re.compile(
    r'href="(http://127\.0\.0\.1:54321/auth/v1/verify\?[^"]+)"'
)
MAGIC_LINK_RATE_LIMIT_RETRY_SECONDS = 3.0
MAGIC_LINK_RATE_LIMIT_POLL_SECONDS = 0.1


@dataclass(frozen=True)
class LocalSupabase:
    api_url: str
    publishable_key: str
    secret_key: str = field(repr=False)
    service_role_key: str = field(repr=False)
    mailpit_url: str


class SensitiveAccessToken(str):
    def __repr__(self) -> str:
        return "<redacted access token>"


def _supabase_executable() -> str:
    executable_name = "supabase.cmd" if os.name == "nt" else "supabase"
    executable = (
        REPOSITORY_ROOT / "node_modules" / ".bin" / executable_name
    )
    if not executable.is_file():
        pytest.fail(
            "Supabase CLI is missing. Run npm install in the Diary "
            "repository."
        )
    return str(executable)


def _frontend_repository() -> Path:
    configured_path = os.environ.get("DIARY_FRONTEND_REPOSITORY")
    candidates = (
        Path(configured_path) if configured_path else None,
        REPOSITORY_ROOT.parent / "personal_website",
        REPOSITORY_ROOT.parent.parent / "personal_website",
    )

    for candidate in candidates:
        if candidate is not None and (candidate / "vite.config.ts").is_file():
            return candidate.resolve()

    pytest.fail(
        "Diary frontend repository not found. Set DIARY_FRONTEND_REPOSITORY "
        "to the personal_website checkout."
    )


def _supabase_cli(
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _supabase_executable(),
            *arguments,
        ],
        cwd=REPOSITORY_ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def _supabase_status() -> LocalSupabase:
    result = _supabase_cli("status", "-o", "json")
    values = json.loads(result.stdout)
    return LocalSupabase(
        api_url=values["API_URL"],
        publishable_key=values["PUBLISHABLE_KEY"],
        secret_key=values["SECRET_KEY"],
        service_role_key=values["SERVICE_ROLE_KEY"],
        mailpit_url=values["MAILPIT_URL"],
    )


@pytest.fixture(scope="session")
def local_supabase() -> Iterator[LocalSupabase]:
    status = _supabase_cli("status", "-o", "json", check=False)
    started_by_test = status.returncode != 0

    if started_by_test:
        _supabase_cli(
            "start",
            "-x",
            (
                "edge-runtime,imgproxy,logflare,postgres-meta,realtime,"
                "storage-api,studio,supavisor,vector"
            ),
        )

    _supabase_cli("db", "reset")
    settings = _supabase_status()

    try:
        yield settings
    finally:
        if started_by_test:
            _supabase_cli("stop")


def _admin_headers(settings: LocalSupabase) -> dict[str, str]:
    return {
        "apikey": settings.service_role_key,
        "Authorization": f"Bearer {settings.service_role_key}",
        "Content-Type": "application/json",
    }


def _public_headers(settings: LocalSupabase) -> dict[str, str]:
    return {
        "apikey": settings.publishable_key,
        "Content-Type": "application/json",
    }


def _create_user(
    settings: LocalSupabase,
    *,
    user_id: UUID,
    email: str,
) -> None:
    response = httpx.post(
        f"{settings.api_url}/auth/v1/admin/users",
        headers=_admin_headers(settings),
        json={
            "id": str(user_id),
            "email": email,
            "email_confirm": True,
        },
        timeout=10,
    )
    assert response.status_code == 200, response.text


@pytest.fixture(scope="session")
def provisioned_users(local_supabase: LocalSupabase) -> LocalSupabase:
    _create_user(local_supabase, user_id=OWNER_ID, email=OWNER_EMAIL)
    _create_user(
        local_supabase,
        user_id=NON_OWNER_ID,
        email=NON_OWNER_EMAIL,
    )
    response = httpx.post(
        f"{local_supabase.api_url}/rest/v1/diary_owners",
        headers=_admin_headers(local_supabase),
        json={"user_id": str(OWNER_ID)},
        timeout=10,
    )
    assert response.status_code == 201, response.text
    return local_supabase


def _request_magic_link(settings: LocalSupabase, email: str) -> None:
    deadline = time.monotonic() + MAGIC_LINK_RATE_LIMIT_RETRY_SECONDS

    while True:
        response = httpx.post(
            f"{settings.api_url}/auth/v1/otp",
            headers=_public_headers(settings),
            json={
                "email": email,
                "create_user": False,
            },
            timeout=10,
        )
        if response.status_code == 200:
            return

        try:
            error_code = response.json().get("error_code")
        except (TypeError, ValueError):
            error_code = None

        if (
            response.status_code != 429
            or error_code != "over_email_send_rate_limit"
            or time.monotonic() >= deadline
        ):
            pytest.fail(
                "Local Supabase did not issue a Magic Link: "
                f"{response.status_code} {response.text}"
            )

        time.sleep(MAGIC_LINK_RATE_LIMIT_POLL_SECONDS)


def _mail_recipient(message: object) -> str:
    if not isinstance(message, dict):
        return ""

    recipients = message.get("To")
    if not isinstance(recipients, list):
        return ""

    addresses = [
        recipient.get("Address", "")
        for recipient in recipients
        if isinstance(recipient, dict)
    ]
    return ",".join(addresses)


def _wait_for_magic_link(
    settings: LocalSupabase,
    email: str,
    *,
    timeout_seconds: float = 10,
) -> str:
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        messages_response = httpx.get(
            f"{settings.mailpit_url}/api/v1/messages",
            timeout=5,
        )
        messages_response.raise_for_status()

        for message in messages_response.json().get("messages", []):
            if email not in _mail_recipient(message):
                continue

            message_id = message["ID"]
            message_response = httpx.get(
                f"{settings.mailpit_url}/api/v1/message/{message_id}",
                timeout=5,
            )
            message_response.raise_for_status()
            message_body = message_response.json()
            match = MAGIC_LINK_PATTERN.search(message_body["HTML"])
            if match is not None:
                return unescape(match.group(1))

        time.sleep(0.1)

    pytest.fail(f"Timed out waiting for the local Magic Link for {email}")


def _sign_in_with_magic_link(settings: LocalSupabase, email: str) -> str:
    _request_magic_link(settings, email)
    magic_link = _wait_for_magic_link(settings, email)
    response = httpx.get(
        magic_link,
        follow_redirects=False,
        timeout=10,
    )
    assert response.status_code in {302, 303}
    parameters = parse_qs(urlparse(response.headers["location"]).fragment)
    return parameters["access_token"][0]


@pytest.fixture
def owner_magic_link(
    provisioned_users: LocalSupabase,
) -> Callable[[], str]:
    return lambda: _wait_for_magic_link(provisioned_users, OWNER_EMAIL)


@pytest.fixture(scope="session")
def owner_access_token(provisioned_users: LocalSupabase) -> str:
    return SensitiveAccessToken(
        _sign_in_with_magic_link(provisioned_users, OWNER_EMAIL)
    )


@pytest.fixture(scope="session")
def non_owner_access_token(provisioned_users: LocalSupabase) -> str:
    return SensitiveAccessToken(
        _sign_in_with_magic_link(provisioned_users, NON_OWNER_EMAIL)
    )


def _local_auth_signing_key() -> dict[str, object]:
    result = subprocess.run(
        [
            "docker",
            "inspect",
            "supabase_auth_diary",
            "--format",
            "{{range .Config.Env}}{{println .}}{{end}}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    keys_environment = next(
        line
        for line in result.stdout.splitlines()
        if line.startswith("GOTRUE_JWT_KEYS=")
    )
    keys = json.loads(keys_environment.removeprefix("GOTRUE_JWT_KEYS="))
    return cast(dict[str, object], keys[0])


@pytest.fixture(scope="session")
def expired_owner_access_token(
    provisioned_users: LocalSupabase,
) -> str:
    signing_jwk = _local_auth_signing_key()
    now = int(time.time())
    private_key = cast(
        EllipticCurvePrivateKey,
        jwt.algorithms.ECAlgorithm.from_jwk(
            json.dumps(signing_jwk)
        ),
    )
    return SensitiveAccessToken(
        jwt.encode(
            {
                "aud": "authenticated",
                "exp": now - 60,
                "iat": now - 120,
                "iss": f"{provisioned_users.api_url}/auth/v1",
                "role": "authenticated",
                "sub": str(OWNER_ID),
            },
            private_key,
            algorithm="ES256",
            headers={"kid": signing_jwk["kid"]},
        )
    )


def _execute_local_database_sql(statement: str) -> None:
    result = subprocess.run(
        [
            "docker",
            "exec",
            "supabase_db_diary",
            "psql",
            "--username",
            "postgres",
            "--dbname",
            "postgres",
            "--set",
            "ON_ERROR_STOP=1",
            "--command",
            statement,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(
            "Could not configure the local RLS system-test boundary: "
            f"{result.stderr.strip()}"
        )


@pytest.fixture
def entry_insert_rls_denial(
    provisioned_users: LocalSupabase,
) -> Iterator[None]:
    policy_name = "system test denies entry inserts"
    _execute_local_database_sql(
        f'create policy "{policy_name}" '
        "on public.entries as restrictive "
        "for insert to authenticated with check (false);"
    )
    try:
        yield
    finally:
        _execute_local_database_sql(
            f'drop policy "{policy_name}" on public.entries;'
        )


def _wait_until_ready(
    process: subprocess.Popen[bytes],
    url: str,
    output: IO[bytes],
    *,
    timeout_seconds: float = 30,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = "service did not respond"

    while time.monotonic() < deadline:
        if process.poll() is not None:
            output.seek(0)
            details = output.read().decode(errors="replace")
            pytest.fail(
                f"Service exited before {url} became ready.\n{details}"
            )

        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
                last_error = f"HTTP {response.status}"
        except (OSError, URLError) as error:
            last_error = str(error)

        time.sleep(0.1)

    pytest.fail(f"Timed out waiting for {url}: {last_error}")


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


@contextmanager
def _running_service(
    command: list[str],
    *,
    cwd: Path,
    ready_url: str,
    env: dict[str, str],
) -> Iterator[None]:
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        try:
            _wait_until_ready(process, ready_url, output)
            yield
        finally:
            _stop_process(process)


@pytest.fixture(scope="session")
def diary_api(
    provisioned_users: LocalSupabase,
) -> Iterator[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "DIARY_ENVIRONMENT": "test",
            "DIARY_PRODUCTION_ORIGIN": (
                "https://oscar940327.github.io"
            ),
            "DIARY_LOCAL_ORIGINS": (
                "http://127.0.0.1:4173,http://127.0.0.1:5173"
            ),
            "SUPABASE_SECRET_KEY": (
                provisioned_users.secret_key
            ),
            "SUPABASE_PUBLISHABLE_KEY": (
                provisioned_users.publishable_key
            ),
            "SUPABASE_URL": provisioned_users.api_url,
        }
    )

    with _running_service(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "diary_api.app:app",
            "--app-dir",
            "src",
            "--host",
            "127.0.0.1",
            "--port",
            "8003",
        ],
        cwd=REPOSITORY_ROOT,
        ready_url=f"{API_BASE_URL}/health",
        env=environment,
    ):
        yield API_BASE_URL


@pytest.fixture(scope="session")
def production_diary_api(
    provisioned_users: LocalSupabase,
) -> Iterator[str]:
    environment = os.environ.copy()
    environment.update(
        {
            "DIARY_ENVIRONMENT": "production",
            "DIARY_PRODUCTION_ORIGIN": (
                "https://oscar940327.github.io"
            ),
            "SUPABASE_SECRET_KEY": (
                provisioned_users.secret_key
            ),
            "SUPABASE_PUBLISHABLE_KEY": (
                provisioned_users.publishable_key
            ),
            "SUPABASE_URL": provisioned_users.api_url,
        }
    )

    with _running_service(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "diary_api.app:app",
            "--app-dir",
            "src",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ],
        cwd=REPOSITORY_ROOT,
        ready_url=f"{PRODUCTION_API_BASE_URL}/health",
        env=environment,
    ):
        yield PRODUCTION_API_BASE_URL


@pytest.fixture(scope="session")
def diary_application(
    diary_api: str,
    provisioned_users: LocalSupabase,
) -> Iterator[str]:
    frontend_repository = _frontend_repository()
    node = shutil.which("node")
    if node is None:
        pytest.fail("Node.js is required for the Diary browser tests.")

    vite_entrypoint = (
        frontend_repository / "node_modules" / "vite" / "bin" / "vite.js"
    )
    if not vite_entrypoint.is_file():
        pytest.fail(
            "Frontend dependencies are missing. Run npm install in "
            f"{frontend_repository}."
        )

    environment = os.environ.copy()
    environment.update(
        {
            "VITE_SUPABASE_URL": provisioned_users.api_url,
            "VITE_SUPABASE_PUBLISHABLE_KEY": (
                provisioned_users.publishable_key
            ),
            "VITE_DIARY_API_URL": API_BASE_URL,
        }
    )

    with _running_service(
        [
            node,
            str(vite_entrypoint),
            "--host",
            "127.0.0.1",
            "--port",
            "4173",
            "--strictPort",
        ],
        cwd=frontend_repository,
        ready_url=f"{FRONTEND_BASE_URL}/diary.html",
        env=environment,
    ):
        yield FRONTEND_BASE_URL
