from collections.abc import Callable
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.ashby_adapter import AshbyAdapter
from app.canonical_job import normalize_ingestion_record
from app.deduplication import deduplicate_jobs
from app.greenhouse_adapter import GreenhouseAdapter
from app.ingestion_contract import JobIngestionRecord
from app.job_repository import JobRepository
from app.job_profile import extract_job_profile
from app.jobly_adapter import JoblyAdapter
from app.lever_adapter import LeverAdapter
from app.source_registry import SourceRegistryRecord


class IngestionRunSummary(BaseModel):
    fetched: int = 0
    valid: int = 0
    rejected: int = 0
    new: int = 0
    duplicate: int = 0
    updated: int = 0
    errors: int = 0


class IngestionPipeline:
    def __init__(
        self,
        adapter_factory: Callable[[str], Any] = GreenhouseAdapter,
        repository: JobRepository | None = None,
    ) -> None:
        self._adapter_factory = adapter_factory
        self._repository = repository or JobRepository()

    def run_source(self, source: SourceRegistryRecord) -> IngestionRunSummary:
        summary = IngestionRunSummary()
        if not source.enabled:
            return summary
        source_type = source.source_type.casefold()
        if source_type not in {"greenhouse", "lever", "ashby", "jobly"}:
            summary.errors = 1
            return summary

        identifier_key = {"greenhouse": "board_token", "lever": "site", "ashby": "board_name", "jobly": "search_term"}[source_type]
        identifier = source.configuration.get(identifier_key)
        if not isinstance(identifier, str) or not identifier.strip():
            summary.errors = 1
            return summary

        try:
            if source_type == "greenhouse":
                if self._adapter_factory is GreenhouseAdapter:
                    adapter = self._adapter_factory(
                        identifier,
                        max_results=source.configuration.get("max_results"),
                    )
                else:
                    adapter = self._adapter_factory(identifier)
            elif source_type == "lever":
                company_name = source.configuration.get("company_name")
                if not isinstance(company_name, str) or not company_name.strip():
                    summary.errors = 1
                    return summary
                adapter = LeverAdapter(
                    identifier,
                    company_name,
                    source.configuration.get("region", "global"),
                    max_results=source.configuration.get("max_results"),
                )
            else:
                company_name = source.configuration.get("company_name")
                if source_type == "ashby":
                    if not isinstance(company_name, str) or not company_name.strip():
                        summary.errors = 1
                        return summary
                    adapter = AshbyAdapter(
                        identifier,
                        company_name,
                        max_results=source.configuration.get("max_results"),
                    )
                else:
                    adapter = JoblyAdapter(
                        search_term=identifier,
                        location=source.configuration.get("location", "Finland"),
                        max_results=source.configuration.get("max_results", 20),
                    )
            records = list(adapter.fetch_jobs())
        except Exception:
            summary.errors = 1
            return summary

        summary.fetched = len(records)
        normalized = []
        for record in records:
            try:
                if not isinstance(record, JobIngestionRecord):
                    raise TypeError("adapter returned an invalid ingestion record")
                normalized.append(normalize_ingestion_record(record))
                summary.valid += 1
            except Exception:
                summary.rejected += 1

        for group in deduplicate_jobs(normalized):
            try:
                existing_job_id = self._repository.find_matching_job(
                    group.representative
                )
                if existing_job_id is None:
                    job_id = self._repository.save_deduplicated_job(group)
                    self._repository.save_job_profile(
                        job_id, extract_job_profile(group.representative)
                    )
                    summary.new += 1
                    summary.duplicate += max(len(group.source_records) - 1, 0)
                else:
                    self._repository.attach_source_records(
                        existing_job_id, group.source_records
                    )
                    self._repository.save_job_profile(
                        existing_job_id, extract_job_profile(group.representative)
                    )
                    summary.duplicate += len(group.source_records)
                    summary.updated += 1
            except Exception:
                summary.errors += 1

        return summary
