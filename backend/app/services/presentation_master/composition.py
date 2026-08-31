"""Offline semantic Composition Contract bridge for Presentation Master V3.

The bridge binds meaning to the formal master contract.  It intentionally
stops before any page, primitive, coordinate, or file representation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable, Mapping

from .definitions import (
    ALLOWED_PROVENANCE_STATES,
    MASTER_REGISTRY,
    MasterDefinition,
)
from .selection import MasterSelectionInput, MasterSelectionResult, select_master


COMPOSITION_STATES = frozenset({"VALID", "DEGRADED", "REVIEW_REQUIRED", "INVALID"})
EVIDENCE_SENSITIVE_TYPES = frozenset({"evidence", "metric", "threshold", "criterion", "outcome", "value"})


@dataclass(frozen=True)
class SemanticContentItem:
    input_item_id: str
    semantic_role: str
    content_type: str
    group_id: str
    value: str
    provenance_state: str
    source_binding: str
    evidence_state: str = "unverified"

    def __post_init__(self) -> None:
        if not self.input_item_id.strip() or not self.semantic_role.strip() or not self.content_type.strip() or not self.group_id.strip():
            raise ValueError("content items require an ID, role, type, and group")
        if self.provenance_state not in ALLOWED_PROVENANCE_STATES:
            raise ValueError(f"unsupported provenance state: {self.provenance_state}")
        if not self.source_binding.strip():
            raise ValueError("source binding is required")


@dataclass(frozen=True)
class GroupBinding:
    group_id: str
    input_item_ids: tuple[str, ...]
    omitted: bool = False


@dataclass(frozen=True)
class SlotBinding:
    input_item_id: str
    slot_id: str
    group_id: str
    semantic_role: str
    content_type: str
    value: str
    provenance_state: str
    source_binding: str
    evidence_state: str


@dataclass(frozen=True)
class RelationshipInstance:
    relationship_type: str
    from_ref: str
    to_ref: str
    from_input_item_ids: tuple[str, ...]
    to_input_item_ids: tuple[str, ...]
    semantic_meaning: str


@dataclass(frozen=True)
class CompositionInstance:
    master_id: str
    master_version: str
    semantic_purpose: str
    bound_groups: tuple[GroupBinding, ...]
    bound_slots: tuple[SlotBinding, ...]
    relationships: tuple[RelationshipInstance, ...]
    reading_order: tuple[str, ...]
    state: str
    degradation_reasons: tuple[str, ...] = ()
    validation_issues: tuple[str, ...] = ()
    human_review_required: bool = False


@dataclass(frozen=True)
class CompositionOutcome:
    state: str
    composition: CompositionInstance | None
    selection: MasterSelectionResult | None = None
    issues: tuple[str, ...] = ()
    degradation_reasons: tuple[str, ...] = ()


def _ref_ids(ref: str, definition: MasterDefinition, bindings: tuple[SlotBinding, ...]) -> tuple[str, ...]:
    slot_ids = {slot.slot_id for slot in definition.slots}
    if ref in slot_ids:
        return tuple(binding.input_item_id for binding in bindings if binding.slot_id == ref)
    return tuple(binding.input_item_id for binding in bindings if binding.group_id == ref)


def build_composition_for_master(
    master_id: str,
    items: Iterable[SemanticContentItem],
    *,
    selection_state: str = "selected",
) -> CompositionOutcome:
    """Bind items to one already identified master without rendering."""

    definition = MASTER_REGISTRY.get(master_id)
    items = tuple(items)
    issues: list[str] = []
    degradations: list[str] = []
    if selection_state not in {"selected", "review_required"}:
        issues.append("composition cannot be forced from a no-match selection")

    item_ids = [item.input_item_id for item in items]
    if len(item_ids) != len(set(item_ids)):
        issues.append("duplicate input item IDs")

    slots_by_group: dict[str, list] = {}
    for slot in definition.slots:
        slots_by_group.setdefault(slot.parent_group, []).append(slot)
    counts: dict[str, int] = {slot.slot_id: 0 for slot in definition.slots}
    assigned: dict[str, SlotBinding] = {}
    unbound: list[str] = []

    for item in items:
        candidates = [
            slot
            for slot in slots_by_group.get(item.group_id, [])
            if slot.semantic_role == item.semantic_role and slot.content_type == item.content_type
        ]
        if not candidates:
            if item.group_id not in {group.group_id for group in definition.information_groups}:
                issues.append(f"unsupported group for input item: {item.input_item_id}")
            else:
                issues.append(f"semantic role or content type mismatch: {item.input_item_id}")
            unbound.append(item.input_item_id)
            continue
        slot = next(
            (candidate for candidate in candidates if candidate.cardinality.max_items is None or counts[candidate.slot_id] < candidate.cardinality.max_items),
            None,
        )
        if slot is None:
            issues.append(f"excessive cardinality for input item: {item.input_item_id}")
            unbound.append(item.input_item_id)
            continue
        counts[slot.slot_id] += 1
        assigned[item.input_item_id] = SlotBinding(
            item.input_item_id,
            slot.slot_id,
            slot.parent_group,
            item.semantic_role,
            item.content_type,
            item.value,
            item.provenance_state,
            item.source_binding,
            item.evidence_state,
        )
        if item.evidence_state == "evidence_backed" and item.provenance_state not in {"source_backed", "evidence_backed"}:
            issues.append(f"provenance conflict for input item: {item.input_item_id}")
        if slot.content_type in EVIDENCE_SENSITIVE_TYPES and item.evidence_state in {"missing", "unverified"}:
            degradations.append(f"evidence review required: {item.input_item_id}")
        text_limit = slot.text_limit_hint or definition.constraints.max_text_chars
        if len(item.value) > text_limit:
            degradations.append(f"text boundary exceeded: {item.input_item_id}")

    group_bindings: list[GroupBinding] = []
    group_ids = {group.group_id for group in definition.information_groups}
    for group in definition.information_groups:
        group_item_ids = tuple(item.input_item_id for item in items if item.group_id == group.group_id and item.input_item_id in assigned)
        group_bindings.append(GroupBinding(group.group_id, group_item_ids, not group_item_ids))
        if not group_item_ids:
            if group.required or group.cardinality.min_items > 0:
                issues.append(f"missing required group: {group.group_id}")
            else:
                degradations.append(f"optional group omitted: {group.group_id}")
        elif len(group_item_ids) < group.cardinality.min_items:
            issues.append(f"insufficient cardinality for group: {group.group_id}")
        elif group.cardinality.max_items is not None and len(group_item_ids) > group.cardinality.max_items:
            issues.append(f"excessive cardinality for group: {group.group_id}")

    for slot in definition.slots:
        count = counts[slot.slot_id]
        if count < slot.cardinality.min_items:
            issues.append(f"insufficient cardinality for slot: {slot.slot_id}")
        if slot.required and count == 0:
            issues.append(f"missing required slot: {slot.slot_id}")
    if unbound:
        issues.append(f"unbound input items: {', '.join(sorted(set(unbound)))}")

    bound_slots = tuple(assigned.values())
    relationship_instances: list[RelationshipInstance] = []
    group_required = {group.group_id: group.required for group in definition.information_groups}
    slot_required = {slot.slot_id: slot.required for slot in definition.slots}
    for relationship in definition.relationships:
        from_ids = _ref_ids(relationship.from_ref, definition, bound_slots)
        to_ids = _ref_ids(relationship.to_ref, definition, bound_slots)
        if not from_ids or not to_ids:
            from_required = slot_required.get(relationship.from_ref, group_required.get(relationship.from_ref, True))
            to_required = slot_required.get(relationship.to_ref, group_required.get(relationship.to_ref, True))
            if not from_required or not to_required:
                degradations.append(f"optional relationship omitted: {relationship.from_ref}->{relationship.to_ref}")
            else:
                issues.append(f"broken relationship: {relationship.from_ref}->{relationship.to_ref}")
            continue
        relationship_instances.append(
            RelationshipInstance(
                relationship.relationship_type,
                relationship.from_ref,
                relationship.to_ref,
                from_ids,
                to_ids,
                relationship.semantic_meaning,
            )
        )

    if issues:
        state = "INVALID"
    elif selection_state == "review_required" or any(reason.startswith("evidence review") or reason.startswith("text boundary") for reason in degradations):
        state = "REVIEW_REQUIRED"
    elif degradations:
        state = "DEGRADED"
    else:
        state = "VALID"
    composition = CompositionInstance(
        master_id,
        definition.version,
        definition.semantic_purpose,
        tuple(group_bindings),
        bound_slots,
        tuple(relationship_instances),
        definition.reading_order,
        state,
        tuple(degradations),
        tuple(issues),
        state in {"REVIEW_REQUIRED", "INVALID"},
    )
    return CompositionOutcome(state, composition, issues=tuple(issues), degradation_reasons=tuple(degradations))


def compose_from_selection(
    selection_input: MasterSelectionInput,
    items: Iterable[SemanticContentItem],
) -> CompositionOutcome:
    """Perform the offline Selection -> Definition -> Composition handoff."""

    selection = select_master(selection_input)
    if selection.selected_master_id is None:
        state = "REVIEW_REQUIRED" if selection.state == "review_required" else "INVALID"
        return CompositionOutcome(state, None, selection, issues=(selection.selection_reason,))
    outcome = build_composition_for_master(selection.selected_master_id, items, selection_state=selection.state)
    composition = outcome.composition
    if composition is not None and selection.state == "review_required" and composition.state == "VALID":
        composition = replace(
            composition,
            state="REVIEW_REQUIRED",
            human_review_required=True,
            validation_issues=composition.validation_issues + ("selection requires human review",),
        )
    return CompositionOutcome(
        composition.state if composition is not None else outcome.state,
        composition,
        selection,
        outcome.issues,
        outcome.degradation_reasons,
    )


__all__ = [
    "COMPOSITION_STATES",
    "CompositionInstance",
    "CompositionOutcome",
    "GroupBinding",
    "RelationshipInstance",
    "SemanticContentItem",
    "SlotBinding",
    "build_composition_for_master",
    "compose_from_selection",
]
