from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from app.candidate_profile import CandidateProfile
from app.candidate_repository import CandidateRepository
from app.canonical_job import CanonicalJob
from app.job_profile import JobProfile
from app.job_repository import JobRepository
from app.pdf_report import generate_job_report
from app.search_service import SearchCandidate, is_eligible, order_results
from app.ingestion_pipeline import IngestionPipeline
from app.source_registry import list_sources
import logging
router = APIRouter(tags=["search"])


class UnifiedSearchRequest(BaseModel):
    candidate_id: UUID


class UnifiedSearchResult(BaseModel):
    company_name: str
    job_title: str
    posted_at: datetime
    job_link: str


class UnifiedSearchResponse(BaseModel):
    candidate_id: UUID
    items: list[UnifiedSearchResult]
    total: int


class UnifiedSearchService:
    def __init__(
        self,
        candidate_repository: CandidateRepository | None = None,
        job_repository: JobRepository | None = None,
    ) -> None:
        self.candidate_repository = candidate_repository or CandidateRepository()
        self.job_repository = job_repository or JobRepository()

    def run(self, candidate_id: UUID) -> UnifiedSearchResponse:
        candidate = self.candidate_repository.get_confirmed_profile(candidate_id)
        if candidate is None:
            raise LookupError("Confirmed candidate profile not found")

        matches: list[SearchCandidate] = []
        for row in self.job_repository.list_search_candidates():
            item = _to_search_candidate(row)
            if is_eligible(candidate, item):
                matches.append(item)

        results = [_to_result(item) for item in order_results(matches)]
        return UnifiedSearchResponse(
            candidate_id=candidate_id,
            items=results,
            total=len(results),
        )


class FetchService:
    """Refresh enabled sources, then reuse the database-only search service."""

    def __init__(
        self,
        source_loader=list_sources,
        pipeline_factory=IngestionPipeline,
        search_service_factory=UnifiedSearchService,
    ) -> None:
        self.source_loader = source_loader
        self.pipeline_factory = pipeline_factory
        self.search_service_factory = search_service_factory

    def run(self, candidate_id: UUID) -> UnifiedSearchResponse:
        pipeline = self.pipeline_factory()
        for source in self.source_loader():
            if source.enabled:
                pipeline.run_source(source)
        return self.search_service_factory().run(candidate_id)


@router.post("/search", response_model=UnifiedSearchResponse)
def unified_search(request: UnifiedSearchRequest) -> UnifiedSearchResponse:
    try:
        return UnifiedSearchService().run(request.candidate_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unified search failed",
        ) from exc


@router.post("/fetch", response_model=UnifiedSearchResponse)
def fetch_and_search(request: UnifiedSearchRequest) -> UnifiedSearchResponse:
    try:
        return FetchService().run(request.candidate_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logging.exception("Fetch and search failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fetch and search failed",
        ) from exc


@router.post("/search/pdf", response_class=Response)
def search_pdf(request: UnifiedSearchRequest) -> Response:
    try:
        results = UnifiedSearchService().run(request.candidate_id)
        pdf = generate_job_report(results.items)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=jobscatter-report.pdf"},
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        logging.exception("Fetch and search failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fetch and search failed",
        ) from exc


def _to_search_candidate(row: dict) -> SearchCandidate:
    job = CanonicalJob(
        source=row.get("source") or "unknown",
        source_job_id=str(row.get("source_job_id") or row["job_id"]),
        company=row["company"],
        title=row["title"],
        description=row.get("description"),
        responsibilities=row.get("responsibilities"),
        locations=row.get("locations"),
        workplace_type=row.get("workplace_type"),
        country=row.get("country"),
        employment_type=row.get("employment_type"),
        opportunity_type=row.get("opportunity_type"),
        posted_at=row.get("posted_at"),
        updated_at=row.get("updated_at"),
        salary=None,
        application_url=row["application_url"],
        source_url=row["source_url"],
        raw_source_data=row.get("raw_source_data"),
        discovered_at=row["discovered_at"],
    )
    profile = JobProfile.model_validate(row.get("job_profile") or {})
    return SearchCandidate(
        job_id=row["job_id"],
        job=job,
        profile=profile,
        status=row.get("status", "unknown"),
    )


def _to_result(item: SearchCandidate) -> UnifiedSearchResult:
    return UnifiedSearchResult(
        company_name=item.job.company,
        job_title=item.job.title,
        posted_at=item.job.posted_at,
        job_link=item.job.application_url or item.job.source_url,
    )
