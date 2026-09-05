from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable
from urllib.parse import urlsplit, urlunsplit

from app.canonical_job import CanonicalJob


@dataclass(frozen=True)
class DeduplicatedJob:
    representative: CanonicalJob
    source_records: tuple[CanonicalJob, ...]


def are_duplicates(left: CanonicalJob, right: CanonicalJob) -> bool:
    """Return True only for strong identity or high-confidence content matches."""
    if _same_source_identity(left, right):
        return True

    left_url = _normalize_url(left.application_url)
    right_url = _normalize_url(right.application_url)
    if left_url and left_url == right_url:
        return True

    return _same_company_high_confidence_match(left, right)


def deduplicate_jobs(jobs: Iterable[CanonicalJob]) -> list[DeduplicatedJob]:
    groups: list[DeduplicatedJob] = []
    for job in jobs:
        matching_group = next(
            (
                group
                for group in groups
                if any(are_duplicates(job, source) for source in group.source_records)
            ),
            None,
        )
        if matching_group is None:
            groups.append(DeduplicatedJob(job, (job,)))
            continue

        groups[groups.index(matching_group)] = DeduplicatedJob(
            matching_group.representative,
            matching_group.source_records + (job,),
        )
    return groups


def _same_source_identity(left: CanonicalJob, right: CanonicalJob) -> bool:
    return (
        _normalize_text(left.source) == _normalize_text(right.source)
        and left.source_job_id == right.source_job_id
    )


def _same_company_high_confidence_match(
    left: CanonicalJob, right: CanonicalJob
) -> bool:
    if _normalize_text(left.company) != _normalize_text(right.company):
        return False
    if not _same_locations(left, right):
        return False
    return (
        _text_similarity(left.title, right.title) >= 0.92
        and _text_similarity(left.description, right.description) >= 0.94
    )


def _same_locations(left: CanonicalJob, right: CanonicalJob) -> bool:
    if not left.locations or not right.locations:
        return False
    return {
        _normalize_text(location) for location in left.locations
    } == {
        _normalize_text(location) for location in right.locations
    }


def _text_similarity(left: str, right: str) -> float:
    left_tokens = sorted(_normalize_text(left).split())
    right_tokens = sorted(_normalize_text(right).split())
    return SequenceMatcher(None, left_tokens, right_tokens).ratio()


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _normalize_url(value: str) -> str:
    cleaned = value.strip()
    try:
        parsed = urlsplit(cleaned)
    except ValueError:
        return cleaned.casefold()
    if not parsed.scheme or not parsed.netloc:
        return cleaned.casefold()
    return urlunsplit(
        (
            parsed.scheme.casefold(),
            parsed.netloc.casefold(),
            parsed.path,
            parsed.query,
            parsed.fragment,
        )
    )
