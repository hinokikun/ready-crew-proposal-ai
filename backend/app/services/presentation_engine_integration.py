from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, TYPE_CHECKING

from app.config import settings
from app.models import PptxDownloadRequest
from app.services.pptx_service import build_pptx_context, build_pptx_result

if TYPE_CHECKING:
    from app.strategy_engine.models import HumanReviewReport, PresentationContext


logger = logging.getLogger(__name__)

ENGINE_MODE_LEGACY = "legacy"
ENGINE_MODE_STRATEGY_V1 = "strategy_v1"
ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1 = "presentation_director_v10_1"
SUPPORTED_ENGINE_MODES = {ENGINE_MODE_LEGACY, ENGINE_MODE_STRATEGY_V1}
PRESENTATION_DIRECTOR_V10_1_FLAG = "PRESENTATION_DESIGN_AI_V10_ENABLED"


@dataclass(frozen=True)
class PresentationEngineResult:
    pptx_bytes: bytes
    engine_mode: str
    presentation_context: Any | None = None
    quality_report: dict[str, Any] | None = None


def resolve_engine_mode(value: str | None = None) -> str:
    mode = (value or settings.presentation_engine_mode or ENGINE_MODE_LEGACY).strip().lower()
    if mode in SUPPORTED_ENGINE_MODES:
        return mode
    logger.warning("presentation_engine_mode_invalid", extra={"engine_mode": mode})
    return ENGINE_MODE_LEGACY


def build_pptx_bytes_for_engine(
    payload: PptxDownloadRequest,
    *,
    engine_mode: str | None = None,
) -> PresentationEngineResult:
    if settings.presentation_design_ai_v10_enabled:
        return _build_v10_1_with_fallback(payload)

    mode = resolve_engine_mode(engine_mode)
    if mode == ENGINE_MODE_LEGACY:
        _log_engine_selection(mode)
        result = build_pptx_result(payload)
        return PresentationEngineResult(
            pptx_bytes=result.pptx_bytes,
            engine_mode=mode,
            quality_report=result.quality_report.to_dict(),
        )

    presentation_context = _presentation_context_from_review_report(payload.strategy_review_report)
    _log_engine_selection(mode, presentation_context)
    result = build_pptx_result(payload, presentation_context=presentation_context)
    return PresentationEngineResult(
        pptx_bytes=result.pptx_bytes,
        engine_mode=mode,
        presentation_context=presentation_context,
        quality_report=result.quality_report.to_dict(),
    )


def _build_v10_1_with_fallback(payload: PptxDownloadRequest) -> PresentationEngineResult:
    requested_version = ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1
    try:
        if payload.summary:
            raise ValueError("presentation_director_v10_1 does not handle summary decks.")
        return _build_v10_1_pptx_result(payload)
    except Exception as exc:
        reason = exc.__class__.__name__
        logger.warning(
            "presentation_director_v10_1_fallback",
            extra={
                "requested_version": requested_version,
                "actual_version": ENGINE_MODE_LEGACY,
                "fallback_used": True,
                "fallback_reason": reason,
            },
        )
        result = build_pptx_result(payload)
        quality_report = result.quality_report.to_dict()
        quality_report.update(
            {
                "requested_version": requested_version,
                "actual_version": ENGINE_MODE_LEGACY,
                "fallback_used": True,
                "fallback_reason": reason,
            }
        )
        return PresentationEngineResult(
            pptx_bytes=result.pptx_bytes,
            engine_mode=ENGINE_MODE_LEGACY,
            quality_report=quality_report,
        )


def _build_v10_1_pptx_result(payload: PptxDownloadRequest) -> PresentationEngineResult:
    from app.presentation_composer import render_director_plan_to_pptx
    from app.presentation_design_ai import design_presentation_deck
    from app.presentation_director import build_directed_presentation_plan, direct_case, validate_director_plan

    case = _case_context_from_payload(payload)
    design_deck = design_presentation_deck(case, force_enabled=True)
    director_plan = direct_case(case, presentation_time_minutes=_presentation_time_minutes(payload))
    validation_errors = validate_director_plan(director_plan)
    if validation_errors:
        raise ValueError(f"presentation_director_v10_1 validation failed: {validation_errors[0]}")
    presentation_plan = build_directed_presentation_plan(case, director_plan)
    pptx_bytes, render_report = render_director_plan_to_pptx(presentation_plan, director_plan)
    quality_report = {
        "requested_version": ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1,
        "actual_version": ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1,
        "fallback_used": False,
        "fallback_reason": "",
        "feature_flag": PRESENTATION_DIRECTOR_V10_1_FLAG,
        "director_recommended_page_count": director_plan.recommended_page_count,
        "director_slide_count": len(director_plan.slide_sequence),
        "design_contract_count": len(design_deck.slide_contracts),
        "render_report": render_report,
    }
    logger.info(
        "presentation_director_v10_1_selected",
        extra={
            "requested_version": ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1,
            "actual_version": ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1,
            "fallback_used": False,
            "fallback_reason": "",
        },
    )
    return PresentationEngineResult(
        pptx_bytes=pptx_bytes,
        engine_mode=ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1,
        quality_report=quality_report,
    )


