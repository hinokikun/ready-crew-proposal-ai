from __future__ import annotations

import json
from collections import Counter
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .quality import ProposalQualityReport, evaluate_proposal_quality
from .quality_fixtures import build_quality_evaluation_input, quality_fixture_choices


class HumanEvaluationField(BaseModel):
    label: str
    score_range: str = "1-5"
    value: Optional[int] = None
    note: str = ""


class HumanEvaluationTemplate(BaseModel):
    ease_of_understanding: HumanEvaluationField = Field(
        default_factory=lambda: HumanEvaluationField(label="理解しやすさ")
    )
    persuasiveness: HumanEvaluationField = Field(default_factory=lambda: HumanEvaluationField(label="説得力"))
    sales_readiness: HumanEvaluationField = Field(
        default_factory=lambda: HumanEvaluationField(label="営業で使えるか")
    )
    revision_effort: HumanEvaluationField = Field(default_factory=lambda: HumanEvaluationField(label="修正量"))
    free_comment: str = ""


class EngineComparisonSnapshot(BaseModel):
    engine_mode: str
    total_score: int
    grade: str
    persona: str
    story: str
    presentation_pack: str
    kpi_pack: str
    risk_messages: List[str] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    human_review_required: bool
    human_review_status: str
    improvement_points: List[str] = Field(default_factory=list)


class ComparisonMetrics(BaseModel):
    score_delta: int
    grade_result: str
    score_result: str
    red_flag_delta: int
    red_flag_result: str
    human_review_result: str


class ProposalComparisonReport(BaseModel):
    schema_version: str = "proposal_comparison_report_v1"
    fixture_name: str
    title: str
    legacy: EngineComparisonSnapshot
    strategy_v1: EngineComparisonSnapshot
    metrics: ComparisonMetrics
    field_comparison: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    improvement_point_comparison: Dict[str, List[str]] = Field(default_factory=dict)
    human_evaluation_template: HumanEvaluationTemplate = Field(default_factory=HumanEvaluationTemplate)


class ComparisonAggregateMetrics(BaseModel):
    case_count: int
    legacy_wins: int
    strategy_v1_wins: int
    ties: int
    average_delta: float
    red_flag_improvement_rate: float
    human_review_improvement_rate: float


def comparison_fixture_choices() -> list[str]:
    return quality_fixture_choices()


def compare_fixture(fixture_name: str) -> ProposalComparisonReport:
    quality_input = build_quality_evaluation_input(fixture_name)
    report = evaluate_proposal_quality(
        quality_input.strategy_brief,
        quality_input.human_review_report,
        quality_input.presentation_context,
    )
    legacy = _snapshot("legacy", quality_input, report)
    strategy = _snapshot("strategy_v1", quality_input, report)
    return ProposalComparisonReport(
        fixture_name=fixture_name,
        title=quality_input.strategy_brief.hero_theme,
        legacy=legacy,
        strategy_v1=strategy,
        metrics=_metrics(legacy, strategy),
        field_comparison=_field_comparison(legacy, strategy),
        improvement_point_comparison=_improvement_point_comparison(legacy, strategy),
    )


def aggregate_comparison_metrics(reports: List[ProposalComparisonReport]) -> ComparisonAggregateMetrics:
    if not reports:
        return ComparisonAggregateMetrics(
            case_count=0,
            legacy_wins=0,
            strategy_v1_wins=0,
            ties=0,
            average_delta=0.0,
            red_flag_improvement_rate=0.0,
            human_review_improvement_rate=0.0,
        )
    counts = Counter(report.metrics.score_result for report in reports)
    deltas = [report.metrics.score_delta for report in reports]
    return ComparisonAggregateMetrics(
        case_count=len(reports),
        legacy_wins=counts["legacy"],
        strategy_v1_wins=counts["strategy_v1"],
        ties=counts["tie"],
        average_delta=round(sum(deltas) / len(deltas), 2),
        red_flag_improvement_rate=_rate(report.metrics.red_flag_result == "strategy_v1" for report in reports),
        human_review_improvement_rate=_rate(
            report.metrics.human_review_result == "strategy_v1" for report in reports
        ),
    )


def comparison_report_json(report: ProposalComparisonReport, *, indent: int = 2) -> str:
    return json.dumps(report.dict(), ensure_ascii=False, indent=indent, sort_keys=True)


