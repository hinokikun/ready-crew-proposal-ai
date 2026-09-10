"""Dedicated API boundary for M30 presentation-content proposals."""

from __future__ import annotations

import logging
from typing import Callable, Sequence

from pydantic import BaseModel, Field

from app.models import (
    BusinessImplicationTransportItem,
    BusinessRelationshipTransportItem,
    ProblemObjectTransportItem,
    SolutionDirectionTransportItem,
)

from .m30_presentation_content_ai_orchestration import (
    M30PresentationContentAIOrchestrationResult,
    orchestrate_m30_presentation_content_ai,
)
from .m30_semantic_bridge import evaluate_m30_semantic_bridge
from .presentation_content_ai_live_adapter import propose_presentation_content
from .presentation_content_ai_proposals import PresentationContentAIProposalRequest
from .presentation_content_candidates import PresentationContentCandidate, PresentationContentSourceIdentity
from .production_semantic_contract import (
    ProductionSemanticCandidate,
    SemanticAuthority,
    SemanticItemType,
    SemanticReviewState,
)


logger = logging.getLogger(__name__)
M30_PROPOSAL_REVISION_V1 = "v1"


class EvidenceCandidateTransportItem(BaseModel):
    semantic_type: str = Field("evidence", min_length=1, max_length=64)
    id: str = Field(..., min_length=1, max_length=160)
    value: str = Field(..., min_length=1, max_length=2000)
    source_type: str = Field(..., min_length=1, max_length=80)
    source_field: str = Field(..., min_length=1, max_length=160)
    source_reference: str = Field(..., min_length=1, max_length=240)
    authority: str = Field(..., min_length=1, max_length=64)
    confidence: float = Field(..., ge=0, le=1)
    review_state: str = Field(..., min_length=1, max_length=32)
    inferred: bool = False
    admissible_as_evidence: bool = False
    confirmation_authority: str | None = Field(None, max_length=64)

    class Config:
        extra = "forbid"


class M30PresentationContentProposalRequest(BaseModel):
    problem_objects: list[ProblemObjectTransportItem] = Field(..., min_items=10, max_items=10)
    business_implications: list[BusinessImplicationTransportItem] = Field(..., min_items=4, max_items=4)
    solution_direction: SolutionDirectionTransportItem
    business_relationships: list[BusinessRelationshipTransportItem] = Field(..., min_items=4, max_items=32)
    evidence_candidates: list[EvidenceCandidateTransportItem] = Field(..., min_items=1, max_items=16)

    class Config:
        extra = "forbid"


class PresentationContentFieldResponse(BaseModel):
    field_role: str
    value: str


class PresentationContentSourceIdentityResponse(BaseModel):
    source_item_id: str
    semantic_role: str
    value: str


class PresentationContentCandidateResponse(BaseModel):
    candidate_id: str
    semantic_role: str
    fields: tuple[PresentationContentFieldResponse, ...]
    source_identities: tuple[PresentationContentSourceIdentityResponse, ...]
    source_fingerprint: str
    derivation_type: str
    authority: str
    review_state: str
    confirmation_authority: str | None


class PresentationContentProposalIssueResponse(BaseModel):
    semantic_role: str
    requested_field_roles: tuple[str, ...]
    safe_error_category: str


class M30PresentationContentProposalResponse(BaseModel):
    presentation_candidates: tuple[PresentationContentCandidateResponse, ...]
    content_acquisition_complete_for_human_review: bool
    issues: tuple[PresentationContentProposalIssueResponse, ...]


