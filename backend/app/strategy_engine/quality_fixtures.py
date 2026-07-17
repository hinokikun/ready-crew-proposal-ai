from __future__ import annotations

from dataclasses import dataclass

from .adapter import adapt_review_report_to_presentation_context
from .enums import EvidenceLevel, ReviewDecision
from .evaluator import evaluate_strategy
from .fixtures import FIXTURES
from .models import HumanReviewReport, HumanReviewResult, PresentationContext, StrategyBrief
from .review import create_review_report


@dataclass(frozen=True)
class QualityEvaluationInput:
    name: str
    strategy_brief: StrategyBrief
    human_review_report: HumanReviewReport
    presentation_context: PresentationContext


QUALITY_VARIANTS = {
    "normal": "ai_ocr",
    "insufficient": "sparse",
    "evidence_shortage": "ai_ocr",
    "kpi_shortage": "ai_ocr",
    "story_inconsistency": "ai_ocr",
}


def quality_fixture_choices() -> list[str]:
    return sorted(set(FIXTURES.keys()) | set(QUALITY_VARIANTS.keys()))


def build_quality_evaluation_input(name: str) -> QualityEvaluationInput:
    fixture_name = QUALITY_VARIANTS.get(name, name)
    if fixture_name not in FIXTURES:
        raise KeyError(f"Unknown quality fixture: {name}")
    brief = evaluate_strategy(FIXTURES[fixture_name])
    brief = _apply_variant(name, brief)
    report = create_review_report(brief, HumanReviewResult(decision=ReviewDecision.APPROVE, reviewer="quality"))
    context = adapt_review_report_to_presentation_context(report)
    if name == "story_inconsistency":
        context = context.copy(update={"story_type": "roi" if context.story_type != "roi" else "quality"})
    return QualityEvaluationInput(
        name=name,
        strategy_brief=brief,
        human_review_report=report,
        presentation_context=context,
    )


def _apply_variant(name: str, brief: StrategyBrief) -> StrategyBrief:
    if name == "evidence_shortage":
        return brief.copy(
            update={
                "evidence_summary": {
                    "budget": EvidenceLevel.MISSING,
                    "scope": EvidenceLevel.INFERRED,
                    "kpi": EvidenceLevel.MISSING,
                },
                "missing_information": ["budget evidence", "scope evidence", "KPI evidence"],
            }
        )
    if name == "kpi_shortage":
        return brief.copy(
            update={
                "kpi_pack": "",
                "required_slide_types": _without_kpi(brief.required_slide_types),
                "optional_slide_types": _without_kpi(brief.optional_slide_types),
            }
        )
    return brief


def _without_kpi(items: list[str]) -> list[str]:
    return [item for item in items if "kpi" not in str(item).lower()]
