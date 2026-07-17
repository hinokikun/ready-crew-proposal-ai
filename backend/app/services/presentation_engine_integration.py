from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, TYPE_CHECKING

from app.config import settings
from app.models import PptxDownloadRequest
from app.services.pptx_service import build_pptx_bytes

if TYPE_CHECKING:
    from app.strategy_engine.models import HumanReviewReport, PresentationContext


logger = logging.getLogger(__name__)

ENGINE_MODE_LEGACY = "legacy"
ENGINE_MODE_STRATEGY_V1 = "strategy_v1"
SUPPORTED_ENGINE_MODES = {ENGINE_MODE_LEGACY, ENGINE_MODE_STRATEGY_V1}


@dataclass(frozen=True)
class PresentationEngineResult:
    pptx_bytes: bytes
    engine_mode: str
    presentation_context: Any | None = None


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
    mode = resolve_engine_mode(engine_mode)
    if mode == ENGINE_MODE_LEGACY:
        _log_engine_selection(mode)
        return PresentationEngineResult(pptx_bytes=build_pptx_bytes(payload), engine_mode=mode)

    presentation_context = _presentation_context_from_review_report(payload.strategy_review_report)
    _log_engine_selection(mode, presentation_context)
    pptx_bytes = build_pptx_bytes(payload, presentation_context=presentation_context)
    return PresentationEngineResult(
        pptx_bytes=pptx_bytes,
        engine_mode=mode,
        presentation_context=presentation_context,
    )


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
