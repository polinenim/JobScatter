from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.canonical_job import CanonicalJob


IT_FIELDS = (
    "AI / Machine Learning",
    "Software Engineering",
    "Data",
    "Cloud / DevOps",
    "Cybersecurity",
    "IT / Systems",
    "QA / Testing",
    "Networking",
    "Embedded / IoT",
    "Robotics / Automation",
    "Web / Digital Technology",
    "Enterprise / Business IT",
    "Research / R&D",
    "Technical Product / Solutions",
    "Other IT / Technology",
)

UNKNOWN = "Unknown"


class ExperienceRequirement(BaseModel):
    minimum_years: float | None = None
    required: bool | None = None
    priority: Literal["highest", "high", "suitable/lower", "ineligible", "unknown"] = "unknown"


class JobProfile(BaseModel):
    """Derived intelligence kept separate from the factual CanonicalJob."""

    model_config = ConfigDict(extra="forbid")

    it_field: str = Field(default=UNKNOWN)
    role_family: str = Field(default=UNKNOWN)
    specific_role: str = Field(default=UNKNOWN)
    seniority: str = Field(default=UNKNOWN)
    opportunity_type: str | None = None
    required_experience: ExperienceRequirement = Field(
        default_factory=ExperienceRequirement
    )
    required_languages: list[str] | None = None
    skills: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)
    education_requirements: str | None = None
    workplace_type: str | None = None
    locations: list[str] | None = None
    analysis_version: str = "deterministic-v1"
    model_version: str | None = None


def extract_job_profile(job: CanonicalJob) -> JobProfile:
    text = f"{job.title}\n{job.description}\n{job.responsibilities or ''}"
    title = job.title.strip()
    lowered_title = title.casefold()
    lowered_text = text.casefold()
    it_field, role_family = _classify_field_and_family(lowered_title, lowered_text)

    return JobProfile(
        it_field=it_field,
        role_family=role_family,
        specific_role=_specific_role(title, lowered_title, it_field),
        seniority=_detect_seniority(lowered_title),
        opportunity_type=job.opportunity_type,
        required_experience=_extract_experience(lowered_text),
        required_languages=_extract_languages(lowered_text),
        skills=_extract_skills(lowered_text),
        capabilities=_extract_capabilities(lowered_title, lowered_text),
        education_requirements=_extract_education(lowered_text),
        workplace_type=job.workplace_type,
        locations=job.locations,
    )


def _classify_field_and_family(title: str, text: str) -> tuple[str, str]:
    if _has_any(title, "ai", "machine learning", "ml", "generative ai", "deep learning", "nlp", "computer vision", "llm"):
        if "architect" in title and _has_any(title, "ai", "machine learning", "ml"):
            return "AI / Machine Learning", "AI Architecture"
        if _has_any(title, "research", "scientist") or "research" in text:
            return "AI / Machine Learning", "AI Research"
        if _has_any(title, "mlops", "ai infrastructure"):
            return "AI / Machine Learning", "MLOps/AI Infrastructure"
        if "generative ai" in title or "llm" in title:
            return "AI / Machine Learning", "Generative AI"
        return "AI / Machine Learning", "Machine Learning"
    if _has_any(title, "cybersecurity", "cyber security", "security engineer", "penetration", "soc analyst"):
        return "Cybersecurity", "Cybersecurity"
    if _has_any(title, "data scientist", "data analyst", "data engineer", "analytics", "data"):
        return "Data", "Data Engineering" if "engineer" in title else "Data"
    if _has_any(title, "devops", "platform engineer", "cloud engineer", "site reliability", "sre", "cloud"):
        return "Cloud / DevOps", "DevOps/Platform"
    if _has_any(title, "qa", "quality assurance", "test engineer", "tester"):
        return "QA / Testing", "Testing/Quality"
    if _has_any(title, "network", "networking"):
        return "Networking", "Networking"
    if _has_any(title, "embedded", "firmware", "iot"):
        return "Embedded / IoT", "Embedded Software"
    if _has_any(title, "robotics", "automation engineer"):
        return "Robotics / Automation", "Robotics / Automation"
    if _has_any(title, "frontend", "front-end", "backend", "back-end", "full stack", "software engineer", "software developer", "mobile developer", "mobile engineer"):
        if _has_any(title, "frontend", "front-end"):
            family = "Frontend"
        elif _has_any(title, "backend", "back-end"):
            family = "Backend"
        elif "full stack" in title:
            family = "Full Stack"
        elif "mobile" in title:
            family = "Mobile"
        else:
            family = "Software Development"
        return "Software Engineering", family
    if _has_any(title, "web", "digital"):
        return "Web / Digital Technology", "Web / Digital Technology"
    if _has_any(title, "product manager", "solutions architect", "solutions engineer", "technical product"):
        return "Technical Product / Solutions", "Architecture" if "architect" in title else "Technical Product / Solutions"
    if _has_any(title, "system administrator", "systems administrator", "it support", "it specialist", "systems engineer"):
        return "IT / Systems", "IT / Systems"
    return UNKNOWN, UNKNOWN


