"""Approved offline semantic fixtures and upstream gap analysis.

Fixtures are contract evidence only.  They contain semantic labels and
provenance metadata, never production data or fabricated business claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from .composition import CompositionOutcome, compose_from_selection
from .definitions import MASTER_REGISTRY
from .selection import MasterSelectionResult, select_master, suitability_metadata
from .upstream_adapter import (
    DerivationLevel,
    MasterCoverage,
    SemanticEnvelope,
    SemanticGap,
    SemanticGroup,
    SemanticItem,
    SemanticRelationship,
    assess_master_coverage,
)


class FixtureKind(str, Enum):
    MINIMUM_SUFFICIENT = "MINIMUM_SUFFICIENT"
    NORMAL_SUFFICIENT = "NORMAL_SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"


class GapCategory(str, Enum):
    EXISTING_BUT_UNSTRUCTURED = "EXISTING_BUT_UNSTRUCTURED"
    DETERMINISTICALLY_DERIVABLE = "DETERMINISTICALLY_DERIVABLE"
    REQUIRES_NEW_UPSTREAM_FIELD = "REQUIRES_NEW_UPSTREAM_FIELD"
    REQUIRES_HUMAN_INPUT = "REQUIRES_HUMAN_INPUT"
    EVIDENCE_BINDING_REQUIRED = "EVIDENCE_BINDING_REQUIRED"
    OPTIONAL = "OPTIONAL"


@dataclass(frozen=True)
class ApprovedSemanticFixture:
    fixture_id: str
    kind: FixtureKind
    intended_scenario: str
    approved_semantic_facts: tuple[str, ...]
    envelope: SemanticEnvelope
    expected_eligible_master_ids: tuple[str, ...]
    expected_selection_state: str
    expected_composition_state: str


@dataclass(frozen=True)
class FixtureEvaluation:
    fixture_id: str
    selection: MasterSelectionResult
    composition: CompositionOutcome
    passed: bool


@dataclass(frozen=True)
class UpstreamGap:
    master_id: str
    semantic_category: str
    category: GapCategory
    basis: str


def _count_for(slot, kind: FixtureKind) -> int:
    if kind == FixtureKind.INSUFFICIENT:
        return slot.cardinality.min_items
    if kind == FixtureKind.NORMAL_SUFFICIENT:
        if slot.cardinality.min_items == 0:
            return 1 if not slot.required else 1
        if slot.cardinality.max_items is not None and slot.cardinality.min_items < slot.cardinality.max_items:
            return slot.cardinality.min_items + 1
    return slot.cardinality.min_items


def _fixture(master_id: str, kind: FixtureKind) -> ApprovedSemanticFixture:
    definition = MASTER_REGISTRY.get(master_id)
    metadata = suitability_metadata(master_id)
    items: list[SemanticItem] = []
    group_members: dict[str, list[str]] = {group.group_id: [] for group in definition.information_groups}
    for slot in definition.slots:
        for index in range(_count_for(slot, kind)):
            item_id = f"{master_id.lower()}:{kind.value.lower()}:{slot.slot_id}:{index}"
            items.append(
                SemanticItem(
                    item_id=item_id,
                    semantic_role=slot.semantic_role,
                    content=f"approved semantic {slot.semantic_role} {index}",
                    content_type=slot.content_type,
                    provenance_state="supplied",
                    evidence_state="source_backed",
                    confidence=0.98,
                    review_required=False,
                    source_field=f"ApprovedSemanticFixture.{master_id}.{slot.slot_id}[{index}]",
                    derivation_level=DerivationLevel.DIRECT,
                    derivation_basis="explicit approved semantic fixture item",
                )
            )
            group_members[slot.parent_group].append(item_id)

    if kind == FixtureKind.INSUFFICIENT:
        required_slot = next(slot for slot in definition.slots if slot.required and slot.cardinality.min_items > 0)
        item_id = f"{master_id.lower()}:{kind.value.lower()}:{required_slot.slot_id}:0"
        items = [item for item in items if item.item_id != item_id]
        group_members[required_slot.parent_group].remove(item_id)

    groups = tuple(
        SemanticGroup(
            group.group_id,
            group.semantic_purpose,
            tuple(group_members[group.group_id]),
            group.required,
            DerivationLevel.DIRECT,
            "explicit approved semantic fixture group",
        )
        for group in definition.information_groups
    )
    relationships = tuple(
        SemanticRelationship(
            relationship.relationship_type,
            relationship.from_ref,
            relationship.to_ref,
            0.98,
            "supplied",
            DerivationLevel.DIRECT,
            "explicit approved semantic fixture relationship",
            False,
        )
        for relationship in definition.relationships
    )
    expected_composition = "DEGRADED" if kind == FixtureKind.MINIMUM_SUFFICIENT and master_id == "M48" else "INVALID" if kind == FixtureKind.INSUFFICIENT else "VALID"
    envelope = SemanticEnvelope(
        source_schema_version="approved_semantic_fixture_v1",
        narrative_intent=definition.narrative_role,
        decision_context=next(iter(metadata.decision_contexts)),
        information_pattern=definition.information_pattern,
        semantic_signals=metadata.positive_signals,
        items=tuple(items),
        groups=groups,
        relationships=relationships,
        evidence_profile=frozenset({"source_backed"}),
        unresolved_gaps=(),
        confidence=0.98,
        human_review_required=False,
        human_review_reasons=(),
    )
    return ApprovedSemanticFixture(
        fixture_id=f"{master_id}_{kind.value.lower()}",
        kind=kind,
        intended_scenario=definition.semantic_purpose,
        approved_semantic_facts=tuple(sorted({f"group:{group.group_id}" for group in definition.information_groups} | {f"relationship:{relationship.relationship_type}" for relationship in definition.relationships})),
        envelope=envelope,
        expected_eligible_master_ids=(master_id,),
        expected_selection_state="selected",
        expected_composition_state=expected_composition,
    )


APPROVED_SEMANTIC_FIXTURES = tuple(
    _fixture(master_id, kind)
    for master_id in (f"M{i}" for i in range(45, 55))
    for kind in FixtureKind
)


def fixtures_for(master_id: str, kind: FixtureKind) -> ApprovedSemanticFixture:
    return next(fixture for fixture in APPROVED_SEMANTIC_FIXTURES if fixture.envelope.semantic_signals and fixture.fixture_id == f"{master_id}_{kind.value.lower()}")


def evaluate_fixture(fixture: ApprovedSemanticFixture) -> FixtureEvaluation:
    selection_input = fixture.envelope.to_selection_input()
    selection = select_master(selection_input)
    from .upstream_adapter import composition_items_for_master

    items = composition_items_for_master(fixture.envelope, fixture.expected_eligible_master_ids[0])
    composition = compose_from_selection(selection_input, items)
    passed = (
        selection.state == fixture.expected_selection_state
        and selection.selected_master_id in fixture.expected_eligible_master_ids
        and composition.state == fixture.expected_composition_state
    )
    return FixtureEvaluation(fixture.fixture_id, selection, composition, passed)


def compare_current_envelope_to_fixture(envelope: SemanticEnvelope, master_id: str) -> tuple[UpstreamGap, ...]:
    definition = MASTER_REGISTRY.get(master_id)
    metadata = suitability_metadata(master_id)
    gaps: list[UpstreamGap] = []
    current_roles = {item.semantic_role for item in envelope.items}
    current_groups = {group.group_id for group in envelope.groups}
    current_relationships = {relationship.relationship_type for relationship in envelope.relationships}
    for group in definition.information_groups:
        if group.required and group.group_id not in current_groups:
            category = GapCategory.EXISTING_BUT_UNSTRUCTURED if group.group_id in {"evidence", "actions", "risks", "responsibilities", "decision"} else GapCategory.REQUIRES_NEW_UPSTREAM_FIELD
            gaps.append(UpstreamGap(master_id, f"group:{group.group_id}", category, "formal group is absent from StrategyBrief-derived envelope"))
    for slot in definition.slots:
        if slot.required and slot.semantic_role not in current_roles:
            category = GapCategory.EVIDENCE_BINDING_REQUIRED if slot.content_type == "evidence" else GapCategory.REQUIRES_NEW_UPSTREAM_FIELD
            gaps.append(UpstreamGap(master_id, f"slot:{slot.semantic_role}", category, "required semantic role is not item-level in StrategyBrief"))
    for relationship in definition.relationships:
        if relationship.relationship_type not in current_relationships:
            category = GapCategory.DETERMINISTICALLY_DERIVABLE if relationship.relationship_type == "sequence" and envelope.items else GapCategory.REQUIRES_NEW_UPSTREAM_FIELD
            gaps.append(UpstreamGap(master_id, f"relationship:{relationship.relationship_type}", category, "required relationship topology is absent or not directionally explicit"))
    if any(item.content_type == "evidence" for item in envelope.items):
        gaps.append(UpstreamGap(master_id, "evidence:item_level_source_binding", GapCategory.EVIDENCE_BINDING_REQUIRED, "StrategyBrief evidence summary has no item-level source record"))
    return tuple(gaps)


def gap_analysis_for_envelope(envelope: SemanticEnvelope) -> dict[str, tuple[UpstreamGap, ...]]:
    return {f"M{i}": compare_current_envelope_to_fixture(envelope, f"M{i}") for i in range(45, 55)}


__all__ = [
    "APPROVED_SEMANTIC_FIXTURES",
    "ApprovedSemanticFixture",
    "FixtureEvaluation",
    "FixtureKind",
    "GapCategory",
    "MasterCoverage",
    "UpstreamGap",
    "assess_master_coverage",
    "compare_current_envelope_to_fixture",
    "evaluate_fixture",
    "fixtures_for",
    "gap_analysis_for_envelope",
]
