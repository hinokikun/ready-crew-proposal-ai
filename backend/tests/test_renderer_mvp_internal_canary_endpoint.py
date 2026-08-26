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
    client_name: str = "株式会社フラワーオークションジャパン",
    deck_title: str = "画像認識AI導入PoC提案",
    project_brief: str = "花卉の商品画像から品質候補を出し、人の最終判断と理由を記録して次回判断へ使う。",
    hearing_result: str = "対象画像、撮影条件、AI候補、人判断、一致と差異、例外条件をPoCで確認したい。",
    own_service_info: str = "画像認識AIと判定記録の運用設計を支援。",
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
    exception: Any,
    expected_reason: str,
) -> None:
    integration, _ = _runtime_modules()
    renderer_module = importlib.import_module("app.services.presentation_master.renderer_mvp")

    def _raise(_payload, *, request_id=None, project_id=None):
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
    assert normal_response.status_code == 200
    assert normal_response.content[:2] == b"PK"
    assert normal_response.headers.get("x-presentation-canary") is None
