import subprocess
import sys

from app.strategy_engine.enums import ReviewDecision
from app.strategy_engine.evaluator import evaluate_strategy
from app.strategy_engine.fixtures import FIXTURES
from app.strategy_engine.models import HumanReviewResult, ReviewOverride
from app.strategy_engine.review import (
    create_review_report,
    render_strategy_brief_markdown,
    review_report_json,
)


def _brief():
    return evaluate_strategy(FIXTURES["ai_ocr"])


def test_approve_review_result_keeps_brief_unchanged():
    brief = _brief()
    report = create_review_report(
        brief,
        HumanReviewResult(
            decision=ReviewDecision.APPROVE,
            reviewer="sales",
            comment="OK",
            reviewed_at="2026-07-17T10:00:00+09:00",
        ),
    )

    assert report.status == "approved"
    assert report.reviewed_brief == brief
    assert report.applied_overrides == []
    assert report.rejected_overrides == []
    assert report.review_required_before_presentation is True


def test_approve_with_changes_applies_only_allowed_overrides():
    brief = _brief()
    report = create_review_report(
        brief,
        HumanReviewResult(
            decision=ReviewDecision.APPROVE_WITH_CHANGES,
            reviewer="sales",
            overrides=[
                ReviewOverride(
                    field="primary_persona",
                    value="department_head",
                    reason="meeting owner is department head",
                ),
                ReviewOverride(
                    field="next_actions",
                    value=["Confirm PoC scope", "Confirm data conditions"],
                    reason="data confirmation needed",
                ),
                ReviewOverride(
                    field="confidence",
                    value=0.99,
                    reason="locked engine evidence",
                ),
            ],
        ),
    )

    assert report.status == "approved_with_changes"
    assert report.reviewed_brief.primary_persona == "department_head"
    assert report.reviewed_brief.next_actions == ["Confirm PoC scope", "Confirm data conditions"]
    assert report.reviewed_brief.confidence == brief.confidence
    assert [override.field for override in report.applied_overrides] == ["primary_persona", "next_actions"]
    assert [override.field for override in report.rejected_overrides] == ["confidence"]

def test_reject_review_result_does_not_apply_overrides():
    brief = _brief()
    report = create_review_report(
        brief,
        HumanReviewResult(
            decision=ReviewDecision.REJECT,
            reviewer="sales",
            comment="Category needs confirmation",
            overrides=[ReviewOverride(field="main_message", value="Different message")],
        ),
    )

    assert report.status == "rejected"
    assert report.reviewed_brief == brief
    assert report.applied_overrides == []
    assert [override.field for override in report.rejected_overrides] == ["main_message"]


def test_re_evaluate_review_result_marks_re_evaluation_required():
    brief = _brief()
    report = create_review_report(
        brief,
        HumanReviewResult(
            decision=ReviewDecision.RE_EVALUATE,
            reviewer="sales",
            comment="Need more KPI evidence",
        ),
    )

    assert report.status == "re_evaluate_required"
    assert report.reviewed_brief == brief
    assert "Need more KPI evidence" in report.markdown_summary


def test_markdown_review_contains_sales_review_sections():
    markdown = render_strategy_brief_markdown(_brief())
    assert "# Strategy Brief" in markdown
    assert "## Review Targets" in markdown
    assert "## Evidence" in markdown
    assert "## Override Rules" in markdown
    assert "- [ ] Approve with Changes" in markdown


def test_review_report_serializes_to_json_and_markdown():
    report = create_review_report(
        _brief(),
        HumanReviewResult(decision=ReviewDecision.APPROVE, reviewer="sales"),
    )
    payload = review_report_json(report)
    assert '"decision": "approve"' in payload
    assert "Strategy Brief Human Review Report" in report.markdown_summary


def test_cli_review_outputs_markdown():
    result = subprocess.run(
        [sys.executable, "-m", "app.strategy_engine.cli", "--review", "ai_ocr"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )

    assert "# Strategy Brief" in result.stdout
    assert "Category: vision_ocr" in result.stdout
    assert "## Review Result" in result.stdout
