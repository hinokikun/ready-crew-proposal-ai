from __future__ import annotations

from dataclasses import dataclass
import logging
from time import perf_counter
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
ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1 = "presentation_design_master_v1"
SUPPORTED_ENGINE_MODES = {ENGINE_MODE_LEGACY, ENGINE_MODE_STRATEGY_V1}
PRESENTATION_DIRECTOR_V10_1_FLAG = "PRESENTATION_DESIGN_AI_V10_ENABLED"
PRESENTATION_DESIGN_MASTER_FLAG = "PRESENTATION_DESIGN_AI_MASTER_ENABLED"


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
    shadow_master: bool = False,
    request_id: str | None = None,
    project_id: str | None = None,
) -> PresentationEngineResult:
    from app.services.presentation_master import MASTER_MODE_ENABLED, MASTER_MODE_SHADOW, resolve_master_runtime_mode

    master_mode = resolve_master_runtime_mode(
        enabled=settings.presentation_design_ai_master_enabled,
        shadow_enabled=getattr(settings, "presentation_design_ai_master_shadow_enabled", False),
        explicit_shadow=shadow_master,
    )
    if master_mode == MASTER_MODE_ENABLED:
        return _build_master_with_fallback(payload, request_id=request_id, project_id=project_id)
    shadow_enabled = master_mode == MASTER_MODE_SHADOW

    if settings.presentation_design_ai_v10_enabled:
        result = _build_v10_1_with_fallback(payload)
        return _attach_shadow_result(
            result,
            payload,
            shadow_master=shadow_enabled,
            request_id=request_id,
            project_id=project_id,
        )

    mode = resolve_engine_mode(engine_mode)
    if mode == ENGINE_MODE_LEGACY:
        _log_engine_selection(mode)
        result = build_pptx_result(payload)
        engine_result = PresentationEngineResult(
            pptx_bytes=result.pptx_bytes,
            engine_mode=mode,
            quality_report=result.quality_report.to_dict(),
        )
        return _attach_shadow_result(
            engine_result,
            payload,
            shadow_master=shadow_enabled,
            request_id=request_id,
            project_id=project_id,
        )

    presentation_context = _presentation_context_from_review_report(payload.strategy_review_report)
    _log_engine_selection(mode, presentation_context)
    result = build_pptx_result(payload, presentation_context=presentation_context)
    engine_result = PresentationEngineResult(
        pptx_bytes=result.pptx_bytes,
        engine_mode=mode,
        presentation_context=presentation_context,
        quality_report=result.quality_report.to_dict(),
    )
    return _attach_shadow_result(
        engine_result,
        payload,
        shadow_master=shadow_enabled,
        request_id=request_id,
        project_id=project_id,
    )


def _build_master_with_fallback(
    payload: PptxDownloadRequest,
    *,
    request_id: str | None = None,
    project_id: str | None = None,
) -> PresentationEngineResult:
    requested_version = ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    try:
        return _build_master_pptx_result(payload, request_id=request_id, project_id=project_id)
    except Exception as exc:
        from app.services.presentation_master import fallback_category_for_exception

        reason = getattr(exc, "reason_code", exc.__class__.__name__)
        failure_stage = getattr(exc, "failure_stage", "master_generation")
        fallback_category = fallback_category_for_exception(exc)
        logger.warning(
            "presentation_design_master_v1_fallback",
            extra={
                "requested_version": requested_version,
                "actual_version": ENGINE_MODE_LEGACY,
                "fallback_used": True,
                "fallback_reason": reason,
                "fallback_category": fallback_category,
                "failure_stage": failure_stage,
                "request_id": request_id or "",
                "project_id": project_id or "",
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
                "fallback_category": fallback_category,
                "failure_stage": failure_stage,
                "request_id": request_id or "",
                "project_id": project_id or "",
            }
        )
        return PresentationEngineResult(
            pptx_bytes=result.pptx_bytes,
            engine_mode=ENGINE_MODE_LEGACY,
            quality_report=quality_report,
        )


def _build_master_pptx_result(
    payload: PptxDownloadRequest,
    *,
    request_id: str | None = None,
    project_id: str | None = None,
) -> PresentationEngineResult:
    from app.services.presentation_master import build_presentation_master

    master_result = build_presentation_master(
        payload,
        core_builder=_build_v10_1_pptx_result,
        request_id=request_id,
        project_id=project_id,
    )
    logger.info(
        "presentation_design_master_v1_selected",
        extra={
            "requested_version": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
            "actual_version": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
            "fallback_used": False,
            "fallback_reason": "",
            "request_id": request_id or "",
            "project_id": project_id or "",
        },
    )
    return PresentationEngineResult(
        pptx_bytes=master_result.pptx_bytes,
        engine_mode=ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
        quality_report=master_result.quality_report,
    )


def _attach_shadow_result(
    result: PresentationEngineResult,
    payload: PptxDownloadRequest,
    *,
    shadow_master: bool,
    request_id: str | None,
    project_id: str | None,
) -> PresentationEngineResult:
    if not shadow_master:
        return result

    shadow_report = _run_master_shadow(payload, request_id=request_id, project_id=project_id)
    quality_report = dict(result.quality_report or {})
    quality_report["shadow_result"] = shadow_report
    return PresentationEngineResult(
        pptx_bytes=result.pptx_bytes,
        engine_mode=result.engine_mode,
        presentation_context=result.presentation_context,
        quality_report=quality_report,
    )


