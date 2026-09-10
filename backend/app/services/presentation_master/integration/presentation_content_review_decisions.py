"""Stateless, backend-owned reconstruction of reviewed presentation candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable

from .presentation_content_candidates import (
    PresentationContentCandidate,
    PresentationContentField,
    SemanticReviewState,
    confirm_presentation_content_candidate,
    correct_presentation_content_candidate,
    reject_presentation_content_candidate,
    validate_presentation_candidate_against_sources,
    validate_presentation_content_candidate,
)
from .production_semantic_contract import SemanticAuthority
from .slot_ready_content import SlotReadyDerivationType


class PresentationContentReviewAction(str, Enum):
    CONFIRM = "CONFIRM"
    CORRECT = "CORRECT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class PresentationContentReviewDecision:
    """The only user-controlled inputs accepted by reconstruction."""

    original_candidate_id: str
    action: PresentationContentReviewAction
    corrected_fields: tuple[PresentationContentField, ...] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.original_candidate_id, str) or not self.original_candidate_id.strip():
            raise ValueError("INVALID_DECISION")
        if not isinstance(self.action, PresentationContentReviewAction):
            raise ValueError("INVALID_DECISION")
        if self.corrected_fields is not None and not isinstance(self.corrected_fields, tuple):
            raise TypeError("corrected_fields must be a tuple or None")


def _original_validation_probe(candidate: PresentationContentCandidate) -> PresentationContentCandidate:
    """Validate an AI candidate with the frozen reviewed-candidate validator."""

    return replace(
        candidate,
        authority=SemanticAuthority.USER_EXPLICIT,
        review_state=SemanticReviewState.CONFIRMED,
        confirmation_authority=SemanticAuthority.USER_EXPLICIT,
    )


def _validate_original(
    candidate: PresentationContentCandidate,
    current_sources: tuple,
) -> None:
    if not isinstance(candidate, PresentationContentCandidate):
        raise ValueError("INVALID_ORIGINAL_CANDIDATE")
    if (
        candidate.authority != SemanticAuthority.AI_PROPOSED
        or candidate.review_state != SemanticReviewState.UNCONFIRMED
        or candidate.confirmation_authority is not None
        or candidate.derivation_type != SlotReadyDerivationType.SEMANTIC_DERIVATION
    ):
        raise ValueError("INVALID_ORIGINAL_CANDIDATE")

    probe = _original_validation_probe(candidate)
    structural_issues = validate_presentation_content_candidate(probe)
    if structural_issues:
        raise ValueError("INVALID_ORIGINAL_CANDIDATE")
    source_issues = validate_presentation_candidate_against_sources(probe, current_sources)
    if source_issues:
        if "source identities do not match current sources" in source_issues or "source fingerprint mismatch" in source_issues:
            raise ValueError("STALE_SOURCE")
        raise ValueError("INVALID_ORIGINAL_CANDIDATE")


def _ordered_corrected_fields(
    original: PresentationContentCandidate,
    corrected_fields: tuple[PresentationContentField, ...] | None,
) -> tuple[PresentationContentField, ...]:
    if corrected_fields is None:
        raise ValueError("INVALID_CORRECTION_FIELDS")
    if any(not isinstance(field, PresentationContentField) for field in corrected_fields):
        raise ValueError("INVALID_CORRECTION_FIELDS")
    original_roles = tuple(field.field_role for field in original.fields)
    corrected_roles = tuple(field.field_role for field in corrected_fields)
    if any(not field.field_role.strip() or not field.value.strip() for field in corrected_fields):
        raise ValueError("INVALID_CORRECTION_FIELDS")
    if len(set(corrected_roles)) != len(corrected_roles) or set(corrected_roles) != set(original_roles):
        raise ValueError("INVALID_CORRECTION_FIELDS")
    by_role = {field.field_role: field for field in corrected_fields}
    return tuple(by_role[role] for role in original_roles)


def reconstruct_presentation_content_candidate(
    original_candidate: PresentationContentCandidate,
    decision: PresentationContentReviewDecision,
    current_sources: Iterable,
) -> PresentationContentCandidate:
    """Rebuild a reviewed candidate from an original AI candidate and a decision.

    The function is stateless: source metadata and review authority come from the
    original candidate and frozen transition helpers, never from the decision.
    """

    if not isinstance(decision, PresentationContentReviewDecision):
        raise ValueError("INVALID_DECISION")
    if decision.original_candidate_id != getattr(original_candidate, "candidate_id", None):
        raise ValueError("CANDIDATE_ID_MISMATCH")
    sources = tuple(current_sources)
    _validate_original(original_candidate, sources)

    if decision.action == PresentationContentReviewAction.CONFIRM:
        if decision.corrected_fields is not None:
            raise ValueError("INVALID_DECISION")
        return confirm_presentation_content_candidate(original_candidate)

    if decision.action == PresentationContentReviewAction.CORRECT:
        fields = _ordered_corrected_fields(original_candidate, decision.corrected_fields)
        return correct_presentation_content_candidate(original_candidate, fields)

    if decision.corrected_fields is not None:
        raise ValueError("INVALID_DECISION")
    return reject_presentation_content_candidate(original_candidate)


__all__ = [
    "PresentationContentReviewAction",
    "PresentationContentReviewDecision",
    "reconstruct_presentation_content_candidate",
]
