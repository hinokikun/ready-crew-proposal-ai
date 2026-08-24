"""Slide-level design contract builder."""

from __future__ import annotations

from app.presentation_components import COMPONENT_REGISTRY
from app.presentation_composer import CaseContext

from .action_title_designer import design_action_title
from .art_direction_rules import (
    act_for_item,
    composition_family_for_item,
    composition_selection_reason,
    dark_mass_usage_for_item,
    dominant_visual_for_item,
    photography_mode_for_item,
    quality_retention_for_item,
    red_semantic_for_item,
    typography_mode_for_item,
    whitespace_strategy_for_item,
)
from .composition_planner import plan_composition
from .density_optimizer import density_target_for_slide, normalize_visible_text
from .diagram_selector import select_diagram
from .emotion_curve import emotion_for_item
from .hierarchy_planner import plan_visual_hierarchy
from .models import CompositionType, DesignSlideContract, InformationItem
from .narrative_planner import next_transition, previous_connection


def design_slide_contract(
    case: CaseContext,
    item: InformationItem,
    index: int,
    total: int,
    story_items: tuple[InformationItem, ...],
    previous_compositions: tuple[CompositionType, ...],
) -> DesignSlideContract:
    diagram = select_diagram(item, case.category)
    composition = plan_composition(item, diagram, index, previous_compositions)
    quality_retention = quality_retention_for_item(item, diagram, case)
    emotion, color_role = emotion_for_item(item.item_id, index, total)
    action_title = design_action_title(case, item, index + 1, total)
    density_target, diagram_ratio = density_target_for_slide(composition)
    core_message = _core_message(item, case)
    evidence = tuple(normalize_visible_text(value, 24) for value in _supporting_evidence(item, case)[:3])
    hierarchy = plan_visual_hierarchy(item, action_title, diagram)
    component_id = _component_for_diagram(diagram.selected_diagram)
    return DesignSlideContract(
        slide_id=f"slide-{index + 1:02d}",
        section_id=_section_id(item.item_id, index, total),
        page_goal=_page_goal(item.item_id, index, total),
        audience=_audience_for_case(case),
        decision_stage=_decision_stage(item.item_id, index, total),
        action_title=action_title,
        core_message=core_message,
        supporting_evidence=evidence,
        expected_emotion=emotion,
        visual_metaphor=_visual_metaphor(diagram.selected_diagram),
        diagram_type=diagram.selected_diagram,
        composition_type=composition,
        information_priority=(hierarchy.priority_1, hierarchy.priority_2, *hierarchy.priority_3),
        reading_order=hierarchy.reading_order,
        focal_point=hierarchy.focal_point,
        secondary_point=hierarchy.secondary_point,
        takeaway=_takeaway(item, case),
        speaker_note_summary=_speaker_note(item, case),
        expected_question=_expected_question(item),
        previous_slide_connection=previous_connection(index, story_items),
        next_slide_transition=next_transition(index, story_items),
        text_density_target=density_target,
        diagram_ratio_target=diagram_ratio,
        color_role=color_role,
        component_ids=(component_id,),
        source_basis=(item.item_id, item.evidence_status),
        confidence=_confidence(item),
        human_review_reason=_human_review_reason(item),
        diagram_decision=diagram,
        visual_hierarchy=hierarchy,
        act=act_for_item(item.item_id),
        dominant_visual=dominant_visual_for_item(item, diagram, case),
        composition_family=composition_family_for_item(item, composition, diagram, previous_compositions),
        typography_mode=typography_mode_for_item(item.item_id, composition),
        photography_mode=photography_mode_for_item(item.item_id, case),
        whitespace_strategy=whitespace_strategy_for_item(item.item_id),
        red_semantic=red_semantic_for_item(item.item_id),
        dark_mass_usage=dark_mass_usage_for_item(item.item_id),
        composition_selection_reason=composition_selection_reason(item, composition, diagram, previous_compositions),
        quality_retention=quality_retention,
    )


def _component_for_diagram(diagram: str) -> str:
    mapping = {
        "hero": "COMP-001",
        "issue_tree": "COMP-003",
        "fishbone": "COMP-052",
        "current_transition_future": "COMP-005",
        "layered_platform": "COMP-014",
        "hub_and_spoke": "COMP-037",
        "phased_roadmap": "COMP-016",
        "kpi_dashboard": "COMP-023",
        "waterfall": "COMP-025",
        "risk_heatmap": "COMP-029",
        "investment_breakdown": "COMP-026",
        "phase_gate": "COMP-017",
    }
    candidate = mapping.get(diagram, "COMP-019")
    ids = {component.component_id for component in COMPONENT_REGISTRY}
    return candidate if candidate in ids else "COMP-019"


