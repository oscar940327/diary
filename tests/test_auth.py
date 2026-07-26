from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from diary_api.app import app
from diary_api.auth import auth_settings, token_verifier


def test_protected_owner_endpoint_rejects_missing_credentials() -> None:
    response = TestClient(app).get("/auth/me")

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
