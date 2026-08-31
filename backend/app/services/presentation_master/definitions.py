"""Renderer-neutral Presentation Master V3 definitions.

This module describes what a master means and what content it accepts.  It
deliberately contains no rendering, file, or runtime-routing dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping


SUPPORTED_RELATIONSHIP_TYPES = frozenset(
    {
        "sequence",
        "causality",
        "dependency",
        "hierarchy",
        "convergence",
        "feedback",
        "decision_boundary",
        "handoff",
    }
)

ALLOWED_PROVENANCE_STATES = frozenset(
    {"supplied", "source_backed", "generated_inferred", "evidence_backed", "unverified"}
)
ALLOWED_MISSING_EVIDENCE_BEHAVIORS = frozenset(
    {"omit", "explicit_unverified_state", "human_review", "defined_degradation"}
)


@dataclass(frozen=True)
class Cardinality:
    min_items: int = 0
    max_items: int | None = None


@dataclass(frozen=True)
class InformationGroup:
    group_id: str
    semantic_purpose: str
    required: bool = True
    cardinality: Cardinality = field(default_factory=Cardinality)


@dataclass(frozen=True)
class SlotDefinition:
    slot_id: str
    semantic_role: str
    required: bool
    content_type: str
    cardinality: Cardinality = field(default_factory=Cardinality)
    parent_group: str = ""
    relationship_participation: tuple[str, ...] = ()
    text_limit_hint: int | None = None


@dataclass(frozen=True)
class RelationshipDefinition:
    relationship_type: str
    from_ref: str
    to_ref: str
    semantic_meaning: str


@dataclass(frozen=True)
class ConstraintPolicy:
    density_intent: str
    whitespace_intent: str
    hierarchy_requirements: tuple[str, ...]
    overflow_behavior: tuple[str, ...]
    degradation_policy: tuple[str, ...]
    likely_overflow_slots: tuple[str, ...] = ()
    max_text_chars: int | None = None


@dataclass(frozen=True)
class ProvenancePolicy:
    required: bool = True
    allowed_states: frozenset[str] = frozenset(ALLOWED_PROVENANCE_STATES)
    source_binding_required: bool = True
    fake_evidence_allowed: bool = False
    missing_evidence_behavior: tuple[str, ...] = ("omit", "explicit_unverified_state", "human_review")


@dataclass(frozen=True)
class EditabilityPolicy:
    required_tier: int = 1
    native_text_required: bool = True
    native_shape_required: bool = True
    rasterization_allowed: bool = False


@dataclass(frozen=True)
class MasterDefinition:
    master_id: str
    version: str
    name: str
    semantic_purpose: str
    intended_use: str
    narrative_role: str
    information_pattern: str
    required_evidence_pattern: str
    semantic_spine: tuple[str, ...]
    information_groups: tuple[InformationGroup, ...]
    hierarchy: tuple[str, ...]
    reading_order: tuple[str, ...]
    relationships: tuple[RelationshipDefinition, ...]
    slots: tuple[SlotDefinition, ...]
    constraints: ConstraintPolicy
    provenance: ProvenancePolicy
    editability: EditabilityPolicy


class MasterDefinitionValidationError(ValueError):
    """Raised when a master definition violates the renderer-neutral contract."""

    def __init__(self, issues: Iterable[str]):
        self.issues = tuple(issues)
        super().__init__("; ".join(self.issues))


def _validate_cardinality(cardinality: Cardinality, label: str, issues: list[str]) -> None:
    if cardinality.min_items < 0:
        issues.append(f"{label}.min_items must be non-negative")
    if cardinality.max_items is not None and cardinality.max_items < 0:
        issues.append(f"{label}.max_items must be non-negative")
    if cardinality.max_items is not None and cardinality.max_items < cardinality.min_items:
        issues.append(f"{label} has impossible min/max cardinality")


def validate_definition(definition: MasterDefinition) -> tuple[str, ...]:
    """Return all contract violations; raise the typed error if any exist."""

    issues: list[str] = []
    for field_name in ("master_id", "version", "name", "semantic_purpose", "intended_use"):
        if not getattr(definition, field_name).strip():
            issues.append(f"missing required identity field: {field_name}")

    if len(definition.semantic_spine) < 2:
        issues.append("definition has no semantic structure")

    group_ids = [group.group_id for group in definition.information_groups]
    slot_ids = [slot.slot_id for slot in definition.slots]
    group_set = set(group_ids)
    slot_set = set(slot_ids)
    known_refs = group_set | slot_set
    if len(group_ids) != len(group_set):
        issues.append("duplicate information group IDs")
    if len(slot_ids) != len(slot_set):
        issues.append("duplicate slot IDs")

    for group in definition.information_groups:
        if not group.group_id.strip() or not group.semantic_purpose.strip():
            issues.append("information groups require an ID and semantic purpose")
        _validate_cardinality(group.cardinality, f"group {group.group_id}", issues)
    for slot in definition.slots:
        if not slot.slot_id.strip() or not slot.semantic_role.strip() or not slot.content_type.strip():
            issues.append(f"slot {slot.slot_id!r} is missing semantic metadata")
        if slot.parent_group not in group_set:
            issues.append(f"slot {slot.slot_id!r} references an unknown group")
        if slot.text_limit_hint is not None and slot.text_limit_hint <= 0:
            issues.append(f"slot {slot.slot_id!r} has an invalid text limit")
        _validate_cardinality(slot.cardinality, f"slot {slot.slot_id}", issues)
        unsupported = set(slot.relationship_participation) - SUPPORTED_RELATIONSHIP_TYPES
        if unsupported:
            issues.append(f"slot {slot.slot_id!r} has unsupported relationship types: {sorted(unsupported)}")

    if not definition.hierarchy:
        issues.append("hierarchy must not be empty")
    if any(ref not in known_refs for ref in definition.hierarchy):
        issues.append("hierarchy references an unknown slot or group")

    if not definition.reading_order or len(set(definition.reading_order)) != len(definition.reading_order):
        issues.append("reading order is empty or contains duplicates")
    elif set(definition.reading_order) != group_set:
        issues.append("reading order must contain each information group exactly once")

    for relationship in definition.relationships:
        if relationship.relationship_type not in SUPPORTED_RELATIONSHIP_TYPES:
            issues.append(f"unsupported relationship type: {relationship.relationship_type}")
        if relationship.from_ref not in known_refs or relationship.to_ref not in known_refs:
            issues.append("relationship references a nonexistent slot or group")
        if not relationship.semantic_meaning.strip():
            issues.append("relationships require semantic meaning")

    if not definition.provenance.required:
        issues.append("required provenance policy is missing")
    if definition.provenance.fake_evidence_allowed:
        issues.append("fake evidence is not permitted")
    if not definition.provenance.allowed_states <= ALLOWED_PROVENANCE_STATES:
        issues.append("provenance policy contains unsupported evidence states")
    if not definition.provenance.missing_evidence_behavior:
        issues.append("missing evidence behavior is required")
    elif not set(definition.provenance.missing_evidence_behavior) <= ALLOWED_MISSING_EVIDENCE_BEHAVIORS:
        issues.append("provenance policy contains unsupported missing-evidence behavior")

    if definition.editability.required_tier < 1:
        issues.append("required editability tier must be at least Tier 1")
    if not definition.editability.native_text_required or not definition.editability.native_shape_required:
        issues.append("native text and native shape editability are required")
    if definition.editability.rasterization_allowed:
        issues.append("raster-only definitions are not permitted")

    _validate_cardinality(
        Cardinality(definition.constraints.max_text_chars or 0, definition.constraints.max_text_chars),
        "constraints.max_text_chars",
        issues,
    ) if definition.constraints.max_text_chars is not None else None
    if not definition.constraints.density_intent.strip() or not definition.constraints.whitespace_intent.strip():
        issues.append("density and whitespace intent are required")
    if not definition.constraints.overflow_behavior or not definition.constraints.degradation_policy:
        issues.append("overflow and degradation behavior are required")
    if any(slot_id not in slot_set for slot_id in definition.constraints.likely_overflow_slots):
        issues.append("likely overflow slot is unknown")

    if issues:
        raise MasterDefinitionValidationError(issues)
    return ()


def validate_registry(definitions: Iterable[MasterDefinition]) -> tuple[MasterDefinition, ...]:
    definitions = tuple(definitions)
    ids = [definition.master_id for definition in definitions]
    issues = ["duplicate master IDs"] if len(ids) != len(set(ids)) else []
    for definition in definitions:
        try:
            validate_definition(definition)
        except MasterDefinitionValidationError as error:
            issues.extend(f"{definition.master_id}: {issue}" for issue in error.issues)
    if issues:
        raise MasterDefinitionValidationError(issues)
    return definitions


class MasterRegistry:
    """Read-only lookup registry; selection and rendering are separate phases."""

    def __init__(self, definitions: Iterable[MasterDefinition]):
        self._definitions = validate_registry(definitions)
        self._by_id: Mapping[str, MasterDefinition] = {
            definition.master_id: definition for definition in self._definitions
        }

    def list_ids(self) -> tuple[str, ...]:
        return tuple(self._by_id)

    def all(self) -> tuple[MasterDefinition, ...]:
        return self._definitions

    def get(self, master_id: str) -> MasterDefinition:
        return self._by_id[master_id]


def _groups(*items: tuple[str, str, bool, int, int | None]) -> tuple[InformationGroup, ...]:
    return tuple(
        InformationGroup(group_id, purpose, required, Cardinality(min_items, max_items))
        for group_id, purpose, required, min_items, max_items in items
    )


def _slots(*items: tuple[str, str, bool, str, str, int, int | None, tuple[str, ...], int | None]) -> tuple[SlotDefinition, ...]:
    return tuple(
        SlotDefinition(
            slot_id,
            role,
            required,
            content_type,
            Cardinality(min_items, max_items),
            parent_group,
            relationships,
            text_limit,
        )
        for slot_id, role, required, content_type, parent_group, min_items, max_items, relationships, text_limit in items
    )


def _definition(
    master_id: str,
    name: str,
    purpose: str,
    use_case: str,
    role: str,
    pattern: str,
    evidence: str,
    spine: tuple[str, ...],
    groups: tuple[InformationGroup, ...],
    slots: tuple[SlotDefinition, ...],
    relationships: tuple[RelationshipDefinition, ...],
    *,
    density: str = "medium",
    overflow: tuple[str, ...] = ("shorten", "reflow", "human_review"),
    likely_overflow: tuple[str, ...] = (),
) -> MasterDefinition:
    return MasterDefinition(
        master_id,
        "presentation_master_v3_definition_v1",
        name,
        purpose,
        use_case,
        role,
        pattern,
        evidence,
        spine,
        groups,
        tuple(group.group_id for group in groups),
        tuple(group.group_id for group in groups),
        relationships,
        slots,
        ConstraintPolicy(
            density,
            "preserve separation between semantic groups",
            ("group hierarchy remains explicit", "reading order remains stable"),
            overflow,
            ("D1_spacing_adjustment", "D2_content_reduction", "D3_human_review"),
            likely_overflow,
            900,
        ),
        ProvenancePolicy(),
        EditabilityPolicy(),
    )


def _rel(kind: str, source: str, target: str, meaning: str) -> RelationshipDefinition:
    return RelationshipDefinition(kind, source, target, meaning)


M45 = _definition(
    "M45", "Thesis Proof Implication", "Connect a claim to proof and its implication.", "decision framing", "argument", "thesis-proof-implication", "proof must be source-backed or explicitly unverified", ("thesis", "proof", "implication", "preconditions"),
    _groups(("thesis", "central claim", True, 1, 1), ("proof", "supporting evidence", True, 1, 4), ("implication", "business implication", True, 1, 1), ("preconditions", "success or precondition boundary", True, 1, 4)),
    _slots(("thesis_statement", "central thesis", True, "claim", "thesis", 1, 1, ("dependency",), 240), ("proof_items", "proof points", True, "evidence", "proof", 1, 4, ("causality",), 180), ("implication_statement", "implication", True, "outcome", "implication", 1, 1, ("causality",), 240), ("success_conditions", "success or preconditions", True, "condition", "preconditions", 1, 4, ("decision_boundary",), 180)),
    (_rel("dependency", "thesis", "proof", "proof is required to support the thesis"), _rel("causality", "proof", "implication", "proof explains the implication"), _rel("decision_boundary", "preconditions", "implication", "conditions bound the implication")), likely_overflow=("proof_items", "success_conditions"),
)

M46 = _definition(
    "M46", "Observation Record Review Decision", "Turn observed facts into verified decision value.", "evidence review and decision", "verification", "observation-record-review-decision", "observation and ledger entries retain source bindings", ("observation", "record", "review", "decision_value"),
    _groups(("observation", "observed facts", True, 1, 5), ("record", "evidence ledger", True, 1, 8), ("review", "review and verification", True, 1, 5), ("decision_value", "decision value", True, 1, 3)),
    _slots(("observation_points", "observations", True, "observation", "observation", 1, 5, ("sequence",), 160), ("evidence_ledger", "evidence ledger entries", True, "evidence", "record", 1, 8, ("dependency",), 160), ("review_findings", "review findings", True, "finding", "review", 1, 5, ("convergence",), 180), ("decision_value_outcomes", "decision value", True, "outcome", "decision_value", 1, 3, ("causality",), 220)),
    (_rel("sequence", "observation", "record", "observations become recorded evidence"), _rel("dependency", "record", "review", "the ledger is reviewed and verified"), _rel("convergence", "review", "decision_value", "verified findings converge into decision value")), likely_overflow=("evidence_ledger", "review_findings"),
)

M47 = _definition(
    "M47", "Purpose Metric Evidence Threshold Action", "Connect purpose to measurable thresholds and action.", "metric-driven operating decision", "measurement", "purpose-metric-evidence-threshold-action", "metrics and evidence require explicit source or derivation", ("purpose", "metric_tree", "evidence", "thresholds", "actions"),
    _groups(("purpose", "measurement purpose", True, 1, 1), ("metric_tree", "metric hierarchy", True, 1, 8), ("evidence", "metric evidence", True, 1, 8), ("thresholds", "threshold definitions", True, 1, 8), ("actions", "decision or action", True, 1, 5)),
    _slots(("purpose_statement", "purpose", True, "purpose", "purpose", 1, 1, ("hierarchy",), 240), ("metric_branches", "metric branches", True, "metric", "metric_tree", 1, 8, ("hierarchy",), 160), ("evidence_items", "metric evidence", True, "evidence", "evidence", 1, 8, ("dependency",), 160), ("threshold_definitions", "thresholds", True, "threshold", "thresholds", 1, 8, ("decision_boundary",), 160), ("decision_actions", "actions", True, "action", "actions", 1, 5, ("decision_boundary",), 180)),
    (_rel("hierarchy", "purpose", "metric_tree", "metrics decompose the purpose"), _rel("dependency", "evidence", "thresholds", "evidence informs thresholds"), _rel("decision_boundary", "thresholds", "actions", "thresholds govern action")), likely_overflow=("metric_branches", "evidence_items", "threshold_definitions"),
)

M48 = _definition(
    "M48", "Preparation Decision Approval Execution", "Move from analysis to execution with clear ownership and escalation.", "governed execution", "operating model", "preparation-decision-approval-execution", "approval and escalation claims remain attributable", ("preparation", "decision", "approval", "execution", "escalation"),
    _groups(("preparation", "preparation and analysis", True, 1, 5), ("decision", "decision", True, 1, 3), ("approval", "approval and responsibility", True, 1, 4), ("execution", "execution actions", True, 1, 6), ("escalation", "escalation route", False, 0, 4)),
    _slots(("preparation_outputs", "analysis outputs", True, "analysis", "preparation", 1, 5, ("sequence",), 180), ("decision_conditions", "decision conditions", True, "condition", "decision", 1, 3, ("decision_boundary",), 180), ("approval_owner", "approval owner", True, "owner", "approval", 1, 4, ("handoff",), 160), ("execution_actions", "execution actions", True, "action", "execution", 1, 6, ("handoff",), 160), ("escalation_route", "escalation route", False, "escalation", "escalation", 0, 4, ("decision_boundary",), 160)),
    (_rel("sequence", "preparation", "decision", "analysis informs a decision"), _rel("handoff", "decision", "approval", "decision moves to accountable approval"), _rel("handoff", "approval", "execution", "approved work moves to execution"), _rel("decision_boundary", "escalation", "decision", "escalation bounds decision authority")), likely_overflow=("preparation_outputs", "execution_actions"),
)

M49 = _definition(
    "M49", "Five Stage Roadmap", "Sequence five stages with outputs, exit criteria and GO/HOLD gates.", "roadmap governance", "roadmap", "five-stage-roadmap", "exit criteria and gate status must be attributable", ("stages", "outputs", "exit_criteria", "gates", "principles"),
    _groups(("stages", "five roadmap stages", True, 5, 5), ("outputs", "stage outputs", True, 5, 5), ("exit_criteria", "exit criteria", True, 5, 5), ("gates", "GO or HOLD decisions", True, 5, 5), ("principles", "common principles", True, 1, 5)),
    _slots(("roadmap_stages", "roadmap stages", True, "stage", "stages", 5, 5, ("sequence",), 150), ("stage_outputs", "outputs", True, "output", "outputs", 5, 5, ("dependency",), 150), ("exit_criteria", "exit criteria", True, "criterion", "exit_criteria", 5, 5, ("decision_boundary",), 150), ("gate_decisions", "GO/HOLD gates", True, "decision", "gates", 5, 5, ("decision_boundary",), 140), ("common_principles", "common principles", True, "principle", "principles", 1, 5, ("feedback",), 180)),
    (_rel("sequence", "stages", "outputs", "each stage produces an output"), _rel("dependency", "outputs", "exit_criteria", "outputs are evaluated against exit criteria"), _rel("decision_boundary", "exit_criteria", "gates", "criteria determine GO/HOLD"), _rel("feedback", "principles", "stages", "principles guide every stage")), density="high", likely_overflow=("exit_criteria", "common_principles"),
)

M50 = _definition(
    "M50", "Six Stage Data Value Chain", "Trace data from source through foundations and analysis to business value.", "data-to-value operating model", "value chain", "six-stage-data-value-chain", "data lineage and evidence quality remain explicit", ("data_sources", "collection", "transformation", "analysis", "decision", "business_value", "foundations"),
    _groups(("data_sources", "data sources", True, 1, 8), ("collection", "collection and integration", True, 1, 8), ("transformation", "transformation and quality", True, 1, 8), ("analysis", "analysis and AI", True, 1, 8), ("decision", "operational decision", True, 1, 6), ("business_value", "business value", True, 1, 5), ("foundations", "supporting foundations", True, 1, 6)),
    _slots(("value_chain_stages", "six value-chain stages", True, "stage", "data_sources", 6, 6, ("sequence",), 150), ("collection_integration", "collection and integration", True, "process", "collection", 1, 8, ("sequence",), 160), ("transformation_quality", "transformation and quality", True, "process", "transformation", 1, 8, ("sequence",), 160), ("analysis_ai", "analysis and AI", True, "analysis", "analysis", 1, 8, ("sequence",), 160), ("operational_decisions", "operational decisions", True, "decision", "decision", 1, 6, ("causality",), 180), ("business_value_outcomes", "business value", True, "outcome", "business_value", 1, 5, ("causality",), 180), ("foundation_items", "supporting foundations", True, "foundation", "foundations", 1, 6, ("dependency",), 160)),
    (_rel("sequence", "data_sources", "business_value", "the chain moves from source to value"), _rel("dependency", "foundations", "data_sources", "foundations enable the chain"), _rel("causality", "decision", "business_value", "decisions realize business value")), density="high", likely_overflow=("value_chain_stages", "foundation_items"),
)

M51 = _definition(
    "M51", "Barrier Intervention Adoption Outcome", "Make behavior change visible from barrier through outcome and learning.", "adoption and improvement", "change journey", "barrier-intervention-behavior-adoption-outcome", "outcome visibility must distinguish evidence from inference", ("barriers", "intervention", "behavior_change", "adoption", "outcome_visibility", "learning"),
    _groups(("barriers", "barriers", True, 1, 6), ("intervention", "interventions", True, 1, 6), ("behavior_change", "behavior change", True, 1, 6), ("adoption", "adoption signals", True, 1, 6), ("outcome_visibility", "outcome visibility", True, 1, 6), ("learning", "learning and improvement", True, 1, 5)),
    _slots(("barrier_items", "barriers", True, "barrier", "barriers", 1, 6, ("causality",), 160), ("intervention_items", "interventions", True, "intervention", "intervention", 1, 6, ("causality",), 160), ("behavior_change_items", "behavior changes", True, "behavior", "behavior_change", 1, 6, ("sequence",), 160), ("adoption_signals", "adoption signals", True, "signal", "adoption", 1, 6, ("dependency",), 160), ("outcome_signals", "outcome signals", True, "outcome", "outcome_visibility", 1, 6, ("feedback",), 160), ("learning_loop", "learning loop", True, "learning", "learning", 1, 5, ("feedback",), 160)),
    (_rel("causality", "barriers", "intervention", "barriers motivate interventions"), _rel("sequence", "intervention", "behavior_change", "interventions seek behavior change"), _rel("dependency", "adoption", "outcome_visibility", "adoption enables visible outcomes"), _rel("feedback", "outcome_visibility", "learning", "outcomes produce learning"), _rel("feedback", "learning", "intervention", "learning improves interventions")), likely_overflow=("intervention_items", "outcome_signals"),
)

M52 = _definition(
    "M52", "Investment Capability Verification Outcome", "Connect investment to capability, proof, outcome and GO/HOLD value decisions.", "investment decision", "investment case", "investment-capability-verification-outcome-value", "verification and value claims require evidence state", ("investment", "capability", "verification", "outcome", "business_value", "gates"),
    _groups(("investment", "investment choices", True, 1, 5), ("capability", "capability build", True, 1, 6), ("verification", "verification", True, 1, 6), ("outcome", "outcomes", True, 1, 6), ("business_value", "business value", True, 1, 5), ("gates", "GO or HOLD boundary", True, 1, 3)),
    _slots(("investment_options", "investment", True, "investment", "investment", 1, 5, ("dependency",), 170), ("capability_steps", "capability", True, "capability", "capability", 1, 6, ("sequence",), 160), ("verification_conditions", "verification", True, "criterion", "verification", 1, 6, ("decision_boundary",), 160), ("outcome_signals", "outcomes", True, "outcome", "outcome", 1, 6, ("causality",), 160), ("business_value_outcomes", "business value", True, "value", "business_value", 1, 5, ("causality",), 180), ("gate_decision", "GO/HOLD", True, "decision", "gates", 1, 3, ("decision_boundary",), 160)),
    (_rel("sequence", "investment", "capability", "investment funds capability"), _rel("dependency", "capability", "verification", "capability is verified"), _rel("decision_boundary", "verification", "gates", "verification sets GO/HOLD"), _rel("causality", "outcome", "business_value", "outcomes generate value")), likely_overflow=("verification_conditions", "business_value_outcomes"),
)

M53 = _definition(
    "M53", "Five Stage Journey Friction Intervention Value", "Show a five-stage journey from friction to intervention and value.", "customer or operational journey improvement", "journey", "five-stage-journey", "friction and value claims remain tied to touchpoints", ("journey_stages", "friction", "intervention", "value", "touchpoints"),
    _groups(("journey_stages", "five journey stages", True, 5, 5), ("friction", "friction points", True, 1, 8), ("intervention", "interventions", True, 1, 8), ("value", "value outcomes", True, 1, 8), ("touchpoints", "touchpoints", True, 1, 8)),
    _slots(("journey_stage_items", "journey stages", True, "stage", "journey_stages", 5, 5, ("sequence",), 150), ("friction_points", "friction points", True, "friction", "friction", 1, 8, ("causality",), 160), ("intervention_items", "interventions", True, "intervention", "intervention", 1, 8, ("causality",), 160), ("value_outcomes", "value outcomes", True, "outcome", "value", 1, 8, ("causality",), 170), ("touchpoint_items", "touchpoints", True, "touchpoint", "touchpoints", 1, 8, ("dependency",), 160)),
    (_rel("sequence", "journey_stages", "touchpoints", "touchpoints occur along the journey"), _rel("causality", "friction", "intervention", "friction motivates intervention"), _rel("causality", "intervention", "value", "intervention seeks value"), _rel("dependency", "touchpoints", "friction", "touchpoints locate friction")), likely_overflow=("friction_points", "intervention_items"),
)

M54 = _definition(
    "M54", "Six Stage Risk Governance Escalation", "Govern six escalation stages with responsibility, levels and principles.", "risk and governance escalation", "governance", "six-stage-escalation", "risk status, responsibility and decisions require attributable records", ("escalation_stages", "responsibilities", "levels", "decision_records", "principles"),
    _groups(("escalation_stages", "six escalation stages", True, 6, 6), ("responsibilities", "responsibility structure", True, 1, 8), ("levels", "escalation levels", True, 1, 6), ("decision_records", "decision records", True, 1, 8), ("principles", "five governance principles", True, 5, 5)),
    _slots(("escalation_stage_items", "escalation stages", True, "stage", "escalation_stages", 6, 6, ("sequence",), 150), ("responsibility_items", "responsibilities", True, "responsibility", "responsibilities", 1, 8, ("handoff",), 160), ("escalation_level_guidance", "escalation levels", True, "level", "levels", 1, 6, ("decision_boundary",), 160), ("decision_record_items", "decision records", True, "record", "decision_records", 1, 8, ("feedback",), 160), ("governance_principles", "governance principles", True, "principle", "principles", 5, 5, ("feedback",), 170)),
    (_rel("sequence", "escalation_stages", "levels", "stages determine escalation level"), _rel("handoff", "responsibilities", "escalation_stages", "responsibility follows escalation stages"), _rel("decision_boundary", "levels", "decision_records", "levels govern decision recording"), _rel("feedback", "decision_records", "principles", "records inform governance learning")), density="high", likely_overflow=("responsibility_items", "decision_record_items"),
)


MASTER_DEFINITIONS = (M45, M46, M47, M48, M49, M50, M51, M52, M53, M54)
MASTER_REGISTRY = MasterRegistry(MASTER_DEFINITIONS)


__all__ = [
    "ALLOWED_MISSING_EVIDENCE_BEHAVIORS",
    "ALLOWED_PROVENANCE_STATES",
    "SUPPORTED_RELATIONSHIP_TYPES",
    "Cardinality",
    "ConstraintPolicy",
    "EditabilityPolicy",
    "InformationGroup",
    "MASTER_DEFINITIONS",
    "MASTER_REGISTRY",
    "MasterDefinition",
    "MasterDefinitionValidationError",
    "MasterRegistry",
    "ProvenancePolicy",
    "RelationshipDefinition",
    "SlotDefinition",
    "validate_definition",
    "validate_registry",
]
