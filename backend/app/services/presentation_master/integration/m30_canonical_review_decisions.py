"""Offline reconstruction of Human decisions for M30 AI candidates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable

from .m30_canonical_ai_acquisition import (
    M30CanonicalAIProposalCandidate,
    M30CanonicalSourceRecord,
    validate_m30_canonical_candidate_current_sources,
)
from .production_semantic_contract import SemanticAuthority, SemanticReviewState


class M30CanonicalReviewDecisionError(ValueError):
    """Bounded error category that never contains semantic source content."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


class M30CanonicalReviewAction(str, Enum):
    CONFIRM = "CONFIRM"
    CORRECT = "CORRECT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class M30CanonicalReviewDecision:
    """The only Human-controlled fields accepted by reconstruction."""

    original_candidate_id: str
    action: M30CanonicalReviewAction
    corrected_value: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.original_candidate_id, str) or not self.original_candidate_id.strip():
            raise M30CanonicalReviewDecisionError("INVALID_DECISION")
        if not isinstance(self.action, M30CanonicalReviewAction):
            raise M30CanonicalReviewDecisionError("INVALID_DECISION")
        if self.corrected_value is not None and not isinstance(self.corrected_value, str):
            raise M30CanonicalReviewDecisionError("INVALID_CORRECTION")


def _validate_original(
    candidate: M30CanonicalAIProposalCandidate,
    current_sources: tuple[M30CanonicalSourceRecord, ...],
) -> None:
    if not isinstance(candidate, M30CanonicalAIProposalCandidate):
        raise M30CanonicalReviewDecisionError("INVALID_ORIGINAL_CANDIDATE")
    if (
        candidate.authority != SemanticAuthority.AI_PROPOSED
        or candidate.review_state != SemanticReviewState.UNCONFIRMED
        or candidate.confirmation_authority is not None
        or candidate.inferred is not True
    ):
        raise M30CanonicalReviewDecisionError("INVALID_ORIGINAL_CANDIDATE")
    if not validate_m30_canonical_candidate_current_sources(candidate, current_sources):
        raise M30CanonicalReviewDecisionError("STALE_SOURCE")


def _reviewed_metadata(
    candidate: M30CanonicalAIProposalCandidate,
    review_state: SemanticReviewState,
) -> M30CanonicalAIProposalCandidate:
    return replace(
        candidate,
        authority=SemanticAuthority.USER_EXPLICIT,
        review_state=review_state,
        confirmation_authority=SemanticAuthority.USER_EXPLICIT,
        inferred=True,
    )


def reconstruct_m30_canonical_candidate(
    original_candidate: M30CanonicalAIProposalCandidate,
    decision: M30CanonicalReviewDecision,
    current_sources: Iterable[M30CanonicalSourceRecord],
) -> M30CanonicalAIProposalCandidate:
    """Apply one bounded Human decision to one current AI candidate."""

    if not isinstance(decision, M30CanonicalReviewDecision):
        raise M30CanonicalReviewDecisionError("INVALID_DECISION")
    if decision.original_candidate_id != getattr(original_candidate, "candidate_id", None):
        raise M30CanonicalReviewDecisionError("CANDIDATE_ID_MISMATCH")
    try:
        sources = tuple(current_sources)
    except TypeError as exc:
        raise M30CanonicalReviewDecisionError("PROVENANCE_ERROR") from exc
    _validate_original(original_candidate, sources)

    if decision.action == M30CanonicalReviewAction.CONFIRM:
        if decision.corrected_value is not None:
            raise M30CanonicalReviewDecisionError("INVALID_DECISION")
        return _reviewed_metadata(original_candidate, SemanticReviewState.CONFIRMED)

    if decision.action == M30CanonicalReviewAction.CORRECT:
        if decision.corrected_value is None or not decision.corrected_value.strip():
            raise M30CanonicalReviewDecisionError("INVALID_CORRECTION")
        return _reviewed_metadata(
            replace(original_candidate, value=decision.corrected_value.strip()),
            SemanticReviewState.CORRECTED,
        )

    if decision.corrected_value is not None:
        raise M30CanonicalReviewDecisionError("INVALID_DECISION")
    return replace(original_candidate, review_state=SemanticReviewState.REJECTED)


__all__ = [
    "M30CanonicalReviewAction",
    "M30CanonicalReviewDecision",
    "M30CanonicalReviewDecisionError",
    "reconstruct_m30_canonical_candidate",
]
