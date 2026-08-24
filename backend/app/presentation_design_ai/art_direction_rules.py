"""Art-direction selection rules for Presentation Design AI Master.

These rules generalize reviewed visual decisions by slide intent and evidence
certainty. They intentionally avoid customer names, slide numbers, and
coordinate-level layout templates.
"""

from __future__ import annotations

from app.presentation_composer import CaseContext

from .models import CompositionType, DiagramDecision, InformationItem, QualityRetentionContract


def act_for_item(item_id: str) -> str:
    if item_id in {"background", "current_state", "problem", "root_cause"}:
        return "Problem / Tension"
    if item_id in {"target_state", "solution_policy", "proposal_content"}:
        return "Insight / Transformation"
    if item_id in {"execution_method", "kpi", "roi", "risk"}:
        return "Proof / Decision"
    return "Execution / Agreement"


def dominant_visual_for_item(item: InformationItem, diagram: DiagramDecision, case: CaseContext) -> str:
    business_object = _business_object(case)
    if item.item_id == "background":
        return f"large business-object title anchored by {business_object}"
    if item.item_id in {"current_state", "problem"}:
        return f"{business_object} context and decision tension"
    if item.item_id == "root_cause":
        return "broken reuse / reason-loss structure"
    if item.item_id in {"target_state", "solution_policy"}:
        return "oversized proposition typography"
    if item.item_id == "proposal_content":
        return "AI-to-human operating boundary"
    if item.item_id in {"kpi", "roi"}:
        return "evidence requirement sheet, not invented numbers"
    if item.item_id == "risk":
        return "exception handling and control boundary"
    if item.item_id == "execution_method":
        return "conditions becoming ready for a start decision"
    if item.item_id in {"decision", "next_action"}:
        return "single decision / agreement moment"
    return "business object as editorial anchor" if not diagram.diagram_required else diagram.selected_diagram


def quality_retention_for_item(
    item: InformationItem,
    diagram: DiagramDecision,
    case: CaseContext,
) -> QualityRetentionContract:
    """Define what must survive layout selection and rendering.

    The contract is intentionally semantic rather than coordinate-based so a
    different composition can still pass when it preserves the reviewed design
    principle.
    """

    return QualityRetentionContract(
        core_message=_retained_core_message(item),
        business_object=business_object_for_item(item.item_id, case),
        decision_role=decision_role_for_item(item.item_id),
        dominant_visual_intent=dominant_visual_for_item(item, diagram, case),
        required_business_evidence=required_business_evidence_for_item(item.item_id, case),
        editorial_temperature=editorial_temperature_for_item(item.item_id),
        must_preserve_semantic_relationship=semantic_relationship_for_item(item.item_id),
    )


def business_object_for_item(item_id: str, case: CaseContext) -> str:
    base = _business_object(case)
    object_set = _business_object_set(case)
    if item_id == "background":
        return f"{base} plus proposal title"
    if item_id in {"current_state", "problem"}:
        return f"{base} and current judgment context"
    if item_id in {"root_cause", "target_state", "solution_policy"}:
        return object_set["reason_object"]
    if item_id == "proposal_content":
        return object_set["operating_boundary"]
    if item_id in {"execution_method", "kpi"}:
        return object_set["evidence_object"]
    if item_id == "roi":
        return "decision threshold without invented ROI values"
    if item_id == "risk":
        return "readiness judgment with exception conditions inside it"
    if item_id == "investment":
        return "scope decision, not fabricated pricing detail"
    if item_id in {"decision", "next_action"}:
        return "next agreement items for PoC start"
    return base


def decision_role_for_item(item_id: str) -> str:
    return {
        "background": "orient the executive to why this proposal deserves attention",
        "current_state": "align on what the next decision is really about",
        "problem": "make the business problem specific enough to justify a PoC",
        "root_cause": "separate observed result from the missing reason",
        "target_state": "shift the decision from AI automation to reusable judgment",
        "solution_policy": "make the operating principle memorable before details",
        "proposal_content": "clarify where AI supports and where people remain responsible",
        "execution_method": "show the concrete PoC record that makes the next decision possible",
        "kpi": "define evidence to keep for the next GO decision",
        "roi": "visualize decision conditions without inventing financial proof",
        "risk": "confirm whether exception controls are ready enough to start",
        "investment": "separate required scope from optional expansion",
        "decision": "turn evidence into a clear approval choice",
        "next_action": "close on the next meeting's concrete agreement items",
    }.get(item_id, "advance the customer decision")


