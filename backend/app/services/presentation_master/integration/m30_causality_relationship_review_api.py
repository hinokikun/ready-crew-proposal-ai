"""Thin authenticated API boundary for stateless M30 relationship review."""

from __future__ import annotations

from enum import Enum
from typing import Callable

from pydantic import BaseModel, Field

from .m30_canonical_ai_acquisition import (
    M30CanonicalAIProposalCandidate,
    M30CanonicalSourceIdentity,
    M30CanonicalSourceRecord,
)
from .m30_causality_relationship_ai_proposals import M30CausalityRelationshipAIProposal
from .m30_causality_relationship_review_decisions import (
    M30CausalityRelationshipReviewAction,
    M30CausalityRelationshipReviewDecision,
    M30ReviewedCausalityRelationship,
    reconstruct_m30_causality_relationship,
)
from .production_semantic_contract import SemanticAuthority, SemanticReviewState


class _SourceIdentityRequest(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=160)
    source_field: str = Field(..., min_length=1, max_length=160)
    source_reference: str = Field(..., min_length=1, max_length=240)

    class Config:
        extra = "forbid"


class _SourceRequest(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=160)
    source_field: str = Field(..., min_length=1, max_length=160)
    value: str = Field(..., min_length=1, max_length=4000)
    source_reference: str = Field(..., min_length=1, max_length=240)

    class Config:
        extra = "forbid"


class _ReviewedNodeRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=240)
    semantic_role: str = Field(..., min_length=1, max_length=64)
    value: str = Field(..., min_length=1, max_length=4000)
    source_type: str = Field(..., min_length=1, max_length=80)
    source_field: str = Field(..., min_length=1, max_length=160)
    source_reference: str = Field(..., min_length=1, max_length=240)
    source_references: list[str] = Field(..., min_items=1, max_items=32)
    source_identities: list[_SourceIdentityRequest] = Field(..., min_items=1, max_items=32)
    source_fingerprint: str = Field(..., min_length=64, max_length=64)
    authority: str = Field(..., min_length=1, max_length=64)
    review_state: str = Field(..., min_length=1, max_length=32)
    confirmation_authority: str | None = Field(None, max_length=64)
    inferred: bool
    acquisition_revision: str = Field(..., min_length=1, max_length=32)
    original_candidate_id: str | None = Field(None, max_length=240)

    class Config:
        extra = "forbid"


class _OriginalRelationshipRequest(BaseModel):
    relationship_id: str = Field(..., min_length=1, max_length=240)
    from_id: str = Field(..., min_length=1, max_length=240)
    to_id: str = Field(..., min_length=1, max_length=240)
    relationship_type: str = Field(..., min_length=1, max_length=64)
    authority: str = Field(..., min_length=1, max_length=64)
    review_state: str = Field(..., min_length=1, max_length=32)
    confirmation_authority: str | None = Field(None, max_length=64)
    inferred: bool
    provenance: str = Field(..., min_length=1, max_length=160)

    class Config:
        extra = "forbid"


class _ReviewedRelationshipRequest(BaseModel):
    relationship_id: str = Field(..., min_length=1, max_length=240)
    original_relationship_id: str = Field(..., min_length=1, max_length=240)
    from_id: str = Field(..., min_length=1, max_length=240)
    to_id: str = Field(..., min_length=1, max_length=240)
    relationship_type: str = Field(..., min_length=1, max_length=64)
    authority: str = Field(..., min_length=1, max_length=64)
    review_state: str = Field(..., min_length=1, max_length=32)
    confirmation_authority: str | None = Field(None, max_length=64)
    inferred: bool
    provenance: str = Field(..., min_length=1, max_length=160)

    class Config:
        extra = "forbid"


class _DecisionRequest(BaseModel):
    original_relationship_id: str = Field(..., min_length=1, max_length=240)
    action: str = Field(..., min_length=1, max_length=16)
    corrected_from_id: str | None = Field(None, max_length=240)
    corrected_to_id: str | None = Field(None, max_length=240)

    class Config:
        extra = "forbid"


class M30CausalityRelationshipReviewRequest(BaseModel):
    original_relationship: _OriginalRelationshipRequest
    current_reviewed_nodes: list[_ReviewedNodeRequest] = Field(..., min_items=1, max_items=32)
    current_reviewed_relationships: list[_ReviewedRelationshipRequest] = Field(default_factory=list, max_items=64)
    current_sources: list[_SourceRequest] = Field(..., min_items=1, max_items=32)
    decision: _DecisionRequest

    class Config:
        extra = "forbid"


class M30CausalityRelationshipReviewResponse(BaseModel):
    relationship: dict


class M30CausalityRelationshipReviewAPIError(ValueError):
    """Bounded error category safe to expose at the HTTP boundary."""

    def __init__(self, category: str, status_code: int = 422) -> None:
        self.category = category
        self.status_code = status_code
        super().__init__(category)


def _enum(value: str, enum_type: type[Enum], category: str):
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        raise M30CausalityRelationshipReviewAPIError(category) from None


def _node_from_request(payload: _ReviewedNodeRequest) -> M30CanonicalAIProposalCandidate:
    try:
        return M30CanonicalAIProposalCandidate(
            candidate_id=payload.candidate_id,
            semantic_role=payload.semantic_role,
            value=payload.value,
            source_type=payload.source_type,
            source_field=payload.source_field,
            source_reference=payload.source_reference,
            source_references=tuple(payload.source_references),
            source_identities=tuple(
                M30CanonicalSourceIdentity(item.source_id, item.source_field, item.source_reference)
                for item in payload.source_identities
            ),
            source_fingerprint=payload.source_fingerprint,
            authority=_enum(payload.authority, SemanticAuthority, "INVALID_NODE"),
            review_state=_enum(payload.review_state, SemanticReviewState, "INVALID_NODE"),
            confirmation_authority=(
                _enum(payload.confirmation_authority, SemanticAuthority, "INVALID_NODE")
                if payload.confirmation_authority is not None
                else None
            ),
            inferred=payload.inferred,
            acquisition_revision=payload.acquisition_revision,
            original_candidate_id=payload.original_candidate_id,
        )
    except M30CausalityRelationshipReviewAPIError:
        raise
    except (TypeError, ValueError):
        raise M30CausalityRelationshipReviewAPIError("INVALID_NODE") from None


