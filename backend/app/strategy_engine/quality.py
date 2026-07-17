from __future__ import annotations

import json
from typing import Dict, Iterable, List

from pydantic import BaseModel, Field

from .models import HumanReviewReport, PresentationContext, StrategyBrief


QUALITY_CATEGORIES = [
    "Story Consistency",
    "Persona Alignment",
    "Strategy Alignment",
    "Message Clarity",
    "Evidence Quality",
    "KPI Quality",
    "Risk Coverage",
    "Roadmap Completeness",
    "Presentation Pack Consistency",
    "Call To Action",
]


class QualityCategoryScore(BaseModel):
    category: str
    score: int
    reason: str
    suggestion: str


class QualityRedFlag(BaseModel):
    code: str
    severity: str
    category: str
    message: str


class ProposalQualityReport(BaseModel):
    schema_version: str = "proposal_quality_report_v1"
    total_score: int
    grade: str
    category_scores: List[QualityCategoryScore] = Field(default_factory=list)
    red_flags: List[QualityRedFlag] = Field(default_factory=list)
    summary: str
    reviewed_strategy_schema_version: str
    presentation_context_version: str
    review_status: str


def evaluate_proposal_quality(
    brief: StrategyBrief,
    review_report: HumanReviewReport,
    presentation_context: PresentationContext,
) -> ProposalQualityReport:
    scores = [
        _story_consistency(brief, presentation_context),
        _persona_alignment(brief, presentation_context),
        _strategy_alignment(brief, presentation_context),
        _message_clarity(brief, presentation_context),
        _evidence_quality(brief),
        _kpi_quality(brief, presentation_context),
        _risk_coverage(brief, presentation_context),
        _roadmap_completeness(brief, presentation_context),
        _pack_consistency(brief, presentation_context),
        _call_to_action(brief, presentation_context),
    ]
    red_flags = _red_flags(brief, review_report, presentation_context)
    total = sum(score.score for score in scores)
    return ProposalQualityReport(
        total_score=total,
        grade=_grade(total),
        category_scores=scores,
        red_flags=red_flags,
        summary=_summary(total, red_flags),
        reviewed_strategy_schema_version=brief.schema_version,
        presentation_context_version=presentation_context.schema_version,
        review_status=review_report.status,
    )


def quality_report_json(report: ProposalQualityReport, *, indent: int = 2) -> str:
    return json.dumps(report.dict(), ensure_ascii=False, indent=indent, sort_keys=True)


def render_quality_report_markdown(report: ProposalQualityReport) -> str:
    lines = [
        "# Proposal Quality Report",
        "",
        f"- Total Score: {report.total_score} / 100",
        f"- Grade: {report.grade}",
        f"- Review Status: {report.review_status}",
        f"- Strategy Schema: {report.reviewed_strategy_schema_version}",
        f"- Presentation Context: {report.presentation_context_version}",
        "",
        "## Category Scores",
    ]
    for item in report.category_scores:
        lines.extend(
            [
                f"### {item.category}",
                f"- Score: {item.score} / 10",
                f"- Reason: {item.reason}",
                f"- Improvement: {item.suggestion}",
                "",
            ]
        )
    lines.append("## Red Flags")
    if report.red_flags:
        for flag in report.red_flags:
            lines.append(f"- [{flag.severity}] {flag.code}: {flag.message}")
    else:
        lines.append("- None")
    lines.extend(["", "## Summary", report.summary, ""])
    return "\n".join(lines)


