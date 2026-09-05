from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app
from app import source_registry

client = TestClient(app)


class FakeResult:
    def __init__(self, record=None, records=None, rowcount=1):
        self.record = record
        self.records = records or []
        self.rowcount = rowcount

    def fetchone(self):
        return self.record

    def fetchall(self):
        return self.records


class FakeConnection:
    def __init__(self, record):
        self.record = record
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if query.startswith("SELECT * FROM source_registry ORDER BY"):
            return FakeResult(records=[self.record])
        if query.startswith("DELETE"):
            return FakeResult(rowcount=1)
        return FakeResult(record=self.record)


def make_record(source_id=None):
    return {
        "source_id": source_id or uuid4(),
        "source_name": "Example Board",
        "source_type": "job_board",
        "access_method": "api",
        "base_endpoint": "https://jobs.example.test",
        "configuration": {"tenant": "demo"},
        "enabled": True,
        "capabilities": ["incremental_sync"],
        "last_successful_run": None,
        "last_error": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def test_create_source_returns_registry_record(monkeypatch):
    record = make_record()
    connection = FakeConnection(record)
    monkeypatch.setattr(source_registry, "_get_connection", lambda: connection)

    response = client.post(
        "/sources",
        json={
            "source_name": "Example Board",
            "source_type": "job_board",
            "access_method": "api",
            "base_endpoint": "https://jobs.example.test",
            "configuration": {"tenant": "demo"},
            "capabilities": ["incremental_sync"],
        },
    )

    assert response.status_code == 201
    assert response.json()["source_name"] == "Example Board"
    assert response.json()["enabled"] is True
    assert isinstance(connection.calls[0][1][0], UUID)


def test_list_sources_returns_registered_sources(monkeypatch):
    connection = FakeConnection(make_record())
    monkeypatch.setattr(source_registry, "_get_connection", lambda: connection)

    response = client.get("/sources")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["source_type"] == "job_board"


def test_update_source_can_record_operational_status(monkeypatch):
    source_id = uuid4()
    record = make_record(source_id)
    connection = FakeConnection(record)
    monkeypatch.setattr(source_registry, "_get_connection", lambda: connection)

    response = client.patch(
        f"/sources/{source_id}",
        json={"enabled": False, "last_error": {"message": "timeout"}},
    )

    assert response.status_code == 200
    assert response.json()["source_id"] == str(source_id)
    assert "updated_at = NOW()" in connection.calls[0][0]


def test_create_source_requires_core_configuration():
    response = client.post("/sources", json={"source_name": "Incomplete"})

    assert response.status_code == 422
