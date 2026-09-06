from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app import ingestion_api
from app.ingestion_pipeline import IngestionRunSummary
from app.main import app
from app.source_registry import SourceRegistryRecord

client = TestClient(app)


def make_source(*, enabled=True, source_type="greenhouse", configuration=None):
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    return SourceRegistryRecord(
        source_id=uuid4(),
        source_name="Example Greenhouse",
        source_type=source_type,
        access_method="api",
        configuration=(
            {"board_token": "example-board"}
            if configuration is None
            else configuration
        ),
        enabled=enabled,
        capabilities=[],
        created_at=now,
        updated_at=now,
    )


def test_run_source_returns_pipeline_summary(monkeypatch):
    source = make_source()
    calls = []

    class FakePipeline:
        def run_source(self, received_source):
            calls.append(received_source)
            return IngestionRunSummary(fetched=2, valid=2, new=2)

    monkeypatch.setattr(ingestion_api, "get_source_record", lambda _: source)
    monkeypatch.setattr(ingestion_api, "IngestionPipeline", FakePipeline)

    response = client.post(f"/ingestion/sources/{source.source_id}/run")

    assert response.status_code == 200
    assert response.json() == {
        "fetched": 2,
        "valid": 2,
        "rejected": 0,
        "new": 2,
        "duplicate": 0,
        "updated": 0,
        "errors": 0,
    }
    assert calls == [source]


def test_run_source_returns_404_when_source_is_missing(monkeypatch):
    monkeypatch.setattr(ingestion_api, "get_source_record", lambda _: None)

    response = client.post(f"/ingestion/sources/{uuid4()}/run")

    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"


def test_run_source_rejects_disabled_source(monkeypatch):
    source = make_source(enabled=False)
    monkeypatch.setattr(ingestion_api, "get_source_record", lambda _: source)

    response = client.post(f"/ingestion/sources/{source.source_id}/run")

    assert response.status_code == 409
    assert response.json()["detail"] == "Source is disabled"


def test_run_source_rejects_missing_board_token(monkeypatch):
    source = make_source(configuration={})
    monkeypatch.setattr(ingestion_api, "get_source_record", lambda _: source)

    response = client.post(f"/ingestion/sources/{source.source_id}/run")

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Greenhouse source requires configuration.board_token"
    )


def test_run_source_accepts_jobly_source(monkeypatch):
    source = make_source(
        source_type="jobly",
        configuration={"search_term": "software", "location": "Finland"},
    )
    calls = []

    class FakePipeline:
        def run_source(self, received_source):
            calls.append(received_source)
            return IngestionRunSummary(fetched=1, valid=1, new=1)

    monkeypatch.setattr(ingestion_api, "get_source_record", lambda _: source)
    monkeypatch.setattr(ingestion_api, "IngestionPipeline", FakePipeline)

    response = client.post(f"/ingestion/sources/{source.source_id}/run")

    assert response.status_code == 200
    assert response.json()["fetched"] == 1
    assert calls == [source]
