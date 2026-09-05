from datetime import datetime, timezone
from uuid import uuid4

from app.canonical_job import CanonicalJob
from app.job_profile_backfill import JobProfileBackfill


def make_job(title: str) -> CanonicalJob:
    return CanonicalJob(
        source="greenhouse",
        source_job_id=title,
        company="Example Co",
        title=title,
        description="Build backend services with Python.",
        application_url=f"https://example.test/{title}",
        source_url=f"https://example.test/{title}",
        raw_source_data={"title": title},
        discovered_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )


class FakeRepository:
    def __init__(self, jobs, existing=None, failing=None):
        self.jobs = jobs
        self.existing = existing or set()
        self.failing = failing or set()
        self.saved = []

    def list_canonical_jobs(self):
        return self.jobs

    def job_profile_exists(self, job_id):
        return job_id in self.existing

    def save_job_profile(self, job_id, profile):
        if job_id in self.failing:
            raise RuntimeError("profile write failed")
        self.saved.append((job_id, profile))


def test_backfill_creates_and_updates_profiles_idempotently():
    first_id = uuid4()
    second_id = uuid4()
    repository = FakeRepository(
        [(first_id, make_job("Backend Engineer")), (second_id, make_job("Data Engineer"))],
        existing={second_id},
    )

    summary = JobProfileBackfill(repository).run()

    assert summary.model_dump() == {
        "processed": 2,
        "created": 1,
        "updated": 1,
        "errors": 0,
    }
    assert len(repository.saved) == 2
    assert repository.saved[0][1].analysis_version == "deterministic-v1"


def test_backfill_isolates_profile_errors():
    failing_id = uuid4()
    good_id = uuid4()
    repository = FakeRepository(
        [(failing_id, make_job("Bad Job")), (good_id, make_job("Backend Engineer"))],
        failing={failing_id},
    )

    summary = JobProfileBackfill(repository).run()

    assert summary.processed == 1
    assert summary.created == 1
    assert summary.updated == 0
    assert summary.errors == 1
