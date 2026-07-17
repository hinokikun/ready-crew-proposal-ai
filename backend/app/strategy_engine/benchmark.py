from __future__ import annotations

import csv
import io
import json
from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

from .benchmark_dataset import CATEGORY_LABELS, EvaluationDatasetCase, dataset_cases
from .quality import evaluate_proposal_quality
from .quality_fixtures import build_quality_evaluation_input


ENGINE_MODES = ("strategy_v1", "legacy")


class EvaluationCaseResult(BaseModel):
    case_id: str
    category: str
    category_label: str
    fixture_name: str
    title: str
    engine_mode: str
    total_score: int
    grade: str
    red_flag_count: int
    red_flags: List[str] = Field(default_factory=list)
    human_review_required: bool
    confidence: float
    persona: str
    story: str
    pack: str
    generic_fallback: bool


class EvaluationMetricSummary(BaseModel):
    engine_mode: str
    case_count: int
    average_score: float
    grade_distribution: Dict[str, int] = Field(default_factory=dict)
    red_flag_count: int
    human_review_rate: float
    generic_fallback_rate: float
    confidence_distribution: Dict[str, int] = Field(default_factory=dict)
    persona_distribution: Dict[str, int] = Field(default_factory=dict)
    story_distribution: Dict[str, int] = Field(default_factory=dict)
    pack_usage: Dict[str, int] = Field(default_factory=dict)


class EvaluationCategorySummary(BaseModel):
    category: str
    category_label: str
    case_count: int
    average_score: float
    grade_distribution: Dict[str, int] = Field(default_factory=dict)
    red_flag_count: int


class LegacyComparisonSummary(BaseModel):
    case_count: int
    average_strategy_v1_score: float
    average_legacy_score: float
    average_score_delta: float
    grade_changes: Dict[str, int] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    schema_version: str = "proposal_evaluation_report_v1"
    dataset_version: str = "evaluation_dataset_v1"
    category_filter: Optional[str] = None
    summary: Dict[str, EvaluationMetricSummary] = Field(default_factory=dict)
    category_summaries: List[EvaluationCategorySummary] = Field(default_factory=list)
    red_flag_summary: Dict[str, int] = Field(default_factory=dict)
    improvement_candidates: List[str] = Field(default_factory=list)
    legacy_comparison: LegacyComparisonSummary
    results: List[EvaluationCaseResult] = Field(default_factory=list)


def run_benchmark(category: str | None = None) -> EvaluationReport:
    cases = dataset_cases(category)
    results: List[EvaluationCaseResult] = []
    for case in cases:
        for mode in case.expected_engine_modes:
            if mode not in ENGINE_MODES:
                continue
            results.append(_evaluate_case(case, mode))
    return EvaluationReport(
        category_filter=category,
        summary={mode: _metric_summary(mode, results) for mode in ENGINE_MODES},
        category_summaries=_category_summaries(results),
        red_flag_summary=dict(_red_flag_counter(results)),
        improvement_candidates=_improvement_candidates(results),
        legacy_comparison=_legacy_comparison(results),
        results=results,
    )


def evaluation_report_json(report: EvaluationReport, *, indent: int = 2) -> str:
    return json.dumps(report.dict(), ensure_ascii=False, indent=indent, sort_keys=True)


