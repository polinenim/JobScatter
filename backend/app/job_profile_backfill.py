from collections.abc import Iterable
from uuid import UUID

from pydantic import BaseModel

from app.canonical_job import CanonicalJob
from app.job_profile import extract_job_profile
from app.job_repository import JobRepository


class JobProfileBackfillSummary(BaseModel):
    processed: int = 0
    created: int = 0
    updated: int = 0
    errors: int = 0


class JobProfileBackfill:
    def __init__(self, repository: JobRepository | None = None) -> None:
        self._repository = repository or JobRepository()

    def run(self) -> JobProfileBackfillSummary:
        summary = JobProfileBackfillSummary()
        try:
            jobs = self._repository.list_canonical_jobs()
        except Exception:
            summary.errors = 1
            return summary

        for job_id, job in jobs:
            try:
                profile = extract_job_profile(job)
                existed = self._repository.job_profile_exists(job_id)
                self._repository.save_job_profile(job_id, profile)
                summary.processed += 1
                if existed:
                    summary.updated += 1
                else:
                    summary.created += 1
            except Exception:
                summary.errors += 1
        return summary
