from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO
from urllib.error import URLError
from urllib.request import urlopen

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
API_READY_URL = "http://127.0.0.1:8000/health"
FRONTEND_READY_URL = (
    "http://127.0.0.1:4174/my-personal-website/index.html"
)


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
    env: dict[str, str] | None = None,
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


@pytest.fixture(scope="session", autouse=True)
def diary_services() -> Iterator[None]:
    frontend_repository = _frontend_repository()
    node = shutil.which("node")
    if node is None:
        pytest.fail("Node.js is required for the Diary browser acceptance test.")

    vite_entrypoint = (
        frontend_repository / "node_modules" / "vite" / "bin" / "vite.js"
    )
    if not vite_entrypoint.is_file():
        pytest.fail(
            "Frontend dependencies are missing. Run npm install in "
            f"{frontend_repository}."
        )

    frontend_environment = os.environ.copy()
    frontend_environment.pop("VITE_DIARY_API_URL", None)
    frontend_environment.update(
        {
            "VITE_SUPABASE_URL": "http://127.0.0.1:54321",
            "VITE_SUPABASE_PUBLISHABLE_KEY": (
                "sb_publishable_ticket_01_acceptance"
            ),
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
            "8000",
        ],
        cwd=REPOSITORY_ROOT,
        ready_url=API_READY_URL,
    ):
        with _running_service(
            [
                node,
                str(vite_entrypoint),
                "--host",
                "127.0.0.1",
                "--port",
                "4174",
                "--strictPort",
            ],
            cwd=frontend_repository,
            ready_url=FRONTEND_READY_URL,
            env=frontend_environment,
        ):
            yield
