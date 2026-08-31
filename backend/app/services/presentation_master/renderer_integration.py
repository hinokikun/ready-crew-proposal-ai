"""Composition-to-renderer structural bridge.

This adapter stops at an in-memory renderer integration specification.  It
does not render, create pages in a file, or invent semantic content.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .composition import CompositionInstance
from .definitions import ALLOWED_PROVENANCE_STATES, MasterDefinition, SUPPORTED_RELATIONSHIP_TYPES


EXISTING_RENDERER_PRIMITIVES = frozenset({"text", "rule", "semantic_container", "connector", "evidence_object", "path_approximation", "boundary"})
EXISTING_RENDERER_RELATIONSHIPS = frozenset({"contrast", "cause", "sequence", "dependency", "boundary", "tension", "convergence", "evidence_supports_decision"})


class IntegrationState(str, Enum):
    VALID = "VALID"
    DEGRADED = "DEGRADED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INVALID = "INVALID"


class RelationshipSupport(str, Enum):
    SUPPORTED_DIRECTLY = "SUPPORTED_DIRECTLY"
    SUPPORTED_WITH_EXISTING_PRIMITIVES = "SUPPORTED_WITH_EXISTING_PRIMITIVES"
    DEGRADED_BUT_SEMANTICALLY_VISIBLE = "DEGRADED_BUT_SEMANTICALLY_VISIBLE"
    NOT_SUPPORTED = "NOT_SUPPORTED"


@dataclass(frozen=True)
class RendererIntegrationObject:
    object_id: str
    semantic_item_id: str
    group_id: str
    slot_id: str
    semantic_role: str
    content_type: str
    value: str
    hierarchy_level: int
    reading_order: int
    primitive_type: str
    provenance_state: str
    evidence_state: str
    confidence: float
    review_required: bool
    required: bool
    source_binding: str = ""


@dataclass(frozen=True)
class RendererIntegrationRelationship:
    relationship_id: str
    semantic_type: str
    from_ref: str
    to_ref: str
    visual_type: str | None
    support: RelationshipSupport
    semantic_meaning: str
    provenance_state: str
    confidence: float
    review_required: bool


@dataclass(frozen=True)
class RendererIntegrationPage:
    page_id: str
    group_id: str
    reading_order: int
    objects: tuple[RendererIntegrationObject, ...]
    semantic_purpose: str = ""
    required: bool = True


@dataclass(frozen=True)
class RendererIntegrationSpec:
    master_id: str
    definition_version: str
    composition_state: str
    integration_state: IntegrationState
    pages: tuple[RendererIntegrationPage, ...]
    relationships: tuple[RendererIntegrationRelationship, ...]
    semantic_signals: tuple[str, ...]
    review_required: bool
    degradation_reasons: tuple[str, ...]
    validation_issues: tuple[str, ...]


class RendererIntegrationValidationError(ValueError):
    def __init__(self, issues: tuple[str, ...]):
        self.issues = issues
        super().__init__("; ".join(issues))


def _primitive_for(content_type: str) -> str:
    if content_type == "evidence":
        return "evidence_object"
    if content_type in {"threshold", "criterion"}:
        return "boundary"
    if content_type in {"relationship", "process", "stage"}:
        return "semantic_container"
    return "text"


def relationship_support(relationship_type: str) -> tuple[str | None, RelationshipSupport]:
    direct = {
        "sequence": "sequence",
        "dependency": "dependency",
        "causality": "cause",
        "convergence": "convergence",
        "decision_boundary": "boundary",
    }
    if relationship_type in direct:
        return direct[relationship_type], RelationshipSupport.SUPPORTED_WITH_EXISTING_PRIMITIVES
    if relationship_type in {"hierarchy", "feedback", "handoff"}:
        return None, RelationshipSupport.DEGRADED_BUT_SEMANTICALLY_VISIBLE
    return None, RelationshipSupport.NOT_SUPPORTED


def build_renderer_integration_spec(composition: CompositionInstance, definition: MasterDefinition) -> RendererIntegrationSpec:
    """Translate a validated composition into a structural renderer spec."""

    issues: list[str] = []
    degradations: list[str] = list(composition.degradation_reasons)
    if composition.master_id != definition.master_id:
        issues.append("composition/definition master mismatch")
    if composition.state == "INVALID":
        issues.append("INVALID composition is not renderer-admissible")
    if composition.state not in {"VALID", "DEGRADED", "REVIEW_REQUIRED", "INVALID"}:
        issues.append(f"unsupported composition state: {composition.state}")

    slot_by_id = {slot.slot_id: slot for slot in definition.slots}
    group_order = {group_id: index for index, group_id in enumerate(definition.reading_order)}
    objects: list[RendererIntegrationObject] = []
    object_ids: set[str] = set()
    for index, binding in enumerate(composition.bound_slots):
        slot = slot_by_id.get(binding.slot_id)
        if slot is None:
            issues.append(f"unknown slot: {binding.slot_id}")
            continue
        if binding.input_item_id in object_ids:
            issues.append(f"duplicate semantic identity: {binding.input_item_id}")
        object_ids.add(binding.input_item_id)
        primitive = _primitive_for(binding.content_type)
        if primitive not in EXISTING_RENDERER_PRIMITIVES:
            issues.append(f"unsupported renderer primitive: {primitive}")
        if binding.provenance_state not in ALLOWED_PROVENANCE_STATES:
            issues.append(f"invalid provenance state: {binding.provenance_state}")
        objects.append(RendererIntegrationObject(
            binding.input_item_id, binding.input_item_id, binding.group_id, binding.slot_id,
            binding.semantic_role, binding.content_type, binding.value,
            definition.hierarchy.index(binding.slot_id) if binding.slot_id in definition.hierarchy else len(definition.hierarchy),
            index, primitive, binding.provenance_state, binding.evidence_state,
            1.0 if binding.evidence_state not in {"missing", "unverified"} else 0.0,
            composition.human_review_required or binding.evidence_state in {"missing", "unverified"},
            slot.required,
            binding.source_binding,
        ))

    pages: list[RendererIntegrationPage] = []
    for group_id in definition.reading_order:
        group_objects = tuple(item for item in objects if item.group_id == group_id)
        group = next(group for group in definition.information_groups if group.group_id == group_id)
        pages.append(RendererIntegrationPage(f"group:{group_id}", group_id, group_order[group_id], group_objects, group.semantic_purpose, group.required))

    relationships: list[RendererIntegrationRelationship] = []
    for index, relationship in enumerate(composition.relationships):
        visual_type, support = relationship_support(relationship.relationship_type)
        if support == RelationshipSupport.NOT_SUPPORTED:
            issues.append(f"unsupported semantic relationship: {relationship.relationship_type}")
        elif support == RelationshipSupport.DEGRADED_BUT_SEMANTICALLY_VISIBLE:
            degradations.append(f"relationship remains semantic-only: {relationship.relationship_type}")
        relationships.append(RendererIntegrationRelationship(
            f"relationship:{index}", relationship.relationship_type, relationship.from_ref, relationship.to_ref,
            visual_type, support, relationship.semantic_meaning, "supplied", 1.0, composition.human_review_required,
        ))

    if composition.state == "INVALID":
        integration_state = IntegrationState.INVALID
    elif issues:
        integration_state = IntegrationState.INVALID
    elif composition.state == "REVIEW_REQUIRED" or composition.human_review_required:
        integration_state = IntegrationState.REVIEW_REQUIRED
    elif degradations:
        integration_state = IntegrationState.DEGRADED
    else:
        integration_state = IntegrationState.VALID
    return RendererIntegrationSpec(
        composition.master_id, definition.version, composition.state, integration_state,
        tuple(pages), tuple(relationships), tuple(sorted({item.semantic_role for item in objects})),
        integration_state == IntegrationState.REVIEW_REQUIRED, tuple(degradations), tuple(issues),
    )


__all__ = [
    "EXISTING_RENDERER_PRIMITIVES", "EXISTING_RENDERER_RELATIONSHIPS", "IntegrationState", "RelationshipSupport",
    "RendererIntegrationObject", "RendererIntegrationPage", "RendererIntegrationRelationship",
    "RendererIntegrationSpec", "RendererIntegrationValidationError", "build_renderer_integration_spec", "relationship_support",
]
