from __future__ import annotations

from io import BytesIO
import importlib
import json
from typing import Any
from urllib.parse import unquote

from fastapi.testclient import TestClient
from pptx import Presentation
import pytest


ENDPOINT = "/api/internal/presentation-master-v3/canary/download-pptx"


def _runtime_modules():
    integration = importlib.import_module("app.services.presentation_engine_integration")
    main = importlib.import_module("app.main")
    return integration, main


def _set_v3_flags(
    *,
    canary: bool,
    renderer_mvp: bool = False,
    shadow: bool = False,
    master: bool = False,
    v10: bool = False,
) -> tuple[Any, dict[str, bool]]:
    integration, main = _runtime_modules()
    settings = integration.settings
    originals = {
        "presentation_master_v3_renderer_mvp_canary_enabled": settings.presentation_master_v3_renderer_mvp_canary_enabled,
        "presentation_master_v3_renderer_mvp_enabled": settings.presentation_master_v3_renderer_mvp_enabled,
        "presentation_master_v3_renderer_mvp_shadow_enabled": settings.presentation_master_v3_renderer_mvp_shadow_enabled,
        "presentation_design_ai_master_enabled": settings.presentation_design_ai_master_enabled,
        "presentation_design_ai_v10_enabled": settings.presentation_design_ai_v10_enabled,
    }
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_canary_enabled", canary)
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_enabled", renderer_mvp)
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", shadow)
    object.__setattr__(settings, "presentation_design_ai_master_enabled", master)
    object.__setattr__(settings, "presentation_design_ai_v10_enabled", v10)
    object.__setattr__(main.settings, "presentation_master_v3_renderer_mvp_canary_enabled", canary)
    return settings, originals


def _restore_flags(settings: Any, originals: dict[str, bool]) -> None:
    for key, value in originals.items():
        object.__setattr__(settings, key, value)


def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    password = f"{role}-password"
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": email, "password": password, "role": role},
    )
    assert create_response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def _quality_report(response) -> dict[str, Any]:
    return json.loads(unquote(response.headers["x-presentation-quality-report"]))


