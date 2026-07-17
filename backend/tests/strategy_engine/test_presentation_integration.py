from __future__ import annotations

import pytest

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest
from app.services import presentation_engine_integration
from app.services.presentation_engine_integration import build_pptx_bytes_for_engine
from app.services.pptx_service import build_pptx_context
from app.strategy_engine.enums import ReviewDecision
from app.strategy_engine.evaluator import evaluate_strategy
from app.strategy_engine.fixtures import FIXTURES
from app.strategy_engine.models import HumanReviewResult
from app.strategy_engine.review import create_review_report


def _review_report(fixture_name: str, decision: ReviewDecision = ReviewDecision.APPROVE):
    brief = evaluate_strategy(FIXTURES[fixture_name])
    return create_review_report(brief, HumanReviewResult(decision=decision, reviewer="sales"))


def _pptx_request(*, review_report=None) -> PptxDownloadRequest:
    return PptxDownloadRequest(
        project_brief="AI-OCR invoice reading PoC with human review and CSV integration.",
        client_company_info="Sample Corp",
        budget_range="up to 10,000,000 JPY",
        desired_launch_timing="2027-05",
        strategy_review_report=review_report.dict() if review_report is not None else None,
        powerpoint_generation_data=PowerPointData(
            deck_title="AI-OCR Proposal",
            client_name="Sample Corp",
            slides=[
                PowerPointSlide(
                    slide_no=1,
                    layout="summary",
                    title="AI-OCR Proposal Summary",
                    bullets=[
                        "Extract invoice fields with AI-OCR.",
                        "Keep human review for exception handling.",
                        "Export approved results by CSV.",
                    ],
                    speaker_notes="Explain the staged PoC scope.",
                    visual_suggestion="process diagram",
                )
            ],
        ),
    )


def test_legacy_engine_does_not_call_strategy_adapter(monkeypatch: pytest.MonkeyPatch):
    def fail_if_called(_report):
        raise AssertionError("legacy mode must not generate Presentation Context")

    monkeypatch.setattr(presentation_engine_integration, "_presentation_context_from_review_report", fail_if_called)

    result = build_pptx_bytes_for_engine(_pptx_request(), engine_mode="legacy")

    assert result.engine_mode == "legacy"
    assert result.presentation_context is None
    assert result.pptx_bytes[:2] == b"PK"


def test_strategy_engine_generates_context_and_pptx_from_approved_review():
    report = _review_report("ai_ocr")
    request = _pptx_request(review_report=report)

    result = build_pptx_bytes_for_engine(request, engine_mode="strategy_v1")

    assert result.engine_mode == "strategy_v1"
    assert result.presentation_context is not None
    assert result.presentation_context.presentation_pack == "vision_ocr"
    assert result.presentation_context.story_type == report.reviewed_brief.story_type
    assert result.presentation_context.persona == report.reviewed_brief.primary_persona
    assert result.pptx_bytes[:2] == b"PK"

    pptx_context = build_pptx_context(request, presentation_context=result.presentation_context)
    assert pptx_context.proposal_category == "ai_ocr"


def test_strategy_engine_requires_approved_review_report():
    with pytest.raises(ValueError, match="approved strategy_review_report"):
        build_pptx_bytes_for_engine(_pptx_request(), engine_mode="strategy_v1")


def test_strategy_engine_rejects_unapproved_review_report():
    report = _review_report("ai_ocr", ReviewDecision.REJECT)

    with pytest.raises(ValueError, match="approved Strategy Brief review"):
        build_pptx_bytes_for_engine(_pptx_request(review_report=report), engine_mode="strategy_v1")


def test_invalid_engine_mode_falls_back_to_legacy():
    result = build_pptx_bytes_for_engine(_pptx_request(), engine_mode="unknown")

    assert result.engine_mode == "legacy"
    assert result.presentation_context is None
    assert result.pptx_bytes[:2] == b"PK"
