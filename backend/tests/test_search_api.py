from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app import search_api
from app.candidate_profile import CandidateProfile
from app.main import app


client = TestClient(app)
NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)


def test_unified_search_reads_stored_jobs_without_collecting_sources():
    candidate_id = uuid4()
    calls = {"jobs": 0}

    class FakeCandidateRepository:
        def get_confirmed_profile(self, received_id):
            assert received_id == candidate_id
            return CandidateProfile(candidate_id=candidate_id, version=1, status="confirmed", created_at=NOW)

    class FakeJobRepository:
        def list_search_candidates(self):
            calls["jobs"] += 1
            return []

    service = search_api.UnifiedSearchService(
        candidate_repository=FakeCandidateRepository(),
        job_repository=FakeJobRepository(),
    )

    result = service.run(candidate_id)

    assert calls["jobs"] == 1
    assert result.total == 0
    assert result.total == 0


def test_post_search_uses_candidate_id_and_returns_pdf_ready_fields(monkeypatch):
    candidate_id = uuid4()

    class FakeService:
        def run(self, received_id):
            assert received_id == candidate_id
            return {
                "candidate_id": candidate_id,
                "items": [{
                    "company_name": "Example Co",
                    "job_title": "Software Engineer",
                    "posted_at": NOW,
                    "job_link": "https://www.jobly.fi/tyopaikka/example-123",
                }],
                "total": 1,
                "source_runs": {},
            }

    monkeypatch.setattr(search_api, "UnifiedSearchService", FakeService)

    response = client.post("/search", json={"candidate_id": str(candidate_id)})

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert set(item) == {"company_name", "job_title", "posted_at", "job_link"}
    assert item["company_name"] == "Example Co"
    assert item["job_title"] == "Software Engineer"
    assert item["posted_at"] == "2026-09-05T00:00:00Z"
    assert item["job_link"].endswith("example-123")


def test_fetch_refreshes_enabled_sources_then_reuses_search_service():
    candidate_id = uuid4()
    enabled = type("Source", (), {"enabled": True, "source_type": "greenhouse"})()
    disabled = type("Source", (), {"enabled": False, "source_type": "lever"})()
    calls = []

    class FakePipeline:
        def run_source(self, source):
            calls.append(("ingest", source.source_type))

    class FakeSearchService:
        def run(self, received_id):
            calls.append(("search", received_id))
            return search_api.UnifiedSearchResponse(
                candidate_id=received_id,
                items=[],
                total=0,
            )

    service = search_api.FetchService(
        source_loader=lambda: [enabled, disabled],
        pipeline_factory=FakePipeline,
        search_service_factory=FakeSearchService,
    )

    result = service.run(candidate_id)

    assert result.total == 0
    assert calls == [("ingest", "greenhouse"), ("search", candidate_id)]
