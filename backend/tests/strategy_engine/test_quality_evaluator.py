from __future__ import annotations

import json
import subprocess
import sys

from app.strategy_engine.quality import (
    QUALITY_CATEGORIES,
    evaluate_proposal_quality,
    quality_report_json,
    render_quality_report_markdown,
)
from app.strategy_engine.quality_fixtures import build_quality_evaluation_input


def _report(name: str):
    quality_input = build_quality_evaluation_input(name)
    return evaluate_proposal_quality(
        quality_input.strategy_brief,
        quality_input.human_review_report,
        quality_input.presentation_context,
    )


def test_quality_report_scores_all_required_categories():
    report = _report("normal")

    assert [item.category for item in report.category_scores] == QUALITY_CATEGORIES
    assert report.total_score == sum(item.score for item in report.category_scores)
    assert 0 <= report.total_score <= 100
    assert report.grade in {"A", "B", "C", "D"}
    assert report.grade in {"A", "B"}


def test_evidence_shortage_creates_red_flag_and_lowers_score():
    normal = _report("normal")
    shortage = _report("evidence_shortage")

    assert shortage.total_score < normal.total_score
    assert any(flag.code == "evidence_insufficient" for flag in shortage.red_flags)


def test_kpi_shortage_creates_red_flag():
    report = _report("kpi_shortage")

    assert any(flag.code == "kpi_missing" for flag in report.red_flags)
    score = next(item for item in report.category_scores if item.category == "KPI Quality")
    assert score.score < 8


def test_story_inconsistency_creates_red_flag():
    report = _report("story_inconsistency")

    assert any(flag.code == "story_inconsistent" for flag in report.red_flags)
    score = next(item for item in report.category_scores if item.category == "Story Consistency")
    assert score.score < 8


def test_insufficient_fixture_receives_lower_grade():
    normal = _report("normal")
    insufficient = _report("insufficient")

    assert insufficient.total_score < normal.total_score
    assert insufficient.grade in {"B", "C", "D"}


def test_quality_report_serializes_to_json_and_markdown():
    report = _report("normal")

    payload = json.loads(quality_report_json(report))
    markdown = render_quality_report_markdown(report)

    assert payload["schema_version"] == "proposal_quality_report_v1"
    assert payload["total_score"] == report.total_score
    assert "# Proposal Quality Report" in markdown
    assert "## Category Scores" in markdown
    assert "## Red Flags" in markdown


def test_cli_evaluate_outputs_markdown():
    result = subprocess.run(
        [sys.executable, "-m", "app.strategy_engine.cli", "--evaluate", "ai_ocr"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )

    assert "# Proposal Quality Report" in result.stdout
    assert "Story Consistency" in result.stdout
    assert "Total Score" in result.stdout


def test_cli_evaluate_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "app.strategy_engine.cli", "--evaluate", "kpi_shortage", "--format", "json"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "proposal_quality_report_v1"
    assert any(flag["code"] == "kpi_missing" for flag in payload["red_flags"])
