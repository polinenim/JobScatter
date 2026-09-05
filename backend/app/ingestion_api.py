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
    if source.source_type.casefold() != "greenhouse":
        raise HTTPException(
            status_code=400,
            detail="Source type must be greenhouse",
        )

    board_token = source.configuration.get("board_token")
    if not isinstance(board_token, str) or not board_token.strip():
        raise HTTPException(
            status_code=400,
            detail="Greenhouse source requires configuration.board_token",
        )

    try:
        return IngestionPipeline().run_source(source)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingestion run failed",
        ) from exc
