from __future__ import annotations

import json
import subprocess
import sys

from app.strategy_engine.comparison import (
    aggregate_comparison_metrics,
    comparison_report_json,
    compare_fixture,
    render_comparison_report_markdown,
)


def test_compare_fixture_builds_required_report_fields():
    report = compare_fixture("ai_ocr")

    assert report.schema_version == "proposal_comparison_report_v1"
    assert report.fixture_name == "ai_ocr"
    assert report.legacy.engine_mode == "legacy"
    assert report.strategy_v1.engine_mode == "strategy_v1"
    assert report.legacy.total_score >= 0
    assert report.strategy_v1.total_score >= 0
    assert report.metrics.score_result in {"strategy_v1", "legacy", "tie"}
    assert report.metrics.grade_result in {"strategy_v1", "legacy", "tie"}


def test_compare_fixture_includes_human_evaluation_template():
    report = compare_fixture("crm")
    template = report.human_evaluation_template

    assert template.ease_of_understanding.label == "理解しやすさ"
    assert template.persuasiveness.label == "説得力"
    assert template.sales_readiness.label == "営業で使えるか"
    assert template.revision_effort.label == "修正量"
    assert template.ease_of_understanding.score_range == "1-5"


def test_comparison_outputs_json_and_markdown():
    report = compare_fixture("ai_ocr")

    payload = json.loads(comparison_report_json(report))
    markdown = render_comparison_report_markdown(report)

    assert payload["schema_version"] == "proposal_comparison_report_v1"
    assert payload["legacy"]["engine_mode"] == "legacy"
    assert payload["strategy_v1"]["engine_mode"] == "strategy_v1"
    assert "# Proposal Comparison Report" in markdown
    assert "## Human Evaluation" in markdown
    assert "理解しやすさ" in markdown


def test_aggregate_comparison_metrics_counts_winners():
    reports = [compare_fixture("ai_ocr"), compare_fixture("sparse")]
    metrics = aggregate_comparison_metrics(reports)

    assert metrics.case_count == 2
    assert metrics.legacy_wins + metrics.strategy_v1_wins + metrics.ties == 2
    assert -100 <= metrics.average_delta <= 100
    assert 0 <= metrics.red_flag_improvement_rate <= 100
    assert 0 <= metrics.human_review_improvement_rate <= 100


def test_cli_compare_outputs_markdown():
    result = subprocess.run(
        [sys.executable, "-m", "app.strategy_engine.cli", "--compare", "ai_ocr"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )

    assert "# Proposal Comparison Report" in result.stdout
    assert "## Score" in result.stdout
    assert "## Human Evaluation" in result.stdout


def test_cli_compare_outputs_json():
    result = subprocess.run(
        [sys.executable, "-m", "app.strategy_engine.cli", "--compare", "crm", "--format", "json"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )

    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "proposal_comparison_report_v1"
    assert payload["fixture_name"] == "crm"
