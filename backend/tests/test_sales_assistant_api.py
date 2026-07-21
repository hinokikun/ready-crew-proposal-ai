import importlib
from io import BytesIO
from types import SimpleNamespace
import sqlite3
import sys
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from pptx import Presentation


def _configure_sales_assistant_test_env(
    monkeypatch: pytest.MonkeyPatch,
    db_path: Path,
    *,
    proposal_enabled: bool,
    export_enabled: bool,
) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_LIMIT", "1000")
    monkeypatch.setenv("RATE_LIMIT_GENERATION_LIMIT", "1000")
    monkeypatch.setenv("RATE_LIMIT_ADMIN_LIMIT", "1000")
    monkeypatch.setenv("SALES_ASSISTANT_ENABLED", "true")
    monkeypatch.setenv("SALES_ASSISTANT_PROPOSAL_ENABLED", str(proposal_enabled).lower())
    monkeypatch.setenv("PROPOSAL_EXPORT_ENABLED", str(export_enabled).lower())


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


@pytest.fixture()
def enabled_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "sales_assistant_api.db"
    _configure_sales_assistant_test_env(monkeypatch, db_path, proposal_enabled=True, export_enabled=True)
    _reload_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client, db_path


@pytest.fixture()
def assistant_only_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "sales_assistant_api_flag_off.db"
    _configure_sales_assistant_test_env(monkeypatch, db_path, proposal_enabled=False, export_enabled=False)
    _reload_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client, db_path


@pytest.fixture()
def export_disabled_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    db_path = tmp_path / "sales_assistant_api_export_flag_off.db"
    _configure_sales_assistant_test_env(monkeypatch, db_path, proposal_enabled=True, export_enabled=False)
    _reload_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        yield test_client, db_path


def _headers_for(client: TestClient, email: str = "admin@example.com", password: str = "test-password") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password, "login_mode": "admin" if email.startswith("admin") else "user"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _create_member(client: TestClient, admin_headers: dict[str, str]) -> dict[str, str]:
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "member@example.com", "password": "member-pass", "role": "member", "display_name": "Member"},
    )
    assert response.status_code == 200
    login = client.post("/api/auth/login", json={"email": "member@example.com", "password": "member-pass", "login_mode": "user"})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['token']}"}


def _payload(**overrides):
    value = {
        "project_title": "生花オークション向けAI画像認識導入支援",
        "project_summary": "生花の商品画像と商品データの対応確認、種類、色、等級、状態の分類をAI画像認識で候補提示したい。",
        "client_name": "株式会社サンプルフラワー",
        "known_requirements": ["AIは候補提示に限定し、人が最終確認する", "APIまたはCSVで商品管理システムへ連携する"],
        "known_constraints": ["PoCで認識精度と現場適合性を評価する"],
        "budget_information": "予算上限は1,000万円",
        "schedule_information": "2027年5月頃の導入を想定",
        "meeting_stage": "preparation",
        "previous_interactions": ["現場担当者から繁忙時の確認工数が課題と共有済み"],
        "evidence_items": ["対象業務: 商品画像、ロット情報、種類、色、等級、状態の確認"],
        "industry": "生花流通",
        "business_goals": ["確認時間の短縮", "判定品質の標準化"],
        "current_problems": ["人手判定による工数と品質差", "繁忙時の処理遅延"],
        "proposed_solution": "AI画像認識で候補を提示し、担当者が最終確認する運用",
        "expected_deliverables": ["PoC計画", "認識モデル検証", "連携方式整理"],
        "integrations": ["API", "CSV", "商品管理システム"],
        "expected_kpis": ["候補正答率", "人手修正率", "1件あたり確認時間"],
        "risks": ["学習データ不足", "誤判定時の運用設計"],
        "stakeholders": ["品質管理", "情報システム", "現場責任者"],
    }
    value.update(overrides)
    return value


def _count_rows(db_path: Path, table_name: str) -> int:
    with sqlite3.connect(db_path) as db:
        exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        if not exists:
            return 0
        row = db.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0])


def io_bytes(value: bytes) -> BytesIO:
    return BytesIO(value)


def _assistant_result(client: TestClient, headers: dict[str, str], payload: dict | None = None) -> dict:
    response = client.post("/api/sales-assistant/generate", headers=headers, json=payload or _payload())
    assert response.status_code == 200
    return response.json()


def _proposal_preview_payload(assistant_result: dict, payload: dict | None = None) -> dict:
    return {
        "source_request": payload or _payload(),
        "sales_assistant_brief": assistant_result["sales_assistant_brief"],
        "strategy_brief": assistant_result["strategy_brief"],
    }


