import pytest

from app.strategy_engine.adapter import adapt_review_report_to_presentation_context
from app.strategy_engine.enums import ReviewDecision
from app.strategy_engine.evaluator import evaluate_strategy
from app.strategy_engine.fixtures import FIXTURES
from app.strategy_engine.models import HumanReviewResult, ReviewOverride
from app.strategy_engine.review import create_review_report


def _report(fixture_name: str, decision: ReviewDecision = ReviewDecision.APPROVE):
    brief = evaluate_strategy(FIXTURES[fixture_name])
    return create_review_report(
        brief,
        HumanReviewResult(decision=decision, reviewer="sales"),
    )


@pytest.mark.parametrize("fixture_name", sorted(FIXTURES.keys()))
def test_all_fixtures_generate_presentation_context_after_approval(fixture_name):
    report = _report(fixture_name)
    context = adapt_review_report_to_presentation_context(report)

    assert context.schema_version == "presentation_context_v1"
    assert context.source_strategy_schema_version == report.reviewed_brief.schema_version
    assert context.review_status == "approved"
    assert context.presentation_pack == report.reviewed_brief.primary_pack
    assert context.main_message == report.reviewed_brief.main_message
    assert context.slide_order[: len(report.reviewed_brief.required_slide_types)] == report.reviewed_brief.required_slide_types
    assert context.hero["theme"] == report.reviewed_brief.hero_theme


def test_approve_with_changes_uses_reviewed_brief():
    brief = evaluate_strategy(FIXTURES["ai_ocr"])
    report = create_review_report(
        brief,
        HumanReviewResult(
            decision=ReviewDecision.APPROVE_WITH_CHANGES,
            reviewer="sales",
            overrides=[
                ReviewOverride(field="main_message", value="Reviewed message", reason="sales review"),
                ReviewOverride(field="next_actions", value=["Confirm data"], reason="sales review"),
            ],
        ),
    )

    context = adapt_review_report_to_presentation_context(report)

    assert context.review_status == "approved_with_changes"
    assert context.main_message == "Reviewed message"
    assert context.hero["main_message"] == "Reviewed message"
    assert context.next_actions == ["Confirm data"]


@pytest.mark.parametrize("decision", [ReviewDecision.REJECT, ReviewDecision.RE_EVALUATE])
def test_reject_and_re_evaluate_cannot_generate_presentation_context(decision):
    report = _report("ai_ocr", decision)

    with pytest.raises(ValueError):
        adapt_review_report_to_presentation_context(report)


def test_context_does_not_expose_strategy_redecision_fields():
    context = adapt_review_report_to_presentation_context(_report("ai_ocr"))
    payload = context.dict()

    assert "confidence" not in payload
    assert "selection_reasons" not in payload
    assert "evidence_summary" not in payload
    assert "human_review_reasons" not in payload


def test_context_preserves_term_guard_for_presentation_validation():
    context = adapt_review_report_to_presentation_context(_report("ai_ocr"))

    assert "OCR" in context.allowed_terms
    assert "CMS" in context.prohibited_terms
