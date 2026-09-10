"""Offline orchestration for M30 presentation-content acquisition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .m30_presentation_content_acquisition import (
    M30PresentationContentAcquisitionProjection,
    project_m30_presentation_content_acquisition,
)
from .m30_semantic_bridge import M30SemanticEvaluation
from .presentation_content_ai_proposals import (
    ParsedPresentationContentAIProposal,
    PresentationContentAIProposalRequest,
    build_presentation_content_candidate,
)
from .presentation_content_candidates import (
    PresentationContentCandidate,
    PresentationContentSourceIdentity,
)
from .problem_structure_transport import is_admitted


@dataclass(frozen=True)
class PresentationContentProposalFailure:
    semantic_role: str
    requested_field_roles: tuple[str, ...]
    safe_error_category: str


@dataclass(frozen=True)
class M30PresentationContentAIOrchestrationResult:
    acquisition_projection: M30PresentationContentAcquisitionProjection
    direct_candidates: tuple[PresentationContentCandidate, ...]
    ai_proposal_candidates: tuple[PresentationContentCandidate, ...]
    failures: tuple[PresentationContentProposalFailure, ...]
    content_acquisition_complete_for_human_review: bool
    presentation_framing_required: bool


ProposalCallable = Callable[[PresentationContentAIProposalRequest], PresentationContentCandidate]
RevisionProvider = Callable[[str, tuple[PresentationContentSourceIdentity, ...], tuple[str, ...]], str]


def _canonical_items(evaluation: M30SemanticEvaluation) -> dict[str, object]:
    values = (
        *evaluation.problem_objects,
        *evaluation.business_implications,
        *((evaluation.solution_direction,) if evaluation.solution_direction else ()),
    )
    return {str(item.id): item for item in values if is_admitted(item)}


def _source_for(item: object, role: str) -> PresentationContentSourceIdentity:
    return PresentationContentSourceIdentity(str(item.id), role, str(item.value))


def _candidate_matches_request(
    candidate: object,
    request: PresentationContentAIProposalRequest,
) -> bool:
    if not isinstance(candidate, PresentationContentCandidate):
        return False
    if tuple(field.field_role for field in candidate.fields) != request.requested_field_roles:
        return False
    expected = build_presentation_content_candidate(
        request,
        ParsedPresentationContentAIProposal(candidate.fields),
    )
    return (
        candidate == expected
        and candidate.candidate_id == expected.candidate_id
        and candidate.authority.value == "AI_PROPOSED"
        and candidate.review_state.value == "UNCONFIRMED"
        and candidate.confirmation_authority is None
    )


def _safe_error_category(error: Exception) -> str:
    category = getattr(error, "category", "proposal_failure")
    return category if isinstance(category, str) and category and len(category) <= 80 else "proposal_failure"


def orchestrate_m30_presentation_content_ai(
    evaluation: M30SemanticEvaluation,
    *,
    proposal_callable: ProposalCallable,
    revision_provider: RevisionProvider,
) -> M30PresentationContentAIOrchestrationResult:
    """Combine frozen acquisition output with injected AI proposal results."""

    if not isinstance(evaluation, M30SemanticEvaluation):
        raise TypeError("evaluation must be an M30SemanticEvaluation")
    projection = project_m30_presentation_content_acquisition(evaluation)
    direct_candidates = tuple(
        item.direct_candidate for item in projection.items if item.direct_candidate is not None
    )
    if not projection.acquisition_plan_complete:
        return M30PresentationContentAIOrchestrationResult(
            projection, direct_candidates, (), (), False, projection.presentation_framing_required
        )

    canonical = _canonical_items(evaluation)
    candidates: list[PresentationContentCandidate] = []
    failures: list[PresentationContentProposalFailure] = []
    for item in projection.items:
        requirements = item.required_derivations
        if not requirements:
            continue
        groups: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
        for requirement in requirements:
            key = (item.semantic_role, requirement.source_item_ids)
            existing = next((index for index, group in enumerate(groups) if group[:2] == key), None)
            if existing is None:
                groups.append((item.semantic_role, requirement.source_item_ids, (requirement.field_role,)))
            else:
                role, source_ids, fields = groups[existing]
                groups[existing] = (role, source_ids, (*fields, requirement.field_role))
        for semantic_role, source_ids, field_roles in groups:
            try:
                sources = tuple(_source_for(canonical[source_id], semantic_role) for source_id in source_ids)
                revision = revision_provider(semantic_role, sources, field_roles)
                request = PresentationContentAIProposalRequest(semantic_role, sources, field_roles, revision)
                candidate = proposal_callable(request)
                if not _candidate_matches_request(candidate, request):
                    raise ValueError("returned candidate contract mismatch")
                candidates.append(candidate)
            except Exception as error:
                failures.append(PresentationContentProposalFailure(semantic_role, field_roles, _safe_error_category(error)))

    complete = projection.acquisition_plan_complete and not failures
    return M30PresentationContentAIOrchestrationResult(
        projection,
        direct_candidates,
        tuple(candidates),
        tuple(failures),
        complete,
        projection.presentation_framing_required,
    )


__all__ = [
    "M30PresentationContentAIOrchestrationResult",
    "PresentationContentProposalFailure",
    "orchestrate_m30_presentation_content_ai",
]