def _case_context_from_payload(payload: PptxDownloadRequest):
    from app.presentation_composer import CaseContext

    data = payload.powerpoint_generation_data
    context = build_pptx_context(payload)
    slides_text = " ".join(
        " ".join([slide.title, " ".join(slide.bullets), slide.visual_suggestion])
        for slide in data.slides
    )
    project_summary = _first_non_empty(payload.project_brief, payload.hearing_result, slides_text, data.deck_title)
    pain_points = _items_from_text(
        _first_non_empty(payload.hearing_result, payload.project_brief, slides_text),
        fallback=("現状課題を整理", "判断材料を明確化", "次アクションを合意"),
        limit=3,
    )
    expected_outcomes = _items_from_text(
        _first_non_empty(payload.own_service_info, payload.case_studies, slides_text),
        fallback=("合意形成を短縮", "提案品質を安定化", "運用負荷を抑制"),
        limit=3,
    )
    if payload.win_probability:
        expected_outcomes = tuple(
            dict.fromkeys(
                list(expected_outcomes)
                + payload.win_probability.positive_factors[:1]
                + payload.win_probability.recommended_next_actions[:1]
            )
        )[:3]
    return CaseContext(
        case_id="production_v10_1",
        case_name=_safe_text(data.deck_title or "提案書"),
        client_name=_safe_text(data.client_name or context.client_name or "顧客企業"),
        industry=_safe_text(_industry_hint(payload) or context.proposal_label or "提案対象"),
        category=_safe_text(context.proposal_category or data.deck_title or "Proposal"),
        project_summary=_safe_text(project_summary),
        pain_points=tuple(_safe_text(item) for item in pain_points),
        expected_outcomes=tuple(_safe_text(item) for item in expected_outcomes),
        budget=_safe_text(payload.budget_range),
        timeline=_safe_text(payload.desired_launch_timing or payload.estimated_page_count),
        decision_maker=_safe_text(_decision_maker_hint(payload)),
        competitor=_safe_text(payload.competitor_company_name or payload.competitor_site_url),
    )


def _presentation_time_minutes(payload: PptxDownloadRequest) -> int:
    text = " ".join([payload.estimated_page_count, payload.hearing_result, payload.project_brief])
    for pattern in (r"(\d+)\s*分", r"(\d+)\s*min", r"(\d+)\s*minutes"):
        match = __import__("re").search(pattern, text, flags=__import__("re").IGNORECASE)
        if match:
            return max(5, min(60, int(match.group(1))))
    return 30


def _decision_maker_hint(payload: PptxDownloadRequest) -> str:
    text = " ".join([payload.client_company_info, payload.hearing_result, payload.project_brief])
    for word in ("経営者", "社長", "役員", "部門責任者", "部長", "情報システム", "IT責任者", "現場責任者"):
        if word in text:
            return word
    return "経営者 / 部門責任者"


def _industry_hint(payload: PptxDownloadRequest) -> str:
    import re

    text = "\n".join([payload.client_company_info, payload.project_brief, payload.hearing_result])
    for pattern in (r"業界[:：]\s*([^\n\r]+)", r"業種[:：]\s*([^\n\r]+)"):
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def _items_from_text(text: str, *, fallback: tuple[str, ...], limit: int) -> tuple[str, ...]:
    import re

    candidates = [
        item.strip(" ・-:：\t\r\n")
        for item in re.split(r"[\n。;；、]", text)
        if item.strip(" ・-:：\t\r\n")
    ]
    cleaned = [_safe_text(item, 42) for item in candidates if len(item.strip()) >= 3]
    return tuple(dict.fromkeys(cleaned[:limit] or list(fallback)[:limit]))


def _first_non_empty(*values: str) -> str:
    return next((value for value in values if value and value.strip()), "")


def _safe_text(value: str, limit: int = 80) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit] if len(text) > limit else text


def _presentation_context_from_review_report(value: dict | None):
    report = _parse_review_report(value)
    if report is None:
        raise ValueError("strategy_v1 requires an approved strategy_review_report.")
    from app.strategy_engine import adapter as strategy_adapter

    return strategy_adapter.adapt_review_report_to_presentation_context(report)


def _parse_review_report(value: Any) -> Any | None:
    if value is None:
        return None
    from app.strategy_engine.models import HumanReviewReport

    if isinstance(value, HumanReviewReport):
        return value
    return HumanReviewReport(**value)


def _log_engine_selection(mode: str, presentation_context: Any | None = None) -> None:
    extra: dict[str, str | None] = {
        "engine_mode": mode,
        "strategy_version": None,
        "presentation_context_version": None,
        "presentation_pack": None,
        "story": None,
        "persona": None,
    }
    if presentation_context is not None:
        extra.update(
            {
                "strategy_version": presentation_context.source_strategy_schema_version,
                "presentation_context_version": presentation_context.schema_version,
                "presentation_pack": str(presentation_context.presentation_pack),
                "story": presentation_context.story_type,
                "persona": presentation_context.persona,
            }
        )
    logger.info("presentation_engine_selected", extra=extra)