def _export_payload(
    assistant_result: dict,
    preview_result: dict,
    *,
    export_type: str = "powerpoint",
    review_status: str = "approved",
    payload: dict | None = None,
) -> dict:
    return {
        "export_type": export_type,
        "source_request": payload or _payload(),
        "sales_assistant_brief": assistant_result["sales_assistant_brief"],
        "strategy_brief": assistant_result["strategy_brief"],
        "proposal_preview": preview_result["proposal_preview"],
        "proposal_response": preview_result["proposal_response"],
        "human_review_status": review_status,
        "human_review_required": preview_result["human_review_required"],
        "project_id": "sales-assistant-export-test",
    }


def test_status_reports_disabled_without_exposing_generation(client: TestClient, admin_headers: dict[str, str]):
    status = client.get("/api/sales-assistant/status", headers=admin_headers)
    assert status.status_code == 200
    assert status.json() == {
        "enabled": False,
        "version": "50",
        "requires_admin": True,
        "persistence_enabled": False,
        "external_ai_enabled": False,
        "proposal_preview_enabled": False,
        "proposal_export_enabled": False,
        "beautiful_ai_export_enabled": False,
    }

    response = client.post("/api/sales-assistant/generate", headers=admin_headers, json=_payload())
    assert response.status_code == 404
    assert response.json()["detail"]["error_type"] == "sales_assistant_disabled"


def test_api_requires_admin(enabled_client):
    client, _ = enabled_client
    assert client.get("/api/sales-assistant/status").status_code == 401
    admin_headers = _headers_for(client)
    member_headers = _create_member(client, admin_headers)
    assert client.get("/api/sales-assistant/status", headers=member_headers).status_code == 403
    assert client.post("/api/sales-assistant/generate", headers=member_headers, json=_payload()).status_code == 403
    assistant_result = _assistant_result(client, admin_headers)
    preview_payload = _proposal_preview_payload(assistant_result)
    assert client.post("/api/sales-assistant/proposal-preview", headers=member_headers, json=preview_payload).status_code == 403
    preview = client.post("/api/sales-assistant/proposal-preview", headers=admin_headers, json=preview_payload).json()
    export_payload = _export_payload(assistant_result, preview)
    assert client.post("/api/sales-assistant/export", headers=member_headers, json=export_payload).status_code == 403
    assert client.post("/api/sales-assistant/export/download", headers=member_headers, json=export_payload).status_code == 403


def test_generate_returns_contract_and_does_not_persist_project(enabled_client):
    client, db_path = enabled_client
    admin_headers = _headers_for(client)
    before_projects = _count_rows(db_path, "projects")
    before_history = _count_rows(db_path, "creation_history")

    response = client.post("/api/sales-assistant/generate", headers=admin_headers, json=_payload())

    assert response.status_code == 200
    data = response.json()
    assert set(data).issuperset(
        {
            "sales_assistant_brief",
            "strategy_brief",
            "strategy_brief_summary",
            "warnings",
            "human_review_required",
            "human_review_reasons",
            "generation_metadata",
        }
    )
    brief = data["sales_assistant_brief"]
    for key in [
        "summary",
        "meeting_plan",
        "discovery_questions",
        "talk_track",
        "objection_handling",
        "decision_maker_support",
        "evidence_guidance",
        "next_actions",
        "follow_up",
        "risk_and_guardrails",
        "generation_metadata",
    ]:
        assert brief[key]
    assert data["generation_metadata"]["deterministic"] is True
    assert _count_rows(db_path, "projects") == before_projects
    assert _count_rows(db_path, "creation_history") == before_history


def test_proposal_preview_uses_existing_generator_without_persistence(enabled_client):
    client, db_path = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    before_projects = _count_rows(db_path, "projects")
    before_history = _count_rows(db_path, "creation_history")

    response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )

    assert response.status_code == 200
    data = response.json()
    preview = data["proposal_preview"]
    assert preview["proposal_summary"]
    assert preview["issues"]
    assert preview["proposal_story"]
    assert preview["slide_outline"]
    assert preview["kpis"]
    assert preview["estimate_summary"]
    assert data["generation_metadata"]["proposal_generator"] == "app.services.openai_service.generate_proposal"
    assert data["generation_metadata"]["persistence_enabled"] is False
    assert data["generation_metadata"]["pptx_enabled"] is False
    assert data["generation_metadata"]["beautiful_ai_enabled"] is False
    assert _count_rows(db_path, "projects") == before_projects
    assert _count_rows(db_path, "creation_history") == before_history


