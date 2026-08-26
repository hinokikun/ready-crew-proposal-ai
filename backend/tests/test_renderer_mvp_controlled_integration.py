from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
import threading
import time
from typing import Any

from pptx import Presentation
import pytest

from app.models import PptxDownloadRequest
from app.services import presentation_engine_integration as integration
from app.services.presentation_master.renderer_mvp import (
    RendererMvpIntegrationError,
    extract_pptx_text,
    inspect_pptx_bytes,
    _wrap,
)


class _LogSpy:
    def __init__(self) -> None:
        self.records: list[SimpleNamespace] = []
        self._lock = threading.Lock()

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._append(message, kwargs.get("extra") or {})

    def warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._append(message, kwargs.get("extra") or {})

    def exception(self, message: str, *args: Any, **kwargs: Any) -> None:
        self._append(message, kwargs.get("extra") or {})

    def _append(self, message: str, extra: dict[str, Any]) -> None:
        with self._lock:
            self.records.append(SimpleNamespace(message=message, **extra))


def _set_flags(
    *,
    renderer_mvp: bool,
    master: bool = False,
    v10: bool = False,
    shadow: bool = False,
    canary: bool = False,
    auto_fallback: bool = True,
) -> tuple[bool, bool, bool, bool, bool, bool]:
    runtime_settings = integration.settings
    original_renderer_mvp = runtime_settings.presentation_master_v3_renderer_mvp_enabled
    original_master = runtime_settings.presentation_design_ai_master_enabled
    original_v10 = runtime_settings.presentation_design_ai_v10_enabled
    original_shadow = runtime_settings.presentation_master_v3_renderer_mvp_shadow_enabled
    original_canary = runtime_settings.presentation_master_v3_renderer_mvp_canary_enabled
    original_auto_fallback = runtime_settings.presentation_master_v3_renderer_mvp_auto_fallback_enabled
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_enabled", renderer_mvp)
    object.__setattr__(runtime_settings, "presentation_design_ai_master_enabled", master)
    object.__setattr__(runtime_settings, "presentation_design_ai_v10_enabled", v10)
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_shadow_enabled", shadow)
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_canary_enabled", canary)
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_auto_fallback_enabled", auto_fallback)
    return (
        original_renderer_mvp,
        original_master,
        original_v10,
        original_shadow,
        original_canary,
        original_auto_fallback,
    )


def _restore_flags(values: tuple[bool, bool, bool, bool, bool, bool]) -> None:
    original_renderer_mvp, original_master, original_v10, original_shadow, original_canary, original_auto_fallback = values
    runtime_settings = integration.settings
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_enabled", original_renderer_mvp)
    object.__setattr__(runtime_settings, "presentation_design_ai_master_enabled", original_master)
    object.__setattr__(runtime_settings, "presentation_design_ai_v10_enabled", original_v10)
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_shadow_enabled", original_shadow)
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_canary_enabled", original_canary)
    object.__setattr__(runtime_settings, "presentation_master_v3_renderer_mvp_auto_fallback_enabled", original_auto_fallback)


def _payload(
    *,
    client_name: str,
    deck_title: str,
    project_brief: str,
    hearing_result: str,
    own_service_info: str = "",
    special_function_required: str = "",
) -> PptxDownloadRequest:
    return PptxDownloadRequest(
        project_brief=project_brief,
        client_company_info=f"{client_name}\n対象: 部門責任者 / 経営",
        hearing_result=hearing_result,
        own_service_info=own_service_info,
        special_function_required=special_function_required,
        desired_launch_timing="次回打ち合わせでPoC条件を確認",
        budget_range="未確定",
        powerpoint_generation_data={
            "deck_title": deck_title,
            "client_name": client_name,
            "slides": [
                {
                    "slide_no": 1,
                    "layout": "proposal",
                    "title": deck_title,
                    "bullets": [project_brief, hearing_result],
                    "speaker_notes": "営業説明用メモ",
                    "visual_suggestion": "編集可能な提案書",
                }
            ],
        },
    )


