"""Dedicated generic API boundary for presentation-content review decisions."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .presentation_content_candidates import (
    PresentationContentCandidate,
    PresentationContentField,
    PresentationContentSourceIdentity,
)
from .presentation_content_review_decisions import (
    PresentationContentReviewAction,
    PresentationContentReviewDecision,
    reconstruct_presentation_content_candidate,
)
from .production_semantic_contract import SemanticAuthority, SemanticReviewState
from .slot_ready_content import SlotReadyDerivationType


class PresentationContentReviewFieldTransport(BaseModel):
    field_role: str = Field(..., min_length=1, max_length=80)
    value: str = Field(..., min_length=1, max_length=4000)

    class Config:
        extra = "forbid"


class PresentationContentReviewSourceTransport(BaseModel):
    source_item_id: str = Field(..., min_length=1, max_length=160)
    semantic_role: str = Field(..., min_length=1, max_length=120)
    value: str = Field(..., min_length=1, max_length=4000)

    class Config:
        extra = "forbid"


class PresentationContentReviewCandidateTransport(BaseModel):
    candidate_id: str = Field(..., min_length=1, max_length=240)
    semantic_role: str = Field(..., min_length=1, max_length=120)
    fields: list[PresentationContentReviewFieldTransport] = Field(..., min_items=1, max_items=32)
    source_identities: list[PresentationContentReviewSourceTransport] = Field(..., min_items=1, max_items=32)
    source_fingerprint: str = Field(..., min_length=64, max_length=64)
    derivation_type: str = Field(..., min_length=1, max_length=64)
    authority: str = Field(..., min_length=1, max_length=64)
    review_state: str = Field(..., min_length=1, max_length=32)
    confirmation_authority: str | None = Field(None, max_length=64)

    class Config:
        extra = "forbid"


class PresentationContentReviewDecisionTransport(BaseModel):
    original_candidate_id: str = Field(..., min_length=1, max_length=240)
    action: str = Field(..., min_length=1, max_length=16)
    corrected_fields: list[PresentationContentReviewFieldTransport] | None = Field(None, max_items=32)

    class Config:
        extra = "forbid"


class PresentationContentReviewRequest(BaseModel):
    original_candidate: PresentationContentReviewCandidateTransport
    current_sources: list[PresentationContentReviewSourceTransport] = Field(..., min_items=1, max_items=32)
    decision: PresentationContentReviewDecisionTransport

    class Config:
        extra = "forbid"


class PresentationContentReviewFieldResponse(BaseModel):
    field_role: str
    value: str


class PresentationContentReviewSourceResponse(BaseModel):
    source_item_id: str
    semantic_role: str
    value: str


class PresentationContentReviewResponse(BaseModel):
    candidate_id: str
    semantic_role: str
    fields: tuple[PresentationContentReviewFieldResponse, ...]
    source_identities: tuple[PresentationContentReviewSourceResponse, ...]
    source_fingerprint: str
    derivation_type: str
    authority: str
    review_state: str
    confirmation_authority: str | None


class PresentationContentReviewAPIError(ValueError):
    """Bounded error category safe to expose to Product."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def _enum(value: str, enum_type: type) -> Any:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise PresentationContentReviewAPIError("INVALID_ORIGINAL_CANDIDATE") from exc


def _candidate_from_transport(transport: PresentationContentReviewCandidateTransport) -> PresentationContentCandidate:
    return PresentationContentCandidate(
        candidate_id=transport.candidate_id,
        semantic_role=transport.semantic_role,
        fields=tuple(PresentationContentField(field.field_role, field.value) for field in transport.fields),
        source_identities=tuple(PresentationContentSourceIdentity(source.source_item_id, source.semantic_role, source.value) for source in transport.source_identities),
        source_fingerprint=transport.source_fingerprint,
        derivation_type=_enum(transport.derivation_type, SlotReadyDerivationType),
        authority=_enum(transport.authority, SemanticAuthority),
        review_state=_enum(transport.review_state, SemanticReviewState),
        confirmation_authority=(
            _enum(transport.confirmation_authority, SemanticAuthority)
            if transport.confirmation_authority is not None
            else None
        ),
    )


def _source_from_transport(transport: PresentationContentReviewSourceTransport) -> PresentationContentSourceIdentity:
    return PresentationContentSourceIdentity(transport.source_item_id, transport.semantic_role, transport.value)


def _decision_from_transport(transport: PresentationContentReviewDecisionTransport) -> PresentationContentReviewDecision:
    try:
        action = PresentationContentReviewAction(transport.action)
    except (TypeError, ValueError) as exc:
        raise PresentationContentReviewAPIError("INVALID_DECISION") from exc
    corrected_fields = None if transport.corrected_fields is None else tuple(
        PresentationContentField(field.field_role, field.value) for field in transport.corrected_fields
    )
    return PresentationContentReviewDecision(transport.original_candidate_id, action, corrected_fields)


def _response(candidate: PresentationContentCandidate) -> PresentationContentReviewResponse:
    return PresentationContentReviewResponse(
        candidate_id=candidate.candidate_id,
        semantic_role=candidate.semantic_role,
        fields=tuple(PresentationContentReviewFieldResponse(field_role=field.field_role, value=field.value) for field in candidate.fields),
        source_identities=tuple(PresentationContentReviewSourceResponse(source_item_id=source.source_item_id, semantic_role=source.semantic_role, value=source.value) for source in candidate.source_identities),
        source_fingerprint=candidate.source_fingerprint,
        derivation_type=str(getattr(candidate.derivation_type, "value", candidate.derivation_type)),
        authority=str(getattr(candidate.authority, "value", candidate.authority)),
        review_state=str(getattr(candidate.review_state, "value", candidate.review_state)),
        confirmation_authority=getattr(candidate.confirmation_authority, "value", candidate.confirmation_authority),
    )


def reconstruct_reviewed_presentation_content(
    payload: PresentationContentReviewRequest,
) -> PresentationContentReviewResponse:
    """Deserialize and delegate the decision to the frozen reconstruction contract."""

    candidate = _candidate_from_transport(payload.original_candidate)
    current_sources = tuple(_source_from_transport(source) for source in payload.current_sources)
    decision = _decision_from_transport(payload.decision)
    if decision.original_candidate_id != candidate.candidate_id:
        raise PresentationContentReviewAPIError("CANDIDATE_ID_MISMATCH")
    try:
        reviewed = reconstruct_presentation_content_candidate(candidate, decision, current_sources)
    except ValueError as exc:
        category = str(exc)
        allowed = {
            "INVALID_DECISION",
            "CANDIDATE_ID_MISMATCH",
            "INVALID_ORIGINAL_CANDIDATE",
            "STALE_SOURCE",
            "INVALID_CORRECTION_FIELDS",
        }
        raise PresentationContentReviewAPIError(category if category in allowed else "INVALID_ORIGINAL_CANDIDATE") from None
    return _response(reviewed)


__all__ = [
    "PresentationContentReviewAPIError",
    "PresentationContentReviewRequest",
    "PresentationContentReviewResponse",
    "reconstruct_reviewed_presentation_content",
]