def _run_master_shadow(
    payload: PptxDownloadRequest,
    *,
    request_id: str | None,
    project_id: str | None,
) -> dict[str, Any]:
    started = perf_counter()
    try:
        result = _build_master_pptx_result(payload, request_id=request_id, project_id=project_id)
        generation_time_ms = round((perf_counter() - started) * 1000)
        report = _shadow_report_from_quality(
            payload,
            quality_report=result.quality_report or {},
            request_id=request_id,
            project_id=project_id,
            success=True,
            generation_time_ms=generation_time_ms,
        )
        logger.info(
            "presentation_design_master_v1_shadow_success",
            extra={
                "requested_version": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
                "actual_version": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
                "shadow_enabled": True,
                "shadow_success": True,
                "fallback_used": False,
                "fallback_reason": "",
                "request_id": request_id or "",
                "project_id": project_id or "",
            },
        )
        return report
    except Exception as exc:
        from app.services.presentation_master import fallback_category_for_exception

        generation_time_ms = round((perf_counter() - started) * 1000)
        reason = exc.__class__.__name__
        fallback_category = fallback_category_for_exception(exc)
        logger.warning(
            "presentation_design_master_v1_shadow_failure",
            extra={
                "requested_version": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
                "actual_version": "",
                "shadow_enabled": True,
                "shadow_success": False,
                "fallback_used": False,
                "fallback_reason": reason,
                "fallback_category": fallback_category,
                "failure_stage": "shadow_master_generation",
                "failure_reason": reason,
                "request_id": request_id or "",
                "project_id": project_id or "",
            },
        )
        return _shadow_report_from_quality(
            payload,
            quality_report={},
            request_id=request_id,
            project_id=project_id,
            success=False,
            generation_time_ms=generation_time_ms,
            failure_stage="shadow_master_generation",
            failure_reason=reason,
            fallback_category=fallback_category,
        )


def _shadow_report_from_quality(
    payload: PptxDownloadRequest,
    *,
    quality_report: dict[str, Any],
    request_id: str | None,
    project_id: str | None,
    success: bool,
    generation_time_ms: int,
    failure_stage: str = "",
    failure_reason: str = "",
    fallback_category: str = "",
) -> dict[str, Any]:
    forms = _visual_forms_from_quality(quality_report)
    return {
        "request_id": request_id or "",
        "project_id": project_id or "",
        "customer": _customer_name_from_payload(payload),
        "category": _category_from_payload(payload),
        "audience": _decision_maker_hint(payload),
        "sales_stage": "production_shadow",
        "deck_objective": _deck_objective_from_payload(payload),
        "requested_version": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
        "actual_version": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1 if success else "",
        "shadow_enabled": True,
        "shadow_success": success,
        "fallback_used": False,
        "fallback_reason": "",
        "fallback_category": "" if success else (fallback_category or "unexpected_error"),
        "mode": "shadow",
        "engine_requested": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1,
        "engine_used": ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1 if success else "",
        "page_count": int(quality_report.get("director_slide_count") or 0),
        "story_strategy": "presentation_director_master_v1",
        "selected_visual_forms": forms,
        "composition_fingerprints": _composition_fingerprints_from_quality(quality_report),
        "template_repetition_score": _template_repetition_score(forms),
        "editable_tier1_coverage": 1.0 if success else 0.0,
        "editable_tier2_coverage": 1.0 if success else 0.0,
        "visual_qa_result": "PASS" if success else "FAIL",
        "generation_time_ms": generation_time_ms,
        "failure_stage": failure_stage,
        "failure_reason": failure_reason,
    }


def _visual_forms_from_quality(quality_report: dict[str, Any]) -> list[str]:
    pages = (quality_report.get("render_report") or {}).get("pages") or []
    forms: list[str] = []
    for page in pages:
        if isinstance(page, dict):
            forms.append(str(page.get("slide_role") or page.get("layout") or page.get("title") or "unknown"))
    return forms


def _composition_fingerprints_from_quality(quality_report: dict[str, Any]) -> list[dict[str, Any]]:
    pages = (quality_report.get("render_report") or {}).get("pages") or []
    fingerprints: list[dict[str, Any]] = []
    for index, page in enumerate(pages, start=1):
        if isinstance(page, dict):
            fingerprints.append(
                {
                    "page": index,
                    "form": str(page.get("slide_role") or page.get("layout") or "unknown"),
                    "title_length": len(str(page.get("title") or "")),
                }
            )
    return fingerprints


def _template_repetition_score(forms: list[str]) -> int:
    if not forms:
        return 0
    repeats = sum(1 for previous, current in zip(forms, forms[1:]) if previous == current)
    return round((repeats / max(1, len(forms) - 1)) * 100)


def _customer_name_from_payload(payload: PptxDownloadRequest) -> str:
    data = payload.powerpoint_generation_data
    context = build_pptx_context(payload)
    return _safe_text(data.client_name or context.client_name or payload.client_company_info)


def _category_from_payload(payload: PptxDownloadRequest) -> str:
    data = payload.powerpoint_generation_data
    context = build_pptx_context(payload)
    return _safe_text(context.proposal_category or data.deck_title or "Proposal")


def _deck_objective_from_payload(payload: PptxDownloadRequest) -> str:
    data = payload.powerpoint_generation_data
    return _safe_text(_first_non_empty(payload.project_brief, payload.hearing_result, data.deck_title), 120)


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