def _source_from_request(payload: _SourceRequest) -> M30CanonicalSourceRecord:
    try:
        return M30CanonicalSourceRecord(payload.source_id, payload.source_field, payload.value, payload.source_reference)
    except (TypeError, ValueError):
        raise M30CausalityRelationshipReviewAPIError("INVALID_SOURCE") from None


def _original_from_request(payload: _OriginalRelationshipRequest) -> M30CausalityRelationshipAIProposal:
    try:
        return M30CausalityRelationshipAIProposal(
            relationship_id=payload.relationship_id,
            from_id=payload.from_id,
            to_id=payload.to_id,
            relationship_type=payload.relationship_type,
            authority=_enum(payload.authority, SemanticAuthority, "INVALID_ORIGINAL_RELATIONSHIP"),
            review_state=_enum(payload.review_state, SemanticReviewState, "INVALID_ORIGINAL_RELATIONSHIP"),
            confirmation_authority=(
                _enum(payload.confirmation_authority, SemanticAuthority, "INVALID_ORIGINAL_RELATIONSHIP")
                if payload.confirmation_authority is not None
                else None
            ),
            inferred=payload.inferred,
            provenance=payload.provenance,
        )
    except M30CausalityRelationshipReviewAPIError:
        raise
    except (TypeError, ValueError):
        raise M30CausalityRelationshipReviewAPIError("INVALID_ORIGINAL_RELATIONSHIP") from None


def _reviewed_relationship_from_request(payload: _ReviewedRelationshipRequest) -> M30ReviewedCausalityRelationship:
    try:
        return M30ReviewedCausalityRelationship(
            payload.relationship_id,
            payload.original_relationship_id,
            payload.from_id,
            payload.to_id,
            payload.relationship_type,
            _enum(payload.authority, SemanticAuthority, "INVALID_REVIEWED_RELATIONSHIP"),
            _enum(payload.review_state, SemanticReviewState, "INVALID_REVIEWED_RELATIONSHIP"),
            (
                _enum(payload.confirmation_authority, SemanticAuthority, "INVALID_REVIEWED_RELATIONSHIP")
                if payload.confirmation_authority is not None
                else None
            ),
            payload.inferred,
            payload.provenance,
        )
    except M30CausalityRelationshipReviewAPIError:
        raise
    except (TypeError, ValueError):
        raise M30CausalityRelationshipReviewAPIError("INVALID_REVIEWED_RELATIONSHIP") from None


def _decision_from_request(payload: _DecisionRequest) -> M30CausalityRelationshipReviewDecision:
    return M30CausalityRelationshipReviewDecision(
        payload.original_relationship_id,
        _enum(payload.action, M30CausalityRelationshipReviewAction, "INVALID_DECISION"),
        payload.corrected_from_id,
        payload.corrected_to_id,
    )


def _relationship_response(relationship: M30ReviewedCausalityRelationship) -> dict:
    return {
        "relationship_id": relationship.relationship_id,
        "original_relationship_id": relationship.original_relationship_id,
        "from_id": relationship.from_id,
        "to_id": relationship.to_id,
        "relationship_type": relationship.relationship_type,
        "authority": relationship.authority.value,
        "review_state": relationship.review_state.value,
        "confirmation_authority": relationship.confirmation_authority.value if relationship.confirmation_authority else None,
        "inferred": relationship.inferred,
        "provenance": relationship.provenance,
    }


def reconstruct_m30_causality_relationship_review_response(
    payload: M30CausalityRelationshipReviewRequest,
    *,
    review_callable: Callable | None = None,
) -> M30CausalityRelationshipReviewResponse:
    """Reconstruct all client state and invoke the frozen review contract once."""

    try:
        original = _original_from_request(payload.original_relationship)
        nodes = tuple(_node_from_request(node) for node in payload.current_reviewed_nodes)
        sources = tuple(_source_from_request(source) for source in payload.current_sources)
        existing = tuple(_reviewed_relationship_from_request(item) for item in payload.current_reviewed_relationships)
        decision = _decision_from_request(payload.decision)
    except M30CausalityRelationshipReviewAPIError:
        raise
    except (TypeError, ValueError):
        raise M30CausalityRelationshipReviewAPIError("INVALID_REVIEW_INPUT") from None

    try:
        reviewed = (review_callable or reconstruct_m30_causality_relationship)(
            original,
            decision,
            nodes,
            sources,
            existing,
            review_revision="v1",
        )
    except M30CausalityRelationshipReviewAPIError:
        raise
    except ValueError as exc:
        raise M30CausalityRelationshipReviewAPIError(getattr(exc, "category", "INVALID_REVIEW_INPUT")) from None
    except Exception:
        raise M30CausalityRelationshipReviewAPIError("INVALID_REVIEW_INPUT") from None
    return M30CausalityRelationshipReviewResponse(relationship=_relationship_response(reviewed))


__all__ = [
    "M30CausalityRelationshipReviewAPIError",
    "M30CausalityRelationshipReviewRequest",
    "M30CausalityRelationshipReviewResponse",
    "reconstruct_m30_causality_relationship_review_response",
]