def _specific_role(title: str, lowered_title: str, it_field: str) -> str:
    if it_field == UNKNOWN:
        return title
    if "ai solutions architect" in lowered_title:
        return title
    return title


def _detect_seniority(title: str) -> str:
    patterns = (
        ("engineering manager", "Engineering Manager"),
        ("director", "Director"),
        ("head", "Head"),
        ("principal", "Principal"),
        ("staff", "Staff"),
        ("lead", "Lead"),
        ("senior", "Senior"),
    )
    for marker, value in patterns:
        if re.search(rf"\b{re.escape(marker)}\b", title):
            return value
    return UNKNOWN


def _extract_experience(text: str) -> ExperienceRequirement:
    if re.search(r"\b(no experience|0 years?|zero years?)\b", text):
        return ExperienceRequirement(minimum_years=0, required=True, priority="highest")
    match = re.search(r"(?:at least|minimum of|minimum)\s+(\d+(?:\.\d+)?)\s+years?", text)
    if not match:
        return ExperienceRequirement()
    years = float(match.group(1))
    required = "required" in text or "must have" in text or "minimum" in text
    if not required:
        return ExperienceRequirement(minimum_years=years, required=False, priority="unknown")
    if years > 2:
        priority = "ineligible"
    elif years <= 1:
        priority = "high"
    else:
        priority = "suitable/lower"
    return ExperienceRequirement(minimum_years=years, required=True, priority=priority)


def _extract_languages(text: str) -> list[str] | None:
    required = []
    for language in ("finnish", "swedish"):
        if re.search(rf"\b{language}\b\s+(?:is\s+)?(?:required|mandatory|needed)", text):
            required.append(language.title())
    if required:
        return required
    if re.search(r"\benglish\b\s+(?:is\s+)?(?:only|required|mandatory)", text):
        return []
    return None


def _extract_skills(text: str) -> list[str]:
    skills = (
        ("python", "Python"), ("sql", "SQL"), ("pytorch", "PyTorch"),
        ("docker", "Docker"), ("fastapi", "FastAPI"), ("git", "Git"),
        ("postgresql", "PostgreSQL"),
    )
    return [display for marker, display in skills if re.search(rf"\b{re.escape(marker)}\b", text)]


def _extract_capabilities(title: str, text: str) -> list[str]:
    capabilities = []
    rules = (
        ("machine learning", "ML"), ("ml", "ML"), ("nlp", "NLP"),
        ("backend", "Backend development"), ("data engineer", "Data engineering"),
        ("mlops", "MLOps"), ("cloud", "Cloud"),
    )
    for marker, capability in rules:
        if re.search(rf"\b{re.escape(marker)}\b", title) or re.search(rf"\b{re.escape(marker)}\b", text):
            if capability not in capabilities:
                capabilities.append(capability)
    return capabilities


def _extract_education(text: str) -> str | None:
    match = re.search(r"\b((?:bachelor|master|phd|doctorate)[^.;,\n]{0,80})", text)
    return match.group(1).strip() if match else None


def _has_any(value: str, *markers: str) -> bool:
    return any(marker in value for marker in markers)
