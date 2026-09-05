from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app import jobs_api
from app.main import app

client = TestClient(app)


class FakeRepository:
    def __init__(self):
        self.arguments = None

    def list_jobs(self, **kwargs):
        self.arguments = kwargs
        return [
            {
                "job_id": uuid4(),
                "company": "Example Co",
                "title": "Backend Engineer",
                "description": "Build APIs",
                "locations": ["Helsinki"],
                "workplace_type": "hybrid",
                "country": "Finland",
                "employment_type": "full-time",
                "opportunity_type": "employment",
                "posted_at": datetime(2026, 9, 5, tzinfo=timezone.utc),
                "updated_at": None,
                "application_url": "https://example.test/apply",
                "source_url": "https://example.test/job",
                "status": "active",
                "source_records": [{
                    "source": "greenhouse",
                    "source_job_id": "123",
                    "source_url": "https://example.test/job",
                    "application_url": "https://example.test/apply",
                }],
                "it_field": "Software Engineering",
                "experience_suitability": "high",
            }
        ], 1


def test_list_jobs_returns_paginated_canonical_jobs(monkeypatch):
    repository = FakeRepository()
    monkeypatch.setattr(jobs_api, "JobRepository", lambda: repository)

    response = client.get(
        "/jobs",
        params={
            "page": 2,
            "page_size": 10,
            "search": "backend",
            "it_field": "Software Engineering",
            "opportunity_type": "employment",
            "experience_suitability": "high",
            "location": "Helsinki",
            "workplace_type": "hybrid",
        },
    )

    assert response.status_code == 200
    assert response.json()["page"] == 2
    assert response.json()["page_size"] == 10
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["application_url"] == "https://example.test/apply"
    assert response.json()["items"][0]["source_records"][0]["source"] == "greenhouse"
    assert repository.arguments["include_inactive"] is False
