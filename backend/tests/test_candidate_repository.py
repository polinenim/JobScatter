from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.candidate_profile import CandidateProfile
from app.candidate_repository import CandidateRepository


class FakeResult:
    def __init__(self, record=None):
        self.record = record

    def fetchone(self):
        return self.record


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.candidate_id = uuid4()
        self.profile_id = self.candidate_id
        self.confirmed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.calls.append((query, params))
        if "MAX(version)" in query:
            return FakeResult({"next_version": 2})
        if "SELECT candidate_id, version, status, profile" in query:
            return FakeResult({
                "candidate_id": self.profile_id,
                "version": 2,
                "status": "confirmed",
                "profile": {"candidate_id": str(self.profile_id), "version": 2},
                "created_at": datetime.now(timezone.utc),
                "confirmed_at": datetime.now(timezone.utc),
            })
        if "RETURNING candidate_id" in query:
            if self.confirmed:
                return FakeResult(None)
            self.confirmed = True
            return FakeResult({
                "candidate_id": self.profile_id,
                "version": 1,
                "status": "confirmed",
                "profile": {"candidate_id": str(self.profile_id), "version": 1},
                "created_at": datetime.now(timezone.utc),
                "confirmed_at": datetime.now(timezone.utc),
            })
        return FakeResult()


def test_profile_versions_are_inserted_and_versioned():
    connection = FakeConnection()
    repository = CandidateRepository(connection_factory=lambda: connection)
    profile = CandidateProfile(
        candidate_id=connection.candidate_id,
        version=1,
        created_at=datetime.now(timezone.utc),
    )

    saved = repository.save_profile_version(profile)

    assert saved == profile
    assert "INSERT INTO candidate_profile_versions" in connection.calls[0][0]
    assert repository.next_profile_version(connection.candidate_id) == 2
    assert connection.calls[1][1] == (connection.candidate_id,)


def test_confirmed_profile_version_can_be_confirmed_once():
    connection = FakeConnection()
    repository = CandidateRepository(connection_factory=lambda: connection)

    confirmed = repository.confirm_profile_version(connection.profile_id, 1)

    assert confirmed.status == "confirmed"
    with pytest.raises(ValueError):
        repository.confirm_profile_version(connection.profile_id, 1)


def test_latest_confirmed_profile_can_be_loaded():
    connection = FakeConnection()
    repository = CandidateRepository(connection_factory=lambda: connection)

    profile = repository.get_confirmed_profile(connection.profile_id)

    assert profile is not None
    assert profile.version == 2
    assert profile.status == "confirmed"
