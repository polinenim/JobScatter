from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.candidate_profile import (
    CandidateProfile,
    Experience,
    ExperienceType,
    Proficiency,
)


def test_candidate_profile_supports_structured_sections_and_proficiency():
    profile = CandidateProfile(
        candidate_id=uuid4(),
        version=1,
        created_at=datetime.now(timezone.utc),
        skills=[{"name": "Python", "proficiency": "advanced"}],
        capabilities=[{"name": "Backend development", "proficiency": "expert"}],
        experience=[
            {
                "organization": "Example Co",
                "title": "Research Assistant",
                "experience_type": "research/academic",
            }
        ],
        target_roles=[{"title": "Backend Engineer"}],
        location_preferences={"workplace_types": ["remote"]},
    )

    assert profile.skills[0].proficiency == Proficiency.ADVANCED
    assert profile.capabilities[0].proficiency == Proficiency.EXPERT
    assert profile.experience[0].experience_type == ExperienceType.RESEARCH_ACADEMIC
    assert profile.status == "draft"


def test_candidate_profile_rejects_unknown_experience_type():
    with pytest.raises(ValidationError):
        Experience(
            organization="Example Co",
            title="Engineer",
            experience_type="volunteer",
        )


def test_experience_rejects_end_date_before_start_date():
    with pytest.raises(ValidationError, match="end_date must be on or after start_date"):
        Experience(
            organization="Example Co",
            title="Engineer",
            experience_type=ExperienceType.PROFESSIONAL,
            start_date=date(2025, 2, 1),
            end_date=date(2025, 1, 31),
        )


def test_experience_allows_open_ended_date_range():
    experience = Experience(
        organization="Example Co",
        title="Engineer",
        experience_type=ExperienceType.PROFESSIONAL,
        start_date=date(2025, 2, 1),
    )

    assert experience.end_date is None
