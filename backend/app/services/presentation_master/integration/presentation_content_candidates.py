"""Generic reviewed presentation-content candidates, before SlotReady conversion."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import json
import re
import unicodedata
from typing import Iterable

from .production_semantic_contract import SemanticAuthority, SemanticReviewState
from .slot_ready_content import (
    SlotReadyDerivationType,
    SlotReadySourceIdentity,
    compute_source_fingerprint,
)


@dataclass(frozen=True)
class PresentationContentField:
    field_role: str
    value: str


@dataclass(frozen=True)
class PresentationContentSourceIdentity:
    source_item_id: str
    semantic_role: str
    value: str


@dataclass(frozen=True)
class PresentationContentCandidate:
    candidate_id: str
    semantic_role: str
    fields: tuple[PresentationContentField, ...]
    source_identities: tuple[PresentationContentSourceIdentity, ...]
    source_fingerprint: str
    derivation_type: SlotReadyDerivationType | str
    authority: SemanticAuthority | str
    review_state: SemanticReviewState | str
    confirmation_authority: SemanticAuthority | str | None


class SlotReadyConversionState(str, Enum):
    CONVERTIBLE = "CONVERTIBLE"
    NOT_CONVERTIBLE_TO_SLOT_READY_V1 = "NOT_CONVERTIBLE_TO_SLOT_READY_V1"


_FINGERPRINT_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).strip().split())


def compute_presentation_content_fingerprint(
    source_identities: Iterable[PresentationContentSourceIdentity],
) -> str:
    """Compute an ordered, aggregate fingerprint of canonical sources only."""

    canonical: list[dict[str, str]] = []
    for source in tuple(source_identities):
        if not isinstance(source, PresentationContentSourceIdentity):
            raise TypeError("source identity must be PresentationContentSourceIdentity")
        if not source.source_item_id.strip() or not source.semantic_role.strip() or not source.value.strip():
            raise ValueError("source identity fields are required")
        canonical.append({
            "source_item_id": _normalize(source.source_item_id),
            "semantic_role": _normalize(source.semantic_role),
            "value": _normalize(source.value),
        })
    encoded = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compute_single_source_slot_ready_fingerprint(
    source: PresentationContentSourceIdentity,
) -> str:
    """Return the existing SlotReady single-source fingerprint for future conversion."""

    return compute_source_fingerprint(SlotReadySourceIdentity(source.source_item_id, source.semantic_role, source.value))


def _enum_value(enum_type: type[Enum], value: object) -> Enum | None:
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        return None


def validate_presentation_content_candidate(candidate: PresentationContentCandidate) -> tuple[str, ...]:
    """Return bounded validation failures without generating or mutating content."""

    if not isinstance(candidate, PresentationContentCandidate):
        return ("candidate must be PresentationContentCandidate",)
    issues: list[str] = []
    if not candidate.candidate_id.strip():
        issues.append("candidate_id is required")
    if not candidate.semantic_role.strip():
        issues.append("semantic_role is required")
    derivation = _enum_value(SlotReadyDerivationType, candidate.derivation_type)
    if derivation is None:
        issues.append("unsupported derivation type")
    authority = _enum_value(SemanticAuthority, candidate.authority)
    if authority is None:
        issues.append("malformed authority")
    review = _enum_value(SemanticReviewState, candidate.review_state)
    if review is None:
        issues.append("unsupported review state")
    confirmation = candidate.confirmation_authority
    if confirmation is not None:
        confirmation = _enum_value(SemanticAuthority, confirmation)
        if confirmation is None:
            issues.append("malformed confirmation authority")
    if not candidate.fields:
        issues.append("at least one presentation field is required")
    field_roles: set[str] = set()
    for field in candidate.fields:
        if not isinstance(field, PresentationContentField):
            issues.append("malformed presentation field")
            continue
        if not field.field_role.strip():
            issues.append("field_role is required")
        elif field.field_role in field_roles:
            issues.append("duplicate presentation field role")
        field_roles.add(field.field_role)
        if not field.value.strip():
            issues.append("presentation field value is required")

    if not candidate.source_identities:
        issues.append("at least one source identity is required")
    source_ids: set[str] = set()
    source_tuples: set[tuple[str, str, str]] = set()
    malformed_source = False
    for source in candidate.source_identities:
        if not isinstance(source, PresentationContentSourceIdentity):
            issues.append("malformed source identity")
            malformed_source = True
            continue
        identity = (source.source_item_id, source.semantic_role, source.value)
        if not source.source_item_id.strip() or not source.semantic_role.strip() or not source.value.strip():
            issues.append("source identity fields are required")
            malformed_source = True
        if source.source_item_id in source_ids:
            issues.append("duplicate source_item_id")
        if identity in source_tuples:
            issues.append("duplicate source identity")
        source_ids.add(source.source_item_id)
        source_tuples.add(identity)
    if not _FINGERPRINT_PATTERN.fullmatch(candidate.source_fingerprint):
        issues.append("source_fingerprint must be 64 lowercase hexadecimal characters")
    if not malformed_source:
        try:
            expected = compute_presentation_content_fingerprint(candidate.source_identities)
        except (TypeError, ValueError):
            expected = None
        if expected is not None and expected != candidate.source_fingerprint:
            issues.append("source fingerprint does not match source identities")

    if confirmation != SemanticAuthority.USER_EXPLICIT:
        issues.append("Human confirmation authority must be USER_EXPLICIT")
    if review not in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}:
        issues.append("presentation candidate is not Human-reviewed")
    if derivation == SlotReadyDerivationType.SEMANTIC_DERIVATION:
        if authority == SemanticAuthority.AI_PROPOSED:
            issues.append("AI_PROPOSED semantic derivation is not admissible")
        if authority != SemanticAuthority.USER_EXPLICIT:
            issues.append("reviewed semantic derivation requires USER_EXPLICIT authority")
    elif authority in {SemanticAuthority.AI_PROPOSED, SemanticAuthority.UNRESOLVED}:
        issues.append("candidate authority is not admissible")
    return tuple(dict.fromkeys(issues))


def validate_presentation_candidate_against_sources(
    candidate: PresentationContentCandidate,
    current_sources: Iterable[PresentationContentSourceIdentity],
) -> tuple[str, ...]:
    issues = list(validate_presentation_content_candidate(candidate))
    current = tuple(current_sources)
    try:
        current_fingerprint = compute_presentation_content_fingerprint(current)
    except (TypeError, ValueError) as exc:
        issues.append(str(exc))
        return tuple(dict.fromkeys(issues))
    if candidate.source_identities != current:
        issues.append("source identities do not match current sources")
    if candidate.source_fingerprint != current_fingerprint:
        issues.append("source fingerprint mismatch")
    return tuple(dict.fromkeys(issues))


def validate_slot_ready_conversion_readiness(
    candidate: PresentationContentCandidate,
    current_sources: Iterable[PresentationContentSourceIdentity],
) -> tuple[SlotReadyConversionState, tuple[str, ...]]:
    issues = list(validate_presentation_candidate_against_sources(candidate, current_sources))
    if len(candidate.source_identities) != 1:
        issues.append("multiple source identities are not convertible to SlotReady V1")
    if issues:
        return SlotReadyConversionState.NOT_CONVERTIBLE_TO_SLOT_READY_V1, tuple(dict.fromkeys(issues))
    return SlotReadyConversionState.CONVERTIBLE, ()


def is_presentation_content_candidate_admissible(
    candidate: PresentationContentCandidate,
    current_sources: Iterable[PresentationContentSourceIdentity] | None = None,
) -> bool:
    issues = (
        validate_presentation_candidate_against_sources(candidate, current_sources)
        if current_sources is not None
        else validate_presentation_content_candidate(candidate)
    )
    return not issues


def confirm_presentation_content_candidate(candidate: PresentationContentCandidate) -> PresentationContentCandidate:
    if candidate.review_state == SemanticReviewState.REJECTED:
        raise ValueError("rejected presentation candidate cannot be confirmed")
    effective_authority = SemanticAuthority.USER_EXPLICIT if candidate.authority == SemanticAuthority.AI_PROPOSED else candidate.authority
    confirmed = replace(candidate, authority=effective_authority, review_state=SemanticReviewState.CONFIRMED, confirmation_authority=SemanticAuthority.USER_EXPLICIT)
    if validate_presentation_content_candidate(confirmed):
        raise ValueError("candidate is not structurally valid for confirmation")
    return confirmed


def correct_presentation_content_candidate(
    candidate: PresentationContentCandidate,
    fields: Iterable[PresentationContentField],
) -> PresentationContentCandidate:
    corrected = replace(
        candidate,
        fields=tuple(fields),
        authority=SemanticAuthority.USER_EXPLICIT if candidate.authority == SemanticAuthority.AI_PROPOSED else candidate.authority,
        review_state=SemanticReviewState.CORRECTED,
        confirmation_authority=SemanticAuthority.USER_EXPLICIT,
    )
    if validate_presentation_content_candidate(corrected):
        raise ValueError("corrected candidate is not structurally valid")
    return corrected


def reject_presentation_content_candidate(candidate: PresentationContentCandidate) -> PresentationContentCandidate:
    return replace(candidate, review_state=SemanticReviewState.REJECTED)


__all__ = [
    "PresentationContentCandidate",
    "PresentationContentField",
    "PresentationContentSourceIdentity",
    "SlotReadyConversionState",
    "compute_presentation_content_fingerprint",
    "compute_single_source_slot_ready_fingerprint",
    "confirm_presentation_content_candidate",
    "correct_presentation_content_candidate",
    "is_presentation_content_candidate_admissible",
    "reject_presentation_content_candidate",
    "validate_presentation_candidate_against_sources",
    "validate_presentation_content_candidate",
    "validate_slot_ready_conversion_readiness",
]
