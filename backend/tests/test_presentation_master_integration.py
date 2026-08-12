from __future__ import annotations

from io import BytesIO

from pptx import Presentation

from app.config import settings
from app.models import PptxDownloadRequest
from app.services import presentation_engine_integration as integration


def _set_flags(*, master: bool, v10: bool) -> tuple[bool, bool]:
    original_master = settings.presentation_design_ai_master_enabled
    original_v10 = settings.presentation_design_ai_v10_enabled
    object.__setattr__(settings, "presentation_design_ai_master_enabled", master)
    object.__setattr__(settings, "presentation_design_ai_v10_enabled", v10)
    return original_master, original_v10


def _restore_flags(values: tuple[bool, bool]) -> None:
    original_master, original_v10 = values
    object.__setattr__(settings, "presentation_design_ai_master_enabled", original_master)
    object.__setattr__(settings, "presentation_design_ai_v10_enabled", original_v10)


def test_master_feature_flag_default_is_off() -> None:
    assert settings.presentation_design_ai_master_enabled is False


def test_master_feature_flag_off_uses_existing_flow(sample_pptx_payload: dict) -> None:
    flags = _set_flags(master=False, v10=False)
    try:
        result = integration.build_pptx_bytes_for_engine(PptxDownloadRequest(**sample_pptx_payload))
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert "shadow_result" not in result.quality_report


def test_master_feature_flag_on_uses_master_version(sample_pptx_payload: dict) -> None:
    flags = _set_flags(master=True, v10=False)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**sample_pptx_payload),
            request_id="req-master",
            project_id="project-master",
        )
    finally:
        _restore_flags(flags)

    prs = Presentation(BytesIO(result.pptx_bytes))
    assert result.engine_mode == integration.ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    assert len(prs.slides) >= 8
    assert result.quality_report
    assert result.quality_report["requested_version"] == integration.ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    assert result.quality_report["actual_version"] == integration.ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    assert result.quality_report["fallback_used"] is False
    assert result.quality_report["feature_flag"] == integration.PRESENTATION_DESIGN_MASTER_FLAG
    assert result.quality_report["request_id"] == "req-master"
    assert result.quality_report["project_id"] == "project-master"


def test_master_shadow_mode_keeps_existing_response(sample_pptx_payload: dict) -> None:
    flags = _set_flags(master=False, v10=False)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**sample_pptx_payload),
            shadow_master=True,
            request_id="req-shadow",
            project_id="project-shadow",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    shadow = result.quality_report["shadow_result"]
    assert shadow["request_id"] == "req-shadow"
    assert shadow["project_id"] == "project-shadow"
    assert shadow["requested_version"] == integration.ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    assert shadow["actual_version"] == integration.ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    assert shadow["shadow_enabled"] is True
    assert shadow["shadow_success"] is True
    assert shadow["fallback_used"] is False
    assert shadow["page_count"] >= 8


def test_master_failure_falls_back_to_existing_flow(monkeypatch, sample_pptx_payload: dict) -> None:
    def _raise(_payload, *, request_id=None, project_id=None):
        raise ValueError("master failed")

    flags = _set_flags(master=True, v10=False)
    monkeypatch.setattr(integration, "_build_master_pptx_result", _raise)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**sample_pptx_payload),
            request_id="req-fallback",
            project_id="project-fallback",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert result.quality_report["requested_version"] == integration.ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    assert result.quality_report["actual_version"] == integration.ENGINE_MODE_LEGACY
    assert result.quality_report["fallback_used"] is True
    assert result.quality_report["fallback_reason"] == "ValueError"


def test_master_shadow_failure_does_not_break_existing_response(monkeypatch, sample_pptx_payload: dict) -> None:
    def _raise(_payload, *, request_id=None, project_id=None):
        raise ValueError("shadow failed")

    flags = _set_flags(master=False, v10=False)
    monkeypatch.setattr(integration, "_build_master_pptx_result", _raise)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**sample_pptx_payload),
            shadow_master=True,
            request_id="req-shadow-fail",
            project_id="project-shadow-fail",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    shadow = result.quality_report["shadow_result"]
    assert shadow["shadow_success"] is False
    assert shadow["failure_stage"] == "shadow_master_generation"
    assert shadow["failure_reason"] == "ValueError"


def test_master_shadow_report_contract(sample_pptx_payload: dict) -> None:
    flags = _set_flags(master=False, v10=False)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**sample_pptx_payload),
            shadow_master=True,
            request_id="req-contract",
            project_id="project-contract",
        )
    finally:
        _restore_flags(flags)

    assert result.quality_report
    shadow = result.quality_report["shadow_result"]
    required = {
        "request_id",
        "project_id",
        "customer",
        "category",
        "audience",
        "sales_stage",
        "deck_objective",
        "requested_version",
        "actual_version",
        "shadow_enabled",
        "shadow_success",
        "fallback_used",
        "fallback_reason",
        "page_count",
        "story_strategy",
        "selected_visual_forms",
        "composition_fingerprints",
        "template_repetition_score",
        "editable_tier1_coverage",
        "editable_tier2_coverage",
        "visual_qa_result",
        "generation_time_ms",
        "failure_stage",
        "failure_reason",
    }
    assert required.issubset(shadow)
