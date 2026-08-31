"""Explicit, offline resolution of proposal semantic requirements."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .approved_fixtures import GapCategory
from .semantic_enrichment import EnrichmentResult, SemanticRequirement
from .semantic_supplement import (
    ProposalSemanticSupplement,
    SupplementMergeResult,
    SupplementMetric,
    merge_semantic_supplement,
)


class ResolutionSourceType(str, Enum):
    STRATEGY_STRUCTURED = "STRATEGY_STRUCTURED"
    DERIVED_DETERMINISTIC = "DERIVED_DETERMINISTIC"
    PROPOSAL_STRUCTURED = "PROPOSAL_STRUCTURED"
    HUMAN_SUPPLIED = "HUMAN_SUPPLIED"
    SOURCE_REFERENCE = "SOURCE_REFERENCE"
    ITEM_BOUND_EVIDENCE = "ITEM_BOUND_EVIDENCE"
    APPROVED_FIXTURE = "APPROVED_FIXTURE"


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    CONFLICT = "CONFLICT"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class ResolutionRule:
    rule_id: str
    requirement_role: str
    admissible_sources: frozenset[ResolutionSourceType]
    prohibited_basis: tuple[str, ...]
    partial_allowed: bool


@dataclass(frozen=True)
class SemanticResolution:
    requirement_id: str
    semantic_role: str
    original_category: GapCategory | None
    status: ResolutionStatus
    resolved_reference: str | None
    source_type: ResolutionSourceType | None
    source_reference: str | None
    provenance_state: str | None
    confidence: float | None
    resolver_rule_id: str | None
    human_review_required: bool
    conflict_state: str | None
    reason: str


@dataclass(frozen=True)
class ResolutionResult:
    merged_envelope: object
    resolutions: tuple[SemanticResolution, ...]
    resolved_requirement_ids: tuple[str, ...]
    unresolved_requirement_ids: tuple[str, ...]
    conflicts: tuple[object, ...]
    lifecycle: tuple[str, ...]
    status: ResolutionStatus
    merge: SupplementMergeResult


RESOLUTION_RULES = (
    ResolutionRule("resolve_kpi_value", "kpi_value", frozenset({ResolutionSourceType.PROPOSAL_STRUCTURED, ResolutionSourceType.HUMAN_SUPPLIED, ResolutionSourceType.SOURCE_REFERENCE, ResolutionSourceType.APPROVED_FIXTURE}), ("confidence", "generic prose", "template expectation"), True),
    ResolutionRule("resolve_kpi_threshold", "threshold", frozenset({ResolutionSourceType.PROPOSAL_STRUCTURED, ResolutionSourceType.HUMAN_SUPPLIED, ResolutionSourceType.SOURCE_REFERENCE, ResolutionSourceType.APPROVED_FIXTURE}), ("confidence", "generic target", "template expectation"), True),
    ResolutionRule("resolve_explicit_stage", "stage", frozenset({ResolutionSourceType.PROPOSAL_STRUCTURED, ResolutionSourceType.HUMAN_SUPPLIED, ResolutionSourceType.APPROVED_FIXTURE}), ("master-required count", "order inference"), True),
    ResolutionRule("resolve_accountable_owner", "responsible_owner", frozenset({ResolutionSourceType.PROPOSAL_STRUCTURED, ResolutionSourceType.HUMAN_SUPPLIED, ResolutionSourceType.APPROVED_FIXTURE}), ("persona alone", "decision maker alone"), False),
    ResolutionRule("resolve_directional_relationship", "relationship_direction", frozenset({ResolutionSourceType.PROPOSAL_STRUCTURED, ResolutionSourceType.DERIVED_DETERMINISTIC, ResolutionSourceType.APPROVED_FIXTURE}), ("causality from order alone",), False),
    ResolutionRule("resolve_item_evidence", "evidence", frozenset({ResolutionSourceType.ITEM_BOUND_EVIDENCE, ResolutionSourceType.SOURCE_REFERENCE, ResolutionSourceType.APPROVED_FIXTURE}), ("summary-only evidence",), False),
)


def _rule(role: str) -> ResolutionRule:
    return next(rule for rule in RESOLUTION_RULES if rule.requirement_role == role)


def _source_for(value: object, *, approved: bool = False) -> ResolutionSourceType:
    if approved:
        return ResolutionSourceType.APPROVED_FIXTURE
    if getattr(value, "human_supplied", False):
        return ResolutionSourceType.HUMAN_SUPPLIED
    evidence_state = getattr(getattr(value, "evidence_state", None), "value", "")
    if evidence_state == "item_bound_evidence":
        return ResolutionSourceType.ITEM_BOUND_EVIDENCE
    if evidence_state in {"source_reference_available", "human_confirmed_evidence"}:
        return ResolutionSourceType.SOURCE_REFERENCE
    if getattr(value, "source_reference", None):
        return ResolutionSourceType.SOURCE_REFERENCE
    return ResolutionSourceType.PROPOSAL_STRUCTURED


def _metric_resolution(requirement: SemanticRequirement, metrics: tuple[SupplementMetric, ...]) -> SemanticResolution | None:
    if requirement.requirement_id == "kpi:value":
        candidates = tuple(metric for metric in metrics if metric.current_value is not None)
        role = "kpi_value"
        reference_value = "current_value"
    elif requirement.requirement_id == "kpi:threshold":
        candidates = tuple(metric for metric in metrics if metric.threshold is not None)
        role = "threshold"
        reference_value = "threshold"
    else:
        return None
    rule = _rule(role)
    if len(candidates) > 1:
        return SemanticResolution(requirement.requirement_id, role, requirement.category, ResolutionStatus.CONFLICT, None, None, None, None, None, rule.rule_id, True, "multiple_candidates", "multiple explicit candidates must be reviewed")
    if not candidates:
        return None
    metric = candidates[0]
    source_type = _source_for(metric)
    if source_type not in rule.admissible_sources:
        return SemanticResolution(requirement.requirement_id, role, requirement.category, ResolutionStatus.UNRESOLVED, None, source_type, metric.source_binding, metric.provenance_state, metric.confidence, rule.rule_id, True, None, "candidate source is not admissible")
    return SemanticResolution(requirement.requirement_id, role, requirement.category, ResolutionStatus.RESOLVED, f"supplement:metric:{metric.metric_id}:{reference_value}", source_type, metric.source_binding, metric.provenance_state, metric.confidence, rule.rule_id, metric.review_required, None, "explicit KPI component supplied")


def _resolve_requirement(requirement: SemanticRequirement, supplement: ProposalSemanticSupplement, merge: SupplementMergeResult) -> SemanticResolution:
    metric_result = _metric_resolution(requirement, supplement.metrics)
    if metric_result is not None:
        return metric_result
    rule = _rule(requirement.semantic_role) if requirement.semantic_role in {item.requirement_role for item in RESOLUTION_RULES} else None
    if requirement.requirement_id in merge.resolved_requirements:
        if requirement.requirement_id == "stage:explicit_items":
            value = supplement.stages[0]
            return SemanticResolution(requirement.requirement_id, requirement.semantic_role, requirement.category, ResolutionStatus.RESOLVED, f"supplement:stage:{value.stage_id}", _source_for(value), value.source_binding, value.provenance_state, value.confidence, "resolve_explicit_stage", value.review_required, None, "explicit ordered stages supplied")
        if requirement.requirement_id == "responsibility:owner":
            value = next(item for item in supplement.responsibilities if item.role == "accountable_owner")
            return SemanticResolution(requirement.requirement_id, requirement.semantic_role, requirement.category, ResolutionStatus.RESOLVED, f"supplement:responsibility:{value.assignment_id}", _source_for(value), value.source_binding, value.provenance_state, value.confidence, "resolve_accountable_owner", value.review_required, None, "explicit accountable owner supplied")
        if requirement.requirement_id == "relationship:direction":
            value = supplement.relationships[0]
            return SemanticResolution(requirement.requirement_id, requirement.semantic_role, requirement.category, ResolutionStatus.RESOLVED, f"relationship:{value.from_ref}->{value.to_ref}", _source_for(value), value.derivation_basis, value.provenance_state, value.confidence, "resolve_directional_relationship", value.human_review_required, None, "explicit directional relationship supplied")
        if requirement.category == GapCategory.EVIDENCE_BINDING_REQUIRED:
            value = next(item for item in supplement.evidence_bindings if item.item_id in requirement.requirement_id)
            source_type = ResolutionSourceType.ITEM_BOUND_EVIDENCE if value.evidence_state.value == "item_bound_evidence" else ResolutionSourceType.SOURCE_REFERENCE
            return SemanticResolution(requirement.requirement_id, requirement.semantic_role, requirement.category, ResolutionStatus.RESOLVED, value.item_id, source_type, value.source_reference, value.provenance_state, None, "resolve_item_evidence", value.review_required, None, "item-level evidence binding supplied")
    status = ResolutionStatus.CONFLICT if any(conflict.semantic_role == requirement.semantic_role for conflict in merge.conflicts) else ResolutionStatus.UNRESOLVED
    return SemanticResolution(requirement.requirement_id, requirement.semantic_role, requirement.category, status, None, None, None, None, None, rule.rule_id if rule else None, True, "conflict" if status == ResolutionStatus.CONFLICT else None, "no admissible explicit input satisfied the requirement")


def resolve_semantic_inputs(enrichment: EnrichmentResult, supplement: ProposalSemanticSupplement) -> ResolutionResult:
    """Resolve requirements, then merge valid supplemental semantics offline."""

    merge = merge_semantic_supplement(enrichment, supplement)
    component_resolutions: list[SemanticResolution] = []
    for metric in supplement.metrics:
        source_type = _source_for(metric)
        if metric.target_value is not None:
            component_resolutions.append(SemanticResolution(f"metric:{metric.metric_id}:target", "kpi_target", None, ResolutionStatus.RESOLVED, f"supplement:metric:{metric.metric_id}:target", source_type, metric.source_binding, metric.provenance_state, metric.confidence, "resolve_kpi_value", metric.review_required, None, "explicit KPI target supplied"))
        if metric.name:
            component_resolutions.append(SemanticResolution(f"metric:{metric.metric_id}:name", "kpi_name", None, ResolutionStatus.RESOLVED, f"supplement:metric:{metric.metric_id}:name", source_type, metric.source_binding, metric.provenance_state, metric.confidence, "resolve_kpi_value", metric.review_required, None, "explicit KPI name supplied"))
    resolutions = tuple(component_resolutions) + tuple(_resolve_requirement(requirement, supplement, merge) for requirement in enrichment.unresolved_requirements)
    resolved = tuple(item.requirement_id for item in resolutions if item.status == ResolutionStatus.RESOLVED)
    unresolved = tuple(item.requirement_id for item in resolutions if item.status in {ResolutionStatus.UNRESOLVED, ResolutionStatus.PARTIALLY_RESOLVED, ResolutionStatus.REVIEW_REQUIRED, ResolutionStatus.CONFLICT})
    lifecycle = tuple(f"{item.requirement_id}:created→candidate_found→admissibility_validated→{item.status.value.lower()}" for item in resolutions)
    if merge.conflicts or any(item.status == ResolutionStatus.CONFLICT for item in resolutions):
        status = ResolutionStatus.CONFLICT
    elif resolved and unresolved:
        status = ResolutionStatus.PARTIALLY_RESOLVED
    elif resolved:
        status = ResolutionStatus.RESOLVED
    else:
        status = ResolutionStatus.UNRESOLVED
    return ResolutionResult(merge.merged_envelope, resolutions, resolved, unresolved, merge.conflicts, lifecycle, status, merge)


__all__ = ["RESOLUTION_RULES", "ResolutionResult", "ResolutionRule", "ResolutionSourceType", "ResolutionStatus", "SemanticResolution", "resolve_semantic_inputs"]
