from fastapi.testclient import TestClient

from diary_api.app import app


def test_protected_owner_endpoint_rejects_missing_credentials() -> None:
    response = TestClient(app).get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["www-authenticate"] == "Bearer"
