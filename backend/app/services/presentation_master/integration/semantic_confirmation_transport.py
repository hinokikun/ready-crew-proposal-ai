from __future__ import annotations

from typing import Any, Iterable

from app.models import SemanticConfirmationTransportItem

from .production_semantic_contract import (
    ProductionSemanticCandidate,
    ProductionSemanticCandidateSet,
    SemanticItemType,
    SemanticReviewState,
    confirm_candidate,
    correct_candidate,
    reject_candidate,
)


class SemanticConfirmationTransportError(ValueError):
    """Review intent that cannot be safely mapped to a backend candidate."""


def apply_semantic_confirmation_state(
    candidates: ProductionSemanticCandidateSet,
    state: Iterable[SemanticConfirmationTransportItem | dict[str, Any]] | None,
) -> ProductionSemanticCandidateSet:
    if state is None:
        return candidates
    by_id = {candidate.id: candidate for candidate in candidates.candidates}
    seen: set[str] = set()
    updated: list[ProductionSemanticCandidate] = []
    for raw_item in state:
        item = raw_item if isinstance(raw_item, SemanticConfirmationTransportItem) else SemanticConfirmationTransportItem.parse_obj(raw_item)
        if item.id in seen:
            raise SemanticConfirmationTransportError(f"duplicate semantic candidate id: {item.id}")
        seen.add(item.id)
        candidate = by_id.get(item.id)
        if candidate is None:
            raise SemanticConfirmationTransportError(f"unknown semantic candidate id: {item.id}")
        try:
            semantic_type = SemanticItemType(item.semantic_type)
            review_state = SemanticReviewState(item.review_state)
        except ValueError as exc:
            raise SemanticConfirmationTransportError("unsupported semantic transport enum") from exc
        if semantic_type != candidate.semantic_type:
            raise SemanticConfirmationTransportError(f"semantic type mismatch for candidate: {item.id}")
        if review_state == SemanticReviewState.UNCONFIRMED:
            updated.append(candidate)
        elif review_state == SemanticReviewState.CONFIRMED:
            updated.append(confirm_candidate(candidate))
        elif review_state == SemanticReviewState.CORRECTED:
            if not item.value or not item.value.strip():
                raise SemanticConfirmationTransportError(f"corrected value is required for candidate: {item.id}")
            updated.append(correct_candidate(candidate, item.value))
        elif review_state == SemanticReviewState.REJECTED:
            updated.append(reject_candidate(candidate))
        else:
            raise SemanticConfirmationTransportError(f"review state is not admissible: {item.review_state}")
    updated.extend(candidate for candidate in candidates.candidates if candidate.id not in seen)
    return ProductionSemanticCandidateSet(tuple(updated))


__all__ = ["SemanticConfirmationTransportError", "apply_semantic_confirmation_state"]
