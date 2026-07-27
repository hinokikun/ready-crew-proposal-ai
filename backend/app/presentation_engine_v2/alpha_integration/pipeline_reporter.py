"""Markdown reporters for Alpha Integration Review."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from .pipeline_models import AlphaCrossCaseSummary, AlphaIntegrationOutput


def human_review_markdown(output: AlphaIntegrationOutput) -> str:
    review = output.human_review_summary
    lines = [
        f"# Alpha Integration Case Review: {review.case_name}",
        "",
        f"- Case ID: `{review.case_id}`",
        f"- Phase 2D Readiness: **{review.phase2d_readiness}**",
        f"- Overall Score: **{output.pipeline_evaluation_result.overall_score} / 100**",
        f"- Grade: **{output.pipeline_evaluation_result.grade}**",
        "",
        "## Proposal Context",
        "",
        review.proposal_context_summary,
        "",
        "## Deck",
        "",
        f"- Audience: {review.audience}",
        f"- Decision Stage: {review.decision_stage}",
        f"- Deck Goal: {review.deck_goal}",
        f"- Story Arc: {review.story_arc}",
        "",
        "## Sections",
        "",
        *[f"- {item}" for item in review.section_summary],
        "",
        "## Slides and Messages",
        "",
        *[f"- {item}" for item in review.headline_summary],
        "",
        "## Required Evidence",
        "",
        *[f"- {item}" for item in review.required_evidence_summary[:40]],
        "",
        "## Missing Evidence",
        "",
        *([f"- {item}" for item in review.missing_evidence_summary] or ["- No major missing evidence was detected."]),
        "",
        "## Warnings",
        "",
        *([f"- {item}" for item in review.key_warnings] or ["- No major warning was detected."]),
        "",
        "## Blocking Issues",
        "",
        *([f"- {item}" for item in review.blocking_issues] or ["- No blocking issue was detected."]),
        "",
        "## Good Points",
        "",
        *[f"- {item}" for item in review.good_points],
        "",
        "## Unnatural / Weak Points",
        "",
        *(
            [f"- {item}" for item in [*review.unnatural_points, *review.weak_sales_points]]
            or ["- No major unnatural or weak sales point was detected."]
        ),
        "",
        "## Improvement Candidates",
        "",
        *(
            [f"- {item}" for item in review.improvement_candidates]
            or ["- No required improvement was detected before Phase 2D."]
        ),
        "",
    ]
    return "\n".join(lines)


def summarize_outputs(outputs: list[AlphaIntegrationOutput]) -> AlphaCrossCaseSummary:
    if not outputs:
        return AlphaCrossCaseSummary(
            case_count=0,
            average_overall_score=0,
            min_overall_score=0,
            max_overall_score=0,
            note="No Alpha Integration outputs were provided.",
        )
    scores = [item.pipeline_evaluation_result.overall_score for item in outputs]
    grades = Counter(item.pipeline_evaluation_result.grade for item in outputs)
    readiness = Counter(str(item.phase2d_readiness) for item in outputs)
    warning_counter = Counter(issue.code for output in outputs for issue in output.warnings)
    blocking_counter = Counter(issue.code for output in outputs for issue in output.blocking_issues)
    dim_scores: dict[str, list[int]] = defaultdict(list)
    for output in outputs:
        for dim in output.pipeline_evaluation_result.dimensions:
            dim_scores[dim.name].append(dim.score)
    weakest = sorted(dim_scores, key=lambda name: mean(dim_scores[name]))[:5]
    strongest = sorted(dim_scores, key=lambda name: mean(dim_scores[name]), reverse=True)[:5]
    industry_scores: dict[str, list[int]] = defaultdict(list)
    audience_scores: dict[str, list[int]] = defaultdict(list)
    decision_scores: dict[str, list[int]] = defaultdict(list)
    for output in outputs:
        context = output.deck_planner_result.context
        industry_scores[context.industry or "unknown"].append(output.pipeline_evaluation_result.overall_score)
        audience_scores[str(output.deck_planner_result.deck_blueprint.primary_audience)].append(
            output.pipeline_evaluation_result.overall_score
        )
        decision_scores[str(output.deck_planner_result.deck_blueprint.decision_stage)].append(
            output.pipeline_evaluation_result.overall_score
        )
    return AlphaCrossCaseSummary(
        case_count=len(outputs),
        average_overall_score=round(mean(scores), 1),
        min_overall_score=min(scores),
        max_overall_score=max(scores),
        grade_distribution=dict(sorted(grades.items())),
        readiness_distribution=dict(sorted(readiness.items())),
        most_frequent_warnings=[f"{code}: {count}" for code, count in warning_counter.most_common(10)],
        most_frequent_blocking_issues=[f"{code}: {count}" for code, count in blocking_counter.most_common(10)],
        weakest_dimensions=weakest,
        strongest_dimensions=strongest,
        industry_tendency={key: round(mean(value), 1) for key, value in sorted(industry_scores.items())},
        audience_tendency={key: round(mean(value), 1) for key, value in sorted(audience_scores.items())},
        decision_stage_tendency={key: round(mean(value), 1) for key, value in sorted(decision_scores.items())},
        note="Fixture evaluation only. This does not guarantee real sales outcome.",
    )


def cross_case_markdown(outputs: list[AlphaIntegrationOutput]) -> str:
    summary = summarize_outputs(outputs)
    lines = [
        "# Alpha Integration Cross-case Quality Report",
        "",
        f"- Case Count: {summary.case_count}",
        f"- Average Score: {summary.average_overall_score}",
        f"- Min Score: {summary.min_overall_score}",
        f"- Max Score: {summary.max_overall_score}",
        "",
        "## Grade Distribution",
        "",
        *[f"- {grade}: {count}" for grade, count in summary.grade_distribution.items()],
        "",
        "## Readiness Distribution",
        "",
        *[f"- {status}: {count}" for status, count in summary.readiness_distribution.items()],
        "",
        "## Frequent Warnings",
        "",
        *([f"- {item}" for item in summary.most_frequent_warnings] or ["- None"]),
        "",
        "## Frequent Blocking Issues",
        "",
        *([f"- {item}" for item in summary.most_frequent_blocking_issues] or ["- None"]),
        "",
        "## Weakest Dimensions",
        "",
        *[f"- {item}" for item in summary.weakest_dimensions],
        "",
        "## Strongest Dimensions",
        "",
        *[f"- {item}" for item in summary.strongest_dimensions],
        "",
        "## Note",
        "",
        summary.note,
        "",
    ]
    return "\n".join(lines)


def improvement_backlog_markdown(outputs: list[AlphaIntegrationOutput]) -> str:
    p0: list[str] = []
    p1: list[str] = []
    p2: list[str] = []
    p3: list[str] = []
    for output in outputs:
        for issue in output.blocking_issues:
            p0.append(f"{output.integration_case_id}: {issue.code} - {issue.message}")
        for item in output.improvement_candidates[:3]:
            p1.append(f"{output.integration_case_id}: {item}")
        if output.pipeline_evaluation_result.overall_score < 85:
            p2.append(f"{output.integration_case_id}: Review low score ({output.pipeline_evaluation_result.overall_score}).")
    if not p0:
        p0.append("No P0 blocker detected in current fixture set.")
    if not p3:
        p3.append("Future: compare Alpha Integration outputs against human-reviewed real cases.")
    lines = [
        "# Alpha Integration Improvement Backlog",
        "",
        "## P0 Blocker",
        "",
        *[f"- {item}" for item in p0[:30]],
        "",
        "## P1 Recommended Before Phase 2D",
        "",
        *([f"- {item}" for item in p1[:30]] or ["- No P1 item detected."]),
        "",
        "## P2 Can Improve Alongside Phase 2D",
        "",
        *([f"- {item}" for item in p2[:30]] or ["- No P2 item detected."]),
        "",
        "## P3 Future",
        "",
        *[f"- {item}" for item in p3[:20]],
        "",
    ]
    return "\n".join(lines)
