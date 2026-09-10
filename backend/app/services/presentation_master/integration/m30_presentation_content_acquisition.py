"""Deterministic, offline acquisition planning for admitted M30 semantics."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from app.models import (
    BusinessImplicationTransportItem,
    ProblemObjectTransportItem,
    SolutionDirectionTransportItem,
)

from .m30_semantic_bridge import M30SemanticEvaluation
from .m30_slot_ready_requirements import get_m30_slot_ready_requirement
from .presentation_content_candidates import (
    PresentationContentCandidate,
    PresentationContentField,
    PresentationContentSourceIdentity,
    compute_presentation_content_fingerprint,
    validate_presentation_content_candidate,
)
from .problem_structure_transport import is_admitted


class PresentationAcquisitionMode(str, Enum):
    DIRECT = "DIRECT"
    AI_PROPOSAL_REQUIRED = "AI_PROPOSAL_REQUIRED"


@dataclass(frozen=True)
class PresentationFieldAcquisitionRequirement:
    semantic_role: str
    field_role: str
    acquisition_mode: PresentationAcquisitionMode | str
    source_item_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class M30PresentationContentAcquisitionItem:
    semantic_role: str
    source_item_id: str
    direct_candidate: PresentationContentCandidate | None
    required_derivations: tuple[PresentationFieldAcquisitionRequirement, ...]


@dataclass(frozen=True)
class M30PresentationContentAcquisitionProjection:
    items: tuple[M30PresentationContentAcquisitionItem, ...]
    acquisition_plan_complete: bool
    presentation_framing_required: bool
    issues: tuple[str, ...]


_REQUIREMENT_REASON = "canonical semantic value is not sufficient for this presentation field without separately reviewed wording"
_ROLE_ORDER = ("visible_issue", "root_cause", "causal_state", "business_implication", "solution_direction")


def _source_identity(item: object, role: str) -> PresentationContentSourceIdentity:
    return PresentationContentSourceIdentity(
        source_item_id=str(getattr(item, "id", "")),
        semantic_role=role,
        value=str(getattr(item, "value", "")),
    )


def _direct_candidate(item: object, role: str, field_role: str) -> PresentationContentCandidate | None:
    source = _source_identity(item, role)
    candidate = PresentationContentCandidate(
        candidate_id=f"presentation:{source.source_item_id}:{field_role}",
        semantic_role=role,
        fields=(PresentationContentField(field_role, source.value),),
        source_identities=(source,),
        source_fingerprint=compute_presentation_content_fingerprint((source,)),
        derivation_type="DIRECT",
        authority=getattr(item, "authority", ""),
        review_state=getattr(item, "review_state", ""),
        confirmation_authority=getattr(item, "confirmation_authority", None),
    )
    return candidate if not validate_presentation_content_candidate(candidate) else None


def _requirement(role: str, item_id: str, field_role: str) -> PresentationFieldAcquisitionRequirement:
    return PresentationFieldAcquisitionRequirement(
        semantic_role=role,
        field_role=field_role,
        acquisition_mode=PresentationAcquisitionMode.AI_PROPOSAL_REQUIRED,
        source_item_ids=(item_id,),
        reason=_REQUIREMENT_REASON,
    )


def _ordered_items(evaluation: M30SemanticEvaluation) -> tuple[tuple[str, object], ...]:
    by_id = {
        item.id: item
        for item in (
            *evaluation.problem_objects,
            *evaluation.business_implications,
            *((evaluation.solution_direction,) if evaluation.solution_direction else ()),
        )
    }
    distinct_ids = {identity.id for identity in evaluation.distinct_admitted_node_identities}
    ordered: list[tuple[str, object]] = []
    for role in _ROLE_ORDER:
        for identity in evaluation.distinct_admitted_node_identities:
            if identity.role != role or identity.id not in distinct_ids or identity.id not in by_id:
                continue
            item = by_id[identity.id]
            if is_admitted(item):
                ordered.append((role, item))
    if evaluation.admitted_solution_direction_id:
        item = by_id.get(evaluation.admitted_solution_direction_id)
        if item is not None and is_admitted(item):
            ordered.append(("solution_direction", item))
    return tuple(ordered)


def project_m30_presentation_content_acquisition(
    evaluation: M30SemanticEvaluation,
) -> M30PresentationContentAcquisitionProjection:
    """Classify presentation acquisition needs without generating wording."""

    if not isinstance(evaluation, M30SemanticEvaluation):
        raise TypeError("evaluation must be an M30SemanticEvaluation")

    issues: list[str] = []
    if not evaluation.m30_semantic_complete:
        issues.extend(evaluation.incompleteness_reasons or ("M30_SEMANTIC_INCOMPLETE",))

    ordered = _ordered_items(evaluation)
    expected_counts = {"visible_issue": 1, "root_cause": 4, "causal_state": 5, "business_implication": 4, "solution_direction": 1}
    for role, expected in expected_counts.items():
        actual = sum(1 for item_role, _ in ordered if item_role == role)
        if actual != expected:
            issues.append(f"{role.upper()}_ADMITTED_CARDINALITY_INCOMPLETE")

    results: list[M30PresentationContentAcquisitionItem] = []
    for role, item in ordered:
        requirement = get_m30_slot_ready_requirement(role)
        if requirement is None:
            issues.append(f"UNSUPPORTED_M30_ROLE:{role}")
            continue
        item_id = str(item.id)
        if role == "visible_issue":
            direct = None
            missing = tuple(_requirement(role, item_id, field) for field in requirement.required_fields)
        elif role == "root_cause":
            direct = _direct_candidate(item, role, "body")
            missing = (_requirement(role, item_id, "title"),) if direct is not None else tuple(_requirement(role, item_id, field) for field in requirement.required_fields)
        elif role == "causal_state":
            direct = _direct_candidate(item, role, "statement")
            missing = () if direct is not None else (_requirement(role, item_id, "statement"),)
        elif role == "business_implication":
            direct = _direct_candidate(item, role, "body")
            missing = (_requirement(role, item_id, "title"),) if direct is not None else tuple(_requirement(role, item_id, field) for field in requirement.required_fields)
        else:
            direct = _direct_candidate(item, role, "statement")
            missing = () if direct is not None else (_requirement(role, item_id, "statement"),)
        results.append(M30PresentationContentAcquisitionItem(role, item_id, direct, missing))

    return M30PresentationContentAcquisitionProjection(
        items=tuple(results),
        acquisition_plan_complete=not issues and bool(results),
        presentation_framing_required=True,
        issues=tuple(dict.fromkeys(issues)),
    )


__all__ = [
    "M30PresentationContentAcquisitionItem",
    "M30PresentationContentAcquisitionProjection",
    "PresentationAcquisitionMode",
    "PresentationFieldAcquisitionRequirement",
    "project_m30_presentation_content_acquisition",
]