def _story_consistency(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    if brief.story_type != context.story_type:
        score -= 5
        reasons.append("story type differs between Strategy Brief and Presentation Context")
    if not _has_any(context.required_slides):
        score -= 3
        reasons.append("required slide order is missing")
    if not brief.required_slide_types:
        score -= 2
        reasons.append("Strategy Brief has no required slides")
    return _score(
        "Story Consistency",
        score,
        reasons or ["story, required slides, and context are aligned"],
        "Align story type and required slide order before presentation generation.",
    )


def _persona_alignment(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    if brief.primary_persona != context.persona:
        score -= 5
        reasons.append("primary persona differs between brief and context")
    if not brief.decision_maker:
        score -= 2
        reasons.append("decision maker is missing")
    if brief.primary_persona == "unknown":
        score -= 2
        reasons.append("primary persona is unknown")
    return _score(
        "Persona Alignment",
        score,
        reasons or ["persona and decision maker are clear"],
        "Clarify the main audience and decision maker.",
    )


def _strategy_alignment(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    if not brief.primary_strategy:
        score -= 4
        reasons.append("primary strategy is missing")
    if brief.primary_pack != context.presentation_pack:
        score -= 4
        reasons.append("presentation pack differs from strategy decision")
    if not brief.selection_reasons:
        score -= 2
        reasons.append("selection reasons are missing")
    return _score(
        "Strategy Alignment",
        score,
        reasons or ["strategy and selected pack are aligned"],
        "Explain why this strategy and pack were selected.",
    )


def _message_clarity(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    message = (context.main_message or brief.main_message or "").strip()
    if not message:
        score -= 6
        reasons.append("main message is missing")
    elif len(message) > 160:
        score -= 3
        reasons.append("main message is too long")
    if len(brief.priority_messages) < 2:
        score -= 2
        reasons.append("priority messages are sparse")
    return _score(
        "Message Clarity",
        score,
        reasons or ["main message and priority messages are clear"],
        "Keep the main message short and support it with two or more priority messages.",
    )


def _evidence_quality(brief: StrategyBrief) -> QualityCategoryScore:
    score = 10
    reasons = []
    values = [str(value) for value in brief.evidence_summary.values()]
    if not values:
        score -= 6
        reasons.append("evidence summary is missing")
    missing_count = sum(1 for value in values if value == "missing")
    inferred_count = sum(1 for value in values if value == "inferred")
    if missing_count:
        score -= min(4, missing_count * 2)
        reasons.append("some evidence is missing")
    if inferred_count >= max(2, len(values)):
        score -= 2
        reasons.append("evidence depends too heavily on inference")
    if len(brief.missing_information) >= 3:
        score -= 2
        reasons.append("missing information list is large")
    if brief.human_review_required:
        score -= 2
        reasons.append("human review gate is still required")
    return _score(
        "Evidence Quality",
        score,
        reasons or ["evidence level is sufficient for review"],
        "Collect confirmed or provided evidence for budget, scope, KPI, and decision maker.",
    )


def _kpi_quality(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    if not context.kpi_pack:
        score -= 5
        reasons.append("KPI pack is missing")
    if not _contains_token(brief.required_slide_types + brief.optional_slide_types, "kpi"):
        score -= 3
        reasons.append("slide plan does not include KPI")
    if "kpi" not in str(brief.kpi_pack).lower():
        score -= 2
        reasons.append("KPI pack name is not explicit")
    return _score(
        "KPI Quality",
        score,
        reasons or ["KPI pack and slide coverage are present"],
        "Add measurable KPI design and keep KPI slide coverage explicit.",
    )


def _risk_coverage(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    risk_count = len(_non_empty(brief.risk_messages or context.risk_messages))
    if risk_count == 0:
        score -= 6
        reasons.append("risk messages are missing")
    elif risk_count == 1:
        score -= 3
        reasons.append("risk coverage has only one point")
    if not _contains_token(brief.required_slide_types + brief.optional_slide_types, "risk"):
        score -= 2
        reasons.append("slide plan does not include risk")
    return _score(
        "Risk Coverage",
        score,
        reasons or ["risk messages are covered"],
        "Add operational, budget, timeline, and adoption risks where applicable.",
    )


def _roadmap_completeness(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    if not context.roadmap_type:
        score -= 4
        reasons.append("roadmap type is missing")
    if not _contains_token(brief.required_slide_types + brief.optional_slide_types, "roadmap", "timeline", "poc"):
        score -= 3
        reasons.append("slide plan lacks roadmap, timeline, or PoC")
    if len(context.next_actions) < 2:
        score -= 2
        reasons.append("next actions are too sparse for roadmap handoff")
    return _score(
        "Roadmap Completeness",
        score,
        reasons or ["roadmap and next action flow are complete"],
        "Define roadmap structure, decision points, and next actions.",
    )


def _pack_consistency(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    if brief.primary_pack != context.presentation_pack:
        score -= 5
        reasons.append("primary pack differs from Presentation Context")
    if str(context.presentation_pack) not in str(context.visual_theme):
        score -= 2
        reasons.append("visual theme does not include selected pack")
    if brief.secondary_pack != context.secondary_presentation_pack:
        score -= 1
        reasons.append("secondary pack differs")
    return _score(
        "Presentation Pack Consistency",
        score,
        reasons or ["pack and visual theme are consistent"],
        "Keep pack, secondary pack, and visual theme synchronized.",
    )


def _call_to_action(brief: StrategyBrief, context: PresentationContext) -> QualityCategoryScore:
    score = 10
    reasons = []
    actions = _non_empty(context.next_actions or brief.next_actions)
    if not actions:
        score -= 7
        reasons.append("next actions are missing")
    elif len(actions) == 1:
        score -= 3
        reasons.append("only one next action is present")
    if not _contains_token(brief.required_slide_types + brief.optional_slide_types, "next", "action"):
        score -= 2
        reasons.append("slide plan does not include next action")
    return _score(
        "Call To Action",
        score,
        reasons or ["next actions are clear"],
        "End the proposal with concrete next actions and owner-ready decision points.",
    )


def _red_flags(
    brief: StrategyBrief,
    report: HumanReviewReport,
    context: PresentationContext,
) -> List[QualityRedFlag]:
    flags: List[QualityRedFlag] = []
    values = [str(value) for value in brief.evidence_summary.values()]
    if not values or all(value in {"missing", "inferred"} for value in values):
        flags.append(_flag("evidence_insufficient", "high", "Evidence Quality", "Evidence is missing or only inferred."))
    if not context.kpi_pack or not _contains_token(brief.required_slide_types + brief.optional_slide_types, "kpi"):
        flags.append(_flag("kpi_missing", "high", "KPI Quality", "KPI pack or KPI slide coverage is missing."))
    if not _non_empty(brief.risk_messages or context.risk_messages):
        flags.append(_flag("risk_missing", "medium", "Risk Coverage", "Risk messages are missing."))
    if brief.story_type != context.story_type:
        flags.append(_flag("story_inconsistent", "high", "Story Consistency", "Story type differs from Presentation Context."))
    if report.status not in {"approved", "approved_with_changes"}:
        flags.append(_flag("review_not_approved", "critical", "Strategy Alignment", "Human review is not approved."))
    if not _non_empty(context.next_actions or brief.next_actions):
        flags.append(_flag("cta_missing", "medium", "Call To Action", "Next actions are missing."))
    return flags


def _score(category: str, score: int, reasons: Iterable[str], suggestion: str) -> QualityCategoryScore:
    return QualityCategoryScore(
        category=category,
        score=max(0, min(10, int(score))),
        reason="; ".join(_non_empty(reasons)),
        suggestion=suggestion,
    )


def _flag(code: str, severity: str, category: str, message: str) -> QualityRedFlag:
    return QualityRedFlag(code=code, severity=severity, category=category, message=message)


def _grade(total: int) -> str:
    if total >= 85:
        return "A"
    if total >= 70:
        return "B"
    if total >= 55:
        return "C"
    return "D"


def _summary(total: int, red_flags: List[QualityRedFlag]) -> str:
    if any(flag.severity == "critical" for flag in red_flags):
        return "Critical review issue detected. Do not pass this report to presentation generation."
    if total >= 85 and not red_flags:
        return "Proposal quality is strong and ready for human final review."
    if total >= 70:
        return "Proposal quality is usable, but red flags or category-level improvements should be reviewed."
    return "Proposal quality needs improvement before presentation generation."


def _has_any(items: Iterable[str]) -> bool:
    return bool(_non_empty(items))


def _non_empty(items: Iterable[str]) -> List[str]:
    return [str(item).strip() for item in items if str(item).strip()]


def _contains_token(items: Iterable[str], *tokens: str) -> bool:
    values = " ".join(str(item).lower() for item in items)
    return any(token.lower() in values for token in tokens)
