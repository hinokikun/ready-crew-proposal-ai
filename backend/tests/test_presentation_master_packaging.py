from __future__ import annotations

from app.models import PptxDownloadRequest
from app.services import presentation_engine_integration as integration
from app.services.presentation_master import (
    MASTER_SOURCE_OF_TRUTH,
    PHASE4C_GRAMMAR_CONTRACT,
    golden_regression_cases,
    route_payload_for_master,
)


def _payload(sample_pptx_payload: dict, **updates) -> PptxDownloadRequest:
    data = dict(sample_pptx_payload)
    data.update(updates)
    return PptxDownloadRequest(**data)


def _set_flags(*, master: bool, v10: bool) -> tuple[bool, bool, bool]:
    original_master = integration.settings.presentation_design_ai_master_enabled
    original_v10 = integration.settings.presentation_design_ai_v10_enabled
    original_shadow = integration.settings.presentation_design_ai_master_shadow_enabled
    object.__setattr__(integration.settings, "presentation_design_ai_master_enabled", master)
    object.__setattr__(integration.settings, "presentation_design_ai_v10_enabled", v10)
    object.__setattr__(integration.settings, "presentation_design_ai_master_shadow_enabled", False)
    return original_master, original_v10, original_shadow


def _restore_flags(values: tuple[bool, bool, bool]) -> None:
    original_master, original_v10, original_shadow = values
    object.__setattr__(integration.settings, "presentation_design_ai_master_enabled", original_master)
    object.__setattr__(integration.settings, "presentation_design_ai_v10_enabled", original_v10)
    object.__setattr__(integration.settings, "presentation_design_ai_master_shadow_enabled", original_shadow)


def test_phase4c_grammar_contract_is_production_native() -> None:
    assert PHASE4C_GRAMMAR_CONTRACT["source_of_truth"] == MASTER_SOURCE_OF_TRUTH
    assert PHASE4C_GRAMMAR_CONTRACT["runtime_artifact_dependency"] is False
    assert "Anti-template divergence" in PHASE4C_GRAMMAR_CONTRACT["quality_axes"]
    assert "fake-data critical violation".replace("-", "_") not in str(PHASE4C_GRAMMAR_CONTRACT)
    assert len(golden_regression_cases()) == 6


def test_master_shadow_feature_flag_default_is_off() -> None:
    assert integration.settings.presentation_design_ai_master_shadow_enabled is False


def test_master_summary_deck_routes_to_legacy(sample_pptx_payload: dict) -> None:
    flags = _set_flags(master=True, v10=False)
    try:
        result = integration.build_pptx_bytes_for_engine(
            _payload(sample_pptx_payload, summary=True),
            request_id="req-summary",
            project_id="project-summary",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.quality_report
    assert result.quality_report["fallback_used"] is True
    assert result.quality_report["fallback_reason"] == "summary_deck_uses_legacy"
    assert result.quality_report["failure_stage"] == "routing"


def test_master_unknown_category_routes_to_legacy(sample_pptx_payload: dict) -> None:
    payload = dict(sample_pptx_payload)
    payload["project_brief"] = "分類しにくい特殊業務の相談。"
    payload["client_company_info"] = "未知カテゴリ株式会社 / Unusual / Unknown"
    flags = _set_flags(master=True, v10=False)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**payload),
            request_id="req-unknown",
            project_id="project-unknown",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.quality_report
    assert result.quality_report["fallback_used"] is True
    assert result.quality_report["fallback_reason"] == "unsupported_category_uses_legacy"
    assert result.quality_report["failure_stage"] == "routing"


def test_master_quality_report_contains_packaging_metadata(sample_pptx_payload: dict) -> None:
    flags = _set_flags(master=True, v10=False)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**sample_pptx_payload),
            request_id="req-native",
            project_id="project-native",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_PRESENTATION_DESIGN_MASTER_V1
    assert result.quality_report
    assert result.quality_report["production_native_module"] == "app.services.presentation_master"
    assert result.quality_report["candidate_source_of_truth"] == MASTER_SOURCE_OF_TRUTH
    assert result.quality_report["visual_logic_duplication"] == 0
    assert result.quality_report["artifact_runtime_dependency"] is False
    assert result.quality_report["master_route"]["route"] == "master_normal_pptx"
    assert result.quality_report["master_qa"]["status"] == "PASS"


def test_master_route_can_be_checked_without_rendering(sample_pptx_payload: dict) -> None:
    normal = route_payload_for_master(PptxDownloadRequest(**sample_pptx_payload))
    summary = route_payload_for_master(_payload(sample_pptx_payload, summary=True))
    assert normal.supported is True
    assert normal.route == "master_normal_pptx"
    assert summary.supported is False
    assert summary.reason_code == "summary_deck_uses_legacy"
