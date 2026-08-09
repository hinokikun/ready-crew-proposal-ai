from __future__ import annotations

from io import BytesIO

from pptx import Presentation

from app.config import settings
from app.models import PptxDownloadRequest
from app.services import presentation_engine_integration as integration


def test_v10_1_feature_flag_off_uses_existing_flow(sample_pptx_payload: dict) -> None:
    original = settings.presentation_design_ai_v10_enabled
    try:
        object.__setattr__(settings, "presentation_design_ai_v10_enabled", False)
        result = integration.build_pptx_bytes_for_engine(PptxDownloadRequest(**sample_pptx_payload))
    finally:
        object.__setattr__(settings, "presentation_design_ai_v10_enabled", original)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"


def test_v10_1_feature_flag_on_uses_director_renderer(sample_pptx_payload: dict) -> None:
    original = settings.presentation_design_ai_v10_enabled
    try:
        object.__setattr__(settings, "presentation_design_ai_v10_enabled", True)
        result = integration.build_pptx_bytes_for_engine(PptxDownloadRequest(**sample_pptx_payload))
    finally:
        object.__setattr__(settings, "presentation_design_ai_v10_enabled", original)

    prs = Presentation(BytesIO(result.pptx_bytes))
    assert result.engine_mode == integration.ENGINE_MODE_PRESENTATION_DIRECTOR_V10_1
    assert len(prs.slides) >= 8
    assert result.quality_report
    assert result.quality_report["fallback_used"] is False


def test_v10_1_falls_back_to_existing_flow(monkeypatch, sample_pptx_payload: dict) -> None:
    def _raise(_payload):
        raise ValueError("director failed")

    original = settings.presentation_design_ai_v10_enabled
    monkeypatch.setattr(integration, "_build_v10_1_pptx_result", _raise)
    try:
        object.__setattr__(settings, "presentation_design_ai_v10_enabled", True)
        result = integration.build_pptx_bytes_for_engine(PptxDownloadRequest(**sample_pptx_payload))
    finally:
        object.__setattr__(settings, "presentation_design_ai_v10_enabled", original)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert result.quality_report["fallback_used"] is True
    assert result.quality_report["fallback_reason"] == "ValueError"
