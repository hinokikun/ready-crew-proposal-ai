"""Thin authenticated API boundary for M30 canonical node proposals."""

from __future__ import annotations

from typing import Callable

from pydantic import BaseModel, Field

from .m30_canonical_ai_acquisition import (
    M30CanonicalAcquisitionRequest,
    M30CanonicalAIProposalCandidate,
    M30CanonicalSourceRecord,
)
from .m30_canonical_ai_live_adapter import (
    M30CanonicalAILiveAdapterError,
    propose_m30_canonical_live,
)


class M30CanonicalSourceRecordRequest(BaseModel):
    source_id: str = Field(..., min_length=1, max_length=160)
    source_field: str = Field(..., min_length=1, max_length=160)
    value: str = Field(..., min_length=1, max_length=4000)
    source_reference: str = Field(..., min_length=1, max_length=240)

    class Config:
        extra = "forbid"


class M30CanonicalNodeProposalRequest(BaseModel):
    semantic_role: str = Field(..., min_length=1, max_length=64)
    requested_count: int = Field(..., ge=1, le=5)
    source_records: list[M30CanonicalSourceRecordRequest] = Field(..., min_items=1, max_items=32)

    class Config:
        extra = "forbid"


class M30CanonicalSourceIdentityResponse(BaseModel):
    source_id: str
    source_field: str
    source_reference: str


class M30CanonicalNodeProposalResponse(BaseModel):
    candidates: tuple[dict, ...]


class M30CanonicalNodeProposalAPIError(ValueError):
    """Bounded API error category safe for clients."""

    def __init__(self, category: str, status_code: int = 422) -> None:
        self.category = category
        self.status_code = status_code
        super().__init__(category)


def _candidate_response(candidate: M30CanonicalAIProposalCandidate) -> dict:
    return {
        "candidate_id": candidate.candidate_id,
        "semantic_role": candidate.semantic_role,
        "value": candidate.value,
        "source_type": candidate.source_type,
        "source_field": candidate.source_field,
        "source_reference": candidate.source_reference,
        "source_references": candidate.source_references,
        "source_identities": tuple(
            {
                "source_id": identity.source_id,
                "source_field": identity.source_field,
                "source_reference": identity.source_reference,
            }
            for identity in candidate.source_identities
        ),
        "source_fingerprint": candidate.source_fingerprint,
        "authority": candidate.authority.value,
        "review_state": candidate.review_state.value,
        "confirmation_authority": candidate.confirmation_authority.value if candidate.confirmation_authority else None,
        "inferred": candidate.inferred,
        "acquisition_revision": candidate.acquisition_revision,
        "original_candidate_id": candidate.original_candidate_id,
    }


def build_m30_canonical_node_proposal_response(
    payload: M30CanonicalNodeProposalRequest,
    *,
    proposal_callable: Callable | None = None,
) -> M30CanonicalNodeProposalResponse:
    """Validate transport, create a backend-owned v1 request, and call the frozen adapter once."""

    try:
        request = M30CanonicalAcquisitionRequest(
            semantic_role=payload.semantic_role,
            requested_count=payload.requested_count,
            source_records=tuple(
                M30CanonicalSourceRecord(
                    source_id=record.source_id,
                    source_field=record.source_field,
                    value=record.value,
                    source_reference=record.source_reference,
                )
                for record in payload.source_records
            ),
            acquisition_revision="v1",
        )
    except (TypeError, ValueError) as exc:
        category = getattr(exc, "category", "INVALID_CANONICAL_INPUT")
        category = {
            "INVALID_ROLE": "INVALID_CANONICAL_INPUT",
            "INVALID_COUNT": "INVALID_REQUEST_COUNT",
            "INVALID_SOURCE": "INVALID_SOURCE_PROVENANCE",
        }.get(category, category)
        raise M30CanonicalNodeProposalAPIError(category) from None

    try:
        candidates = (proposal_callable or propose_m30_canonical_live)(request)
    except M30CanonicalAILiveAdapterError as exc:
        raise M30CanonicalNodeProposalAPIError(exc.category, exc.status_code) from None
    except Exception:
        raise M30CanonicalNodeProposalAPIError("AI_REQUEST_FAILED", 502) from None
    return M30CanonicalNodeProposalResponse(candidates=tuple(_candidate_response(candidate) for candidate in candidates))


__all__ = [
    "M30CanonicalNodeProposalAPIError",
    "M30CanonicalNodeProposalRequest",
    "M30CanonicalNodeProposalResponse",
    "M30CanonicalSourceRecordRequest",
    "build_m30_canonical_node_proposal_response",
]