def render_comparison_report_markdown(report: ProposalComparisonReport) -> str:
    lines = [
        "# Proposal Comparison Report",
        "",
        f"- Fixture: {report.fixture_name}",
        f"- Title: {report.title}",
        f"- Schema: {report.schema_version}",
        "",
        "## Score",
        "| Item | Legacy | Strategy v1 | Result |",
        "|---|---:|---:|---|",
        (
            f"| Total Score | {report.legacy.total_score} | {report.strategy_v1.total_score} | "
            f"{report.metrics.score_result} |"
        ),
        f"| Grade | {report.legacy.grade} | {report.strategy_v1.grade} | {report.metrics.grade_result} |",
        (
            f"| Red Flags | {len(report.legacy.red_flags)} | {len(report.strategy_v1.red_flags)} | "
            f"{report.metrics.red_flag_result} |"
        ),
        (
            f"| Human Review | {_yes_no(report.legacy.human_review_required)} | "
            f"{_yes_no(report.strategy_v1.human_review_required)} | {report.metrics.human_review_result} |"
        ),
        "",
        "## Proposal Fields",
        "| Field | Legacy | Strategy v1 |",
        "|---|---|---|",
    ]
    for field, values in report.field_comparison.items():
        lines.append(f"| {field} | {values['legacy']} | {values['strategy_v1']} |")
    lines.extend(["", "## Red Flags"])
    if report.legacy.red_flags or report.strategy_v1.red_flags:
        lines.append(f"- Legacy: {_format_list(report.legacy.red_flags)}")
        lines.append(f"- Strategy v1: {_format_list(report.strategy_v1.red_flags)}")
    else:
        lines.append("- None")
    lines.extend(["", "## Improvement Points"])
    lines.append(f"- Legacy: {_format_list(report.improvement_point_comparison['legacy'])}")
    lines.append(f"- Strategy v1: {_format_list(report.improvement_point_comparison['strategy_v1'])}")
    lines.extend(
        [
            "",
            "## Human Evaluation",
            "| Item | Score (1-5) | Note |",
            "|---|---:|---|",
            "| 理解しやすさ |  |  |",
            "| 説得力 |  |  |",
            "| 営業で使えるか |  |  |",
            "| 修正量 |  |  |",
            "",
            "### 自由コメント",
            "",
            "",
        ]
    )
    return "\n".join(lines)


def _snapshot(engine_mode: str, quality_input, report: ProposalQualityReport) -> EngineComparisonSnapshot:
    brief = quality_input.strategy_brief
    review = quality_input.human_review_report
    context = quality_input.presentation_context
    return EngineComparisonSnapshot(
        engine_mode=engine_mode,
        total_score=report.total_score,
        grade=report.grade,
        persona=str(context.persona),
        story=str(context.story_type),
        presentation_pack=str(context.presentation_pack),
        kpi_pack=str(context.kpi_pack),
        risk_messages=list(context.risk_messages or brief.risk_messages),
        red_flags=[flag.code for flag in report.red_flags],
        human_review_required=brief.human_review_required,
        human_review_status=review.status,
        improvement_points=[
            score.suggestion for score in report.category_scores if score.score < 8
        ],
    )


def _metrics(legacy: EngineComparisonSnapshot, strategy: EngineComparisonSnapshot) -> ComparisonMetrics:
    score_delta = strategy.total_score - legacy.total_score
    red_flag_delta = len(strategy.red_flags) - len(legacy.red_flags)
    return ComparisonMetrics(
        score_delta=score_delta,
        grade_result=_grade_result(legacy.grade, strategy.grade),
        score_result=_winner(score_delta),
        red_flag_delta=red_flag_delta,
        red_flag_result=_winner(-red_flag_delta),
        human_review_result=_human_review_result(legacy.human_review_required, strategy.human_review_required),
    )


def _field_comparison(
    legacy: EngineComparisonSnapshot,
    strategy: EngineComparisonSnapshot,
) -> Dict[str, Dict[str, str]]:
    return {
        "Persona": {"legacy": legacy.persona, "strategy_v1": strategy.persona},
        "Story": {"legacy": legacy.story, "strategy_v1": strategy.story},
        "Presentation Pack": {
            "legacy": legacy.presentation_pack,
            "strategy_v1": strategy.presentation_pack,
        },
        "KPI Pack": {"legacy": legacy.kpi_pack, "strategy_v1": strategy.kpi_pack},
        "Risk": {
            "legacy": _format_list(legacy.risk_messages),
            "strategy_v1": _format_list(strategy.risk_messages),
        },
        "Human Review": {
            "legacy": legacy.human_review_status,
            "strategy_v1": strategy.human_review_status,
        },
    }


def _improvement_point_comparison(
    legacy: EngineComparisonSnapshot,
    strategy: EngineComparisonSnapshot,
) -> Dict[str, List[str]]:
    return {
        "legacy": legacy.improvement_points,
        "strategy_v1": strategy.improvement_points,
    }


def _grade_result(legacy_grade: str, strategy_grade: str) -> str:
    delta = _grade_rank(legacy_grade) - _grade_rank(strategy_grade)
    return _winner(delta)


def _winner(delta: int) -> str:
    if delta > 0:
        return "strategy_v1"
    if delta < 0:
        return "legacy"
    return "tie"


def _human_review_result(legacy_required: bool, strategy_required: bool) -> str:
    if legacy_required and not strategy_required:
        return "strategy_v1"
    if strategy_required and not legacy_required:
        return "legacy"
    return "tie"


def _grade_rank(grade: str) -> int:
    return {"A": 1, "B": 2, "C": 3, "D": 4}.get(grade, 9)


def _rate(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(1 for item in items if item) * 100 / len(items), 2)


def _format_list(values: List[str]) -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    return ", ".join(items) if items else "None"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
