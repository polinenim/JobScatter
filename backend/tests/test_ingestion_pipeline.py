from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.ingestion_contract import JobIngestionRecord
from app.ingestion_pipeline import IngestionPipeline
from app.source_registry import SourceRegistryRecord


class FakeAdapter:
    def __init__(self, records):
        self.records = records

    def fetch_jobs(self):
        return self.records


class FakeRepository:
    def __init__(self, existing_source_job_ids=None, failing_source_job_ids=None):
        self.existing_source_job_ids = existing_source_job_ids or set()
        self.failing_source_job_ids = failing_source_job_ids or set()
        self.saved = []
        self.attached = []
        self.profiles = []

    def find_matching_job(self, candidate):
        if candidate.source_job_id in self.existing_source_job_ids:
            return UUID("00000000-0000-0000-0000-000000000001")
        return None

    def save_deduplicated_job(self, group):
        if group.representative.source_job_id in self.failing_source_job_ids:
            raise RuntimeError("persistence failure")
        self.saved.append(group)
        return uuid4()

    def attach_source_records(self, job_id, source_records):
        self.attached.append((job_id, source_records))

    def save_job_profile(self, job_id, profile):
        self.profiles.append((job_id, profile))


def make_record(source_job_id, application_url=None):
    return JobIngestionRecord(
        source="greenhouse",
        source_job_id=source_job_id,
        company="Example Co",
        title="Software Engineer",
        description="Build reliable software.",
        application_url=application_url or f"https://jobs.example.test/{source_job_id}",
        source_url=f"https://source.example.test/{source_job_id}",
        raw_source_data={"id": source_job_id},
        discovered_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
    )


def make_source(enabled=True, configuration=None):
    now = datetime(2026, 9, 5, tzinfo=timezone.utc)
    source_configuration = (
        {"board_token": "example-board"}
        if configuration is None
        else configuration
    )
    return SourceRegistryRecord(
        source_id=uuid4(),
        source_name="Example Greenhouse",
        source_type="greenhouse",
        access_method="api",
        configuration=source_configuration,
        enabled=enabled,
        capabilities=[],
        created_at=now,
        updated_at=now,
    )


def test_pipeline_connects_adapter_normalization_deduplication_and_persistence():
    records = [
        make_record("new-1", "https://jobs.example.test/new"),
        make_record("new-2", "https://jobs.example.test/new"),
        make_record("existing-1"),
        object(),
    ]
    repository = FakeRepository(existing_source_job_ids={"existing-1"})
    tokens = []

    def adapter_factory(board_token):
        tokens.append(board_token)
        return FakeAdapter(records)

    summary = IngestionPipeline(adapter_factory, repository).run_source(make_source())

    assert tokens == ["example-board"]
    assert summary.model_dump() == {
        "fetched": 4,
        "valid": 3,
        "rejected": 1,
        "new": 1,
        "duplicate": 2,
        "updated": 1,
        "errors": 0,
    }
    assert len(repository.saved) == 1
    assert len(repository.attached) == 1
    assert len(repository.profiles) == 2
    assert repository.profiles[0][1].analysis_version == "deterministic-v1"


def test_pipeline_isolates_persistence_failure_and_continues():
    records = [make_record("bad"), make_record("good")]
    repository = FakeRepository(failing_source_job_ids={"bad"})

    summary = IngestionPipeline(
        lambda _: FakeAdapter(records), repository
    ).run_source(make_source())

    assert summary.new == 1
    assert summary.errors == 1
    assert len(repository.saved) == 1
    assert repository.saved[0].representative.source_job_id == "good"
    assert len(repository.profiles) == 1


def test_pipeline_does_not_process_disabled_source():
    called = False

    def adapter_factory(_):
        nonlocal called
        called = True
        return FakeAdapter([])

    summary = IngestionPipeline(adapter_factory, FakeRepository()).run_source(
        make_source(enabled=False)
    )

    assert summary.model_dump() == {
        "fetched": 0,
        "valid": 0,
        "rejected": 0,
        "new": 0,
        "duplicate": 0,
        "updated": 0,
        "errors": 0,
    }
    assert called is False


def test_pipeline_reports_missing_board_token():
    summary = IngestionPipeline(lambda _: FakeAdapter([]), FakeRepository()).run_source(
        make_source(configuration={})
    )

    assert summary.errors == 1
    assert summary.fetched == 0
