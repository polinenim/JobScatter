from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_is_available() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_database_state() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}
