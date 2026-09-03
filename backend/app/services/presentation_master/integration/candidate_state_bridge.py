from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from app.models import PptxDownloadRequest, SemanticRelationshipTransportItem

from .production_semantic_contract import (
    ProductionSemanticCandidate,
    ProductionSemanticCandidateSet,
    SemanticAuthority,
    SemanticItemType,
    SemanticReviewState,
)
from app.services.presentation_master.definitions import SUPPORTED_RELATIONSHIP_TYPES
from app.services.presentation_master.upstream_adapter import DerivationLevel, SemanticRelationship
from .shadow_candidate_binding import ShadowCandidateBinding, bind_shadow_candidates


class CandidateStateBridgeError(ValueError):
    """Raised when the optional authoritative candidate transport is malformed."""


@dataclass(frozen=True)
class ProductionShadowCandidateContext:
    """Bounded, typed state reserved for a future Shadow hook."""

    request_id: str
    candidates: ProductionSemanticCandidateSet
    binding: ShadowCandidateBinding
    relationships: tuple[SemanticRelationship, ...] = ()


def build_candidate_state_bridge(
    payload: PptxDownloadRequest,
    *,
    request_id: str,
) -> ProductionShadowCandidateContext | None:
    """Convert the existing structured response transport into future-hook state.

    This is deliberately side-effect free. It does not enqueue Shadow work and
    returns ``None`` for absent, summary, or unconfirmed state.
    """
    if not isinstance(payload, PptxDownloadRequest) or payload.summary:
        return None
    if payload.semantic_candidates is None or payload.semantic_confirmation_state is None:
        return None
    try:
        candidates = candidate_set_from_dict(payload.semantic_candidates)
        binding = bind_shadow_candidates(
            payload,
            request_id=request_id,
            candidates=candidates,
            confirmation_state=payload.semantic_confirmation_state,
        )
    except (TypeError, ValueError, KeyError) as exc:
        raise CandidateStateBridgeError("candidate transport is malformed") from exc
    if binding is None:
        return None
    relationships = relationships_from_transport(payload.semantic_relationships, binding.candidates)
    binding = replace(binding, relationships=relationships)
    return ProductionShadowCandidateContext(
        request_id=request_id,
        candidates=candidates,
        binding=binding,
        relationships=relationships,
    )


def relationships_from_transport(
    raw: list[SemanticRelationshipTransportItem] | None,
    candidates: ProductionSemanticCandidateSet,
) -> tuple[SemanticRelationship, ...]:
    if not raw:
        return ()
    by_id = {candidate.id: candidate for candidate in candidates.candidates}
    relationships: list[SemanticRelationship] = []
    for item in raw:
        if item.relationship_type not in {"causality", "dependency"} or item.relationship_type not in SUPPORTED_RELATIONSHIP_TYPES:
            raise CandidateStateBridgeError("unsupported relationship type")
        if item.from_item == item.to_item or item.from_item not in by_id or item.to_item not in by_id:
            raise CandidateStateBridgeError("relationship endpoint is invalid")
        source = by_id[item.from_item]
        target = by_id[item.to_item]
        if source.review_state not in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED} or target.review_state not in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}:
            raise CandidateStateBridgeError("relationship endpoint is not reviewed")
        if item.review_state not in {"CONFIRMED", "CORRECTED"} or item.authority != SemanticAuthority.USER_EXPLICIT or item.confirmation_authority != SemanticAuthority.USER_EXPLICIT or item.provenance_state != "supplied":
            raise CandidateStateBridgeError("relationship is not explicitly confirmed")
        relationships.append(SemanticRelationship(item.relationship_type, item.from_item, item.to_item, 1.0, item.provenance_state, DerivationLevel.DIRECT, "explicit user-confirmed relationship", False))
    return tuple(relationships)


def candidate_set_from_dict(raw: Any) -> ProductionSemanticCandidateSet:
    """Parse only the existing structured candidate representation."""
    if not isinstance(raw, dict) or not isinstance(raw.get("candidates"), list):
        raise CandidateStateBridgeError("candidate set must contain a candidates list")
    parsed: list[ProductionSemanticCandidate] = []
    for item in raw["candidates"]:
        if not isinstance(item, dict):
            raise CandidateStateBridgeError("candidate must be an object")
        try:
            parsed.append(
                ProductionSemanticCandidate(
                    id=_required_string(item, "id"),
                    semantic_type=SemanticItemType(_required_string(item, "semantic_type")),
                    value=_required_string(item, "value"),
                    source_type=_required_string(item, "source_type"),
                    source_field=_required_string(item, "source_field"),
                    authority=SemanticAuthority(_required_string(item, "authority")),
                    confidence=float(item["confidence"]),
                    review_state=SemanticReviewState(_required_string(item, "review_state")),
                    inferred=bool(item.get("inferred", False)),
                    admissible_as_evidence=bool(item.get("admissible_as_evidence", False)),
                    source_reference=str(item.get("source_reference") or ""),
                    from_item=str(item.get("from_item") or ""),
                    to_item=str(item.get("to_item") or ""),
                    relationship_type=str(item.get("relationship_type") or ""),
                    original_candidate_id=str(item.get("original_candidate_id") or ""),
                    confirmation_authority=(
                        SemanticAuthority(item["confirmation_authority"])
                        if item.get("confirmation_authority")
                        else None
                    ),
                )
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise CandidateStateBridgeError("candidate item is malformed") from exc
    try:
        return ProductionSemanticCandidateSet(tuple(parsed))
    except ValueError as exc:
        raise CandidateStateBridgeError("candidate ids must be unique") from exc


def _required_string(item: dict[str, Any], key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CandidateStateBridgeError(f"candidate field {key} is required")
    return value


__all__ = [
    "CandidateStateBridgeError",
    "ProductionShadowCandidateContext",
    "build_candidate_state_bridge",
    "candidate_set_from_dict",
    "relationships_from_transport",
]