def _fixture_cases() -> dict[str, PptxDownloadRequest]:
    return {
        "faj": _payload(
            client_name="株式会社フラワーオークションジャパン",
            deck_title="画像認識AI導入PoC提案",
            project_brief="花卉の商品画像から品質候補を出し、人の最終判断と理由を記録して次回判断へ使う。",
            hearing_result="対象画像、撮影条件、AI候補、人判断、一致と差異、例外条件をPoCで確認したい。",
            own_service_info="画像認識AIと判定記録の運用設計を支援。",
        ),
        "logistics": _payload(
            client_name="関西ロジスティクス株式会社",
            deck_title="配送ルート最適化PoC提案",
            project_brief="配車計画で時間指定、積載、人員、配送先条件が衝突し、候補ルートの理由を残したい。",
            hearing_result="AI候補、人の補正、例外条件、TMSへ戻せる粒度をPoCで確認する。",
            own_service_info="配送計画AIと運用説明可能性の設計を支援。",
            special_function_required="TMS連携前提の確認",
        ),
        "commerce": _payload(
            client_name="北都コマース株式会社",
            deck_title="顧客導線改善提案",
            project_brief="ECサイトで流入、比較、問い合わせの間に判断材料が不足し、顧客が迷う場所を特定したい。",
            hearing_result="訴求、証拠、相談理由を導線上に戻し、次の投資判断条件を整理する。",
            own_service_info="Web改善、SEO、顧客導線設計を支援。",
        ),
    }


def test_renderer_mvp_feature_flag_default_is_off() -> None:
    runtime_settings = integration.settings
    assert runtime_settings.presentation_master_v3_renderer_mvp_enabled is False
    assert runtime_settings.presentation_master_v3_renderer_mvp_shadow_enabled is False
    assert runtime_settings.presentation_master_v3_renderer_mvp_canary_enabled is False
    assert runtime_settings.presentation_master_v3_renderer_mvp_auto_fallback_enabled is True
    assert runtime_settings.presentation_master_v3_renderer_mvp_shadow_max_workers >= 1
    assert runtime_settings.presentation_master_v3_renderer_mvp_shadow_max_pending >= 1


def test_renderer_mvp_japanese_title_wrap_keeps_semantic_units() -> None:
    wrapped = _wrap("PoCは精度証明ではなく、次回判断の証拠を残す", 6.4, 35, 3)

    assert "証\n拠" not in wrapped
    assert "判\n断" not in wrapped
    assert "証拠" in wrapped
    assert len(wrapped.splitlines()) <= 3


def test_renderer_mvp_flag_off_preserves_current_production_flow(sample_pptx_payload: dict[str, Any]) -> None:
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=False, canary=False)
    try:
        result = integration.build_pptx_bytes_for_engine(PptxDownloadRequest(**sample_pptx_payload))
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert result.quality_report.get("actual_version") != integration.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP


def test_renderer_mvp_flag_on_generates_valid_pptx_for_three_categories() -> None:
    flags = _set_flags(renderer_mvp=True, master=False, v10=False, shadow=False, canary=False)
    try:
        results = {
            case_id: integration.build_pptx_bytes_for_engine(payload, request_id=f"req-{case_id}")
            for case_id, payload in _fixture_cases().items()
        }
    finally:
        _restore_flags(flags)

    families_by_case = {}
    for case_id, result in results.items():
        assert result.engine_mode == integration.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP
        assert result.pptx_bytes[:2] == b"PK"
        prs = Presentation(BytesIO(result.pptx_bytes))
        assert len(prs.slides) == 5
        assert result.quality_report
        assert result.quality_report["requested_version"] == integration.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP
        assert result.quality_report["actual_version"] == integration.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP
        assert result.quality_report["fallback_used"] is False
        assert result.quality_report["feature_flag"] == integration.PRESENTATION_MASTER_V3_RENDERER_MVP_FLAG
        assert result.quality_report["artifact_runtime_dependency"] is False
        assert result.quality_report["architecture_deviation_count"] == 0
        assert result.quality_report["fake_evidence_count"] == 0
        assert result.quality_report["placeholder_internal_label_count"] == 0
        assert result.quality_report["tier1_editability"] == 1.0
        assert result.quality_report["rasterization_ratio"] == 0.0
        render_pages = result.quality_report["render_report"]["pages"]
        assert sum(page["overflow_count"] for page in render_pages) == 0
        assert sum(page["collision_count"] for page in render_pages) == 0
        assert sum(page["clipping_count"] for page in render_pages) == 0
        assert sum(page["off_canvas_count"] for page in render_pages) == 0
        audit = inspect_pptx_bytes(result.pptx_bytes, source_payload=_fixture_cases()[case_id])
        assert audit["placeholder_count"] == 0
        assert audit["internal_label_count"] == 0
        assert audit["fake_evidence_count"] == 0
        assert _fixture_cases()[case_id].powerpoint_generation_data.client_name in extract_pptx_text(result.pptx_bytes)
        families_by_case[case_id] = tuple(result.quality_report["template_collapse"]["family_sequence"])

    assert len(set(families_by_case.values())) == len(families_by_case)


