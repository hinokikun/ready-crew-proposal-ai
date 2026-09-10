"""Thin authenticated API boundary for stateless M30 node review."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .m30_canonical_ai_acquisition import (
    M30CanonicalAIProposalCandidate,
    M30CanonicalSourceIdentity,
    M30CanonicalSourceRecord,
)
from .m30_canonical_review_decisions import (
    M30CanonicalReviewAction,
    M30CanonicalReviewDecision,
    reconstruct_m30_canonical_candidate,
)
from .production_semantic_contract import SemanticAuthority, SemanticReviewState


class M30CanonicalReviewSourceIdentityRequest(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=160)
    source_field: str = Field(..., min_length=1, max_length=160)
    source_reference: str = Field(..., min_length=1, max_length=240)

    class Config:
        extra = "forbid"


class M30CanonicalReviewSourceRequest(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=160)
    source_field: str = Field(..., min_length=1, max_length=160)
    value: str = Field(..., min_length=1, max_length=4000)
    source_reference: str = Field(..., min_length=1, max_length=240)

    class Config:
        extra = "forbid"


class M30CanonicalOriginalCandidateRequest(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=240)
    semantic_role: str = Field(..., min_length=1, max_length=64)
    value: str = Field(..., min_length=1, max_length=4000)
    source_type: str = Field(..., min_length=1, max_length=80)
    source_field: str = Field(..., min_length=1, max_length=4000)
    source_reference: str = Field(..., min_length=1, max_length=4000)
    source_references: list[str] = Field(..., min_items=1, max_items=32)
    source_identities: list[M30CanonicalReviewSourceIdentityRequest] = Field(..., min_items=1, max_items=32)
    source_fingerprint: str = Field(..., min_length=64, max_length=64)
    authority: str = Field(..., min_length=1, max_length=64)
    review_state: str = Field(..., min_length=1, max_length=32)
    confirmation_authority: str | None = Field(None, max_length=64)
    inferred: bool
    acquisition_revision: str = Field(..., min_length=1, max_length=32)
    original_candidate_id: str | None = Field(None, max_length=240)

    class Config:
        extra = "forbid"


class M30CanonicalReviewDecisionRequest(BaseModel):
    original_candidate_id: str = Field(..., min_length=1, max_length=240)
    action: str = Field(..., min_length=1, max_length=16)
    corrected_value: str | None = Field(None, max_length=4000)

    class Config:
        extra = "forbid"


class M30CanonicalNodeReviewRequest(BaseModel):
    original_candidate: M30CanonicalOriginalCandidateRequest
    current_sources: list[M30CanonicalReviewSourceRequest] = Field(..., min_items=1, max_items=32)
    decision: M30CanonicalReviewDecisionRequest

    class Config:
        extra = "forbid"


class M30CanonicalNodeReviewResponse(BaseModel):
    candidate: dict


class M30CanonicalNodeReviewAPIError(ValueError):
    """Bounded error safe to expose at the HTTP boundary."""

    def __init__(self, category: str, status_code: int = 422) -> None:
        self.category = category
        self.status_code = status_code
        super().__init__(category)


def _enum(value: str, enum_type: type[Enum], category: str):
    try:
        return enum_type(value)
    except (TypeError, ValueError):
        raise M30CanonicalNodeReviewAPIError(category) from None


def _candidate_from_request(payload: M30CanonicalOriginalCandidateRequest) -> M30CanonicalAIProposalCandidate:
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
                M30CanonicalSourceIdentity(identity.source_id, identity.source_field, identity.source_reference)
                for identity in payload.source_identities
            ),
            source_fingerprint=payload.source_fingerprint,
            authority=_enum(payload.authority, SemanticAuthority, "INVALID_ORIGINAL_CANDIDATE"),
            review_state=_enum(payload.review_state, SemanticReviewState, "INVALID_ORIGINAL_CANDIDATE"),
            confirmation_authority=(
                _enum(payload.confirmation_authority, SemanticAuthority, "INVALID_ORIGINAL_CANDIDATE")
                if payload.confirmation_authority is not None
                else None
            ),
            inferred=payload.inferred,
            acquisition_revision=payload.acquisition_revision,
            original_candidate_id=payload.original_candidate_id,
        )
    except M30CanonicalNodeReviewAPIError:
        raise
    except (TypeError, ValueError):
        raise M30CanonicalNodeReviewAPIError("INVALID_ORIGINAL_CANDIDATE") from None


def _source_from_request(payload: M30CanonicalReviewSourceRequest) -> M30CanonicalSourceRecord:
    try:
        return M30CanonicalSourceRecord(payload.source_id, payload.source_field, payload.value, payload.source_reference)
    except (TypeError, ValueError):
        raise M30CanonicalNodeReviewAPIError("INVALID_SOURCE_PROVENANCE") from None


def _decision_from_request(payload: M30CanonicalReviewDecisionRequest) -> M30CanonicalReviewDecision:
    action = _enum(payload.action, M30CanonicalReviewAction, "INVALID_DECISION")
    try:
        return M30CanonicalReviewDecision(payload.original_candidate_id, action, payload.corrected_value)
    except (TypeError, ValueError):
        raise M30CanonicalNodeReviewAPIError("INVALID_DECISION") from None


def _candidate_response(candidate: M30CanonicalAIProposalCandidate) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "semantic_role": candidate.semantic_role,
        "value": candidate.value,
        "source_type": candidate.source_type,
        "source_field": candidate.source_field,
        "source_reference": candidate.source_reference,
        "source_references": candidate.source_references,
        "source_identities": tuple({
            "source_id": identity.source_id,
            "source_field": identity.source_field,
            "source_reference": identity.source_reference,
        } for identity in candidate.source_identities),
        "source_fingerprint": candidate.source_fingerprint,
        "authority": candidate.authority.value,
        "review_state": candidate.review_state.value,
        "confirmation_authority": candidate.confirmation_authority.value if candidate.confirmation_authority else None,
        "inferred": candidate.inferred,
        "acquisition_revision": candidate.acquisition_revision,
        "original_candidate_id": candidate.original_candidate_id,
    }


def reconstruct_m30_canonical_node_review_response(
    payload: M30CanonicalNodeReviewRequest,
) -> M30CanonicalNodeReviewResponse:
    candidate = _candidate_from_request(payload.original_candidate)
    current_sources = tuple(_source_from_request(source) for source in payload.current_sources)
    decision = _decision_from_request(payload.decision)
    try:
        reviewed = reconstruct_m30_canonical_candidate(candidate, decision, current_sources)
    except ValueError as exc:
        category = getattr(exc, "category", str(exc))
        category_map = {
            "PROVENANCE_ERROR": "INVALID_SOURCE_PROVENANCE",
            "INVALID_ORIGINAL_CANDIDATE": "INVALID_ORIGINAL_CANDIDATE",
            "CANDIDATE_ID_MISMATCH": "CANDIDATE_ID_MISMATCH",
            "INVALID_DECISION": "INVALID_DECISION",
            "INVALID_CORRECTION": "INVALID_CORRECTION",
            "STALE_SOURCE": "STALE_SOURCE",
        }
        raise M30CanonicalNodeReviewAPIError(category_map.get(category, "INVALID_REVIEW_INPUT")) from None
    return M30CanonicalNodeReviewResponse(candidate=_candidate_response(reviewed))


__all__ = [
    "M30CanonicalNodeReviewAPIError",
    "M30CanonicalNodeReviewRequest",
    "M30CanonicalNodeReviewResponse",
    "reconstruct_m30_canonical_node_review_response",
]