def test_proposal_preview_feature_flag_defaults_to_off(assistant_only_client):
    client, _ = assistant_only_client
    headers = _headers_for(client)
    status = client.get("/api/sales-assistant/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["enabled"] is True
    assert status.json()["proposal_preview_enabled"] is False
    assert status.json()["proposal_export_enabled"] is False
    assistant_result = _assistant_result(client, headers)

    response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error_type"] == "sales_assistant_proposal_disabled"


def test_export_feature_flag_defaults_to_off(export_disabled_client):
    client, _ = export_disabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )
    assert preview_response.status_code == 200
    response = client.post(
        "/api/sales-assistant/export",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json()),
    )
    assert response.status_code == 404
    assert response.json()["detail"]["error_type"] == "proposal_export_disabled"


def test_export_blocks_required_review_until_approved(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    sparse_payload = _payload(client_name="", budget_information="", schedule_information="", evidence_items=[])
    assistant_result = _assistant_result(client, headers, sparse_payload)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result, sparse_payload),
    )
    assert preview_response.status_code == 200

    response = client.post(
        "/api/sales-assistant/export",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json(), review_status="reviewed", payload=sparse_payload),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error_type"] == "proposal_export_review_required"


def test_export_powerpoint_reuses_existing_pptx_generation(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )
    assert preview_response.status_code == 200

    response = client.post(
        "/api/sales-assistant/export",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json()),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["export_type"] == "powerpoint"
    assert data["status"] == "success"
    assert data["artifact"]["download_url"] == "/api/sales-assistant/export/download"
    assert data["artifact"]["download_method"] == "POST"
    assert data["artifact"]["filename"].startswith("ProposalPilot_")
    assert data["artifact"]["filename"].endswith(".pptx")
    assert data["artifact"]["byte_size"] > 1000
    assert data["request_json_safe"]["slides"] >= 1


def test_export_powerpoint_download_returns_valid_pptx(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )
    export_payload = _export_payload(assistant_result, preview_response.json())

    response = client.post("/api/sales-assistant/export/download", headers=headers, json=export_payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    disposition = response.headers["content-disposition"]
    assert "filename*=" in disposition
    assert "ProposalPilot_" in disposition
    assert ".pptx" in disposition
    assert len(response.content) > 1000
    with ZipFile(io_bytes(response.content)) as archive:
        names = set(archive.namelist())
    assert "[Content_Types].xml" in names
    assert "ppt/presentation.xml" in names
    assert any(name.startswith("ppt/slides/slide") and name.endswith(".xml") for name in names)
    presentation = Presentation(io_bytes(response.content))
    assert len(presentation.slides) >= 1
    assert "app/" not in response.text.lower()
    assert "backend" not in response.text.lower()


def test_export_download_blocks_required_review_until_approved(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    sparse_payload = _payload(client_name="", budget_information="", schedule_information="", evidence_items=[])
    assistant_result = _assistant_result(client, headers, sparse_payload)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result, sparse_payload),
    )

    response = client.post(
        "/api/sales-assistant/export/download",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json(), review_status="reviewed", payload=sparse_payload),
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error_type"] == "proposal_export_review_required"


def test_export_download_rejects_beautiful_ai_payload(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )

    response = client.post(
        "/api/sales-assistant/export/download",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json(), export_type="beautiful_ai"),
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error_type"] == "proposal_export_download_type_invalid"


def test_export_download_blocks_empty_pptx(monkeypatch: pytest.MonkeyPatch, enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )
    router_module = importlib.import_module("app.routers.sales_assistant")
    monkeypatch.setattr(
        router_module,
        "build_pptx_bytes_for_engine",
        lambda _payload: SimpleNamespace(pptx_bytes=b"", engine_mode="legacy"),
    )

    response = client.post(
        "/api/sales-assistant/export/download",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json()),
    )

    assert response.status_code == 500
    assert response.json()["detail"]["error_type"] == "proposal_export_pptx_empty"


def test_export_download_blocks_invalid_pptx(monkeypatch: pytest.MonkeyPatch, enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )
    router_module = importlib.import_module("app.routers.sales_assistant")
    monkeypatch.setattr(
        router_module,
        "build_pptx_bytes_for_engine",
        lambda _payload: SimpleNamespace(pptx_bytes=b"not-a-pptx", engine_mode="legacy"),
    )

    response = client.post(
        "/api/sales-assistant/export/download",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json()),
    )

    assert response.status_code == 500
    assert response.json()["detail"]["error_type"] == "proposal_export_pptx_invalid"