def test_renderer_mvp_failure_falls_back_to_existing_production_flow(monkeypatch, sample_pptx_payload: dict[str, Any]) -> None:
    def _raise(_payload, *, request_id=None, project_id=None):
        raise RuntimeError("renderer mvp failed")

    flags = _set_flags(renderer_mvp=True, master=False, v10=False, shadow=False, canary=False)
    monkeypatch.setattr(integration, "_build_renderer_mvp_pptx_result", _raise)
    try:
        result = integration.build_pptx_bytes_for_engine(
            PptxDownloadRequest(**sample_pptx_payload),
            request_id="req-renderer-fallback",
            project_id="project-renderer-fallback",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert result.quality_report["requested_version"] == integration.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP
    assert result.quality_report["actual_version"] == integration.ENGINE_MODE_LEGACY
    assert result.quality_report["fallback_used"] is True
    assert result.quality_report["fallback_reason"] == "RuntimeError"


def test_renderer_mvp_summary_deck_falls_back_to_existing_renderer(sample_pptx_payload: dict[str, Any]) -> None:
    payload = PptxDownloadRequest(**{**sample_pptx_payload, "summary": True})
    flags = _set_flags(renderer_mvp=True, master=False, v10=False, shadow=False, canary=False)
    try:
        result = integration.build_pptx_bytes_for_engine(payload, request_id="req-summary")
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.quality_report
    assert result.quality_report["fallback_used"] is True
    assert result.quality_report["fallback_reason"] == "summary_deck_uses_existing_renderer"


def test_renderer_mvp_shadow_mode_keeps_legacy_response_and_logs_side_record(monkeypatch) -> None:
    payload = _fixture_cases()["faj"]
    log_spy = _LogSpy()
    monkeypatch.setattr(integration, "logger", log_spy)
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=True, canary=False)
    try:
        result = integration.build_pptx_bytes_for_engine(payload, request_id="req-shadow", project_id="project-shadow")
        assert integration.wait_for_renderer_mvp_shadow_tasks(timeout_seconds=5.0) is True
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert "renderer_mvp_shadow_result" not in result.quality_report
    messages = [record.message for record in log_spy.records]
    assert "v3_shadow_started" in messages
    assert "v3_shadow_success" in messages


@pytest.mark.parametrize(
    ("exception", "expected_reason"),
    [
        (RuntimeError("renderer exception"), "RuntimeError"),
        (
            RendererMvpIntegrationError("renderer_mvp_invalid_contract", failure_stage="contract_validation"),
            "renderer_mvp_invalid_contract",
        ),
        (
            RendererMvpIntegrationError("renderer_mvp_fake_evidence_block", failure_stage="runtime_validation"),
            "renderer_mvp_fake_evidence_block",
        ),
        (TimeoutError("renderer timeout"), "TimeoutError"),
        (
            RendererMvpIntegrationError("renderer_mvp_unsupported_primitive", failure_stage="contract_validation"),
            "renderer_mvp_unsupported_primitive",
        ),
        (
            RendererMvpIntegrationError("renderer_mvp_qa_blocking_failure", failure_stage="visual_qa"),
            "renderer_mvp_qa_blocking_failure",
        ),
    ],
)
def test_renderer_mvp_shadow_failure_does_not_affect_legacy_response(
    monkeypatch,
    exception,
    expected_reason: str,
) -> None:
    def _raise(_payload, *, request_id=None, project_id=None):
        raise exception

    payload = _fixture_cases()["logistics"]
    log_spy = _LogSpy()
    monkeypatch.setattr(integration, "logger", log_spy)
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=True, canary=False)
    monkeypatch.setattr(integration, "_build_renderer_mvp_pptx_result", _raise)
    try:
        result = integration.build_pptx_bytes_for_engine(payload, request_id="req-shadow-failure")
        assert integration.wait_for_renderer_mvp_shadow_tasks(timeout_seconds=5.0) is True
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert "renderer_mvp_shadow_result" not in result.quality_report
    messages = [record.message for record in log_spy.records]
    assert "v3_shadow_started" in messages
    assert ("v3_shadow_timeout" if expected_reason == "TimeoutError" else "v3_shadow_failure") in messages
    assert any(getattr(record, "fallback_reason", "") == expected_reason for record in log_spy.records)


def test_renderer_mvp_canary_requires_env_flag_and_explicit_selector() -> None:
    payload = _fixture_cases()["commerce"]
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=False, canary=False)
    try:
        result = integration.build_pptx_bytes_for_engine(payload, renderer_mvp_canary=True, request_id="req-canary-off")
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.quality_report
    assert "renderer_mvp_shadow_result" not in result.quality_report


