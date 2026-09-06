from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.candidate_profile import CandidateProfile, LocationPreferences, TargetRole, WorkPreferences
from app.canonical_job import CanonicalJob
from app.job_profile import ExperienceRequirement, JobProfile
from app.search_service import SearchCandidate, is_eligible, order_results


NOW = datetime(2026, 9, 5, tzinfo=timezone.utc)
CANDIDATE_ID = UUID("00000000-0000-0000-0000-000000000001")


def candidate(**overrides):
    values = {
        "candidate_id": CANDIDATE_ID,
        "version": 1,
        "status": "confirmed",
        "created_at": NOW,
        "target_roles": [TargetRole(title="Software Engineer", role_family="Software Development", it_field="Software Engineering")],
    }
    values.update(overrides)
    return CandidateProfile(**values)


def item(*, title="Software Engineer", profile=None, status="active", posted_at=NOW, country="FI", locations=None):
    job_id = uuid4()
    job = CanonicalJob(
        source="greenhouse",
        source_job_id=str(job_id),
        company="Example Co",
        title=title,
        description="Build reliable software.",
        locations=locations if locations is not None else ["Helsinki"],
        country=country,
        application_url=f"https://jobs.example/{job_id}",
        source_url=f"https://jobs.example/{job_id}",
        raw_source_data={"id": str(job_id)},
        posted_at=posted_at,
        discovered_at=NOW,
    )
    return SearchCandidate(job_id, job, profile or JobProfile(), status)


def test_basic_eligibility_requires_active_posted_role_and_finland_location():
    profile = JobProfile(opportunity_type="internship")
    preferences = candidate(
        location_preferences=LocationPreferences(countries=["Finland"]),
        work_preferences=WorkPreferences(opportunity_types=["internship"]),
    )

    assert is_eligible(preferences, item(profile=profile))
    assert not is_eligible(preferences, item(profile=profile, title="Marketing Manager"))
    assert not is_eligible(preferences, item(profile=profile, country="DE", locations=["Berlin"]))
    assert not is_eligible(preferences, item(profile=profile, status="closed"))
    assert not is_eligible(preferences, item(profile=profile, posted_at=None))
    assert not is_eligible(preferences, item(profile=JobProfile(opportunity_type="full-time")))


def test_search_requires_finland_and_it_relevance():
    assert is_eligible(candidate(target_roles=[]), item(title="Software Engineer"))
    assert not is_eligible(candidate(target_roles=[]), item(title="Sales Associate", country="FI"))
    assert not is_eligible(candidate(target_roles=[]), item(title="Software Engineer", country="US", locations=["New York"]))


def test_senior_titles_are_hard_excluded():
    excluded_titles = [
        "Senior Software Engineer",
        "Lead Data Engineer",
        "Staff Engineer",
        "Principal Engineer",
        "Solutions Architect",
        "Engineering Manager",
        "Director of Engineering",
        "Head of Data",
        "VP Engineering",
        "Chief Technology Officer",
    ]

    for title in excluded_titles:
        assert not is_eligible(candidate(), item(title=title))


def test_early_career_and_neutral_titles_are_allowed():
    allowed_titles = [
        "Software Engineering Intern",
        "Trainee Developer",
        "Graduate Data Analyst",
        "Working Student Software Engineer",
        "Junior Backend Engineer",
        "Entry-Level Developer",
        "New Grad Software Engineer",
        "Associate Software Engineer",
        "Software Engineer",
    ]

    for title in allowed_titles:
        assert is_eligible(candidate(target_roles=[]), item(title=title))


def test_required_experience_and_unknown_or_preferred_requirements():
    assert not is_eligible(candidate(), item(profile=JobProfile(required_experience=ExperienceRequirement(minimum_years=3, required=True))))
    assert is_eligible(candidate(), item(profile=JobProfile(required_experience=ExperienceRequirement(minimum_years=3, required=False))))
    assert is_eligible(candidate(), item(profile=JobProfile()))


def test_order_is_newest_posted_first_with_deterministic_tie_breaking():
    older = item(posted_at=datetime(2026, 9, 1, tzinfo=timezone.utc))
    newer = item(posted_at=datetime(2026, 9, 5, tzinfo=timezone.utc))
    ordered = order_results([older, newer])

    assert ordered == [newer, older]
