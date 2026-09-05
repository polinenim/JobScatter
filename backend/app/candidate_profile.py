from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Proficiency(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ExperienceType(StrEnum):
    PROFESSIONAL = "professional"
    INTERNSHIP = "internship"
    TRAINEESHIP = "traineeship"
    WORKING_STUDENT = "working-student"
    RESEARCH_ACADEMIC = "research/academic"
    PROJECT = "project"


class Education(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    details: str | None = None


class Skill(BaseModel):
    name: str
    proficiency: Proficiency | None = None


class Capability(BaseModel):
    name: str
    proficiency: Proficiency | None = None


class Project(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class Experience(BaseModel):
    organization: str
    title: str
    experience_type: ExperienceType
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    skills: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)


class Certification(BaseModel):
    name: str
    issuer: str | None = None
    issued_date: date | None = None
    expires_date: date | None = None


class Language(BaseModel):
    name: str
    proficiency: Proficiency | None = None


class TargetRole(BaseModel):
    title: str
    role_family: str | None = None
    it_field: str | None = None


class LocationPreferences(BaseModel):
    countries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    workplace_types: list[Literal["remote", "hybrid", "on-site"]] = Field(
        default_factory=list
    )


class WorkPreferences(BaseModel):
    employment_types: list[str] = Field(default_factory=list)
    opportunity_types: list[str] = Field(default_factory=list)
    availability: str | None = None


class Candidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: UUID
    created_at: datetime
    updated_at: datetime


class CandidateProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: UUID
    version: int = Field(ge=1)
    status: Literal["draft", "confirmed"] = "draft"
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    capabilities: list[Capability] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    target_roles: list[TargetRole] = Field(default_factory=list)
    location_preferences: LocationPreferences = Field(
        default_factory=LocationPreferences
    )
    work_preferences: WorkPreferences = Field(default_factory=WorkPreferences)
    created_at: datetime
    confirmed_at: datetime | None = None
