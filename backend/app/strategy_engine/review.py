import json
from typing import Dict, Iterable, List, Optional

from .enums import ReviewDecision
from .models import HumanReviewReport, HumanReviewResult, ReviewOverride, StrategyBrief


MUTABLE_FIELDS = {
    "primary_persona",
    "secondary_personas",
    "decision_maker",
    "story_type",
    "hero_theme",
    "main_message",
    "priority_messages",
    "risk_messages",
    "next_actions",
    "required_slide_types",
    "optional_slide_types",
}

IMMUTABLE_FIELDS = {
    "schema_version",
    "project_category",
    "secondary_category",
    "primary_pack",
    "secondary_pack",
    "confidence",
    "selection_reasons",
    "assumptions",
    "missing_information",
    "evidence_summary",
    "allowed_terms",
    "conditional_terms",
    "prohibited_terms",
}


def render_strategy_brief_markdown(brief: StrategyBrief) -> str:
    lines = [
        "# Strategy Brief",
        "",
        "## Summary",
        f"- Category: {brief.project_category}",
        f"- Secondary Category: {brief.secondary_category or '-'}",
        f"- Persona: {brief.primary_persona}",
        f"- Decision Maker: {brief.decision_maker}",
        f"- Strategy: {brief.primary_strategy}",
        f"- Story: {brief.story_type}",
        f"- Presentation Pack: {brief.primary_pack}",
        f"- KPI Pack: {brief.kpi_pack}",
        f"- Estimate Pack: {brief.estimate_pack}",
        f"- Confidence: {brief.confidence:.2f}",
        f"- Human Review Required: {brief.human_review_required}",
        "",
        "## Main Message",
        brief.main_message,
        "",
        "## Review Targets",
        _bullets(
            [
                f"Hero Theme: {brief.hero_theme}",
                f"Problem Theme: {brief.problem_theme}",
                f"Before / After Type: {brief.before_after_type}",
                f"Architecture Type: {brief.architecture_type}",
                f"Roadmap Type: {brief.roadmap_type}",
            ]
        ),
        "",
        "## Priority Messages",
        _bullets(brief.priority_messages),
        "",
        "## Risk Messages",
        _bullets(brief.risk_messages),
        "",
        "## Next Actions",
        _bullets(brief.next_actions),
        "",
        "## Evidence",
        _bullets([f"{key}: {value}" for key, value in sorted(brief.evidence_summary.items())]),
        "",
        "## Human Review Reasons",
        _bullets(brief.human_review_reasons or ["No review reason generated."]),
        "",
        "## Selection Reasons",
        _bullets(brief.selection_reasons),
        "",
        "## Override Rules",
        "- Changeable: Persona, Story, Hero Theme, Main Message, Priority Message, Risk Message, Next Action, slide type order.",
        "- Locked: schema_version, Evidence, Selection Reasons, confidence, pack/category decisions, term guard lists.",
        "",
        "## Review Result",
        "- [ ] Approve",
        "- [ ] Approve with Changes",
        "- [ ] Reject",
        "- [ ] Re-evaluate",
        "",
    ]
    return "\n".join(lines)


def create_review_report(
    brief: StrategyBrief,
    result: HumanReviewResult,
) -> HumanReviewReport:
    applied: List[ReviewOverride] = []
    rejected: List[ReviewOverride] = []
    reviewed_data: Dict[str, object] = brief.dict()

    if result.decision == ReviewDecision.APPROVE_WITH_CHANGES:
        for override in result.overrides:
            if override.field in MUTABLE_FIELDS:
                reviewed_data[override.field] = override.value
                applied.append(override)
            else:
                rejected.append(override)
    else:
        rejected.extend(result.overrides)

    reviewed_brief = StrategyBrief(**reviewed_data)
    status = _status_for_decision(result.decision)
    report = HumanReviewReport(
        decision=result.decision,
        reviewer=result.reviewer,
        comment=result.comment,
        reviewed_at=result.reviewed_at,
        status=status,
        applied_overrides=applied,
        rejected_overrides=rejected,
        original_brief=brief,
        reviewed_brief=reviewed_brief,
    )
    report.markdown_summary = render_review_report_markdown(report)
    return report


def render_review_report_markdown(report: HumanReviewReport) -> str:
    lines = [
        "# Strategy Brief Human Review Report",
        "",
        f"- Decision: {report.decision}",
        f"- Status: {report.status}",
        f"- Reviewer: {report.reviewer or '-'}",
        f"- Reviewed At: {report.reviewed_at or '-'}",
        f"- Comment: {report.comment or '-'}",
        "",
        "## Applied Overrides",
        _override_bullets(report.applied_overrides),
        "",
        "## Rejected Overrides",
        _override_bullets(report.rejected_overrides),
        "",
        "## Reviewed Strategy Brief",
        f"- Category: {report.reviewed_brief.project_category}",
        f"- Persona: {report.reviewed_brief.primary_persona}",
        f"- Strategy: {report.reviewed_brief.primary_strategy}",
        f"- Story: {report.reviewed_brief.story_type}",
        f"- Presentation Pack: {report.reviewed_brief.primary_pack}",
        f"- Main Message: {report.reviewed_brief.main_message}",
        "",
        "## Boundary",
        "This report is for offline review only. It does not send the Strategy Brief to Presentation Engine.",
        "",
    ]
    return "\n".join(lines)


def review_report_json(report: HumanReviewReport, *, indent: int = 2) -> str:
    return json.dumps(report.dict(), ensure_ascii=False, indent=indent, sort_keys=True)


def _status_for_decision(decision: ReviewDecision) -> str:
    return {
        ReviewDecision.APPROVE: "approved",
        ReviewDecision.APPROVE_WITH_CHANGES: "approved_with_changes",
        ReviewDecision.REJECT: "rejected",
        ReviewDecision.RE_EVALUATE: "re_evaluate_required",
    }[ReviewDecision(decision)]


def _bullets(items: Iterable[str]) -> str:
    values = [str(item) for item in items if str(item)]
    if not values:
        return "- -"
    return "\n".join(f"- {item}" for item in values)


def _override_bullets(overrides: Optional[List[ReviewOverride]]) -> str:
    if not overrides:
        return "- None"
    return "\n".join(f"- {override.field}: {override.value} ({override.reason or 'no reason'})" for override in overrides)