def required_business_evidence_for_item(item_id: str, case: CaseContext) -> tuple[str, ...]:
    object_set = _business_object_set(case)
    if item_id in {"execution_method", "kpi"}:
        return object_set["required_evidence"]
    if item_id == "roi":
        return (
            "baseline to measure",
            "effect mechanism",
            "payback condition",
            "unconfirmed values clearly left uncreated",
        )
    if item_id == "risk":
        return ("exception condition", "control owner", "readiness threshold", "start decision impact")
    if item_id in {"decision", "next_action"}:
        return ("agreement item", "decision owner", "PoC start condition")
    if item_id in {"root_cause", "target_state", "solution_policy"}:
        return object_set["reason_evidence"]
    if item_id == "background":
        return (case.client_name or "customer", case.category or "proposal theme", _business_object(case))
    return ("customer business context", "decision relevance")


def editorial_temperature_for_item(item_id: str) -> str:
    return {
        "background": "high-impact editorial hero",
        "current_state": "calm context with business tension",
        "problem": "specific tension",
        "root_cause": "fracture / loss",
        "target_state": "sharp insight",
        "solution_policy": "memorable proposition",
        "proposal_content": "operating clarity",
        "execution_method": "decision-ready proof",
        "kpi": "dense business evidence",
        "roi": "judgment pressure",
        "risk": "controlled caution",
        "investment": "commercial clarity",
        "decision": "commitment",
        "next_action": "agreement",
    }.get(item_id, "editorial clarity")


def semantic_relationship_for_item(item_id: str) -> str:
    return {
        "background": "meaningful photography must amplify hero typography, not become a side illustration",
        "current_state": "business context must lead to verification conditions",
        "problem": "symptoms must connect to lost reusable judgment",
        "root_cause": "result remains visible while reason is shown as the missing element",
        "target_state": "AI candidate and human reason must become reusable criteria",
        "solution_policy": "AI support must not erase human accountability",
        "proposal_content": "AI area and human responsibility boundary must remain explicit",
        "execution_method": "target image must connect to a single retained decision record",
        "kpi": "input, record, and decision must stay integrated as one business object",
        "roi": "measurement evidence must flow into a decision threshold, not a generic three-step process",
        "risk": "exception conditions must support readiness judgment instead of replacing it",
        "investment": "scope must explain decision options without fake amounts",
        "decision": "evidence must visibly lead to GO / REVIEW / HOLD style judgment",
        "next_action": "agreement items must visibly unlock PoC start",
    }.get(item_id, "business object must stay connected to the decision")


def _business_object_set(case: CaseContext) -> dict[str, tuple[str, ...] | str]:
    text = _case_text(case)
    if any(key in text for key in ("web", "marketing", "brand", "creative", "site", "conversion", "e-commerce", "ecommerce", "online store")):
        return {
            "reason_object": "content hierarchy / conversion point / approval reason",
            "operating_boundary": "brand story, page hierarchy, and sales handoff boundary",
            "evidence_object": "one page decision record: target audience, content block, conversion action, approval reason",
            "required_evidence": (
                "target audience",
                "page hierarchy",
                "content block",
                "conversion point",
                "approval reason",
                "measurement condition",
                "next direction decision",
            ),
            "reason_evidence": ("content hierarchy", "conversion point", "approval reason", "sales handoff"),
        }
    if any(key in text for key in ("recruit", "採用", "hr", "talent", "people", "education", "learning")):
        return {
            "reason_object": "candidate profile / screening criteria / human review reason",
            "operating_boundary": "AI screening support and recruiter accountability boundary",
            "evidence_object": "one candidate review record: profile signal, screening criteria, recruiter judgment, handoff reason",
            "required_evidence": (
                "candidate profile signal",
                "screening criteria",
                "AI support note",
                "recruiter judgment",
                "interview handoff reason",
                "candidate experience risk",
                "next workflow decision",
            ),
            "reason_evidence": ("candidate profile", "screening criteria", "recruiter judgment", "handoff reason"),
        }
    if any(key in text for key in ("manufacturing", "factory", "quality", "defect", "plant", "inspection")):
        return {
            "reason_object": "defect image / inspection finding / quality reason",
            "operating_boundary": "inspection support and QA approval boundary",
            "evidence_object": "one quality gate record: defect image, finding, exception, QA judgment, rollout condition",
            "required_evidence": (
                "defect image or inspection point",
                "finding category",
                "exception condition",
                "QA judgment",
                "root cause note",
                "rollout gate condition",
                "next quality decision",
            ),
            "reason_evidence": ("defect image", "inspection finding", "QA judgment", "quality reason"),
        }
    return {
        "reason_object": "AI candidate / human judgment / judgment reason",
        "operating_boundary": "AI candidate and human final judgment boundary",
        "evidence_object": "one decision record: target image, AI candidate, human judgment, reason, difference",
        "required_evidence": (
            "target image or condition",
            "AI candidate",
            "human final judgment",
            "judgment reason",
            "match / difference",
            "exception condition",
            "next GO condition",
        ),
        "reason_evidence": ("AI candidate", "human judgment", "judgment reason", "next standard"),
    }


