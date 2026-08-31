"""Bridge RendererIntegrationSpec into the existing renderer payload schema."""

from __future__ import annotations

from enum import Enum
from typing import Any

from .renderer_integration import IntegrationState, RendererIntegrationSpec


class StructuralCapacity(str, Enum):
    WITHIN_STRUCTURAL_CAPACITY = "WITHIN_STRUCTURAL_CAPACITY"
    CAPACITY_REVIEW_REQUIRED = "CAPACITY_REVIEW_REQUIRED"
    UNSUPPORTED_STRUCTURE = "UNSUPPORTED_STRUCTURE"


_VISUAL_RELATIONSHIP_FOR_DEGRADED = {
    "hierarchy": "boundary",
    "handoff": "boundary",
    "feedback": "convergence",
}


def classify_structural_capacity(spec: RendererIntegrationSpec) -> StructuralCapacity:
    if spec.integration_state == IntegrationState.INVALID or not spec.pages:
        return StructuralCapacity.UNSUPPORTED_STRUCTURE
    if any(not page.objects and page.required for page in spec.pages):
        return StructuralCapacity.CAPACITY_REVIEW_REQUIRED
    return StructuralCapacity.WITHIN_STRUCTURAL_CAPACITY


def _relationship_payload(relationship) -> dict[str, Any]:
    visual_type = relationship.visual_type or _VISUAL_RELATIONSHIP_FOR_DEGRADED.get(relationship.semantic_type)
    return {
        "relationship_id": relationship.relationship_id,
        "type": visual_type,
        "semantic_type": relationship.semantic_type,
        "from_object": relationship.from_ref,
        "to_object": relationship.to_ref,
        "semantic_meaning": relationship.semantic_meaning,
        "mapping_status": relationship.support.value,
        "direction_preserved": bool(relationship.from_ref and relationship.to_ref),
        "provenance_state": relationship.provenance_state,
        "confidence": relationship.confidence,
        "review_required": relationship.review_required,
    }


def build_renderer_structural_contract(spec: RendererIntegrationSpec) -> dict[str, Any]:
    """Build the dict expected immediately before the existing renderer linter."""

    pages: list[dict[str, Any]] = []
    ordered_pages = sorted(spec.pages, key=lambda item: item.reading_order)
    relationship_payloads = [_relationship_payload(rel) for rel in spec.relationships]
    for page_index, page in enumerate(ordered_pages):
        objects = []
        for item in sorted(page.objects, key=lambda value: value.reading_order):
            objects.append({
                "object_id": item.object_id,
                "semantic_item_id": item.semantic_item_id,
                "group_id": item.group_id,
                "slot_id": item.slot_id,
                "semantic_role": item.semantic_role,
                "content_type": item.content_type,
                "content": item.value,
                "primitive_type": item.primitive_type,
                "hierarchy_level": item.hierarchy_level,
                "reading_order": item.reading_order,
                "review_required": item.review_required,
                "required": item.required,
                "evidence_state": item.evidence_state,
                "confidence": item.confidence,
                "source_binding": {
                    "source_type": item.provenance_state,
                    "source_field": item.source_binding or item.semantic_item_id,
                    "provenance_id": item.semantic_item_id,
                },
                "editable": {"tier": 1, "required": True},
            })
        core_message = objects[0]["content"] if objects else page.semantic_purpose
        pages.append({
            "page_id": page.page_id,
            "page_role": page.group_id,
            "group_id": page.group_id,
            "semantic_purpose": page.semantic_purpose,
            "core_message": core_message,
            "visual_thesis": page.semantic_purpose,
            "dominant_visual": "semantic_container",
            "reading_order": page.reading_order,
            "review_required": spec.review_required,
            "objects": objects,
            "relationships": relationship_payloads if page_index == 0 else [],
            "constraints": {
                "semantic_group_id": page.group_id,
                "required": page.required,
                "actual_object_count": len(objects),
                "review_required": spec.review_required,
                "allow_rasterization": False,
            },
        })
    return {
        "contract_version": "presentation_master_v3_renderer_mvp_adapter_v1",
        "render_mode": "structural_bridge_v1",
        "case_summary": {
            "customer": "Presentation Master V3",
            "industry": "semantic proposal",
            "category": spec.master_id,
            "proposal_theme": "offline structural renderer execution",
            "audience": [],
            "decision_stage": "offline validation",
            "project_brief": "Composition semantic structure",
            "hearing_result": "",
        },
        "master_id": spec.master_id,
        "definition_version": spec.definition_version,
        "page_count": len(pages),
        "pages": pages,
        "review_state": "REVIEW_REQUIRED" if spec.review_required else "NONE",
        "review_reasons": list(spec.validation_issues) + list(spec.degradation_reasons),
        "composition_state": spec.composition_state,
        "integration_state": spec.integration_state.value,
        "capacity_state": classify_structural_capacity(spec).value,
        "semantic_signals": list(spec.semantic_signals),
        "cardinality": {page.group_id: len(page.objects) for page in spec.pages},
    }


def validate_renderer_structural_contract(contract: dict[str, Any]) -> tuple[dict[str, str], ...]:
    """Reuse the existing pure linter; this function never invokes rendering."""

    from .renderer_mvp import RendererMvpContractLinter

    return tuple(RendererMvpContractLinter().lint(contract))


__all__ = ["StructuralCapacity", "build_renderer_structural_contract", "classify_structural_capacity", "validate_renderer_structural_contract"]
