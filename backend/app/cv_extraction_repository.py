from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict
from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.config import settings


class ExtractionJobStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DraftValidationStatus(StrEnum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"


class ExtractionJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    candidate_id: UUID
    status: ExtractionJobStatus
    error_info: dict[str, Any] | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    model_name: str | None = None
    model_version: str | None = None


class CandidateProfileDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: UUID
    candidate_id: UUID
    extraction_job_id: UUID
    structured_draft: dict[str, Any]
    validation_status: DraftValidationStatus
    model_name: str | None = None
    model_version: str | None = None
    created_at: datetime


class CvExtractionRepository:
    def __init__(self, connection_factory=None) -> None:
        self._connection_factory = connection_factory or self._get_connection

    @staticmethod
    def _get_connection():
        return connect(settings.database_url, row_factory=dict_row)

    def create_extraction_job(
        self,
        candidate_id: UUID,
        model_name: str | None = None,
        model_version: str | None = None,
    ) -> ExtractionJob:
        job_id = uuid4()
        with self._connection_factory() as connection:
            record = connection.execute(
                """
                INSERT INTO cv_extraction_jobs (
                    job_id, candidate_id, status, model_name, model_version
                )
                VALUES (%s, %s, 'queued', %s, %s)
                RETURNING *
                """,
                (job_id, candidate_id, model_name, model_version),
            ).fetchone()
        return ExtractionJob.model_validate(record)

    def update_extraction_job(
        self,
        job_id: UUID,
        status: ExtractionJobStatus,
        error_info: dict[str, Any] | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> ExtractionJob:
        with self._connection_factory() as connection:
            record = connection.execute(
                """
                UPDATE cv_extraction_jobs
                SET status = %s,
                    error_info = %s,
                    started_at = COALESCE(%s, started_at),
                    completed_at = COALESCE(%s, completed_at)
                WHERE job_id = %s
                RETURNING *
                """,
                (
                    status.value,
                    Jsonb(error_info) if error_info is not None else None,
                    started_at,
                    completed_at,
                    job_id,
                ),
            ).fetchone()
        if record is None:
            raise ValueError("Extraction job not found")
        return ExtractionJob.model_validate(record)

    def get_extraction_job(self, job_id: UUID) -> ExtractionJob | None:
        with self._connection_factory() as connection:
            record = connection.execute(
                "SELECT * FROM cv_extraction_jobs WHERE job_id = %s", (job_id,)
            ).fetchone()
        return ExtractionJob.model_validate(record) if record else None

    def create_profile_draft(
        self,
        candidate_id: UUID,
        extraction_job_id: UUID,
        structured_draft: dict[str, Any],
        validation_status: DraftValidationStatus = DraftValidationStatus.PENDING,
        model_name: str | None = None,
        model_version: str | None = None,
    ) -> CandidateProfileDraft:
        draft_id = uuid4()
        with self._connection_factory() as connection:
            record = connection.execute(
                """
                INSERT INTO candidate_profile_drafts (
                    draft_id, candidate_id, extraction_job_id, structured_draft,
                    validation_status, model_name, model_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    draft_id,
                    candidate_id,
                    extraction_job_id,
                    Jsonb(structured_draft),
                    validation_status.value,
                    model_name,
                    model_version,
                ),
            ).fetchone()
        return CandidateProfileDraft.model_validate(record)

    def get_profile_draft(self, draft_id: UUID) -> CandidateProfileDraft | None:
        with self._connection_factory() as connection:
            record = connection.execute(
                "SELECT * FROM candidate_profile_drafts WHERE draft_id = %s",
                (draft_id,),
            ).fetchone()
        return CandidateProfileDraft.model_validate(record) if record else None
