from datetime import datetime, timezone
from uuid import uuid4

from app.cv_extraction_repository import (
    CandidateProfileDraft,
    CvExtractionRepository,
    DraftValidationStatus,
    ExtractionJobStatus,
)


class FakeResult:
    def __init__(self, record=None):
        self.record = record

    def fetchone(self):
        return self.record


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.job_id = uuid4()
        self.candidate_id = uuid4()
        self.draft_id = uuid4()
        self.now = datetime(2026, 9, 5, tzinfo=timezone.utc)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if "cv_extraction_jobs" in query and "UPDATE" not in query and "SELECT" not in query:
            return FakeResult({
                "job_id": self.job_id,
                "candidate_id": self.candidate_id,
                "status": "queued",
                "error_info": None,
                "created_at": self.now,
                "started_at": None,
                "completed_at": None,
                "model_name": "test-model",
                "model_version": "v1",
            })
        if "candidate_profile_drafts" in query:
            return FakeResult({
                "draft_id": self.draft_id,
                "candidate_id": self.candidate_id,
                "extraction_job_id": self.job_id,
                "structured_draft": {"skills": [{"name": "Python"}]},
                "validation_status": "pending",
                "model_name": "test-model",
                "model_version": "v1",
                "created_at": self.now,
            })
        if "UPDATE cv_extraction_jobs" in query:
            return FakeResult({
                "job_id": self.job_id,
                "candidate_id": self.candidate_id,
                "status": "failed",
                "error_info": {"message": "validation failed"},
                "created_at": self.now,
                "started_at": self.now,
                "completed_at": self.now,
                "model_name": "test-model",
                "model_version": "v1",
            })
        if "SELECT * FROM cv_extraction_jobs" in query:
            return FakeResult({
                "job_id": self.job_id,
                "candidate_id": self.candidate_id,
                "status": "queued",
                "error_info": None,
                "created_at": self.now,
                "started_at": None,
                "completed_at": None,
                "model_name": "test-model",
                "model_version": "v1",
            })
        if "SELECT * FROM candidate_profile_drafts" in query:
            return FakeResult({
                "draft_id": self.draft_id,
                "candidate_id": self.candidate_id,
                "extraction_job_id": self.job_id,
                "structured_draft": {"skills": [{"name": "Python"}]},
                "validation_status": "pending",
                "model_name": "test-model",
                "model_version": "v1",
                "created_at": self.now,
            })
        return FakeResult(None)


def test_repository_persists_extraction_job_and_draft_without_pdf_data():
    connection = FakeConnection()
    repository = CvExtractionRepository(connection_factory=lambda: connection)

    job = repository.create_extraction_job(
        connection.candidate_id, model_name="test-model", model_version="v1"
    )
    updated = repository.update_extraction_job(
        job.job_id,
        ExtractionJobStatus.FAILED,
        error_info={"message": "validation failed"},
        started_at=connection.now,
        completed_at=connection.now,
    )
    draft = repository.create_profile_draft(
        connection.candidate_id,
        job.job_id,
        {"skills": [{"name": "Python"}]},
        DraftValidationStatus.PENDING,
        model_name="test-model",
        model_version="v1",
    )
    read_job = repository.get_extraction_job(job.job_id)
    read_draft = repository.get_profile_draft(draft.draft_id)

    assert job.status == ExtractionJobStatus.QUEUED
    assert updated.status == ExtractionJobStatus.FAILED
    assert draft.structured_draft == {"skills": [{"name": "Python"}]}
    assert read_job is not None
    assert read_draft is not None
    assert isinstance(draft, CandidateProfileDraft)
    assert all("pdf" not in query.lower() for query, _ in connection.calls)
    assert connection.calls[2][1][3].obj == {"skills": [{"name": "Python"}]}