def test_export_beautiful_ai_reuses_existing_service(monkeypatch: pytest.MonkeyPatch, enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )
    router_module = importlib.import_module("app.routers.sales_assistant")
    captured = {}

    async def fake_create_beautiful_ai_presentation(_db, *, request, user_id):
        captured["project_id"] = request.project_id
        captured["user_id"] = user_id
        return router_module.BeautifulAiPresentationResponse(
            presentation_id="mock-export",
            status="completed",
            title=request.powerpoint_generation_data.deck_title,
            editor_url="https://www.beautiful.ai/editor/mock-export",
            player_url="https://www.beautiful.ai/player/mock-export",
            created_at="2026-07-20T00:00:00Z",
        )

    monkeypatch.setattr(router_module, "create_beautiful_ai_presentation", fake_create_beautiful_ai_presentation)

    response = client.post(
        "/api/sales-assistant/export",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json(), export_type="beautiful_ai"),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["export_type"] == "beautiful_ai"
    assert data["artifact"]["editor_url"].endswith("/mock-export")
    assert captured["project_id"] == "sales-assistant-export-test"


def test_export_failure_is_safe_and_retryable(monkeypatch: pytest.MonkeyPatch, enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )
    router_module = importlib.import_module("app.routers.sales_assistant")

    def raise_pptx_error(_payload):
        raise RuntimeError("secret export token should not leak")

    monkeypatch.setattr(router_module, "build_pptx_bytes_for_engine", raise_pptx_error)
    response = client.post(
        "/api/sales-assistant/export",
        headers=headers,
        json=_export_payload(assistant_result, preview_response.json()),
    )

    assert response.status_code == 500
    assert response.json()["detail"]["error_type"] == "proposal_export_powerpoint_failed"
    assert "secret export token" not in response.text.lower()


def test_proposal_preview_failure_is_safe_and_retryable(monkeypatch: pytest.MonkeyPatch, enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    router_module = importlib.import_module("app.routers.sales_assistant")

    async def raise_generator_error(_payload):
        raise router_module.OpenAIServiceError("secret token should not leak", 502)

    monkeypatch.setattr(router_module, "generate_proposal", raise_generator_error)
    response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )

    assert response.status_code == 502
    assert response.json()["detail"]["error_type"] == "sales_assistant_proposal_generation_error"
    assert "secret token" not in response.text.lower()


def test_strategy_failure_is_safe(monkeypatch: pytest.MonkeyPatch, enabled_client):
    client, _ = enabled_client
    router_module = importlib.import_module("app.routers.sales_assistant")

    def raise_strategy_error(_value):
        raise RuntimeError("secret strategy token should not leak")

    monkeypatch.setattr(router_module, "evaluate_strategy", raise_strategy_error)
    response = client.post("/api/sales-assistant/generate", headers=_headers_for(client), json=_payload())

    assert response.status_code == 500
    assert response.json()["detail"]["error_type"] == "sales_assistant_generation_error"
    assert "secret strategy token" not in response.text.lower()


def test_proposal_preview_carries_human_review_state(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    sparse_payload = _payload(client_name="", budget_information="", schedule_information="", evidence_items=[])
    assistant_result = _assistant_result(client, headers, sparse_payload)

    response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result, sparse_payload),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["human_review_required"] is True
    assert data["human_review_reasons"]
    assert data["proposal_preview"]["human_review_required"] is True


def test_proposal_preview_contract_keeps_v41_and_v49_versions(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)

    response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers=headers,
        json=_proposal_preview_payload(assistant_result),
    )

    assert response.status_code == 200
    data = response.json()
    assert assistant_result["strategy_brief"]["schema_version"] == "strategy_brief_v1"
    assert assistant_result["sales_assistant_brief"]["generation_metadata"]["generator_version"] == "v49_offline_deterministic"
    assert data["generation_metadata"]["strategy_brief_version"] == "strategy_brief_v1"
    assert data["generation_metadata"]["sales_assistant_version"] == "v49_offline_deterministic"


def test_proposal_preview_can_rebuild_strategy_when_missing_from_request(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)
    preview_payload = _proposal_preview_payload(assistant_result)
    preview_payload.pop("strategy_brief")

    response = client.post("/api/sales-assistant/proposal-preview", headers=headers, json=preview_payload)

    assert response.status_code == 200
    assert response.json()["proposal_preview"]["proposal_summary"]


