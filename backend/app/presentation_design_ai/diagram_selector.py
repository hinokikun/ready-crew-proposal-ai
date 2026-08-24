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
    "evidence_decision": ("decision_threshold", "evidence_architecture", "measurement_logic", "condition_map", "proof_requirement", "decision_gate"),
    "structure": ("architecture", "layered_platform", "process_flow", "data_flow", "service_blueprint"),
    "experience": ("customer_journey", "user_flow", "touchpoint_map", "experience_funnel"),
}


def select_diagram(item: InformationItem, category: str) -> DiagramDecision:
    item_id = item.item_id
    diagram_required = True
    necessity_reason = "The business message needs a visible structure to become decision-ready."
    if item_id in {"problem", "root_cause"}:
        selected = "issue_tree" if item_id == "problem" else "fishbone"
        rejected = ("cause_effect", "causal_chain")
        reason = "The slide must explain why the problem exists, not list symptoms."
    elif item_id in {"target_state", "solution_policy"}:
        selected = "typography_anchor"
        rejected = ("before_after", "transformation_bridge", "generic_flowchart")
        reason = "The insight should land as a proposition before it becomes a diagram."
        diagram_required = False
        necessity_reason = "Typography and business-object framing communicate the transformation faster than a default diagram."
    elif item_id in {"proposal_content"}:
        selected = "layered_platform" if _is_tech(category) else "hub_and_spoke"
        rejected = ("process_flow", "service_blueprint")
        reason = "The proposal should be read as an integrated system rather than isolated functions."
    elif item_id in {"execution_method"}:
        selected = "readiness_threshold"
        rejected = ("timeline", "milestone_plan", "generic_roadmap")
        reason = "Execution should show which conditions make the next step possible, not only dates."
        diagram_required = False
        necessity_reason = "A readiness threshold is a decision object, while a roadmap would imply unconfirmed schedule certainty."
    elif item_id == "kpi":
        selected = "evidence_architecture"
        rejected = ("kpi_dashboard", "progress_meter", "benefit_bridge", "axis_dots")
        reason = "KPI must show the evidence to retain for a decision, without inventing target values."
    elif item_id == "roi":
        selected = "decision_threshold"
        rejected = ("waterfall", "investment_breakdown", "benefit_bridge")
        reason = "ROI should be a decision threshold and evidence path until customer baseline values are confirmed."
    elif item_id == "risk":
        selected = "risk_heatmap"
        rejected = ("two_by_two", "prioritization_matrix")
        reason = "Risks need severity and controllability, not only a text list."
    elif item_id == "investment":
        selected = "investment_breakdown"
        rejected = ("waterfall", "comparison_matrix")
        reason = "Cost should be explained by required, recommended, and optional scope."
    elif item_id in {"decision", "next_action"}:
        selected = "decision_gate"
        rejected = ("timeline", "step_flow", "option_comparison")
        reason = "The closing page must make the evidence-to-decision relationship unambiguous."
    elif item_id == "background":
        selected = "hero_business_object"
        rejected = ("comparison_matrix", "dashboard", "generic_ai_diagram")
        reason = "The opening needs orientation and confidence, not detail."
        diagram_required = False
        necessity_reason = "A dominant title and meaningful business object are stronger than an abstract diagram on the cover."
    elif item_id == "current_state":
        selected = "editorial_context"
        rejected = ("dashboard", "three_column_cards", "generic_matrix")
        reason = "Current state should frame the business reality, not become a UI-like status board."
        diagram_required = False
        necessity_reason = "Photography and a judgement note can carry context without a generic process diagram."
    else:
        selected = "process_flow"
        rejected = ("matrix", "timeline")
        reason = "A simple process flow is the safest fallback for customer-facing explanation."

    return DiagramDecision(
        selected_diagram=selected,
        diagram_required=diagram_required,
        rejected_candidates=rejected,
        selection_reason=reason,
        necessity_reason=necessity_reason,
        required_evidence=_required_evidence(item_id),
        visual_risk=_visual_risk(item),
        fallback_diagram="process_flow",
    )


def _is_tech(category: str) -> bool:
    value = category.lower()
    return any(key in value for key in ("ai", "dx", "ocr", "saas", "crm", "system", "security"))


def _required_evidence(item_id: str) -> tuple[str, ...]:
    return {
        "kpi": ("measurement definition", "evidence record", "decision threshold"),
        "roi": ("baseline to measure", "effect mechanism", "payback condition"),
        "risk": ("exception condition", "risk owner", "verification timing"),
        "investment": ("required scope", "recommended scope", "customer decision point"),
        "execution_method": ("start condition", "owner", "confirmation item"),
        "decision": ("agreement item", "decision owner", "next meeting output"),
        "next_action": ("agreement item", "decision owner", "next meeting output"),
    }.get(item_id, ("customer interview", "current process observation"))


def _visual_risk(item: InformationItem) -> str:
    if item.evidence_status in {"hypothesis", "missing"}:
        return "Mark assumptions clearly; visualize what must be measured without inventing KPI, ROI, accuracy, sample count, cost, schedule, or results."
    return "Keep business specificity visible and avoid decorative diagrams, equal cards, UI fields, and repeated silhouettes."
