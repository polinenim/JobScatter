from datetime import datetime, timezone
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
