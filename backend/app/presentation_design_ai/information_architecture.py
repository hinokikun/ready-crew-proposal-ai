"""Information architecture first pass for Presentation Design AI."""

from __future__ import annotations

from app.presentation_composer import CaseContext

from .models import InformationArchitecture, InformationItem


def build_information_architecture(case: CaseContext) -> InformationArchitecture:
    pain = tuple(case.pain_points or ())
    outcomes = tuple(case.expected_outcomes or ())
    items = (
        _item("background", "background", f"{case.industry} / {case.category}", "dedicated_slide", True, False, "sufficient", "Needed to frame why the proposal matters."),
        _item("current_state", "current state", _first_sentence(case.project_summary), "dedicated_slide", True, False, "partial", "Visible because the customer needs a shared starting point."),
        _item("problem", "problem", _join_short(pain[:3]), "dedicated_slide", True, False, "partial", "Problems must be visible before the solution is credible."),
        _item("root_cause", "root cause", _root_cause_summary(pain), "dedicated_slide", True, False, "hypothesis", "Cause is inferred from the supplied pain points and should be marked as a hypothesis."),
        _item("business_impact", "business impact", _join_short(outcomes[:2]), "merge", True, False, "partial", "Impact is merged into the executive summary or KPI slide."),
        _item("target_state", "target state", _target_state(case), "dedicated_slide", True, False, "partial", "The target state turns the proposal into a decision path."),
        _item("solution_policy", "solution policy", _solution_policy(case), "dedicated_slide", True, False, "partial", "Visible because it explains why this approach is recommended."),
        _item("proposal_content", "proposal content", case.category, "dedicated_slide", True, False, "sufficient", "Proposal content anchors the offering."),
        _item("execution_method", "execution method", case.timeline, "dedicated_slide", True, False, "partial", "Execution method reduces delivery anxiety."),
        _item("kpi", "KPI", _join_short(outcomes[:3]), "dedicated_slide", True, False, "partial", "KPIs support measurement and acceptance."),
        _item("roi", "ROI", _roi_basis(case), "dedicated_slide", True, False, "hypothesis", "ROI is a decision topic but requires customer confirmation."),
        _item("risk", "risk", _risk_basis(case), "dedicated_slide", True, False, "hypothesis", "Risks should be transparent rather than hidden."),
        _item("investment", "investment", case.budget, "dedicated_slide", True, False, "partial", "Investment must be explained as scope and payback logic."),
        _item("decision", "decision item", "Approve the next validation step.", "dedicated_slide", True, False, "sufficient", "The deck must end with a clear ask."),
        _item("next_action", "next action", "Confirm assumptions and start the next meeting.", "dedicated_slide", True, False, "sufficient", "The salesperson needs a concrete close."),
    )
    removed = tuple(item.item_id for item in items if item.disposition == "delete")
    merged = tuple(item.item_id for item in items if item.disposition == "merge")
    hypotheses = tuple(item.item_id for item in items if item.evidence_status == "hypothesis")
    return InformationArchitecture(case_id=case.case_id, items=items, removed_items=removed, merged_items=merged, hypothesis_items=hypotheses)


def _item(
    item_id: str,
    label: str,
    summary: str,
    disposition,
    customer_visible: bool,
    notes_only: bool,
    evidence,
    reason: str,
) -> InformationItem:
    return InformationItem(
        item_id=item_id,
        label=label,
        summary=_clean(summary, 96),
        disposition=disposition,
        customer_visible=customer_visible,
        speaker_notes_only=notes_only,
        evidence_status=evidence,
        reason=reason,
    )


def _clean(text: str, limit: int) -> str:
    value = " ".join(str(text or "").replace("\n", " ").split())
    return value[:limit].rstrip("、。,. ") if len(value) > limit else value


def _first_sentence(text: str) -> str:
    value = str(text or "").replace("。", "。 ").split("。 ")[0]
    return value or "Current work depends on manual interpretation and fragmented confirmation."


def _join_short(values: tuple[str, ...]) -> str:
    return " / ".join(_clean(value, 28) for value in values if value) or "Confirm baseline and target during discovery."


def _root_cause_summary(pain: tuple[str, ...]) -> str:
    if not pain:
        return "Root cause is not explicit; treat as a hypothesis."
    return f"Common causes appear to be fragmented process, unclear criteria, and repeated manual checks: {_join_short(pain[:2])}"


def _target_state(case: CaseContext) -> str:
    return f"{case.client_name} can make faster decisions with a visible, measurable operating flow."


def _solution_policy(case: CaseContext) -> str:
    text = f"{case.category} {case.project_summary}".lower()
    if any(word in text for word in ("ai", "ocr", "生成")):
        return "Combine AI judgment with human confirmation so accuracy and operational control are balanced."
    if any(word in text for word in ("web", "ec", "marketing", "採用")):
        return "Rebuild the customer journey around conversion, credibility, and measurable next actions."
    return "Clarify the operating model, decision criteria, and phased implementation path."


def _roi_basis(case: CaseContext) -> str:
    outcomes = _join_short(tuple(case.expected_outcomes[:2]))
    return f"Investment: {case.budget}; return hypothesis: {outcomes}"


def _risk_basis(case: CaseContext) -> str:
    competitor = f"Competitive context: {case.competitor}" if case.competitor else "Competitive context must be confirmed."
    return f"Assumption risk, adoption risk, and integration risk. {competitor}"