class M30PresentationContentRequestError(ValueError):
    """Bounded client error without source or presentation content."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


def _enum(value: str, enum_type: type) -> object:
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise M30PresentationContentRequestError("INVALID_CANONICAL_INPUT") from exc


def _to_evidence(item: EvidenceCandidateTransportItem) -> ProductionSemanticCandidate:
    if item.semantic_type != SemanticItemType.EVIDENCE.value:
        raise M30PresentationContentRequestError("INVALID_CANONICAL_INPUT")
    return ProductionSemanticCandidate(
        id=item.id,
        semantic_type=SemanticItemType.EVIDENCE,
        value=item.value,
        source_type=item.source_type,
        source_field=item.source_field,
        authority=_enum(item.authority, SemanticAuthority),
        confidence=item.confidence,
        review_state=_enum(item.review_state, SemanticReviewState),
        inferred=item.inferred,
        admissible_as_evidence=item.admissible_as_evidence,
        source_reference=item.source_reference,
        confirmation_authority=(
            _enum(item.confirmation_authority, SemanticAuthority)
            if item.confirmation_authority is not None
            else None
        ),
    )


def _validate_request(payload: M30PresentationContentProposalRequest):
    role_counts: dict[str, int] = {}
    all_items = (*payload.problem_objects, *payload.business_implications, payload.solution_direction)
    ids = [item.id for item in all_items]
    if len(set(ids)) != len(ids):
        raise M30PresentationContentRequestError("DUPLICATE_ITEM_ID")
    relationship_ids = [item.id for item in payload.business_relationships]
    evidence_ids = [item.id for item in payload.evidence_candidates]
    if len(set(relationship_ids)) != len(relationship_ids) or len(set(evidence_ids)) != len(evidence_ids):
        raise M30PresentationContentRequestError("DUPLICATE_ITEM_ID")
    for item in payload.problem_objects:
        role_counts[item.role] = role_counts.get(item.role, 0) + 1
    role_counts["business_implication"] = len(payload.business_implications)
    role_counts["solution_direction"] = 1
    if role_counts.get("visible_issue", 0) != 1 or role_counts.get("root_cause", 0) != 4 or role_counts.get("causal_state", 0) != 5:
        raise M30PresentationContentRequestError("M30_SEMANTIC_INCOMPLETE")

    try:
        problem_objects = tuple(
            item.copy(update={"authority": _enum(item.authority, SemanticAuthority), "review_state": _enum(item.review_state, SemanticReviewState), "confirmation_authority": _enum(item.confirmation_authority, SemanticAuthority) if item.confirmation_authority else None})
            for item in payload.problem_objects
        )
        implications = tuple(
            item.copy(update={"authority": _enum(item.authority, SemanticAuthority), "review_state": _enum(item.review_state, SemanticReviewState), "confirmation_authority": _enum(item.confirmation_authority, SemanticAuthority) if item.confirmation_authority else None})
            for item in payload.business_implications
        )
        solution = payload.solution_direction.copy(update={"authority": _enum(payload.solution_direction.authority, SemanticAuthority), "review_state": _enum(payload.solution_direction.review_state, SemanticReviewState), "confirmation_authority": _enum(payload.solution_direction.confirmation_authority, SemanticAuthority) if payload.solution_direction.confirmation_authority else None})
        relationships = tuple(
            item.copy(update={"authority": _enum(item.authority, SemanticAuthority), "review_state": _enum(item.review_state, SemanticReviewState), "confirmation_authority": _enum(item.confirmation_authority, SemanticAuthority) if item.confirmation_authority else None})
            for item in payload.business_relationships
        )
        evidence = tuple(_to_evidence(item) for item in payload.evidence_candidates)
    except M30PresentationContentRequestError:
        raise
    except (TypeError, ValueError) as exc:
        raise M30PresentationContentRequestError("INVALID_CANONICAL_INPUT") from exc

    if any(not getattr(item, "source_reference", "").strip() for item in (*problem_objects, *implications, solution, *relationships)):
        raise M30PresentationContentRequestError("INVALID_SOURCE_PROVENANCE")
    if any(item.authority == SemanticAuthority.AI_PROPOSED or item.review_state in {SemanticReviewState.UNCONFIRMED, SemanticReviewState.REJECTED, SemanticReviewState.UNRESOLVED} for item in (*problem_objects, *implications, solution)):
        raise M30PresentationContentRequestError("INVALID_AUTHORITY")

    evaluation = evaluate_m30_semantic_bridge(problem_objects, implications, solution, relationships, evidence_candidates=evidence)
    if not evaluation.m30_semantic_complete:
        category = "EVIDENCE_INSUFFICIENT" if "EVIDENCE_INSUFFICIENT" in evaluation.incompleteness_reasons else "M30_SEMANTIC_INCOMPLETE"
        raise M30PresentationContentRequestError(category)
    return evaluation


def _revision_provider(_role: str, _sources: tuple[PresentationContentSourceIdentity, ...], _fields: tuple[str, ...]) -> str:
    return M30_PROPOSAL_REVISION_V1


def _candidate_response(candidate: PresentationContentCandidate) -> PresentationContentCandidateResponse:
    return PresentationContentCandidateResponse(
        candidate_id=candidate.candidate_id,
        semantic_role=candidate.semantic_role,
        fields=tuple(PresentationContentFieldResponse(field_role=field.field_role, value=field.value) for field in candidate.fields),
        source_identities=tuple(PresentationContentSourceIdentityResponse(source_item_id=source.source_item_id, semantic_role=source.semantic_role, value=source.value) for source in candidate.source_identities),
        source_fingerprint=candidate.source_fingerprint,
        derivation_type=str(getattr(candidate.derivation_type, "value", candidate.derivation_type)),
        authority=str(getattr(candidate.authority, "value", candidate.authority)),
        review_state=str(getattr(candidate.review_state, "value", candidate.review_state)),
        confirmation_authority=getattr(candidate.confirmation_authority, "value", candidate.confirmation_authority),
    )


def build_m30_presentation_content_proposal_response(
    payload: M30PresentationContentProposalRequest,
    *,
    proposal_callable: Callable | None = None,
) -> M30PresentationContentProposalResponse:
    """Validate canonical input and run the frozen orchestration once."""

    evaluation = _validate_request(payload)
    result: M30PresentationContentAIOrchestrationResult = orchestrate_m30_presentation_content_ai(
        evaluation,
        proposal_callable=proposal_callable or propose_presentation_content,
        revision_provider=_revision_provider,
    )
    logger.info(
        "m30_presentation_content_proposals_completed candidates=%d successes=%d failures=%d complete=%s",
        len(result.ai_proposal_candidates),
        len(result.ai_proposal_candidates),
        len(result.failures),
        result.content_acquisition_complete_for_human_review,
    )
    return M30PresentationContentProposalResponse(
        presentation_candidates=tuple(_candidate_response(candidate) for candidate in result.ai_proposal_candidates),
        content_acquisition_complete_for_human_review=result.content_acquisition_complete_for_human_review,
        issues=tuple(PresentationContentProposalIssueResponse(
            semantic_role=failure.semantic_role,
            requested_field_roles=failure.requested_field_roles,
            safe_error_category=failure.safe_error_category,
        ) for failure in result.failures),
    )


__all__ = [
    "EvidenceCandidateTransportItem",
    "M30PresentationContentProposalRequest",
    "M30PresentationContentProposalResponse",
    "M30PresentationContentRequestError",
    "build_m30_presentation_content_proposal_response",
]