def test_renderer_mvp_canary_generates_only_for_explicit_internal_request() -> None:
    payload = _fixture_cases()["commerce"]
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=False, canary=True)
    try:
        normal_result = integration.build_pptx_bytes_for_engine(payload, request_id="req-normal")
        canary_result = integration.build_pptx_bytes_for_engine(
            payload,
            renderer_mvp_canary=True,
            request_id="req-canary",
        )
    finally:
        _restore_flags(flags)

    assert normal_result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert canary_result.engine_mode == integration.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP
    assert canary_result.quality_report
    assert canary_result.quality_report["routing_mode"] == "canary"
    assert canary_result.quality_report["canary_success"] is True


def test_renderer_mvp_canary_failure_falls_back_to_existing_renderer(monkeypatch) -> None:
    def _raise(_payload, *, request_id=None, project_id=None):
        raise RendererMvpIntegrationError("renderer_mvp_invalid_contract", failure_stage="contract_validation")

    payload = _fixture_cases()["faj"]
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=False, canary=True)
    monkeypatch.setattr(integration, "_build_renderer_mvp_pptx_result", _raise)
    try:
        result = integration.build_pptx_bytes_for_engine(
            payload,
            renderer_mvp_canary=True,
            request_id="req-canary-fallback",
        )
    finally:
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert result.quality_report
    assert result.quality_report["routing_mode"] == "canary"
    assert result.quality_report["canary_success"] is False
    assert result.quality_report["fallback_used"] is True
    assert result.quality_report["fallback_reason"] == "renderer_mvp_invalid_contract"


def test_renderer_mvp_shadow_execution_is_off_the_response_critical_path(monkeypatch) -> None:
    original_builder = integration._build_renderer_mvp_pptx_result
    shadow_started = threading.Event()
    release_shadow = threading.Event()

    def _slow_builder(_payload, *, request_id=None, project_id=None):
        shadow_started.set()
        release_shadow.wait(timeout=5.0)
        return original_builder(_payload, request_id=request_id, project_id=project_id)

    payload = _fixture_cases()["faj"]
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=True, canary=False)
    monkeypatch.setattr(integration, "_build_renderer_mvp_pptx_result", _slow_builder)
    started = time.perf_counter()
    try:
        result = integration.build_pptx_bytes_for_engine(payload, request_id="req-shadow-latency")
        response_duration = time.perf_counter() - started
        assert shadow_started.wait(timeout=2.0) is True
        release_shadow.set()
        assert integration.wait_for_renderer_mvp_shadow_tasks(timeout_seconds=5.0) is True
    finally:
        release_shadow.set()
        _restore_flags(flags)

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert response_duration < 5.0
    assert "renderer_mvp_shadow_result" not in (result.quality_report or {})


def test_renderer_mvp_concurrent_shadow_execution_keeps_all_responses_legacy() -> None:
    from concurrent.futures import ThreadPoolExecutor

    payloads = list(_fixture_cases().values())
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=True, canary=False)
    try:
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(
                executor.map(
                    lambda item: integration.build_pptx_bytes_for_engine(
                        item[1],
                        request_id=f"req-shadow-concurrent-{item[0]}",
                    ),
                    enumerate(payloads),
                )
            )
        assert integration.wait_for_renderer_mvp_shadow_tasks(timeout_seconds=5.0) is True
    finally:
        _restore_flags(flags)

    assert len(results) == 3
    assert all(result.engine_mode == integration.ENGINE_MODE_LEGACY for result in results)
    assert all(result.pptx_bytes[:2] == b"PK" for result in results)
    assert all("renderer_mvp_shadow_result" not in (result.quality_report or {}) for result in results)


def test_renderer_mvp_shadow_capacity_saturation_skips_without_waiting(monkeypatch) -> None:
    assert integration.wait_for_renderer_mvp_shadow_tasks(timeout_seconds=5.0) is True
    acquired = 0
    while integration._SHADOW_CAPACITY.acquire(blocking=False):
        acquired += 1
    assert acquired > 0

    payload = _fixture_cases()["faj"]
    log_spy = _LogSpy()
    monkeypatch.setattr(integration, "logger", log_spy)
    flags = _set_flags(renderer_mvp=False, master=False, v10=False, shadow=True, canary=False)
    try:
        result = integration.build_pptx_bytes_for_engine(payload, request_id="req-shadow-capacity")
    finally:
        _restore_flags(flags)
        for _ in range(acquired):
            integration._SHADOW_CAPACITY.release()

    assert result.engine_mode == integration.ENGINE_MODE_LEGACY
    assert result.pptx_bytes[:2] == b"PK"
    assert "renderer_mvp_shadow_result" not in (result.quality_report or {})
    messages = [record.message for record in log_spy.records]
    assert "v3_shadow_skipped_capacity" in messages
    assert "v3_shadow_started" not in messages
