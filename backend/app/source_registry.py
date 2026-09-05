from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.config import settings

router = APIRouter(prefix="/sources", tags=["source registry"])


class SourceRegistryCreate(BaseModel):
    source_name: str = Field(min_length=1, max_length=255)
    source_type: str = Field(min_length=1, max_length=100)
    access_method: str = Field(min_length=1, max_length=100)
    base_endpoint: str | None = Field(default=None, max_length=2048)
    configuration: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=list)


class SourceRegistryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_name: str | None = Field(default=None, min_length=1, max_length=255)
    source_type: str | None = Field(default=None, min_length=1, max_length=100)
    access_method: str | None = Field(default=None, min_length=1, max_length=100)
    base_endpoint: str | None = Field(default=None, max_length=2048)
    configuration: dict[str, Any] | None = None
    enabled: bool | None = None
    capabilities: list[str] | None = None
    last_successful_run: datetime | None = None
    last_error: dict[str, Any] | None = None


class SourceRegistryRecord(SourceRegistryCreate):
    source_id: UUID
    last_successful_run: datetime | None = None
    last_error: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


def _get_connection():
    return connect(settings.database_url, row_factory=dict_row)


def _database_value(field: str, value: Any) -> Any:
    if field in {"configuration", "capabilities", "last_error"}:
        return Jsonb(value)
    return value


def get_source_record(source_id: UUID) -> SourceRegistryRecord | None:
    with _get_connection() as connection:
        record = connection.execute(
            "SELECT * FROM source_registry WHERE source_id = %s", (source_id,)
        ).fetchone()
    return SourceRegistryRecord.model_validate(record) if record else None


@router.post("", response_model=SourceRegistryRecord, status_code=status.HTTP_201_CREATED)
def create_source(source: SourceRegistryCreate) -> SourceRegistryRecord:
    source_id = uuid4()
    query = """
        INSERT INTO source_registry (
            source_id, source_name, source_type, access_method, base_endpoint,
            configuration, enabled, capabilities
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *
    """
    with _get_connection() as connection:
        record = connection.execute(
            query,
            (
                source_id,
                source.source_name,
                source.source_type,
                source.access_method,
                source.base_endpoint,
                Jsonb(source.configuration),
                source.enabled,
                Jsonb(source.capabilities),
            ),
        ).fetchone()
    return SourceRegistryRecord.model_validate(record)


@router.get("", response_model=list[SourceRegistryRecord])
def list_sources() -> list[SourceRegistryRecord]:
    with _get_connection() as connection:
        records = connection.execute(
            "SELECT * FROM source_registry ORDER BY source_name"
        ).fetchall()
    return [SourceRegistryRecord.model_validate(record) for record in records]


@router.get("/{source_id}", response_model=SourceRegistryRecord)
def get_source(source_id: UUID) -> SourceRegistryRecord:
    source = get_source_record(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceRegistryRecord)
def update_source(source_id: UUID, source: SourceRegistryUpdate) -> SourceRegistryRecord:
    updates = source.model_dump(exclude_unset=True)
    if not updates:
        return get_source(source_id)

    assignments = ", ".join(f"{field} = %s" for field in updates)
    values = [_database_value(field, updates[field]) for field in updates]
    values.append(source_id)
    query = f"""
        UPDATE source_registry
        SET {assignments}, updated_at = NOW()
        WHERE source_id = %s
        RETURNING *
    """
    with _get_connection() as connection:
        record = connection.execute(query, values).fetchone()
    if record is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceRegistryRecord.model_validate(record)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: UUID) -> None:
    with _get_connection() as connection:
        result = connection.execute(
            "DELETE FROM source_registry WHERE source_id = %s", (source_id,)
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Source not found")
