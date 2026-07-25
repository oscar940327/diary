from fastapi.testclient import TestClient

from diary_api.app import app


def test_health_endpoint_reports_that_diary_api_is_ready() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "diary-api",
        "status": "ready",
    }
