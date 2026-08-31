"""Renderer-neutral proposal semantic supplements and offline merge contract.

This module carries explicit proposal/business semantics that are not safe to
derive from StrategyBrief.  It deliberately has no knowledge of masters,
templates, slides, or rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Any

from .approved_fixtures import GapCategory
from .definitions import ALLOWED_PROVENANCE_STATES, SUPPORTED_RELATIONSHIP_TYPES
from .semantic_enrichment import (
    EnrichmentResult,
    EvidenceBindingRequirement,
    HumanInputRequirement,
    SemanticRequirement,
)
from .upstream_adapter import (
    DerivationLevel,
    SemanticEnvelope,
    SemanticGap,
    SemanticGroup,
    SemanticItem,
    SemanticRelationship,
)


class EvidenceState(str, Enum):
    NONE = "none"
    SUMMARY_ONLY = "summary_evidence_only"
    SOURCE_REFERENCE = "source_reference_available"
    ITEM_BOUND = "item_bound_evidence"
    HUMAN_CONFIRMED = "human_confirmed_evidence"


class SupplementMergeStatus(str, Enum):
    MERGED = "MERGED"
    PARTIAL = "PARTIAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True)
class SupplementMetric:
    metric_id: str
    name: str
    current_value: float | str | None = None
    target_value: float | str | None = None
    threshold: float | str | None = None
    unit: str | None = None
    comparison_operator: str | None = None
    measurement_period: str | None = None
    provenance_state: str = "supplied"
    source_binding: str = ""
    evidence_state: EvidenceState = EvidenceState.NONE
    human_supplied: bool = False
    review_required: bool = False
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.metric_id.strip() or not self.name.strip():
            raise ValueError("metric_id and name are required")
        _validate_provenance(self.provenance_state)
        _validate_confidence(self.confidence)
        if self.current_value is None and self.target_value is None and self.threshold is None:
            raise ValueError("a metric must contain at least one explicit value")
        if self.human_supplied and self.provenance_state in {"source_backed", "evidence_backed"}:
            raise ValueError("human-supplied semantics cannot be source-backed automatically")


@dataclass(frozen=True)
class DecisionCondition:
    condition_id: str
    semantic_meaning: str
    referenced_metric_id: str | None = None
    operator: str | None = None
    value: float | str | None = None
    outcome: str = ""
    provenance_state: str = "supplied"
    source_binding: str = ""
    human_supplied: bool = False
    review_required: bool = False
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.condition_id.strip() or not self.semantic_meaning.strip() or not self.outcome.strip():
            raise ValueError("decision conditions require identity, meaning, and outcome")
        _validate_provenance(self.provenance_state)
        _validate_confidence(self.confidence)
        if self.human_supplied and self.provenance_state in {"source_backed", "evidence_backed"}:
            raise ValueError("human-supplied conditions cannot be source-backed automatically")


@dataclass(frozen=True)
class ProposalStage:
    stage_id: str
    name: str
    semantic_purpose: str
    order: int
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    responsible_party: str | None = None
    exit_criterion_id: str | None = None
    provenance_state: str = "supplied"
    source_binding: str = ""
    human_supplied: bool = False
    review_required: bool = False
    confidence: float = 0.0

    def __post_init__(self) -> None:
        if not self.stage_id.strip() or not self.name.strip() or not self.semantic_purpose.strip():
            raise ValueError("stages require identity, name, and purpose")
        if self.order < 0:
            raise ValueError("stage order must be non-negative")
        _validate_provenance(self.provenance_state)
        _validate_confidence(self.confidence)


@dataclass(frozen=True)
class ResponsibilityAssignment:
    assignment_id: str
    party: str
    role: str
    target_id: str
    provenance_state: str = "supplied"
    source_binding: str = ""
    human_supplied: bool = False
    review_required: bool = False
    confidence: float = 0.0

    def __post_init__(self) -> None:
        valid_roles = {"stakeholder", "accountable_owner", "responsible_executor", "approver", "decision_maker", "escalation_owner", "consulted_party"}
        if not self.assignment_id.strip() or not self.party.strip() or not self.target_id.strip() or self.role not in valid_roles:
            raise ValueError("responsibility assignment has invalid identity or role")
        _validate_provenance(self.provenance_state)
        _validate_confidence(self.confidence)


@dataclass(frozen=True)
class SupplementEvidenceBinding:
    binding_id: str
    item_id: str
    evidence_state: EvidenceState
    source_reference: str | None = None
    provenance_state: str = "supplied"
    review_required: bool = True
    human_supplied: bool = False

    def __post_init__(self) -> None:
        if not self.binding_id.strip() or not self.item_id.strip():
            raise ValueError("evidence binding requires binding and item IDs")
        if self.evidence_state in {EvidenceState.SOURCE_REFERENCE, EvidenceState.ITEM_BOUND, EvidenceState.HUMAN_CONFIRMED} and not self.source_reference:
            raise ValueError("bound evidence requires a source reference")
        _validate_provenance(self.provenance_state)
        if self.human_supplied and self.provenance_state in {"source_backed", "evidence_backed"}:
            raise ValueError("human evidence confirmation cannot upgrade provenance automatically")


@dataclass(frozen=True)
class ProposalSemanticSupplement:
    semantic_items: tuple[SemanticItem, ...] = ()
    groups: tuple[SemanticGroup, ...] = ()
    relationships: tuple[SemanticRelationship, ...] = ()
    metrics: tuple[SupplementMetric, ...] = ()
    decision_conditions: tuple[DecisionCondition, ...] = ()
    stages: tuple[ProposalStage, ...] = ()
    responsibilities: tuple[ResponsibilityAssignment, ...] = ()
    evidence_bindings: tuple[SupplementEvidenceBinding, ...] = ()
    confidence: float = 0.0
    provenance_state: str = "supplied"
    review_required: bool = False

    def __post_init__(self) -> None:
        _validate_provenance(self.provenance_state)
        _validate_confidence(self.confidence)
        if len({item.item_id for item in self.semantic_items}) != len(self.semantic_items):
            raise ValueError("supplement semantic item IDs must be unique")
        if len({metric.metric_id for metric in self.metrics}) != len(self.metrics):
            raise ValueError("supplement metric IDs must be unique")
        orders = [stage.order for stage in self.stages]
        if len(orders) != len(set(orders)):
            raise ValueError("supplement stage order must be unique")
        for relationship in self.relationships:
            if relationship.relationship_type not in SUPPORTED_RELATIONSHIP_TYPES:
                raise ValueError(f"unsupported relationship type: {relationship.relationship_type}")


@dataclass(frozen=True)
class SemanticConflict:
    conflict_id: str
    semantic_role: str
    upstream_values: tuple[str, ...]
    supplement_values: tuple[str, ...]
    reason: str
    review_required: bool = True


@dataclass(frozen=True)
class SupplementMergeResult:
    merged_envelope: SemanticEnvelope
    resolved_requirements: tuple[str, ...]
    unresolved_requirements: tuple[SemanticRequirement, ...]
    unresolved_human_inputs: tuple[HumanInputRequirement, ...]
    unresolved_evidence_bindings: tuple[EvidenceBindingRequirement, ...]
    conflicts: tuple[SemanticConflict, ...]
    normalized_duplicate_ids: tuple[str, ...]
    gap_history: tuple[SemanticGap, ...]
    status: SupplementMergeStatus
    traceability: tuple[str, ...]


def _validate_provenance(value: str) -> None:
    if value not in ALLOWED_PROVENANCE_STATES:
        raise ValueError(f"unsupported provenance state: {value}")


def _validate_confidence(value: float) -> None:
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError("confidence must be between 0 and 1")


def _metric_item(metric: SupplementMetric) -> SemanticItem:
    parts = [metric.name]
    if metric.current_value is not None:
        parts.append(f"current={metric.current_value}")
    if metric.target_value is not None:
        parts.append(f"target={metric.target_value}")
    if metric.threshold is not None:
        parts.append(f"threshold={metric.threshold}")
    return SemanticItem(
        f"supplement:metric:{metric.metric_id}", "metric", " | ".join(parts), "metric",
        metric.provenance_state, metric.evidence_state.value, metric.confidence,
        metric.review_required, metric.source_binding or f"ProposalSemanticSupplement.metrics[{metric.metric_id}]",
        DerivationLevel.DIRECT, "explicit supplemental metric semantics",
    )


def _stage_item(stage: ProposalStage) -> SemanticItem:
    return SemanticItem(
        f"supplement:stage:{stage.stage_id}", "stage", stage.name, "stage",
        stage.provenance_state, "unverified", stage.confidence, stage.review_required,
        stage.source_binding or f"ProposalSemanticSupplement.stages[{stage.stage_id}]",
        DerivationLevel.DIRECT, "explicit supplemental stage semantics",
    )


def _responsibility_item(assignment: ResponsibilityAssignment) -> SemanticItem:
    return SemanticItem(
        f"supplement:responsibility:{assignment.assignment_id}", assignment.role, assignment.party, "owner",
        assignment.provenance_state, "unverified", assignment.confidence, assignment.review_required,
        assignment.source_binding or f"ProposalSemanticSupplement.responsibilities[{assignment.assignment_id}]",
        DerivationLevel.DIRECT, "explicit supplemental responsibility semantics",
    )


def _condition_item(condition: DecisionCondition) -> SemanticItem:
    value = "" if condition.value is None else f" {condition.operator or ''} {condition.value}"
    return SemanticItem(
        f"supplement:condition:{condition.condition_id}", condition.semantic_meaning, f"{condition.outcome}{value}".strip(), "criterion",
        condition.provenance_state, "unverified", condition.confidence, condition.review_required,
        condition.source_binding or f"ProposalSemanticSupplement.decision_conditions[{condition.condition_id}]",
        DerivationLevel.DIRECT, "explicit supplemental decision condition",
    )


def _as_tuple(values: list[Any]) -> tuple[Any, ...]:
    return tuple(values)


def _requirement_satisfied(requirement: SemanticRequirement, supplement: ProposalSemanticSupplement) -> bool:
    role = requirement.semantic_role
    if requirement.requirement_id in {"kpi:value", "kpi:threshold"}:
        return any((metric.current_value is not None if role == "kpi_value" else metric.threshold is not None) for metric in supplement.metrics)
    if requirement.requirement_id == "stage:explicit_items":
        return bool(supplement.stages)
    if requirement.requirement_id == "responsibility:owner":
        return any(assignment.role == "accountable_owner" for assignment in supplement.responsibilities)
    if requirement.requirement_id == "relationship:direction":
        return bool(supplement.relationships)
    if requirement.category == GapCategory.EVIDENCE_BINDING_REQUIRED:
        return any(binding.item_id in requirement.requirement_id for binding in supplement.evidence_bindings)
    if role == "decision_context":
        return any(assignment.role == "decision_maker" for assignment in supplement.responsibilities)
    if role == "review_confirmation":
        return supplement.review_required
    return False


def _find_conflicts(envelope: SemanticEnvelope, supplement: ProposalSemanticSupplement) -> tuple[SemanticConflict, ...]:
    conflicts: list[SemanticConflict] = []
    upstream_by_id = {item.item_id: item for item in envelope.items}
    for item in supplement.semantic_items:
        if item.item_id in upstream_by_id and (item.content != upstream_by_id[item.item_id].content or item.semantic_role != upstream_by_id[item.item_id].semantic_role):
            conflicts.append(SemanticConflict(f"conflict:item:{item.item_id}", item.semantic_role, (upstream_by_id[item.item_id].content,), (item.content,), "same identity has incompatible explicit content"))
    upstream_metrics = {item.item_id: item.content for item in envelope.items if item.content_type == "metric"}
    for metric in supplement.metrics:
        key = f"supplement:metric:{metric.metric_id}"
        if key in upstream_metrics and metric.name not in upstream_metrics[key]:
            conflicts.append(SemanticConflict(f"conflict:metric:{metric.metric_id}", "metric", (upstream_metrics[key],), (metric.name,), "same metric identity has incompatible meaning"))
    owners = {item.content for item in envelope.items if item.semantic_role in {"owner", "responsibility", "accountable_owner"}}
    supplemental_owners = {assignment.party for assignment in supplement.responsibilities if assignment.role == "accountable_owner"}
    if owners and supplemental_owners and not supplemental_owners.issubset(owners):
        conflicts.append(SemanticConflict("conflict:accountable_owner", "accountable_owner", tuple(sorted(owners)), tuple(sorted(supplemental_owners)), "upstream and supplemental accountability disagree"))
    return tuple(conflicts)


def merge_semantic_supplement(enrichment: EnrichmentResult, supplement: ProposalSemanticSupplement) -> SupplementMergeResult:
    """Merge explicit supplemental semantics without silent overwrite."""

    envelope = enrichment.enriched_envelope
    conflicts = _find_conflicts(envelope, supplement)
    existing_items = {item.item_id: item for item in envelope.items}
    normalized: list[str] = []
    added_items: list[SemanticItem] = []
    candidates = list(supplement.semantic_items) + [_metric_item(metric) for metric in supplement.metrics] + [_stage_item(stage) for stage in supplement.stages] + [_responsibility_item(item) for item in supplement.responsibilities] + [_condition_item(item) for item in supplement.decision_conditions]
    for item in candidates:
        if item.item_id in existing_items:
            if item == existing_items[item.item_id]:
                normalized.append(item.item_id)
            continue
        existing_items[item.item_id] = item
        added_items.append(item)

    group_members = {group.group_id: list(group.member_item_ids) for group in envelope.groups}
    for item in added_items:
        group_id = {"metric": "metrics", "stage": "stages", "owner": "responsibility", "criterion": "decision"}.get(item.content_type, "supplement")
        group_members.setdefault(group_id, []).append(item.item_id)
    groups = list(envelope.groups)
    known_groups = {group.group_id for group in groups}
    for group_id, members in group_members.items():
        if group_id not in known_groups and members:
            groups.append(SemanticGroup(group_id, f"supplemental {group_id} semantics", tuple(members), False, DerivationLevel.DIRECT, "explicit supplemental group"))
        elif group_id in known_groups:
            index = next(index for index, group in enumerate(groups) if group.group_id == group_id)
            groups[index] = replace(groups[index], member_item_ids=tuple(dict.fromkeys(members)))

    relationships = list(envelope.relationships)
    existing_relationships = {(item.relationship_type, item.from_ref, item.to_ref) for item in relationships}
    for relationship in supplement.relationships:
        key = (relationship.relationship_type, relationship.from_ref, relationship.to_ref)
        if key not in existing_relationships:
            relationships.append(relationship)

    evidence_profile = set(envelope.evidence_profile)
    for binding in supplement.evidence_bindings:
        evidence_profile.add(binding.evidence_state.value)
        if binding.item_id in existing_items:
            item = existing_items[binding.item_id]
            binding_trace = f"binding:{binding.binding_id}|source:{binding.source_reference or binding.binding_id}"
            source_field = item.source_field if binding_trace in item.source_field else f"{item.source_field}|{binding_trace}"
            existing_items[binding.item_id] = replace(item, evidence_state=binding.evidence_state.value, source_field=source_field)
    signals = set(envelope.semantic_signals)
    if supplement.metrics:
        signals.update({"kpi", "metric"})
        if any(metric.threshold is not None for metric in supplement.metrics):
            signals.add("threshold")
    if supplement.stages:
        signals.update({"roadmap", "staged", "stage"})
    if supplement.responsibilities:
        signals.update({assignment.role for assignment in supplement.responsibilities})
        if any(assignment.role == "escalation_owner" for assignment in supplement.responsibilities):
            signals.add("escalation")
    if supplement.decision_conditions:
        signals.update({"decision_boundary"})
        if any(condition.outcome.lower() in {"go", "hold"} for condition in supplement.decision_conditions):
            signals.add("go_hold")
    resolved = tuple(requirement.requirement_id for requirement in enrichment.unresolved_requirements if _requirement_satisfied(requirement, supplement))
    unresolved = tuple(requirement for requirement in enrichment.unresolved_requirements if requirement.requirement_id not in resolved)
    unresolved_human = tuple(item for item in enrichment.human_input_requirements if item.requirement_id not in resolved)
    unresolved_evidence = tuple(item for item in enrichment.evidence_binding_requirements if item.requirement_id not in resolved)
    conflict_gaps = tuple(SemanticGap(item.conflict_id, item.reason, (item.semantic_role,)) for item in conflicts)
    gap_history = envelope.unresolved_gaps + conflict_gaps
    merged = replace(
        envelope,
        items=tuple(existing_items.values()),
        groups=tuple(groups),
        relationships=tuple(relationships),
        evidence_profile=frozenset(evidence_profile),
        semantic_signals=frozenset(signals),
        unresolved_gaps=gap_history,
        confidence=min(envelope.confidence, supplement.confidence) if supplement.confidence else envelope.confidence,
        human_review_required=envelope.human_review_required or supplement.review_required or bool(conflicts) or bool(unresolved),
        human_review_reasons=envelope.human_review_reasons + tuple(item.conflict_id for item in conflicts),
    )
    if not merged.items:
        status = SupplementMergeStatus.INSUFFICIENT
    elif conflicts:
        status = SupplementMergeStatus.REVIEW_REQUIRED
    elif unresolved:
        status = SupplementMergeStatus.PARTIAL
    else:
        status = SupplementMergeStatus.MERGED
    traceability = tuple(item.source_field for item in added_items) + tuple(binding.source_reference or binding.binding_id for binding in supplement.evidence_bindings)
    return SupplementMergeResult(merged, resolved, unresolved, unresolved_human, unresolved_evidence, conflicts, tuple(normalized), gap_history, status, traceability)


__all__ = [
    "DecisionCondition", "EvidenceState", "ProposalSemanticSupplement", "ProposalStage",
    "ResponsibilityAssignment", "SemanticConflict", "SupplementEvidenceBinding", "SupplementMergeResult",
    "SupplementMergeStatus", "SupplementMetric", "merge_semantic_supplement",
]
