from datetime import datetime, timezone
from uuid import UUID, uuid4

from psycopg import connect
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.candidate_profile import Candidate, CandidateProfile
from app.config import settings


class CandidateRepository:
    def __init__(self, connection_factory=None) -> None:
        self._connection_factory = connection_factory or self._get_connection

    @staticmethod
    def _get_connection():
        return connect(settings.database_url, row_factory=dict_row)

    def create_candidate(self) -> Candidate:
        candidate_id = uuid4()
        now = datetime.now(timezone.utc)
        with self._connection_factory() as connection:
            connection.execute(
                "INSERT INTO candidates (candidate_id, created_at, updated_at) VALUES (%s, %s, %s)",
                (candidate_id, now, now),
            )
        return Candidate(candidate_id=candidate_id, created_at=now, updated_at=now)

    def save_profile_version(self, profile: CandidateProfile) -> CandidateProfile:
        with self._connection_factory() as connection:
            connection.execute(
                """
                INSERT INTO candidate_profile_versions (
                    candidate_id, version, status, profile, created_at, confirmed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    profile.candidate_id,
                    profile.version,
                    profile.status,
                    Jsonb(profile.model_dump(mode="json")),
                    profile.created_at,
                    profile.confirmed_at,
                ),
            )
        return profile

    def next_profile_version(self, candidate_id: UUID) -> int:
        with self._connection_factory() as connection:
            result = connection.execute(
                """
                SELECT COALESCE(MAX(version), 0) + 1 AS next_version
                FROM candidate_profile_versions
                WHERE candidate_id = %s
                """,
                (candidate_id,),
            ).fetchone()
        return result["next_version"]

    def confirm_profile_version(
        self, candidate_id: UUID, version: int
    ) -> CandidateProfile:
        confirmed_at = datetime.now(timezone.utc)
        with self._connection_factory() as connection:
            result = connection.execute(
                """
                UPDATE candidate_profile_versions
                SET status = 'confirmed', confirmed_at = %s
                WHERE candidate_id = %s AND version = %s AND status = 'draft'
                RETURNING candidate_id, version, status, profile, created_at, confirmed_at
                """,
                (confirmed_at, candidate_id, version),
            ).fetchone()
        if result is None:
            raise ValueError("Profile version is missing or already confirmed")
        return CandidateProfile.model_validate(result["profile"] | {
            "candidate_id": result["candidate_id"],
            "version": result["version"],
            "status": result["status"],
            "created_at": result["created_at"],
            "confirmed_at": result["confirmed_at"],
        })

    def get_confirmed_profile(self, candidate_id: UUID) -> CandidateProfile | None:
        with self._connection_factory() as connection:
            result = connection.execute(
                """
                SELECT candidate_id, version, status, profile, created_at, confirmed_at
                FROM candidate_profile_versions
                WHERE candidate_id = %s AND status = 'confirmed'
                ORDER BY version DESC
                LIMIT 1
                """,
                (candidate_id,),
            ).fetchone()
        if result is None:
            return None
        return CandidateProfile.model_validate(result["profile"] | {
            "candidate_id": result["candidate_id"],
            "version": result["version"],
            "status": result["status"],
            "created_at": result["created_at"],
            "confirmed_at": result["confirmed_at"],
        })
