"""Adapter from Version 9 Design Contract to the existing editable PPTX renderer."""

from __future__ import annotations

from app.presentation_composer import PageSpec, PresentationPlan, render_plan_to_pptx

from .evaluator import quality_retention_report
from .models import DesignDeck, DesignSlideContract


def design_deck_to_presentation_plan(deck: DesignDeck) -> PresentationPlan:
    pages = tuple(_contract_to_page(contract, index + 1) for index, contract in enumerate(deck.slide_contracts))
    return PresentationPlan(
        case=_case_proxy(deck),
        pages=pages,
        palette_id="proposalpilot_v9",
        design_system_version=deck.design_version,
        provider=deck.design_version,
    )


def render_design_deck_to_pptx(deck: DesignDeck) -> tuple[bytes, dict]:
    plan = design_deck_to_presentation_plan(deck)
    pptx_bytes, report = render_plan_to_pptx(plan)
    report.update(
        {
            "design_version": deck.design_version,
            "component_ids": sorted({component_id for contract in deck.slide_contracts for component_id in contract.component_ids}),
            "diagram_types": [contract.diagram_type for contract in deck.slide_contracts],
            "acts": [contract.act for contract in deck.slide_contracts],
            "dominant_visuals": [contract.dominant_visual for contract in deck.slide_contracts],
            "composition_families": [contract.composition_family for contract in deck.slide_contracts],
            "quality_retention": quality_retention_report(deck),
            "diagram_required": [contract.diagram_decision.diagram_required for contract in deck.slide_contracts],
            "fallback_count": deck.fallback_count,
            "native_fallback_count": deck.native_fallback_count,
            "design_plan_fingerprint": deck.design_plan_fingerprint,
            "render_warnings": list(deck.render_warnings),
            "refinement_count": 0,
        }
    )
    return pptx_bytes, report


def _contract_to_page(contract: DesignSlideContract, slide_no: int) -> PageSpec:
    return PageSpec(
        slide_no=slide_no,
        component_id=contract.component_ids[0] if contract.component_ids else "COMP-019",
        component_name=contract.composition_type,
        visual_type=_visual_type_for_contract(contract),
        layout_family=f"v9_{contract.composition_type}_{contract.diagram_type}",
        action_title=contract.action_title,
        conclusion=contract.core_message,
        diagram_labels=_diagram_labels(contract),
        evidence=contract.supporting_evidence[0] if contract.supporting_evidence else contract.source_basis[0],
        next_action=contract.next_slide_transition,
        diagram_ratio=contract.diagram_ratio_target,
        text_ratio=round(1 - contract.diagram_ratio_target, 2),
        speaker_notes={
            "summary": contract.speaker_note_summary,
            "expected_question": contract.expected_question,
            "previous": contract.previous_slide_connection,
            "next": contract.next_slide_transition,
            "human_review_reason": contract.human_review_reason,
        },
    )


def _visual_type_for_contract(contract: DesignSlideContract) -> str:
    mapping = {
        "hero": "hero",
        "section_divider": "pyramid",
        "full_width_diagram": "issue_tree",
        "central_hub": "fishbone",
        "three_column": "current_future",
        "split_content": "before_after",
        "left_visual_right_text": "flow",
        "right_visual_left_text": "architecture",
        "dashboard": "kpi_dashboard",
        "timeline": "timeline",
        "matrix": "matrix",
        "comparison": "risk_matrix",
        "cycle": "cycle",
        "hierarchy": "organization",
        "four_stage": "waterfall",
        "closing_decision": "next_action",
    }
    if contract.diagram_type == "waterfall":
        return "waterfall"
    if contract.diagram_type in {"measurement_logic", "evidence_architecture", "condition_map", "proof_requirement"}:
        return "flow"
    if contract.diagram_type == "decision_threshold":
        return "matrix"
    if contract.diagram_type == "decision_gate":
        return "next_action"
    if contract.diagram_type == "risk_heatmap":
        return "risk_matrix"
    if contract.diagram_type == "phased_roadmap":
        return "timeline"
    if contract.diagram_type == "layered_platform":
        return "architecture"
    return mapping.get(contract.composition_type, "flow")


def _diagram_labels(contract: DesignSlideContract) -> tuple[str, ...]:
    labels = [contract.focal_point, contract.secondary_point, contract.takeaway]
    labels.extend(contract.information_priority[:2])
    return tuple(_short(label, 18) for label in labels if label)


def _short(value: str, limit: int) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit].rstrip("、。,. ") if len(text) > limit else text


def _case_proxy(deck: DesignDeck):
    from app.presentation_composer import CaseContext

    return CaseContext(
        case_id=deck.case_id,
        case_name=deck.case_name,
        client_name=deck.client_name,
        industry="",
        category="Presentation Design AI",
        project_summary="",
        pain_points=(),
        expected_outcomes=(),
        budget="",
        timeline="",
        decision_maker="",
        competitor="",
    )