def _canary_payload(
    *,
    client_name: str = "株式会社サンプル",
    deck_title: str = "業務判断高度化提案",
    project_brief: str = "業務情報を整理し、責任者の判断と実行計画をつなぐ。",
    hearing_result: str = "現状業務、判断条件、責任者、承認者、実行内容を確認したい。",
    own_service_info: str = "業務設計と導入計画の整理を支援。",
    special_function_required: str = "",
) -> dict[str, Any]:
    return {
        "project_brief": project_brief,
        "client_company_info": f"{client_name}\n対象: 部門責任者 / 経営",
        "hearing_result": hearing_result,
        "own_service_info": own_service_info,
        "special_function_required": special_function_required,
        "desired_launch_timing": "次回打ち合わせでPoC条件を確認",
        "budget_range": "未確定",
        "powerpoint_generation_data": {
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
        "semantic_candidates": {
            "candidates": [
                {"id": "prep", "semantic_type": "preparation_analysis", "value": "現状業務と要件を確認する", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED"},
                {"id": "condition", "semantic_type": "decision_condition", "value": "要件と予算を確認できた場合に次工程へ進む", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED"},
                {"id": "owner", "semantic_type": "accountable_owner", "value": "顧客責任者", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED"},
                {"id": "approver", "semantic_type": "approver", "value": "顧客責任者", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED"},
                {"id": "action", "semantic_type": "execution_action", "value": "合意した実行計画を開始する", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED"},
                {"id": "context", "semantic_type": "decision_context", "value": "導入判断", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED", "from_item": "owner", "to_item": "approver", "relationship_type": "handoff"},
                {"id": "escalation", "semantic_type": "escalation", "value": "未解決事項は顧客責任者へ確認する", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED"},
                {"id": "evidence", "semantic_type": "evidence", "value": "顧客ヒアリング記録", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED", "admissible_as_evidence": True, "source_reference": "hearing_result:evidence"},
                {"id": "ai-note", "semantic_type": "kpi_name", "value": "導入判断メモ", "source_type": "user_text", "source_field": "hearing_result", "authority": "SYSTEM_EXTRACTED", "confidence": 0.8, "review_state": "CONFIRMED"},
            ]
        },
        "semantic_confirmation_state": [
            {"id": candidate_id, "semantic_type": semantic_type, "review_state": "CONFIRMED"}
            for candidate_id, semantic_type in (
                ("prep", "preparation_analysis"), ("condition", "decision_condition"),
                ("owner", "accountable_owner"), ("approver", "approver"),
                ("action", "execution_action"), ("context", "decision_context"),
                ("escalation", "escalation"), ("evidence", "evidence"), ("ai-note", "kpi_name"),
            )
        ],
    }


def test_public_download_route_ignores_canary_flag_query_body_and_header(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    settings, originals = _set_v3_flags(canary=True, renderer_mvp=False, shadow=False)
    try:
        response = client.post(
            "/api/download-pptx?renderer_mvp_canary=true",
            headers={**admin_headers, "X-Presentation-Canary": "true"},
            json={**sample_pptx_payload, "renderer_mvp_canary": True},
        )
    finally:
        _restore_flags(settings, originals)

    assert response.status_code == 200
    assert response.content[:2] == b"PK"
    assert response.headers.get("x-presentation-canary") is None
    quality_report = _quality_report(response)
    assert quality_report.get("actual_version") != "presentation_master_v3_renderer_mvp"
    assert quality_report.get("routing_mode") != "internal_canary"


def test_internal_canary_endpoint_requires_admin_and_flag(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    payload = _canary_payload()
    unauthenticated = client.post(ENDPOINT, json=payload)
    assert unauthenticated.status_code == 401

    member_headers = _create_user_and_login(client, admin_headers, "canary-member@example.com", "member")
    non_admin = client.post(ENDPOINT, headers=member_headers, json=payload)
    assert non_admin.status_code == 403

    settings, originals = _set_v3_flags(canary=False, renderer_mvp=False, shadow=True)
    try:
        disabled = client.post(ENDPOINT, headers=admin_headers, json=payload)
    finally:
        _restore_flags(settings, originals)

    assert disabled.status_code == 404
    assert disabled.json()["detail"]["error_type"] == "internal_canary_disabled"
    assert disabled.json()["detail"]["fallback_used"] is False


def test_internal_canary_endpoint_returns_identifiable_v3_pptx_for_admin(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    settings, originals = _set_v3_flags(canary=True, renderer_mvp=False, shadow=True)
    try:
        response = client.post(ENDPOINT, headers=admin_headers, json=_canary_payload())
    finally:
        _restore_flags(settings, originals)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    assert response.headers["x-presentation-engine"] == "renderer-mvp-v3"
    assert response.headers["x-presentation-canary"] == "true"
    assert response.headers["x-presentation-canary-success"] == "true"
    assert response.content[:2] == b"PK"
    assert len(Presentation(BytesIO(response.content)).slides) == 5
    quality_report = _quality_report(response)
    assert quality_report["actual_version"] == "presentation_master_v3_renderer_mvp"
    assert quality_report["routing_mode"] == "internal_canary"
    assert quality_report["internal_canary"] is True
    assert quality_report["canary_success"] is True
    assert quality_report["fallback_used"] is False


@pytest.mark.parametrize(
    ("exception", "expected_reason"),
    [
        (RuntimeError("renderer exception"), "RuntimeError"),
        ("invalid_contract", "renderer_mvp_invalid_contract"),
        ("evidence_violation", "renderer_mvp_fake_evidence_block"),
        ("qa_blocking", "renderer_mvp_qa_blocking_failure"),
        ("unsupported_primitive", "renderer_mvp_unsupported_primitive"),
        (TimeoutError("renderer timeout"), "TimeoutError"),
        ("malformed_pptx", "renderer_mvp_malformed_pptx"),
        (Exception("unexpected"), "Exception"),
    ],
)
def test_internal_canary_failures_are_explicit_errors_not_legacy_success(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
    admin_headers: dict[str, str],
    caplog: pytest.LogCaptureFixture,
    exception: Any,
    expected_reason: str,
) -> None:
    integration, _ = _runtime_modules()
    renderer_module = importlib.import_module("app.services.presentation_master.renderer_mvp")
    caplog.set_level("WARNING", logger=integration.logger.name)

    def _raise(_payload, *, request_id=None, project_id=None, semantic_gate=False):
        assert semantic_gate is True
        if exception == "invalid_contract":
            raise renderer_module.RendererMvpIntegrationError(
                "renderer_mvp_invalid_contract",
                failure_stage="contract_validation",
            )
        if exception == "evidence_violation":
            raise renderer_module.RendererMvpIntegrationError(
                "renderer_mvp_fake_evidence_block",
                failure_stage="runtime_validation",
            )
        if exception == "qa_blocking":
            raise renderer_module.RendererMvpIntegrationError(
                "renderer_mvp_qa_blocking_failure",
                failure_stage="visual_qa",
            )
        if exception == "unsupported_primitive":
            raise renderer_module.RendererMvpIntegrationError(
                "renderer_mvp_unsupported_primitive",
                failure_stage="contract_validation",
            )
        if exception == "malformed_pptx":
            return integration.PresentationEngineResult(
                pptx_bytes=b"not-a-pptx",
                engine_mode=integration.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP,
                quality_report={},
            )
        raise exception

    settings, originals = _set_v3_flags(canary=True, renderer_mvp=False, shadow=True)
    monkeypatch.setattr(integration, "_build_renderer_mvp_pptx_result", _raise)
    try:
        response = client.post(ENDPOINT, headers=admin_headers, json=_canary_payload())
        normal_response = client.post("/api/download-pptx", headers=admin_headers, json=_canary_payload())
    finally:
        _restore_flags(settings, originals)

    assert response.status_code == 500
    assert response.content[:2] != b"PK"
    detail = response.json()["detail"]
    assert detail["error_type"] == "internal_canary_generation_failed"
    assert detail["fallback_used"] is False
    assert detail["fallback_reason"] == expected_reason
    failure_logs = [record.getMessage() for record in caplog.records if record.getMessage().startswith("v3_internal_canary_failure")]
    assert failure_logs
    assert f"error_type={'RendererMvpIntegrationError' if isinstance(exception, str) or exception == 'malformed_pptx' or exception in {'evidence_violation', 'qa_blocking', 'unsupported_primitive'} else type(exception).__name__}" in failure_logs[-1]
    assert "Authorization" not in failure_logs[-1]
    assert "Bearer" not in failure_logs[-1]
    assert "Product" not in failure_logs[-1]
    if isinstance(exception, BaseException):
        assert str(exception) not in failure_logs[-1]
    assert normal_response.status_code == 200
    assert normal_response.content[:2] == b"PK"
    assert normal_response.headers.get("x-presentation-canary") is None
