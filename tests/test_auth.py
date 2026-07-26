import json
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import cast

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from httpx import Response
from pytest import MonkeyPatch, mark

from diary_api.app import app
from diary_api.auth import auth_settings, token_verifier

UNKNOWN_KID_TOKEN = (
    "eyJhbGciOiJFUzI1NiIsImtpZCI6Im1pc3NpbmcifQ."
    "eyJhdWQiOiJhdXRoZW50aWNhdGVkIn0."
    "c2lnbmF0dXJl"
)


@contextmanager
def _jwks_endpoint(response_body: bytes) -> Iterator[str]:
    class JwksHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), JwksHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _request_with_jwks(
    monkeypatch: MonkeyPatch,
    response_body: bytes,
    token: str | Callable[[str], str] = UNKNOWN_KID_TOKEN,
) -> Response:
    with _jwks_endpoint(response_body) as supabase_url:
        access_token = token(supabase_url) if callable(token) else token
        monkeypatch.setenv("DIARY_ENVIRONMENT", "test")
        monkeypatch.setenv("SUPABASE_URL", supabase_url)
        auth_settings.cache_clear()
        token_verifier.cache_clear()
        try:
            return cast(
                Response,
                TestClient(app).get(
                    "/auth/me",
                    headers={
                        "Authorization": f"Bearer {access_token}"
                    },
                ),
            )
        finally:
            auth_settings.cache_clear()
            token_verifier.cache_clear()


def _es256_signing_material(
    kid: str = "matching",
) -> tuple[ec.EllipticCurvePrivateKey, bytes]:
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_jwk = cast(
        dict[str, object],
        json.loads(
            jwt.algorithms.ECAlgorithm.to_jwk(private_key.public_key())
        ),
    )
    public_jwk.update(
        {
            "alg": "ES256",
            "kid": kid,
            "use": "sig",
        }
    )
    return (
        private_key,
        json.dumps({"keys": [public_jwk]}).encode(),
    )


def test_protected_owner_endpoint_rejects_missing_credentials() -> None:
    response = TestClient(app).get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"


@mark.parametrize(
    "token_case",
    ["malformed", "expired", "invalid-claims", "invalid-signature"],
)
def test_protected_owner_endpoint_uniformly_rejects_invalid_tokens(
    monkeypatch: MonkeyPatch,
    token_case: str,
) -> None:
    private_key, jwks_body = _es256_signing_material()

    def build_token(issuer: str) -> str:
        claims: dict[str, object] = {
            "aud": "authenticated",
            "exp": int(time.time()) + 300,
            "iss": issuer,
            "sub": "61c2f4ca-2fab-4b50-a0cf-12aac0ec0b24",
        }
        signing_key = private_key
        if token_case == "expired":
            claims["exp"] = int(time.time()) - 60
        elif token_case == "invalid-claims":
            del claims["sub"]
        elif token_case == "invalid-signature":
            signing_key = ec.generate_private_key(ec.SECP256R1())
        return jwt.encode(
            claims,
            signing_key,
            algorithm="ES256",
            headers={"kid": "matching"},
        )

    request_token: str | Callable[[str], str]
    if token_case == "malformed":
        request_token = "definitely-not-a-jwt"
    else:
        request_token = build_token

    response = _request_with_jwks(
        monkeypatch,
        jwks_body,
        request_token,
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_owner_endpoint_reports_unavailable_jwks(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("DIARY_ENVIRONMENT", "test")
    monkeypatch.setenv("SUPABASE_URL", "http://127.0.0.1:9")
    auth_settings.cache_clear()
    token_verifier.cache_clear()

    try:
        token_with_unreachable_jwks = (
            "eyJhbGciOiJFUzI1NiIsImtpZCI6Im1pc3NpbmcifQ."
            "eyJhdWQiOiJhdXRoZW50aWNhdGVkIn0."
            "c2lnbmF0dXJl"
        )
        response = TestClient(app).get(
            "/auth/me",
            headers={
                "Authorization": (
                    f"Bearer {token_with_unreachable_jwks}"
                )
            },
        )
    finally:
        auth_settings.cache_clear()
        token_verifier.cache_clear()

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Authentication service unavailable"
    }


def test_protected_owner_endpoint_reports_non_object_jwks_as_unavailable(
    monkeypatch: MonkeyPatch,
) -> None:
    response = _request_with_jwks(
        monkeypatch,
        b'["sensitive upstream diagnostic"]',
    )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Authentication service unavailable"
    }


@mark.parametrize(
    "jwks_body",
    [
        b"{",
        b"{}",
        b'{"keys":[null]}',
        (
            b'{"keys":[{"kty":"oct","k":"c2VjcmV0",'
            b'"use":"enc","kid":"not-for-signing"}]}'
        ),
    ],
    ids=[
        "malformed-json",
        "empty",
        "malformed-key",
        "no-usable-signing-key",
    ],
)
def test_protected_owner_endpoint_reports_invalid_jwks_as_unavailable(
    monkeypatch: MonkeyPatch,
    jwks_body: bytes,
) -> None:
    response = _request_with_jwks(monkeypatch, jwks_body)

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Authentication service unavailable"
    }


def test_protected_owner_endpoint_rejects_unknown_kid_in_valid_jwks(
    monkeypatch: MonkeyPatch,
) -> None:
    response = _request_with_jwks(
        monkeypatch,
        (
            b'{"keys":[{"kty":"oct","k":"c2VjcmV0LXNlY3JldA",'
            b'"alg":"HS256","use":"sig","kid":"available"}]}'
        ),
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"
