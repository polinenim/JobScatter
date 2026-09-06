from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID

from app.candidate_profile import CandidateProfile
from app.canonical_job import CanonicalJob
from app.job_profile import JobProfile


@dataclass(frozen=True)
class SearchCandidate:
    job_id: UUID
    job: CanonicalJob
    profile: JobProfile
    status: str


def is_eligible(candidate: CandidateProfile, item: SearchCandidate) -> bool:
    if item.status.casefold() != "active" or item.job.posted_at is None:
        return False
    return all((
        _seniority_allowed(item.job.title),
        _finland_it_job(item.job, item.profile),
        _role_matches(candidate, item.job, item.profile),
        _location_matches(candidate, item.job, item.profile),
        _opportunity_matches(candidate, item.profile),
        _experience_eligible(candidate, item.profile),
        _language_matches(candidate, item.profile),
        _required_skills_match(candidate, item.profile),
        _required_capabilities_match(candidate, item.profile),
        _education_matches(candidate, item.profile),
    ))


_IT_TITLE_MARKERS = (
    "software", "developer", "engineering", "engineer", "data", "ai", "machine learning",
    "ml", "cloud", "devops", "cyber", "security", "qa", "test", "network", "web",
    "technology", "technical", "systems", "programmer", "backend", "frontend", "full stack",
)


def _finland_it_job(job: CanonicalJob, profile: JobProfile) -> bool:
    locations = " ".join(job.locations or profile.locations or []).casefold()
    country = (job.country or "").casefold()
    finland = country in {"fi", "finland", "suomi"} or any(
        marker in locations
        for marker in ("finland", "suomi", "helsinki", "espoo", "tampere", "turku", "oulu", "vantaa", "jyvaskyla", "kuopio", "vaasa", "lahti")
    )
    if not finland:
        return False
    if profile.it_field != "Unknown":
        return True
    title = _normalize(job.title)
    return any(marker in title for marker in _IT_TITLE_MARKERS)


_EXCLUDED_SENIORITY_MARKERS = (
    "senior",
    "lead",
    "staff",
    "principal",
    "architect",
    "manager",
    "director",
    "head",
    "vp",
    "chief",
)


def _seniority_allowed(title: str) -> bool:
    normalized_title = _normalize(title)
    return not any(
        re.search(rf"\b{re.escape(marker)}\b", normalized_title)
        for marker in _EXCLUDED_SENIORITY_MARKERS
    )


def order_results(items: list[SearchCandidate]) -> list[SearchCandidate]:
    return sorted(items, key=lambda item: (-item.job.posted_at.timestamp(), str(item.job_id)))


def _role_matches(candidate: CandidateProfile, job: CanonicalJob, profile: JobProfile) -> bool:
    if not candidate.target_roles:
        return True
    title = _normalize(job.title)
    return any(
        (target.title and (_normalize(target.title) in title or _token_overlap(target.title, job.title) >= 0.5))
        or (target.role_family and _normalize(target.role_family) == _normalize(profile.role_family))
        or (target.it_field and _normalize(target.it_field) == _normalize(profile.it_field))
        for target in candidate.target_roles
    )


def _location_matches(candidate: CandidateProfile, job: CanonicalJob, profile: JobProfile) -> bool:
    preferences = candidate.location_preferences
    locations = {_normalize(value) for value in (job.locations or profile.locations or [])}
    country = _normalize(job.country or "")
    if preferences.countries and locations and not any(
        _country_key(value) == _country_key(country)
        or _normalize(value) in country
        or any(_normalize(value) in location or location in _normalize(value) for location in locations)
        for value in preferences.countries
    ):
        return False
    if preferences.cities and locations and not any(
        _normalize(city) in location or location in _normalize(city)
        for city in preferences.cities for location in locations
    ):
        return False
    workplace = profile.workplace_type or job.workplace_type
    return not preferences.workplace_types or not workplace or _normalize(workplace) in {
        _normalize(value) for value in preferences.workplace_types
    }


def _opportunity_matches(candidate: CandidateProfile, profile: JobProfile) -> bool:
    preferences = {_normalize(value) for value in candidate.work_preferences.opportunity_types}
    return not preferences or not profile.opportunity_type or _normalize(profile.opportunity_type) in preferences


def _experience_eligible(candidate: CandidateProfile, profile: JobProfile) -> bool:
    requirement = profile.required_experience
    if requirement.required is not True or requirement.minimum_years is None:
        return True
    if requirement.minimum_years > 2:
        return False
    years = _candidate_experience_years(candidate)
    return years is None or years >= requirement.minimum_years


def _language_matches(candidate: CandidateProfile, profile: JobProfile) -> bool:
    required = {_normalize(value) for value in (profile.required_languages or [])}
    required -= {"english", "englanti"}
    available = {_normalize(language.name) for language in candidate.languages}
    return required.issubset(available)


def _required_skills_match(candidate: CandidateProfile, profile: JobProfile) -> bool:
    available = _candidate_skills(candidate)
    return all(any(skill in value or value in skill for value in available) for skill in map(_normalize, profile.skills))


def _required_capabilities_match(candidate: CandidateProfile, profile: JobProfile) -> bool:
    available = _candidate_capabilities(candidate)
    return all(any(capability in value or value in capability for value in available) for capability in map(_normalize, profile.capabilities))


def _education_matches(candidate: CandidateProfile, profile: JobProfile) -> bool:
    requirement = profile.education_requirements
    if not requirement or not any(marker in _normalize(requirement) for marker in ("required", "must", "mandatory", "needed")):
        return True
    education = " ".join(
        _normalize(" ".join(value for value in (item.degree, item.field_of_study) if value))
        for item in candidate.education
    )
    return any(token in education for token in ("bachelor", "master", "phd", "doctor", "university", "degree"))


def _candidate_skills(candidate: CandidateProfile) -> set[str]:
    values = {_normalize(skill.name) for skill in candidate.skills}
    values.update(_normalize(value) for project in candidate.projects for value in project.technologies)
    values.update(_normalize(value) for experience in candidate.experience for value in experience.skills)
    return {value for value in values if value}


def _candidate_capabilities(candidate: CandidateProfile) -> set[str]:
    values = {_normalize(capability.name) for capability in candidate.capabilities}
    values.update(_normalize(value) for project in candidate.projects for value in project.capabilities)
    values.update(_normalize(value) for experience in candidate.experience for value in experience.capabilities)
    return {value for value in values if value}


def _candidate_experience_years(candidate: CandidateProfile) -> float | None:
    periods: list[tuple[date, date]] = []
    today = datetime.now(timezone.utc).date()
    for experience in candidate.experience:
        if experience.start_date is not None:
            periods.append((experience.start_date, experience.end_date or today))
    if not periods:
        return 0.0
    return sum(max((end - start).days, 0) for start, end in periods) / 365.25


def _country_key(value: str) -> str:
    return {"fi": "finland", "suomi": "finland"}.get(_normalize(value), _normalize(value))


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _token_overlap(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[a-z0-9]+", _normalize(left)))
    right_tokens = set(re.findall(r"[a-z0-9]+", _normalize(right)))
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens) if left_tokens and right_tokens else 0.0
