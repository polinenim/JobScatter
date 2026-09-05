from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.canonical_job import CanonicalJob
from app.deduplication import DeduplicatedJob
from app.job_repository import JobRepository, JobStatus
from app.job_profile import JobProfile


class FakeResult:
    def __init__(self, record):
        self.record = record

    def fetchone(self):
        return self.record


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.company_id = uuid4()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if "INSERT INTO companies" in query:
            return FakeResult({"company_id": self.company_id})
        return FakeResult(None)


def make_job(source: str, source_job_id: str, raw_source_data: dict) -> CanonicalJob:
    return CanonicalJob(
        source=source,
        source_job_id=source_job_id,
        company="Example Co",
        title="Software Engineer",
        description="Build reliable software.",
        locations=["New York, NY"],
        salary={"currency": "USD", "min": 100000},
        application_url=f"https://jobs.example.test/{source_job_id}",
        source_url=f"https://source.example.test/{source_job_id}",
        posted_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        discovered_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        raw_source_data=raw_source_data,
    )


def test_save_deduplicated_job_persists_company_job_and_all_source_records():
    first = make_job("greenhouse", "123", {"id": 123})
    second = make_job("lever", "456", {"id": "456"})
    group = DeduplicatedJob(first, (first, second))
    connection = FakeConnection()
    repository = JobRepository(connection_factory=lambda: connection)

    job_id = repository.save_deduplicated_job(group)

    assert isinstance(job_id, UUID)
    assert len(connection.calls) == 4
    assert "INSERT INTO companies" in connection.calls[0][0]
    assert "INSERT INTO canonical_jobs" in connection.calls[1][0]
    assert "INSERT INTO job_source_records" in connection.calls[2][0]
    assert "INSERT INTO job_source_records" in connection.calls[3][0]
    assert connection.calls[1][1][1] == connection.company_id
    assert connection.calls[1][1][16] == JobStatus.UNKNOWN.value
    assert connection.calls[1][1][5].obj == ["New York, NY"]
    assert connection.calls[1][1][10].obj == {"currency": "USD", "min": 100000}
    assert connection.calls[2][1][1] == job_id
    assert connection.calls[2][1][7].obj == {"id": 123}
    assert connection.calls[3][1][7].obj == {"id": "456"}


def test_save_deduplicated_job_persists_requested_status():
    job = make_job("greenhouse", "123", {"id": 123})
    connection = FakeConnection()
    repository = JobRepository(connection_factory=lambda: connection)

    repository.save_deduplicated_job(
        DeduplicatedJob(job, (job,)), status=JobStatus.ACTIVE
    )

    assert connection.calls[1][1][16] == "active"


def test_save_job_profile_upserts_derived_profile_and_versions():
    connection = FakeConnection()
    repository = JobRepository(connection_factory=lambda: connection)
    job_id = uuid4()
    profile = JobProfile(
        it_field="Software Engineering",
        role_family="Backend",
        specific_role="Backend Engineer",
        skills=["Python"],
    )

    repository.save_job_profile(job_id, profile)

    query, params = connection.calls[0]
    assert "INSERT INTO job_profiles" in query
    assert "ON CONFLICT (job_id) DO UPDATE" in query
    assert params[0] == job_id
    assert params[1].obj["role_family"] == "Backend"
    assert params[2] == "deterministic-v1"


def test_repository_reads_stored_canonical_jobs_and_profile_existence():
    job_id = uuid4()
    job = make_job("greenhouse", "123", {"id": 123})

    class ReadConnection(FakeConnection):
        def execute(self, query, params=None):
            self.calls.append((query, params))
            if "DISTINCT ON" in query:
                return type("Result", (), {
                    "fetchall": lambda _: [{
                        "job_id": job_id,
                        "ingestion_record": job.model_dump(mode="json"),
                    }]
                })()
            return FakeResult({"?column?": 1})

    connection = ReadConnection()
    repository = JobRepository(connection_factory=lambda: connection)

    jobs = repository.list_canonical_jobs()
    exists = repository.job_profile_exists(job_id)

    assert jobs == [(job_id, job)]
    assert exists is True


def test_list_jobs_builds_filters_and_null_last_sort():
    connection = FakeConnection()

    class JobsConnection(FakeConnection):
        def execute(self, query, params=None):
            self.calls.append((query, params))
            if "COUNT(*) AS total" in query:
                return FakeResult({"total": 1})
            return type("Result", (), {
                "fetchall": lambda _: [{
                    "job_id": uuid4(),
                    "company": "Example Co",
                    "title": "Backend Engineer",
                    "description": "Build APIs",
                    "locations": ["Helsinki"],
                    "workplace_type": "remote",
                    "country": "Finland",
                    "employment_type": "full-time",
                    "opportunity_type": "employment",
                    "posted_at": None,
                    "updated_at": None,
                    "application_url": "https://example.test/apply",
                    "source_url": "https://example.test/job",
                    "status": "unknown",
                    "source_records": [],
                    "it_field": "Software Engineering",
                    "experience_suitability": "high",
                }]
            })()

    connection = JobsConnection()
    repository = JobRepository(connection_factory=lambda: connection)
    records, total = repository.list_jobs(
        page=1,
        page_size=10,
        search="backend",
        it_field="Software Engineering",
        opportunity_type="employment",
        experience_suitability="high",
        location="Helsinki",
        workplace_type="remote",
    )

    assert total == 1
    assert records[0]["application_url"] == "https://example.test/apply"
    assert "j.status NOT IN ('closed', 'expired')" in connection.calls[0][0]
    assert "ORDER BY j.posted_at DESC NULLS LAST" in connection.calls[1][0]
