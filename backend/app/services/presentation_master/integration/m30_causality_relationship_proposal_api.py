"""Thin authenticated API boundary for stateless M30 causal proposals."""

from __future__ import annotations

from enum import Enum
from typing import Callable, Iterable

from pydantic import BaseModel, Field

from .m30_canonical_ai_acquisition import (
    M30CanonicalAIProposalCandidate,
    M30CanonicalSourceIdentity,
    M30CanonicalSourceRecord,
)
from .m30_causality_relationship_ai_live_adapter import (
    M30CausalityRelationshipAILiveAdapterError,
    propose_m30_causality_relationships_live,
)
from .m30_causality_relationship_ai_proposals import (
    M30CausalityRelationshipProposalError,
    M30CausalityRelationshipProposalRequest,
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


class M30CausalityRelationshipProposalRequestModel(BaseModel):
    current_reviewed_nodes: list[_ReviewedNodeRequest] = Field(..., min_items=1, max_items=32)
    current_sources: list[_SourceRequest] = Field(..., min_items=1, max_items=32)
    requested_count: int = Field(..., ge=1, le=32)

    class Config:
        extra = "forbid"


class M30CausalityRelationshipProposalResponse(BaseModel):
    relationships: tuple[dict, ...]


class M30CausalityRelationshipProposalAPIError(ValueError):
    """Bounded error category safe to expose at the HTTP boundary."""

    def __init__(self, category: str, status_code: int = 422) -> None:
        self.category = category
        self.status_code = status_code
        super().__init__(category)


def _enum(value: str, enum_type: type[Enum], category: str):
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        raise M30CausalityRelationshipProposalAPIError(category) from None


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
    except M30CausalityRelationshipProposalAPIError:
        raise
    except (TypeError, ValueError):
        raise M30CausalityRelationshipProposalAPIError("INVALID_NODE") from None


def _source_from_request(payload: _SourceRequest) -> M30CanonicalSourceRecord:
    try:
        return M30CanonicalSourceRecord(payload.source_id, payload.source_field, payload.value, payload.source_reference)
    except (TypeError, ValueError):
        raise M30CausalityRelationshipProposalAPIError("INVALID_SOURCE") from None


def _relationship_response(relationship) -> dict:
    return {
        "relationship_id": relationship.relationship_id,
        "from_id": relationship.from_id,
        "to_id": relationship.to_id,
        "relationship_type": relationship.relationship_type,
        "authority": relationship.authority.value,
        "review_state": relationship.review_state.value,
        "confirmation_authority": relationship.confirmation_authority.value if relationship.confirmation_authority else None,
        "inferred": relationship.inferred,
        "provenance": relationship.provenance,
    }


def build_m30_causality_relationship_proposal_response(
    payload: M30CausalityRelationshipProposalRequestModel,
    *,
    proposal_callable: Callable | None = None,
) -> M30CausalityRelationshipProposalResponse:
    """Reconstruct reviewed nodes and invoke the frozen live adapter once."""

    try:
        nodes = tuple(_node_from_request(node) for node in payload.current_reviewed_nodes)
        sources = tuple(_source_from_request(source) for source in payload.current_sources)
        request = M30CausalityRelationshipProposalRequest(
            current_nodes=nodes,
            requested_count=payload.requested_count,
            proposal_revision="v1",
        )
    except M30CausalityRelationshipProposalAPIError:
        raise
    except (TypeError, ValueError):
        raise M30CausalityRelationshipProposalAPIError("INVALID_REQUEST") from None

    try:
        relationships = (proposal_callable or propose_m30_causality_relationships_live)(request, sources)
    except M30CausalityRelationshipAILiveAdapterError as exc:
        raise M30CausalityRelationshipProposalAPIError(exc.category, exc.status_code) from None
    except M30CausalityRelationshipProposalError as exc:
        raise M30CausalityRelationshipProposalAPIError("OFFLINE_CONTRACT_REJECTED") from None
    except Exception:
        raise M30CausalityRelationshipProposalAPIError("AI_REQUEST_FAILED", 502) from None
    return M30CausalityRelationshipProposalResponse(
        relationships=tuple(_relationship_response(item) for item in relationships)
    )


__all__ = [
    "M30CausalityRelationshipProposalAPIError",
    "M30CausalityRelationshipProposalRequestModel",
    "M30CausalityRelationshipProposalResponse",
    "build_m30_causality_relationship_proposal_response",
]
