"""Master-neutral semantic enrichment for Presentation Master V3."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from .approved_fixtures import GapCategory
from .upstream_adapter import (
    DerivationLevel,
    SemanticEnvelope,
    SemanticGap,
    SemanticItem,
    SemanticRelationship,
)


class EnrichmentStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT = "INSUFFICIENT"


@dataclass(frozen=True)
class EnrichmentRule:
    rule_id: str
    semantic_purpose: str
    input_requirement: str
    output_semantic_type: str
    derivation_level: DerivationLevel
    confidence_behavior: str
    provenance_behavior: str
    review_behavior: str


@dataclass(frozen=True)
class AppliedEnrichmentRule:
    rule_id: str
    applied: bool
    derivation_basis: str
    derived_count: int = 0
    requirement_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SemanticRequirement:
    requirement_id: str
    semantic_role: str
    reason: str
    category: GapCategory
    required: bool
    target_group: str
    expected_content_type: str
    provenance_requirement: str
    blocking: bool
    source_basis: str


@dataclass(frozen=True)
class HumanInputRequirement:
    requirement_id: str
    semantic_role: str
    reason: str
    required: bool
    target_group: str
    expected_content_type: str
    provenance_requirement: str
    blocking: bool


@dataclass(frozen=True)
class EvidenceBindingRequirement:
    requirement_id: str
    item_id: str | None
    required_evidence_state: str
    source_binding_required: bool
    review_required: bool
    downstream_consequence: str


@dataclass(frozen=True)
class EnrichmentResult:
    enriched_envelope: SemanticEnvelope
    applied_rules: tuple[AppliedEnrichmentRule, ...]
    derived_items: tuple[SemanticItem, ...]
    derived_groups: tuple[object, ...]
    derived_relationships: tuple[SemanticRelationship, ...]
    unresolved_requirements: tuple[SemanticRequirement, ...]
    human_input_requirements: tuple[HumanInputRequirement, ...]
    evidence_binding_requirements: tuple[EvidenceBindingRequirement, ...]
    confidence_before: float
    confidence_after: float
    review_required: bool
    status: EnrichmentStatus
    traceability: tuple[str, ...]


ENRICHMENT_RULES = (
    EnrichmentRule("derive_explicit_action_sequence", "preserve explicit ordered actions", "two or more ordered action items", "sequence relationship", DerivationLevel.DERIVED, "never above lowest source confidence", "generated/inferred only", "review when source confidence is low"),
    EnrichmentRule("expose_kpi_requirements", "separate KPI intent from KPI value and threshold", "KPI signal without item-level values", "semantic requirements", DerivationLevel.UNRESOLVED, "unchanged", "no evidence promotion", "human input or upstream field required"),
    EnrichmentRule("expose_stage_requirements", "separate roadmap label from ordered stages", "roadmap signal without stage items", "semantic requirements", DerivationLevel.UNRESOLVED, "unchanged", "no stage invention", "upstream structure required"),
    EnrichmentRule("expose_responsibility_requirements", "separate decision maker from accountable owner", "decision context without owner item", "semantic requirements", DerivationLevel.UNRESOLVED, "unchanged", "no owner inference", "human input required"),
    EnrichmentRule("preserve_evidence_binding_boundary", "keep summary evidence distinct from item evidence", "evidence summary without item source binding", "evidence requirement", DerivationLevel.UNRESOLVED, "unchanged", "never promote evidence state", "review required"),
    EnrichmentRule("surface_semantic_conflicts", "surface incompatible semantic identity", "duplicate identity or conflicting explicit owner", "conflict requirement", DerivationLevel.UNRESOLVED, "unchanged", "preserve all source items", "review required"),
)


def _rule(rule_id: str) -> EnrichmentRule:
    return next(rule for rule in ENRICHMENT_RULES if rule.rule_id == rule_id)


def _requirement(
    requirement_id: str,
    role: str,
    reason: str,
    category: GapCategory,
    *,
    target_group: str,
    content_type: str,
    provenance: str,
    blocking: bool = True,
    source_basis: str,
) -> SemanticRequirement:
    return SemanticRequirement(requirement_id, role, reason, category, True, target_group, content_type, provenance, blocking, source_basis)


def _existing_gap_requirements(envelope: SemanticEnvelope) -> list[SemanticRequirement]:
    requirements: list[SemanticRequirement] = []
    for gap in envelope.unresolved_gaps:
        if gap.gap_id == "evidence_item_binding_missing":
            category = GapCategory.EVIDENCE_BINDING_REQUIRED
            role, content_type, group = "evidence", "evidence", "evidence"
        elif gap.gap_id == "kpi_values_missing":
            category = GapCategory.REQUIRES_NEW_UPSTREAM_FIELD
            role, content_type, group = "kpi_value", "metric", "metrics"
        elif gap.gap_id == "stage_items_missing":
            category = GapCategory.REQUIRES_NEW_UPSTREAM_FIELD
            role, content_type, group = "stage", "stage", "stages"
        elif gap.gap_id == "decision_context_unclear":
            category = GapCategory.REQUIRES_HUMAN_INPUT
            role, content_type, group = "decision_context", "decision", "decision"
        elif gap.gap_id == "low_confidence":
            category = GapCategory.REQUIRES_HUMAN_INPUT
            role, content_type, group = "review_confirmation", "review", "review"
        else:
            category = GapCategory.EXISTING_BUT_UNSTRUCTURED
            role, content_type, group = gap.gap_id, "semantic_requirement", "unresolved"
        requirements.append(_requirement(gap.gap_id, role, gap.description, category, target_group=group, content_type=content_type, provenance="source-backed or explicit human input", source_basis=f"existing adapter gap {gap.gap_id}"))
    return requirements


def _add_requirement(requirements: dict[str, SemanticRequirement], requirement: SemanticRequirement) -> None:
    requirements.setdefault(requirement.requirement_id, requirement)


def _derive_action_sequence(envelope: SemanticEnvelope) -> tuple[SemanticRelationship, ...]:
    action_group = next((group for group in envelope.groups if group.group_id == "actions"), None)
    if action_group is None or len(action_group.member_item_ids) < 2:
        return ()
    existing = {(relationship.from_ref, relationship.to_ref, relationship.relationship_type) for relationship in envelope.relationships}
    derived: list[SemanticRelationship] = []
    item_by_id = {item.item_id: item for item in envelope.items}
    for source_id, target_id in zip(action_group.member_item_ids, action_group.member_item_ids[1:]):
        key = (source_id, target_id, "sequence")
        if key in existing or source_id not in item_by_id or target_id not in item_by_id:
            continue
        confidence = min(item_by_id[source_id].confidence, item_by_id[target_id].confidence, envelope.confidence)
        derived.append(SemanticRelationship("sequence", source_id, target_id, confidence, "generated_inferred", DerivationLevel.DERIVED, "explicit order in upstream action group", confidence < 0.75))
    return tuple(derived)


def _conflict_requirements(envelope: SemanticEnvelope) -> tuple[SemanticRequirement, ...]:
    item_ids = [item.item_id for item in envelope.items]
    requirements: list[SemanticRequirement] = []
    if len(item_ids) != len(set(item_ids)):
        requirements.append(_requirement("conflict:duplicate_item_id", "semantic_item_identity", "duplicate item IDs cannot be merged safely", GapCategory.REQUIRES_HUMAN_INPUT, target_group="unresolved", content_type="semantic_item", provenance="explicit source identity", source_basis="duplicate explicit item IDs"))
    owners = [item for item in envelope.items if item.semantic_role in {"owner", "responsibility", "approver", "executor"}]
    if len({item.content for item in owners}) > 1:
        requirements.append(_requirement("conflict:multiple_owners", "responsible_owner", "multiple explicit responsibility values must not be silently chosen", GapCategory.REQUIRES_HUMAN_INPUT, target_group="responsibility", content_type="owner", provenance="explicit human or source-backed input", source_basis="conflicting explicit owner items"))
    return tuple(requirements)


def enrich_semantic_envelope(envelope: SemanticEnvelope) -> EnrichmentResult:
    """Enrich only from the semantic envelope; no master identifier is accepted."""

    requirements: dict[str, SemanticRequirement] = {}
    for requirement in _existing_gap_requirements(envelope):
        _add_requirement(requirements, requirement)

    rule_results: list[AppliedEnrichmentRule] = []
    derived_relationships = _derive_action_sequence(envelope)
    rule_results.append(AppliedEnrichmentRule(_rule("derive_explicit_action_sequence").rule_id, bool(derived_relationships), "explicit ordered action group", derived_count=len(derived_relationships)))

    item_types = {item.content_type for item in envelope.items}
    if "kpi" in envelope.semantic_signals and "metric" not in item_types:
        _add_requirement(requirements, _requirement("kpi:value", "kpi_value", "KPI intent exists but no KPI value is present", GapCategory.REQUIRES_NEW_UPSTREAM_FIELD, target_group="metrics", content_type="metric", provenance="source-backed or explicit human input", source_basis="explicit KPI signal without metric item"))
        _add_requirement(requirements, _requirement("kpi:threshold", "threshold", "threshold is a decision boundary and cannot be inferred", GapCategory.REQUIRES_HUMAN_INPUT, target_group="thresholds", content_type="threshold", provenance="explicit human or source-backed input", source_basis="no explicit threshold semantics"))
        rule_results.append(AppliedEnrichmentRule(_rule("expose_kpi_requirements").rule_id, True, "KPI signal is not treated as a value", requirement_ids=("kpi:value", "kpi:threshold")))
    else:
        rule_results.append(AppliedEnrichmentRule(_rule("expose_kpi_requirements").rule_id, False, "no unsupported KPI inference"))

    has_stage_items = any(item.content_type == "stage" for item in envelope.items)
    if "roadmap" in envelope.semantic_signals and not has_stage_items:
        _add_requirement(requirements, _requirement("stage:explicit_items", "stage", "roadmap label does not provide ordered stage items", GapCategory.REQUIRES_NEW_UPSTREAM_FIELD, target_group="stages", content_type="stage", provenance="source-backed or explicit human input", source_basis="roadmap type without stage records"))
        rule_results.append(AppliedEnrichmentRule(_rule("expose_stage_requirements").rule_id, True, "roadmap label preserved without stage invention", requirement_ids=("stage:explicit_items",)))
    else:
        rule_results.append(AppliedEnrichmentRule(_rule("expose_stage_requirements").rule_id, False, "no unsupported stage inference"))

    responsibility_context = bool(set(envelope.semantic_signals) & {"governance", "escalation", "approval", "handoff", "responsibility", "risk"})
    has_owner = any(
        item.content_type in {"owner", "responsibility"}
        or any(token in item.semantic_role.lower() for token in ("owner", "responsib", "approver", "executor"))
        for item in envelope.items
    )
    if responsibility_context and not has_owner:
        _add_requirement(requirements, _requirement("responsibility:owner", "responsible_owner", "decision maker or persona does not establish accountability", GapCategory.REQUIRES_HUMAN_INPUT, target_group="responsibility", content_type="owner", provenance="explicit human or source-backed input", source_basis="no explicit responsibility item"))
        rule_results.append(AppliedEnrichmentRule(_rule("expose_responsibility_requirements").rule_id, True, "decision context is not promoted to owner", requirement_ids=("responsibility:owner",)))
    else:
        rule_results.append(AppliedEnrichmentRule(_rule("expose_responsibility_requirements").rule_id, False, "explicit responsibility item exists"))

    evidence_items = tuple(item for item in envelope.items if item.content_type == "evidence")
    evidence_requirements: list[EvidenceBindingRequirement] = []
    for item in evidence_items:
        if "evidence_summary" in item.source_field:
            requirement_id = f"evidence_binding:{item.item_id}"
            _add_requirement(requirements, _requirement(requirement_id, "evidence", "summary evidence lacks item-level source binding", GapCategory.EVIDENCE_BINDING_REQUIRED, target_group="evidence", content_type="evidence", provenance="item-level source reference required", source_basis=item.source_field))
            evidence_requirements.append(EvidenceBindingRequirement(requirement_id, item.item_id, "source_backed or evidence_backed", True, True, "candidate remains review-required until binding is supplied"))
    if evidence_requirements:
        rule_results.append(AppliedEnrichmentRule(_rule("preserve_evidence_binding_boundary").rule_id, True, "summary evidence is not promoted", requirement_ids=tuple(item.requirement_id for item in evidence_requirements)))
    else:
        rule_results.append(AppliedEnrichmentRule(_rule("preserve_evidence_binding_boundary").rule_id, False, "no summary-only evidence detected"))

    if len(envelope.groups) > 1 and not any(item.relationship_type != "sequence" for item in envelope.relationships):
        _add_requirement(requirements, _requirement("relationship:direction", "relationship_direction", "group affinity alone does not establish causal or dependency direction", GapCategory.REQUIRES_NEW_UPSTREAM_FIELD, target_group="unresolved", content_type="relationship", provenance="explicit structured relationship or human review", source_basis="no directional relationship basis"))
    rule_results.append(AppliedEnrichmentRule("preserve_relationship_direction_boundary", True, "only explicit order is derivable", requirement_ids=("relationship:direction",)) if "relationship:direction" in requirements else AppliedEnrichmentRule("preserve_relationship_direction_boundary", False, "directional relationships already explicit"))

    conflict_requirements = _conflict_requirements(envelope)
    for requirement in conflict_requirements:
        _add_requirement(requirements, requirement)
    rule_results.append(AppliedEnrichmentRule(_rule("surface_semantic_conflicts").rule_id, bool(conflict_requirements), "explicit identity and owner conflicts are not merged", requirement_ids=tuple(item.requirement_id for item in conflict_requirements)))

    derived_items: tuple[SemanticItem, ...] = ()
    derived_groups: tuple[object, ...] = ()
    all_relationships = envelope.relationships + derived_relationships
    all_requirements = tuple(requirements.values())
    new_gaps = tuple(
        SemanticGap(requirement.requirement_id, requirement.reason, (requirement.semantic_role, requirement.target_group))
        for requirement in all_requirements
        if requirement.requirement_id not in {gap.gap_id for gap in envelope.unresolved_gaps}
    )
    enriched = replace(
        envelope,
        relationships=all_relationships,
        unresolved_gaps=envelope.unresolved_gaps + new_gaps,
        human_review_required=envelope.human_review_required or bool(all_requirements),
        human_review_reasons=envelope.human_review_reasons + tuple(requirement.requirement_id for requirement in all_requirements),
    )
    confidence_after = min([envelope.confidence] + [relationship.confidence for relationship in derived_relationships])
    human_input = tuple(
        HumanInputRequirement(requirement.requirement_id, requirement.semantic_role, requirement.reason, requirement.required, requirement.target_group, requirement.expected_content_type, requirement.provenance_requirement, requirement.blocking)
        for requirement in all_requirements
        if requirement.category == GapCategory.REQUIRES_HUMAN_INPUT
    )
    if not envelope.items:
        status = EnrichmentStatus.INSUFFICIENT
    elif all_requirements:
        status = EnrichmentStatus.REVIEW_REQUIRED
    elif derived_relationships:
        status = EnrichmentStatus.PARTIAL
    else:
        status = EnrichmentStatus.COMPLETE
    traceability = tuple(item.source_field for item in envelope.items) + tuple(relationship.derivation_basis for relationship in derived_relationships)
    return EnrichmentResult(enriched, tuple(rule_results), derived_items, derived_groups, derived_relationships, all_requirements, human_input, tuple(evidence_requirements), envelope.confidence, confidence_after, bool(all_requirements) or envelope.human_review_required, status, traceability)


__all__ = [
    "AppliedEnrichmentRule",
    "ENRICHMENT_RULES",
    "EnrichmentResult",
    "EnrichmentRule",
    "EnrichmentStatus",
    "EvidenceBindingRequirement",
    "HumanInputRequirement",
    "SemanticRequirement",
    "enrich_semantic_envelope",
]
