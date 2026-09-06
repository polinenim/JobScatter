from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.ingestion_pipeline import IngestionPipeline, IngestionRunSummary
from app.source_registry import SourceRegistryRecord, get_source_record

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post(
    "/sources/{source_id}/run",
    response_model=IngestionRunSummary,
)
def run_source_ingestion(source_id: UUID) -> IngestionRunSummary:
    try:
        source = get_source_record(source_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Source Registry is unavailable",
        ) from exc

    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    if not source.enabled:
        raise HTTPException(status_code=409, detail="Source is disabled")
    source_type = source.source_type.casefold()
    if source_type not in {"greenhouse", "lever", "ashby", "jobly"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported source type",
        )

    identifier_key = {"greenhouse": "board_token", "lever": "site", "ashby": "board_name", "jobly": "search_term"}[source_type]
    identifier = source.configuration.get(identifier_key)
    if not isinstance(identifier, str) or not identifier.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                f"Greenhouse source requires configuration.{identifier_key}"
                if source_type == "greenhouse"
                else f"{source_type.title()} source requires configuration.{identifier_key}"
            ),
        )

    try:
        return IngestionPipeline().run_source(source)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingestion run failed",
        ) from exc