def render_evaluation_report_markdown(report: EvaluationReport) -> str:
    lines = [
        "# Proposal Evaluation Report",
        "",
        f"- Schema: {report.schema_version}",
        f"- Dataset: {report.dataset_version}",
        f"- Category Filter: {report.category_filter or 'all'}",
        "",
        "## Summary",
    ]
    for mode, summary in report.summary.items():
        lines.extend(
            [
                f"### {mode}",
                f"- Cases: {summary.case_count}",
                f"- Average Score: {summary.average_score:.1f}",
                f"- Red Flags: {summary.red_flag_count}",
                f"- Human Review Rate: {summary.human_review_rate:.1f}%",
                f"- Generic Fallback Rate: {summary.generic_fallback_rate:.1f}%",
                f"- Grade Distribution: {_format_counts(summary.grade_distribution)}",
                f"- Confidence Distribution: {_format_counts(summary.confidence_distribution)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Category Summary",
            "| Category | Cases | Average Score | Grades | Red Flags |",
            "|---|---:|---:|---|---:|",
        ]
    )
    for item in report.category_summaries:
        lines.append(
            f"| {item.category_label} | {item.case_count} | {item.average_score:.1f} | "
            f"{_format_counts(item.grade_distribution)} | {item.red_flag_count} |"
        )
    lines.extend(
        [
            "",
            "## Legacy Comparison",
            f"- Cases: {report.legacy_comparison.case_count}",
            f"- Strategy v1 Average: {report.legacy_comparison.average_strategy_v1_score:.1f}",
            f"- Legacy Average: {report.legacy_comparison.average_legacy_score:.1f}",
            f"- Delta: {report.legacy_comparison.average_score_delta:.1f}",
            f"- Grade Changes: {_format_counts(report.legacy_comparison.grade_changes)}",
            "",
            "## Red Flags",
        ]
    )
    if report.red_flag_summary:
        for code, count in sorted(report.red_flag_summary.items()):
            lines.append(f"- {code}: {count}")
    else:
        lines.append("- None")
    lines.extend(["", "## Improvement Candidates"])
    if report.improvement_candidates:
        for item in report.improvement_candidates:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Case Results",
            "| Case | Category | Mode | Score | Grade | Persona | Story | Pack | Red Flags |",
            "|---|---|---|---:|---|---|---|---|---:|",
        ]
    )
    for result in report.results:
        lines.append(
            f"| {result.case_id} | {result.category_label} | {result.engine_mode} | "
            f"{result.total_score} | {result.grade} | {result.persona} | {result.story} | "
            f"{result.pack} | {result.red_flag_count} |"
        )
    lines.append("")
    return "\n".join(lines)


def evaluation_report_csv(report: EvaluationReport) -> str:
    stream = io.StringIO()
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        [
            "case_id",
            "category",
            "category_label",
            "fixture_name",
            "title",
            "engine_mode",
            "total_score",
            "grade",
            "red_flag_count",
            "red_flags",
            "human_review_required",
            "confidence",
            "persona",
            "story",
            "pack",
            "generic_fallback",
        ]
    )
    for result in report.results:
        writer.writerow(
            [
                result.case_id,
                result.category,
                result.category_label,
                result.fixture_name,
                result.title,
                result.engine_mode,
                result.total_score,
                result.grade,
                result.red_flag_count,
                ";".join(result.red_flags),
                result.human_review_required,
                f"{result.confidence:.2f}",
                result.persona,
                result.story,
                result.pack,
                result.generic_fallback,
            ]
        )
    return stream.getvalue()


def _evaluate_case(case: EvaluationDatasetCase, engine_mode: str) -> EvaluationCaseResult:
    quality_input = build_quality_evaluation_input(case.fixture_name)
    report = evaluate_proposal_quality(
        quality_input.strategy_brief,
        quality_input.human_review_report,
        quality_input.presentation_context,
    )
    brief = quality_input.strategy_brief
    context = quality_input.presentation_context
    return EvaluationCaseResult(
        case_id=case.case_id,
        category=case.category,
        category_label=CATEGORY_LABELS[case.category],
        fixture_name=case.fixture_name,
        title=case.title,
        engine_mode=engine_mode,
        total_score=report.total_score,
        grade=report.grade,
        red_flag_count=len(report.red_flags),
        red_flags=[flag.code for flag in report.red_flags],
        human_review_required=brief.human_review_required,
        confidence=brief.confidence,
        persona=str(context.persona),
        story=str(context.story_type),
        pack=str(context.presentation_pack),
        generic_fallback=str(context.presentation_pack) == "generic_consulting"
        or str(brief.project_category) == "generic_consulting",
    )


