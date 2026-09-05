from app.main import app
from fastapi.testclient import TestClient


def test_health_returns_non_sensitive_service_status() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "cloudguard-api",
        "environment": "development",
    }


def test_versioned_health_matches_frontend_api_base_path() -> None:
    response = TestClient(app).get('/api/v1/health')

    assert response.status_code == 200
    assert response.json()['status'] == 'ok'