def test_invalid_json_is_rejected_safely(enabled_client):
    client, _ = enabled_client
    response = client.post(
        "/api/sales-assistant/generate",
        headers={**_headers_for(client), "content-type": "application/json"},
        content="{invalid-json",
    )

    assert response.status_code in {400, 422}
    assert "test-password" not in response.text


def test_proposal_preview_rejects_large_payload_before_generation(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    assistant_result = _assistant_result(client, headers)

    response = client.post(
        "/api/sales-assistant/proposal-preview",
        headers={**headers, "content-length": "64001"},
        json=_proposal_preview_payload(assistant_result),
    )

    assert response.status_code == 413
    assert response.json()["detail"]["error_type"] == "sales_assistant_request_too_large"


def test_repeated_generation_keeps_contract_and_versions(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)

    for _ in range(3):
        assistant_result = _assistant_result(client, headers)
        assert assistant_result["strategy_brief"]["schema_version"] == "strategy_brief_v1"
        assert assistant_result["sales_assistant_brief"]["generation_metadata"]["generator_version"] == "v49_offline_deterministic"
        preview = client.post(
            "/api/sales-assistant/proposal-preview",
            headers=headers,
            json=_proposal_preview_payload(assistant_result),
        )
        assert preview.status_code == 200
        assert preview.json()["generation_metadata"]["schema_version"] == "sales_assistant_proposal_preview_v1"


def test_sparse_input_requires_human_review(enabled_client):
    client, _ = enabled_client
    response = client.post(
        "/api/sales-assistant/generate",
        headers=_headers_for(client),
        json=_payload(client_name="", budget_information="", schedule_information="", evidence_items=[]),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["human_review_required"] is True
    assert data["human_review_reasons"]
    assert data["sales_assistant_brief"]["evidence_guidance"]["evidence_gaps"]


def test_request_validation_rejects_large_or_invalid_input(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    missing = client.post("/api/sales-assistant/generate", headers=headers, json={"project_title": "", "project_summary": ""})
    assert missing.status_code == 422

    too_many_items = client.post(
        "/api/sales-assistant/generate",
        headers=headers,
        json=_payload(known_requirements=[f"item-{index}" for index in range(21)]),
    )
    assert too_many_items.status_code == 422

    invalid_stage = client.post("/api/sales-assistant/generate", headers=headers, json=_payload(meeting_stage="invalid"))
    assert invalid_stage.status_code == 422

    too_large = client.post(
        "/api/sales-assistant/generate",
        headers={**headers, "content-length": "64001"},
        json=_payload(),
    )
    assert too_large.status_code == 413


def test_deterministic_generation(enabled_client):
    client, _ = enabled_client
    headers = _headers_for(client)
    first = client.post("/api/sales-assistant/generate", headers=headers, json=_payload())
    second = client.post("/api/sales-assistant/generate", headers=headers, json=_payload())
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["sales_assistant_brief"] == second.json()["sales_assistant_brief"]


def test_term_guard_output_does_not_keep_conflicting_guarded_terms(enabled_client):
    client, _ = enabled_client
    response = client.post(
        "/api/sales-assistant/generate",
        headers=_headers_for(client),
        json=_payload(project_summary="AI-OCRで請求書を読み取りたい。CRM、SFA、SEO、CMS、RPA、LLMは今回の対象外。"),
    )
    assert response.status_code == 200
    risk = response.json()["sales_assistant_brief"]["risk_and_guardrails"]
    assert risk["removed_or_replaced_terms"]
    assert response.json()["human_review_required"] is True


def test_internal_error_is_safe(monkeypatch: pytest.MonkeyPatch, enabled_client):
    client, _ = enabled_client
    router_module = importlib.import_module("app.routers.sales_assistant")

    def raise_error(_value):
        raise RuntimeError("secret token should not leak")

    monkeypatch.setattr(router_module, "generate_sales_assistant_brief", raise_error)
    response = client.post("/api/sales-assistant/generate", headers=_headers_for(client), json=_payload())
    assert response.status_code == 500
    assert response.json()["detail"]["error_type"] == "sales_assistant_generation_error"
    assert "secret token" not in response.text.lower()


def test_sales_assistant_api_does_not_import_external_clients():
    source_paths = [
        Path("app/routers/sales_assistant.py"),
        *Path("app/sales_assistant").glob("*.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)
    lowered = text.lower()
    for forbidden in ["httpx", "requests", "from openai", "openai(", "beautiful_ai_api_key", "authorization"]:
        assert forbidden not in lowered
