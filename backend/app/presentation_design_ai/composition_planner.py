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


def plan_composition(item: InformationItem, diagram: DiagramDecision, slide_index: int, previous: tuple[CompositionType, ...]) -> CompositionType:
    by_item: dict[str, CompositionType] = {
        "background": "hero",
        "current_state": "section_divider",
        "problem": "full_width_diagram",
        "root_cause": "central_hub",
        "business_impact": "three_column",
        "target_state": "split_content",
        "solution_policy": "left_visual_right_text",
        "proposal_content": "right_visual_left_text",
        "execution_method": "timeline",
        "kpi": "dashboard",
        "roi": "matrix",
        "risk": "comparison",
        "investment": "four_stage",
        "decision": "hierarchy",
        "next_action": "closing_decision",
    }
    composition = by_item.get(item.item_id)
    if not composition:
        composition = _composition_for_diagram(diagram.selected_diagram)
    if _would_repeat_three_times(previous, composition):
        composition = _next_distinct(composition, previous)
    return composition


def _composition_for_diagram(diagram: str) -> CompositionType:
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


def _next_distinct(current: CompositionType, previous: tuple[CompositionType, ...]) -> CompositionType:
    for candidate in COMPOSITION_SEQUENCE:
        if candidate != current and not _would_repeat_three_times(previous, candidate):
            return candidate
    return current
