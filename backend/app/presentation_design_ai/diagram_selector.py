"""Meaning-based diagram selection for Presentation Design AI."""

from __future__ import annotations

from .models import DiagramDecision, InformationItem


DIAGRAM_GROUPS = {
    "cause": ("cause_effect", "issue_tree", "fishbone", "causal_chain"),
    "stage": ("maturity_model", "stage_progression", "step_flow", "phase_gate"),
    "transformation": ("point_line_surface", "current_transition_future", "before_after", "transformation_bridge"),
    "relationship": ("stakeholder_map", "hub_and_spoke", "ecosystem", "shared_foundation", "layered_relationship"),
    "cycle": ("improvement_cycle", "flywheel", "feedback_loop", "operating_cycle"),
    "comparison": ("comparison_matrix", "current_future_table", "option_comparison", "capability_comparison"),
    "priority": ("two_by_two", "prioritization_matrix", "impact_effort", "risk_heatmap"),
    "time": ("timeline", "phased_roadmap", "swimlane", "milestone_plan"),
    "organization": ("organization_chart", "governance_model", "role_map", "responsibility_matrix"),
    "numeric": ("kpi_dashboard", "waterfall", "progress_meter", "benefit_bridge", "investment_breakdown"),
    "structure": ("architecture", "layered_platform", "process_flow", "data_flow", "service_blueprint"),
    "experience": ("customer_journey", "user_flow", "touchpoint_map", "experience_funnel"),
}


def select_diagram(item: InformationItem, category: str) -> DiagramDecision:
    item_id = item.item_id
    if item_id in {"problem", "root_cause"}:
        selected = "issue_tree" if item_id == "problem" else "fishbone"
        rejected = ("cause_effect", "causal_chain")
        reason = "The slide must explain why the problem exists, not list symptoms."
    elif item_id in {"target_state", "solution_policy"}:
        selected = "current_transition_future"
        rejected = ("before_after", "transformation_bridge")
        reason = "The audience needs to see movement from current reality to the desired operating state."
    elif item_id in {"proposal_content"}:
        selected = "layered_platform" if _is_tech(category) else "hub_and_spoke"
        rejected = ("process_flow", "service_blueprint")
        reason = "The proposal should be read as an integrated system rather than isolated functions."
    elif item_id in {"execution_method"}:
        selected = "phased_roadmap"
        rejected = ("timeline", "milestone_plan")
        reason = "A phased roadmap makes implementation and decision gates visible."
    elif item_id == "kpi":
        selected = "kpi_dashboard"
        rejected = ("progress_meter", "benefit_bridge")
        reason = "KPI must be scanned as a management dashboard."
    elif item_id == "roi":
        selected = "waterfall"
        rejected = ("investment_breakdown", "benefit_bridge")
        reason = "ROI should show investment, effect, payback, and future value."
    elif item_id == "risk":
        selected = "risk_heatmap"
        rejected = ("two_by_two", "prioritization_matrix")
        reason = "Risks need severity and controllability, not only a text list."
    elif item_id == "investment":
        selected = "investment_breakdown"
        rejected = ("waterfall", "comparison_matrix")
        reason = "Cost should be explained by required, recommended, and optional scope."
    elif item_id in {"decision", "next_action"}:
        selected = "phase_gate"
        rejected = ("timeline", "step_flow")
        reason = "The closing page must make the approval step unambiguous."
    elif item_id == "background":
        selected = "hero"
        rejected = ("comparison_matrix", "dashboard")
        reason = "The opening needs orientation and confidence, not detail."
    else:
        selected = "process_flow"
        rejected = ("matrix", "timeline")
        reason = "A simple process flow is the safest fallback for customer-facing explanation."

    return DiagramDecision(
        selected_diagram=selected,
        rejected_candidates=rejected,
        selection_reason=reason,
        required_evidence=_required_evidence(item_id),
        visual_risk=_visual_risk(item),
        fallback_diagram="process_flow",
    )


def _is_tech(category: str) -> bool:
    value = category.lower()
    return any(key in value for key in ("ai", "dx", "ocr", "saas", "crm", "system", "security"))


def _required_evidence(item_id: str) -> tuple[str, ...]:
    return {
        "kpi": ("baseline value", "target value", "measurement timing"),
        "roi": ("investment range", "time reduction", "payback assumption"),
        "risk": ("risk owner", "mitigation action", "verification timing"),
        "investment": ("required scope", "optional scope", "customer decision point"),
    }.get(item_id, ("customer interview", "current process observation"))


def _visual_risk(item: InformationItem) -> str:
    if item.evidence_status in {"hypothesis", "missing"}:
        return "Mark assumptions clearly and avoid overclaiming."
    return "No special visual risk beyond keeping the diagram concise."
