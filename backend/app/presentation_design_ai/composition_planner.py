"""Composition planning rules."""

from __future__ import annotations

from .models import CompositionType, DiagramDecision, InformationItem


COMPOSITION_SEQUENCE: tuple[CompositionType, ...] = (
    "hero",
    "section_divider",
    "full_width_diagram",
    "central_hub",
    "three_column",
    "split_content",
    "left_visual_right_text",
    "right_visual_left_text",
    "dashboard",
    "timeline",
    "matrix",
    "comparison",
    "cycle",
    "hierarchy",
    "four_stage",
    "closing_decision",
)

PANEL_LIKE_COMPOSITIONS: tuple[CompositionType, ...] = (
    "three_column",
    "four_stage",
    "dashboard",
    "comparison",
)

SYMMETRIC_COMPOSITIONS: tuple[CompositionType, ...] = (
    "central_hub",
    "matrix",
    "hierarchy",
)

ITEM_COMPOSITION_ALTERNATIVES: dict[str, tuple[CompositionType, ...]] = {
    "background": ("hero", "split_content"),
    "current_state": ("section_divider", "full_width_diagram", "split_content"),
    "problem": ("full_width_diagram", "central_hub", "split_content"),
    "root_cause": ("split_content", "central_hub", "full_width_diagram"),
    "business_impact": ("split_content", "central_hub", "matrix"),
    "target_state": ("split_content", "left_visual_right_text", "right_visual_left_text"),
    "solution_policy": ("section_divider", "left_visual_right_text", "split_content"),
    "proposal_content": ("right_visual_left_text", "full_width_diagram", "split_content"),
    "execution_method": ("left_visual_right_text", "timeline", "split_content"),
    "kpi": ("split_content", "central_hub", "matrix"),
    "roi": ("split_content", "matrix", "central_hub"),
    "risk": ("split_content", "matrix", "comparison"),
    "investment": ("split_content", "four_stage", "matrix"),
    "decision": ("closing_decision", "split_content", "hierarchy"),
    "next_action": ("closing_decision", "left_visual_right_text", "hierarchy"),
}


def plan_composition(item: InformationItem, diagram: DiagramDecision, slide_index: int, previous: tuple[CompositionType, ...]) -> CompositionType:
    by_item: dict[str, CompositionType] = {
        "background": "hero",
        "current_state": "split_content",
        "problem": "full_width_diagram",
        "root_cause": "split_content",
        "business_impact": "split_content",
        "target_state": "split_content",
        "solution_policy": "section_divider",
        "proposal_content": "right_visual_left_text",
        "execution_method": "left_visual_right_text",
        "kpi": "split_content",
        "roi": "closing_decision",
        "risk": "closing_decision",
        "investment": "split_content",
        "decision": "closing_decision",
        "next_action": "closing_decision",
    }
    composition = by_item.get(item.item_id)
    if not composition:
        composition = _composition_for_diagram(diagram.selected_diagram)
    composition = _apply_anti_template_penalty(item.item_id, composition, previous)
    if _would_repeat_three_times(previous, composition):
        composition = _next_distinct(composition, previous)
    return composition


def _composition_for_diagram(diagram: str) -> CompositionType:
    if diagram in {"decision_threshold", "evidence_architecture", "measurement_logic", "condition_map", "proof_requirement"}:
        return "central_hub"
    if diagram == "decision_gate":
        return "closing_decision"
    if diagram in {"kpi_dashboard", "waterfall", "progress_meter", "investment_breakdown"}:
        return "dashboard"
    if diagram in {"timeline", "phased_roadmap", "swimlane", "milestone_plan"}:
        return "timeline"
    if diagram in {"two_by_two", "prioritization_matrix", "risk_heatmap", "comparison_matrix"}:
        return "matrix"
    if diagram in {"organization_chart", "governance_model", "role_map"}:
        return "hierarchy"
    if diagram in {"improvement_cycle", "flywheel", "feedback_loop"}:
        return "cycle"
    return "full_width_diagram"


def _would_repeat_three_times(previous: tuple[CompositionType, ...], composition: CompositionType) -> bool:
    return len(previous) >= 2 and previous[-1] == composition and previous[-2] == composition


def _apply_anti_template_penalty(item_id: str, composition: CompositionType, previous: tuple[CompositionType, ...]) -> CompositionType:
    alternatives = ITEM_COMPOSITION_ALTERNATIVES.get(item_id, (composition,))
    if not _has_template_risk(composition, previous):
        return composition
    for candidate in alternatives:
        if candidate == composition:
            continue
        if not _has_template_risk(candidate, previous):
            return candidate
    return _next_distinct_family(composition, previous)


def _has_template_risk(composition: CompositionType, previous: tuple[CompositionType, ...]) -> bool:
    if not previous:
        return False
    recent = previous[-3:]
    if composition in PANEL_LIKE_COMPOSITIONS and any(item in PANEL_LIKE_COMPOSITIONS for item in recent[-2:]):
        return True
    if composition in {"dashboard", "timeline", "matrix"} and any(item in {"dashboard", "timeline", "matrix"} for item in recent[-2:]):
        return True
    if composition in SYMMETRIC_COMPOSITIONS and len(recent) >= 2 and all(item in SYMMETRIC_COMPOSITIONS for item in recent[-2:]):
        return True
    if len(recent) >= 1 and recent[-1] == composition:
        return True
    return False


def _next_distinct_family(current: CompositionType, previous: tuple[CompositionType, ...]) -> CompositionType:
    for candidate in COMPOSITION_SEQUENCE:
        if candidate == current:
            continue
        if _has_template_risk(candidate, previous):
            continue
        return candidate
    return _next_distinct(current, previous)


def _next_distinct(current: CompositionType, previous: tuple[CompositionType, ...]) -> CompositionType:
    for candidate in COMPOSITION_SEQUENCE:
        if candidate != current and not _would_repeat_three_times(previous, candidate):
            return candidate
    return current
