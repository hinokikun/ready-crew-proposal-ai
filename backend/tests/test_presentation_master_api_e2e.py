from __future__ import annotations

import json
from urllib.parse import unquote

from fastapi.testclient import TestClient


def _quality(response) -> dict:
    value = response.headers.get("x-presentation-quality-report", "")
    assert value
    return json.loads(unquote(value))


def _set_flags(master: bool, shadow: bool, v10: bool = False):
    from app.config import settings

    original = (
        settings.presentation_design_ai_master_enabled,
        settings.presentation_design_ai_master_shadow_enabled,
        settings.presentation_design_ai_v10_enabled,
    )
    object.__setattr__(settings, "presentation_design_ai_master_enabled", master)
    object.__setattr__(settings, "presentation_design_ai_master_shadow_enabled", shadow)
    object.__setattr__(settings, "presentation_design_ai_v10_enabled", v10)
    return original


def _restore_flags(original) -> None:
    from app.config import settings

    object.__setattr__(settings, "presentation_design_ai_master_enabled", original[0])
    object.__setattr__(settings, "presentation_design_ai_master_shadow_enabled", original[1])
    object.__setattr__(settings, "presentation_design_ai_v10_enabled", original[2])


def _post_download(client: TestClient, headers: dict[str, str], payload: dict) -> tuple[object, dict]:
    response = client.post("/api/download-pptx", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.content[:2] == b"PK"
    assert "application/vnd.openxmlformats-officedocument.presentationml.presentation" in response.headers["content-type"]
    assert "attachment;" in response.headers["content-disposition"]
    assert "master" not in unquote(response.headers["content-disposition"]).lower()
    assert "shadow" not in unquote(response.headers["content-disposition"]).lower()
    return response, _quality(response)


def test_download_pptx_flag_off_e2e_uses_legacy(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict) -> None:
    original = _set_flags(master=False, shadow=False)
    try:
        _, quality = _post_download(client, admin_headers, sample_pptx_payload)
    finally:
        _restore_flags(original)

    assert "shadow_result" not in quality
    assert quality.get("requested_version") != "presentation_design_master_v1"


def test_download_pptx_shadow_e2e_keeps_legacy_response(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict) -> None:
    original = _set_flags(master=False, shadow=True)
    try:
        _, quality = _post_download(client, admin_headers, sample_pptx_payload)
    finally:
        _restore_flags(original)

    shadow = quality["shadow_result"]
    assert shadow["mode"] == "shadow"
    assert shadow["shadow_enabled"] is True
    assert shadow["shadow_success"] is True
    assert shadow["actual_version"] == "presentation_design_master_v1"


def test_download_pptx_enabled_e2e_uses_master(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict) -> None:
    original = _set_flags(master=True, shadow=False)
    try:
        _, quality = _post_download(client, admin_headers, sample_pptx_payload)
    finally:
        _restore_flags(original)

    assert quality["requested_version"] == "presentation_design_master_v1"
    assert quality["actual_version"] == "presentation_design_master_v1"
    assert quality["fallback_used"] is False
    assert quality["production_native_module"] == "app.services.presentation_master"
    assert quality["master_qa"]["status"] == "PASS"


def test_download_summary_pptx_e2e_routes_to_legacy(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict) -> None:
    original = _set_flags(master=True, shadow=False)
    try:
        response = client.post("/api/download-summary-pptx", json=sample_pptx_payload, headers=admin_headers)
        quality = _quality(response)
    finally:
        _restore_flags(original)

    assert response.status_code == 200
    assert response.content[:2] == b"PK"
    assert quality["actual_version"] == "legacy"
    assert quality["fallback_reason"] == "summary_deck_uses_legacy"
    assert quality["failure_stage"] == "routing"


def test_download_pptx_e2e_routes_unknown_category_to_legacy(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict) -> None:
    payload = dict(sample_pptx_payload)
    payload["client_company_info"] = "未知カテゴリ株式会社 / Unusual / Unknown"
    payload["project_brief"] = "分類しにくい特殊業務の相談。"
    original = _set_flags(master=True, shadow=False)
    try:
        _, quality = _post_download(client, admin_headers, payload)
    finally:
        _restore_flags(original)

    assert quality["actual_version"] == "legacy"
    assert quality["fallback_reason"] == "unsupported_category_uses_legacy"
    assert quality["fallback_category"] == "unsupported"


def test_download_pptx_shadow_failure_does_not_break_api(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict, monkeypatch) -> None:
    from app.services import presentation_engine_integration as integration

    def _timeout(*_args, **_kwargs):
        raise TimeoutError("shadow timeout")

    original = _set_flags(master=False, shadow=True)
    monkeypatch.setattr(integration, "_build_master_pptx_result", _timeout)
    try:
        response, quality = _post_download(client, admin_headers, sample_pptx_payload)
    finally:
        _restore_flags(original)

    assert response.status_code == 200
    assert quality["shadow_result"]["shadow_success"] is False
    assert quality["shadow_result"]["failure_reason"] == "TimeoutError"