def _metric_summary(engine_mode: str, results: List[EvaluationCaseResult]) -> EvaluationMetricSummary:
    mode_results = [result for result in results if result.engine_mode == engine_mode]
    return EvaluationMetricSummary(
        engine_mode=engine_mode,
        case_count=len(mode_results),
        average_score=_average(result.total_score for result in mode_results),
        grade_distribution=dict(Counter(result.grade for result in mode_results)),
        red_flag_count=sum(result.red_flag_count for result in mode_results),
        human_review_rate=_rate(result.human_review_required for result in mode_results),
        generic_fallback_rate=_rate(result.generic_fallback for result in mode_results),
        confidence_distribution=dict(Counter(_confidence_bucket(result.confidence) for result in mode_results)),
        persona_distribution=dict(Counter(result.persona for result in mode_results)),
        story_distribution=dict(Counter(result.story for result in mode_results)),
        pack_usage=dict(Counter(result.pack for result in mode_results)),
    )


def _category_summaries(results: List[EvaluationCaseResult]) -> List[EvaluationCategorySummary]:
    strategy_results = [result for result in results if result.engine_mode == "strategy_v1"]
    grouped: Dict[str, List[EvaluationCaseResult]] = defaultdict(list)
    for result in strategy_results:
        grouped[result.category].append(result)
    summaries: List[EvaluationCategorySummary] = []
    for category in sorted(grouped):
        items = grouped[category]
        summaries.append(
            EvaluationCategorySummary(
                category=category,
                category_label=CATEGORY_LABELS[category],
                case_count=len(items),
                average_score=_average(item.total_score for item in items),
                grade_distribution=dict(Counter(item.grade for item in items)),
                red_flag_count=sum(item.red_flag_count for item in items),
            )
        )
    return summaries


def _legacy_comparison(results: List[EvaluationCaseResult]) -> LegacyComparisonSummary:
    by_case: Dict[str, Dict[str, EvaluationCaseResult]] = defaultdict(dict)
    for result in results:
        by_case[result.case_id][result.engine_mode] = result
    strategy_scores: List[int] = []
    legacy_scores: List[int] = []
    grade_changes = Counter()
    for modes in by_case.values():
        strategy = modes.get("strategy_v1")
        legacy = modes.get("legacy")
        if not strategy or not legacy:
            continue
        strategy_scores.append(strategy.total_score)
        legacy_scores.append(legacy.total_score)
        if strategy.grade == legacy.grade:
            grade_changes["same"] += 1
        elif _grade_rank(strategy.grade) < _grade_rank(legacy.grade):
            grade_changes["strategy_v1_higher"] += 1
        else:
            grade_changes["legacy_higher"] += 1
    strategy_average = _average(strategy_scores)
    legacy_average = _average(legacy_scores)
    return LegacyComparisonSummary(
        case_count=len(strategy_scores),
        average_strategy_v1_score=strategy_average,
        average_legacy_score=legacy_average,
        average_score_delta=round(strategy_average - legacy_average, 2),
        grade_changes=dict(grade_changes),
    )


def _red_flag_counter(results: List[EvaluationCaseResult]) -> Counter:
    counter: Counter = Counter()
    for result in results:
        if result.engine_mode != "strategy_v1":
            continue
        counter.update(result.red_flags)
    return counter


def _improvement_candidates(results: List[EvaluationCaseResult]) -> List[str]:
    counter = _red_flag_counter(results)
    if not counter:
        return []
    return [f"{code}: review {count} affected case(s)" for code, count in counter.most_common()]


def _confidence_bucket(confidence: float) -> str:
    if confidence >= 0.8:
        return "high"
    if confidence >= 0.6:
        return "medium"
    return "low"


def _rate(values: Iterable[bool]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(1 for item in items if item) * 100 / len(items), 2)


def _average(values: Iterable[int]) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 2)


def _grade_rank(grade: str) -> int:
    return {"A": 1, "B": 2, "C": 3, "D": 4}.get(grade, 9)


def _format_counts(values: Dict[str, int]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in sorted(values.items()))
