from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter

from app.strategy_engine.benchmark import (
    ENGINE_MODES,
    evaluation_report_csv,
    evaluation_report_json,
    render_evaluation_report_markdown,
    run_benchmark,
)
from app.strategy_engine.benchmark_dataset import CATEGORY_LABELS, EVALUATION_DATASET, dataset_cases


def test_evaluation_dataset_covers_required_categories_with_multiple_cases():
    counts = Counter(case.category for case in EVALUATION_DATASET)

    assert set(CATEGORY_LABELS).issubset(counts)
    for category in CATEGORY_LABELS:
        assert counts[category] >= 2


def test_benchmark_report_contains_required_metrics_and_modes():
    report = run_benchmark()

    assert set(report.summary) == set(ENGINE_MODES)
    assert report.summary["strategy_v1"].case_count == len(EVALUATION_DATASET)
    assert report.summary["legacy"].case_count == len(EVALUATION_DATASET)
    assert report.summary["strategy_v1"].average_score > 0
    assert report.summary["strategy_v1"].grade_distribution
    assert report.summary["strategy_v1"].confidence_distribution
    assert report.summary["strategy_v1"].persona_distribution
    assert report.summary["strategy_v1"].story_distribution
    assert report.summary["strategy_v1"].pack_usage
    assert report.legacy_comparison.case_count == len(EVALUATION_DATASET)


def test_benchmark_category_filter_limits_dataset():
    report = run_benchmark("vision_ocr")

    assert report.category_filter == "vision_ocr"
    assert {result.category for result in report.results} == {"vision_ocr"}
    assert report.summary["strategy_v1"].case_count == len(dataset_cases("vision_ocr"))
    assert len(report.category_summaries) == 1
    assert report.category_summaries[0].category == "vision_ocr"


def test_benchmark_outputs_json_markdown_and_csv():
    report = run_benchmark("vision_ocr")

    payload = json.loads(evaluation_report_json(report))
    markdown = render_evaluation_report_markdown(report)
    rows = list(csv.DictReader(evaluation_report_csv(report).splitlines()))

    assert payload["schema_version"] == "proposal_evaluation_report_v1"
    assert "# Proposal Evaluation Report" in markdown
    assert "## Legacy Comparison" in markdown
    assert len(rows) == len(report.results)
    assert rows[0]["engine_mode"] in ENGINE_MODES


def test_cli_benchmark_outputs_markdown():
    result = subprocess.run(
        [sys.executable, "-m", "app.strategy_engine.cli", "--benchmark"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )

    assert "# Proposal Evaluation Report" in result.stdout
    assert "## Category Summary" in result.stdout
    assert "## Legacy Comparison" in result.stdout


def test_cli_benchmark_category_outputs_csv():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.strategy_engine.cli",
            "--benchmark",
            "--category",
            "vision_ocr",
            "--format",
            "csv",
        ],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )

    rows = list(csv.DictReader(result.stdout.splitlines()))
    assert rows
    assert {row["category"] for row in rows} == {"vision_ocr"}