def _retained_core_message(item: InformationItem) -> str:
    return {
        "background": "Proposal hero must be strong enough to frame the customer decision.",
        "execution_method": "PoC starts only when one inspectable decision record can be created.",
        "kpi": "PoC leaves evidence for the next decision, not fabricated accuracy numbers.",
        "roi": "ROI is a threshold to validate, not a generic measurement diagram.",
        "risk": "Risk belongs inside readiness judgment, not as an isolated exception page.",
    }.get(item.item_id, item.summary)


def composition_family_for_item(
    item: InformationItem,
    composition: CompositionType,
    diagram: DiagramDecision,
    previous: tuple[CompositionType, ...],
) -> str:
    if item.item_id == "root_cause":
        return "reason-loss editorial fracture"
    if item.item_id == "kpi":
        return "business evidence sheet"
    if item.item_id == "roi":
        return "decision threshold, not generic measurement process"
    if item.item_id == "risk":
        return "readiness judgment with exception controls"
    if item.item_id == "proposal_content":
        return "responsibility boundary"
    if item.item_id == "execution_method":
        return "readiness threshold path"
    if item.item_id in {"decision", "next_action"}:
        return "decision agreement page"
    if not diagram.diagram_required:
        return "typography-led editorial page"
    if composition in {"three_column", "four_stage", "dashboard"}:
        return "panel layout used only because the message needs comparable groups"
    return f"{composition} / {diagram.selected_diagram}"


def typography_mode_for_item(item_id: str, composition: CompositionType) -> str:
    if item_id in {"background", "solution_policy", "target_state", "decision", "next_action"}:
        return "typography_as_visual_anchor"
    if composition in {"dashboard", "matrix", "comparison"}:
        return "editorial_labels_with_one_hero_signal"
    return "takeaway_title_plus_business_detail"


def photography_mode_for_item(item_id: str, case: CaseContext) -> str:
    has_business_object = bool(_business_object(case))
    if not has_business_object:
        return "none"
    if item_id in {"background", "current_state", "solution_policy", "kpi"}:
        return "meaningful_business_object"
    return "none"


def whitespace_strategy_for_item(item_id: str) -> str:
    if item_id in {"background", "solution_policy", "decision", "next_action"}:
        return "asymmetric_whitespace_to_amplify_hero"
    if item_id in {"kpi", "roi", "risk"}:
        return "dense_editorial_sheet_with_clear_reading_lane"
    return "intentional_empty_field_around_business_object"


def red_semantic_for_item(item_id: str) -> str:
    return {
        "root_cause": "lost_reason_boundary",
        "solution_policy": "core_insight_underline",
        "proposal_content": "responsibility_boundary",
        "kpi": "evidence_difference",
        "roi": "decision_threshold",
        "risk": "readiness_exception_boundary",
        "execution_method": "start_condition",
        "decision": "decision",
        "next_action": "agreement",
    }.get(item_id, "single_emphasis_only")


def dark_mass_usage_for_item(item_id: str) -> str:
    if item_id in {"proposal_content", "decision", "next_action"}:
        return "decision_weight_only"
    if item_id == "risk":
        return "readiness_gate_only"
    if item_id == "investment":
        return "limited_control_surface"
    return "avoid_as_default_anchor"


def composition_selection_reason(
    item: InformationItem,
    composition: CompositionType,
    diagram: DiagramDecision,
    previous: tuple[CompositionType, ...],
) -> str:
    risk = "avoids adjacent template repetition" if previous and composition != previous[-1] else "fits the slide intent"
    diagram_note = "diagram suppressed" if not diagram.diagram_required else f"diagram retained: {diagram.selected_diagram}"
    return f"{risk}; {diagram_note}; selected because {item.label} must be expressed as business decision information."


def _business_object(case: CaseContext) -> str:
    text = _case_text(case)
    if any(key in text for key in ("flower", "花", "花卉", "生花")):
        return "flower quality image"
    if any(key in text for key in ("web", "marketing", "brand", "creative")):
        return "site and conversion artifact"
    if any(key in text for key in ("manufacturing", "factory", "quality", "defect", "plant", "inspection")):
        return "quality inspection record"
    if any(key in text for key in ("recruit", "採用", "hr", "talent", "people")):
        return "candidate review record"
    if any(key in text for key in ("ai", "dx", "data", "system")):
        return "operational data object"
    return "customer business object"


def _case_text(case: CaseContext) -> str:
    return " ".join([case.industry, case.category, case.project_summary]).lower()