def _section_id(item_id: str, index: int, total: int) -> str:
    if index == 0:
        return "opening"
    if item_id in {"problem", "root_cause", "business_impact"}:
        return "diagnosis"
    if item_id in {"target_state", "solution_policy", "proposal_content"}:
        return "recommendation"
    if item_id in {"execution_method", "kpi", "roi", "risk", "investment"}:
        return "execution"
    if index >= total - 2:
        return "decision"
    return "body"


def _page_goal(item_id: str, index: int, total: int) -> str:
    if index == 0:
        return "understand"
    if item_id in {"problem", "root_cause"}:
        return "tension"
    if item_id in {"target_state", "solution_policy", "proposal_content"}:
        return "conviction"
    if item_id in {"execution_method", "risk"}:
        return "reassurance"
    if item_id in {"kpi", "roi", "investment"}:
        return "decision_support"
    if index >= total - 2:
        return "decision"
    return "expectation"


def _audience_for_case(case: CaseContext) -> str:
    decision = case.decision_maker or "sales and operations stakeholders"
    return normalize_visible_text(decision, 42)


def _decision_stage(item_id: str, index: int, total: int) -> str:
    if item_id in {"background", "current_state", "problem"}:
        return "problem_alignment"
    if item_id in {"target_state", "solution_policy", "proposal_content"}:
        return "solution_alignment"
    if item_id in {"kpi", "roi", "investment"}:
        return "investment_decision"
    if index >= total - 2:
        return "approval"
    return "execution_planning"


def _supporting_evidence(item: InformationItem, case: CaseContext) -> tuple[str, ...]:
    if item.item_id == "kpi":
        return tuple(case.expected_outcomes[:3]) or ("Baseline and target will be confirmed during discovery.",)
    if item.item_id == "roi":
        return (case.budget, "Payback logic should be validated with measured baseline.")
    if item.item_id == "risk":
        return ("Assumptions must be checked before full rollout.",)
    if item.item_id == "problem":
        return tuple(case.pain_points[:3]) or ("Customer pain points are not yet explicit.",)
    return (item.summary,)


def _core_message(item: InformationItem, case: CaseContext) -> str:
    messages = {
        "background": "判断の前提をそろえます",
        "current_state": "確認作業が分散しています",
        "problem": "課題を3つに絞ります",
        "root_cause": "原因は仮説として扱います",
        "business_impact": "事業影響へつなげます",
        "target_state": "AIと人の役割を分けます",
        "solution_policy": "例外は人が確認します",
        "proposal_content": "業務内に自然に組み込みます",
        "execution_method": "段階的に移行します",
        "kpi": "初期計測で確定します",
        "roi": "削減時間と品質で見ます",
        "risk": "先に対策を決めます",
        "investment": "必須と任意を分けます",
        "decision": "判断事項を明確にします",
        "next_action": "次回合意へ進めます",
    }
    return messages.get(item.item_id, normalize_visible_text(item.summary, 28))


def _visual_metaphor(diagram: str) -> str:
    return {
        "issue_tree": "branching causes",
        "fishbone": "root cause spine",
        "current_transition_future": "bridge from current to future",
        "typography_anchor": "oversized business proposition",
        "hero_business_object": "dominant title and business object",
        "editorial_context": "business context as an editorial field",
        "readiness_threshold": "conditions becoming ready for a decision",
        "layered_platform": "stacked operating layers",
        "phased_roadmap": "progressive path",
        "kpi_dashboard": "management cockpit",
        "waterfall": "investment to effect bridge",
        "risk_heatmap": "controlled warning map",
        "phase_gate": "approval gate",
    }.get(diagram, "structured visual explanation")


def _takeaway(item: InformationItem, case: CaseContext) -> str:
    if item.evidence_status == "hypothesis":
        return "仮説は次回確認します。"
    if item.item_id in {"decision", "next_action"}:
        return "検証条件を合意します。"
    return "次の判断材料にします。"


def _speaker_note(item: InformationItem, case: CaseContext) -> str:
    return f"Explain {item.label} briefly, then connect it to {case.category}. Keep assumptions explicit."


def _expected_question(item: InformationItem) -> str:
    return {
        "kpi": "Which baseline should we measure first?",
        "roi": "What assumption has the largest impact on payback?",
        "risk": "Which risk must be resolved before rollout?",
        "investment": "Which scope is required and which is optional?",
    }.get(item.item_id, "What should we confirm before moving forward?")


def _confidence(item: InformationItem) -> float:
    return {"sufficient": 0.9, "partial": 0.74, "hypothesis": 0.58, "missing": 0.4}[item.evidence_status]


def _human_review_reason(item: InformationItem) -> str:
    if item.evidence_status == "hypothesis":
        return "Evidence is a hypothesis and should be confirmed by the salesperson."
    if item.evidence_status == "partial":
        return "Baseline or customer-specific evidence is partial."
    return "No mandatory review reason beyond visual confirmation."
