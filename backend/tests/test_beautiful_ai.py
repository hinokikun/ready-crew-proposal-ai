import importlib
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _client_with_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **overrides: str) -> TestClient:
    env = {
        "DATABASE_URL": f"sqlite:///{tmp_path / 'beautiful-test.db'}",
        "USE_MOCK_AI": "true",
        "APP_AUTH_SECRET": "test-secret",
        "INITIAL_ADMIN_EMAIL": "admin@example.com",
        "INITIAL_ADMIN_PASSWORD": "test-password",
        "CORS_ORIGINS": "http://localhost:3000",
        "RATE_LIMIT_LOGIN_LIMIT": "1000",
        "RATE_LIMIT_GENERATION_LIMIT": "1000",
        "RATE_LIMIT_ADMIN_LIMIT": "1000",
    }
    env.update(overrides)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    _reload_app_modules()
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def _login(client: TestClient, email: str = "admin@example.com", password: str = "test-password") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    password = "test-password"
    response = client.post("/api/users", headers=admin_headers, json={"email": email, "password": password, "role": role})
    assert response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def _complete_quality_gate(client: TestClient, headers: dict[str, str], project_id: str) -> None:
    response = client.patch(
        f"/api/quality-gates/{project_id}/complete",
        headers=headers,
        json={"checklist_items": ["company", "budget", "deadline", "human_review"]},
    )
    assert response.status_code == 200
    assert response.json()["gate"]["download_unlocked"] is True


def _beautiful_payload(sample_pptx_payload: dict[str, Any], project_id: str) -> dict[str, Any]:
    return {**sample_pptx_payload, "project_id": project_id}


def test_beautiful_ai_status_disabled(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.get("/api/beautiful-ai/status", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["api_reachable"] is True
    assert body["route_found"] is True
    assert body["api_mode"] == "prompt"
    assert body["resolved_endpoint"].endswith("/generatePresentation")
    assert "backend_version" in body
    assert "last_success_at" in body
    assert "last_error_type" in body
    assert "api_key" not in str(body).lower()


def test_beautiful_ai_diagnostics_returns_settings_and_recent_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_env(
        monkeypatch,
        tmp_path,
        BEAUTIFUL_AI_ENABLED="true",
        BEAUTIFUL_AI_MOCK="true",
        BEAUTIFUL_AI_DEFAULT_THEME_ID="minimal",
        BEAUTIFUL_AI_WORKSPACE_ID="workspace-demo",
    ) as client:
        headers = _login(client)
        project_id = "diagnostics-history-project"
        _complete_quality_gate(client, headers, project_id)

        create_response = client.post("/api/beautiful-ai/presentations", headers=headers, json=_beautiful_payload(sample_pptx_payload, project_id))
        assert create_response.status_code == 200

        diagnostics = client.get("/api/beautiful-ai/diagnostics", headers=headers)
        assert diagnostics.status_code == 200
        body = diagnostics.json()
        assert body["enabled"] is True
        assert body["api_mode"] == "prompt"
        assert body["theme_id"] == "minimal"
        assert body["workspace_id"] == "workspace-demo"
        assert body["last_http_status"] == 200
        assert body["history"]
        assert body["history"][0]["project_id"] == project_id
        assert "api_key" not in str(body).lower()


def test_beautiful_ai_connection_test_uses_empty_payload_and_saves_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    with _client_with_env(
        monkeypatch,
        tmp_path,
        BEAUTIFUL_AI_ENABLED="true",
        BEAUTIFUL_AI_MOCK="false",
        BEAUTIFUL_AI_API_KEY="dummy-beautiful-ai-key",
    ) as client:
        service = importlib.import_module("app.services.beautiful_ai_service")
        captured: dict[str, Any] = {}

        class FakeResponse:
            status_code = 400
            headers = {"Content-Type": "application/json"}
            text = '{"error":"prompt is required"}'

            def json(self) -> dict[str, Any]:
                return {}

        class FakeClient:
            def __init__(self, *_: Any, **__: Any) -> None:
                pass

            async def __aenter__(self) -> "FakeClient":
                return self

            async def __aexit__(self, *_: Any) -> None:
                return None

            async def post(self, *_: Any, **kwargs: Any) -> FakeResponse:
                captured["json"] = kwargs["json"]
                captured["authorization"] = kwargs["headers"]["Authorization"]
                return FakeResponse()

        monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)
        headers = _login(client)

        response = client.post("/api/beautiful-ai/diagnostics/test", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["ok"] is True
        assert body["http_status"] == 400
        assert body["response_text"].startswith('{"error"')
        assert captured["json"] == {}
        assert captured["authorization"] == "Bearer dummy-beautiful-ai-key"

        diagnostics = client.get("/api/beautiful-ai/diagnostics", headers=headers)
        assert diagnostics.status_code == 200
        history = diagnostics.json()["history"]
        assert history[0]["project_id"] == "__diagnostic__"
        assert history[0]["status"] == "diagnostic_ok"
        assert history[0]["http_status"] == 400
        assert "dummy-beautiful-ai-key" not in str(diagnostics.json())


def test_beautiful_ai_diagnostics_requires_admin_or_manager(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    with _client_with_env(monkeypatch, tmp_path, BEAUTIFUL_AI_ENABLED="true", BEAUTIFUL_AI_MOCK="true") as client:
        admin_headers = _login(client)
        member_headers = _create_user_and_login(client, admin_headers, "diagnostic-member@example.com", "member")
        assert client.get("/api/beautiful-ai/diagnostics", headers=member_headers).status_code == 403
        assert client.post("/api/beautiful-ai/diagnostics/test", headers=member_headers).status_code == 403


def test_beautiful_ai_mock_success_and_duplicate_prevention(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_env(monkeypatch, tmp_path, BEAUTIFUL_AI_ENABLED="true", BEAUTIFUL_AI_MOCK="true") as client:
        headers = _login(client)
        project_id = "beautiful-mock-project"
        _complete_quality_gate(client, headers, project_id)
        payload = _beautiful_payload(sample_pptx_payload, project_id)

        first = client.post("/api/beautiful-ai/presentations", headers=headers, json=payload)
        second = client.post("/api/beautiful-ai/presentations", headers=headers, json=payload)
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["presentation_id"] == second.json()["presentation_id"]
        assert first.json()["editor_url"].startswith("https://www.beautiful.ai/")
        assert first.json()["player_url"].startswith("https://www.beautiful.ai/")

        records = client.get(f"/api/beautiful-ai/presentations/{project_id}", headers=headers)
        assert records.status_code == 200
        assert len(records.json()["presentations"]) == 1


def test_beautiful_ai_presentations_are_separated_by_workspace(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_env(monkeypatch, tmp_path, BEAUTIFUL_AI_ENABLED="true", BEAUTIFUL_AI_MOCK="true") as client:
        headers = _login(client)
        project_id = "beautiful-workspace-project"
        _complete_quality_gate(client, headers, project_id)

        default_create = client.post("/api/beautiful-ai/presentations", headers=headers, json=_beautiful_payload(sample_pptx_payload, project_id))
        assert default_create.status_code == 200
        default_records = client.get(f"/api/beautiful-ai/presentations/{project_id}", headers=headers)
        assert default_records.status_code == 200
        assert len(default_records.json()["presentations"]) == 1

        org_response = client.post("/api/organizations", headers=headers, json={"name": "Beautiful Org", "slug": "beautiful-org"})
        assert org_response.status_code == 200
        organization_id = int(org_response.json()["organization"]["id"])
        context = client.get("/api/organizations/context", headers=headers)
        workspace_id = next(item["workspace_id"] for item in context.json()["available"] if item["organization_id"] == organization_id)
        switched = client.patch(
            "/api/organizations/context",
            headers=headers,
            json={"organization_id": organization_id, "workspace_id": workspace_id},
        )
        assert switched.status_code == 200

        separated_records = client.get(f"/api/beautiful-ai/presentations/{project_id}", headers=headers)
        assert separated_records.status_code == 200
        assert separated_records.json()["presentations"] == []

        _complete_quality_gate(client, headers, project_id)
        workspace_create = client.post(
            "/api/beautiful-ai/presentations",
            headers=headers,
            json=_beautiful_payload({**sample_pptx_payload, "force_new": True}, project_id),
        )
        assert workspace_create.status_code == 200
        workspace_records = client.get(f"/api/beautiful-ai/presentations/{project_id}", headers=headers)
        assert len(workspace_records.json()["presentations"]) == 1


def test_beautiful_ai_member_can_create_with_real_api_mode(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_env(
        monkeypatch,
        tmp_path,
        BEAUTIFUL_AI_ENABLED="true",
        BEAUTIFUL_AI_MOCK="false",
        BEAUTIFUL_AI_API_KEY="dummy-beautiful-ai-key",
    ) as client:
        service = importlib.import_module("app.services.beautiful_ai_service")

        async def fake_post(_: dict[str, Any]) -> dict[str, Any]:
            return {
                "id": "real-mode-test",
                "editor_url": "https://www.beautiful.ai/editor/real-mode-test",
                "player_url": "https://www.beautiful.ai/player/real-mode-test",
                "status": "created",
            }

        monkeypatch.setattr(service, "_post_payload", fake_post)
        admin_headers = _login(client)
        member_headers = _create_user_and_login(client, admin_headers, "beautiful-member@example.com", "member")
        project_id = "member-real-mode-project"
        _complete_quality_gate(client, member_headers, project_id)

        response = client.post(
            "/api/beautiful-ai/presentations",
            headers=member_headers,
            json=_beautiful_payload(sample_pptx_payload, project_id),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["presentation_id"] == "real-mode-test"
        assert body["editor_url"].startswith("https://www.beautiful.ai/")


def test_beautiful_ai_requires_completed_quality_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_env(monkeypatch, tmp_path, BEAUTIFUL_AI_ENABLED="true", BEAUTIFUL_AI_MOCK="true") as client:
        headers = _login(client)
        response = client.post(
            "/api/beautiful-ai/presentations",
            headers=headers,
            json=_beautiful_payload(sample_pptx_payload, "gate-incomplete-project"),
        )
        assert response.status_code == 409
        assert response.json()["detail"]["error_type"] == "quality_gate_incomplete"


def test_beautiful_ai_viewer_cannot_create(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_env(monkeypatch, tmp_path, BEAUTIFUL_AI_ENABLED="true", BEAUTIFUL_AI_MOCK="true") as client:
        admin_headers = _login(client)
        viewer_headers = _create_user_and_login(client, admin_headers, "beautiful-viewer@example.com", "viewer")
        _complete_quality_gate(client, admin_headers, "viewer-project")
        response = client.post(
            "/api/beautiful-ai/presentations",
            headers=viewer_headers,
            json=_beautiful_payload(sample_pptx_payload, "viewer-project"),
        )
        assert response.status_code == 403


def test_beautiful_ai_runtime_maintenance_blocks_create(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_env(monkeypatch, tmp_path, BEAUTIFUL_AI_ENABLED="true", BEAUTIFUL_AI_MOCK="true") as client:
        headers = _login(client)
        project_id = "maintenance-project"
        _complete_quality_gate(client, headers, project_id)
        enabled = client.patch("/api/pilot/maintenance", headers=headers, json={"enabled": True, "reason": "test"})
        assert enabled.status_code == 200
        response = client.post("/api/beautiful-ai/presentations", headers=headers, json=_beautiful_payload(sample_pptx_payload, project_id))
        assert response.status_code == 503


@pytest.mark.parametrize(
    ("status_code", "error_type", "expected_status"),
    [
        (400, "beautiful_ai_bad_request", 400),
        (401, "beautiful_ai_invalid_api_key", 401),
        (403, "beautiful_ai_access_not_enabled", 403),
        (502, "beautiful_ai_endpoint_not_found", 502),
        (429, "beautiful_ai_rate_limit", 429),
        (502, "beautiful_ai_service_error", 502),
    ],
)
def test_beautiful_ai_safe_error_mapping(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
    status_code: int,
    error_type: str,
    expected_status: int,
) -> None:
    with _client_with_env(
        monkeypatch,
        tmp_path,
        BEAUTIFUL_AI_ENABLED="true",
        BEAUTIFUL_AI_MOCK="false",
        BEAUTIFUL_AI_API_KEY="dummy-beautiful-ai-key",
    ) as client:
        service = importlib.import_module("app.services.beautiful_ai_service")

        async def fake_post(_: dict[str, Any]) -> dict[str, Any]:
            raise service.BeautifulAiServiceError(status_code=status_code, error_type=error_type, message="safe message", retry_after_seconds=30 if status_code == 429 else None)

        monkeypatch.setattr(service, "_post_payload", fake_post)
        headers = _login(client)
        project_id = f"safe-error-{status_code}"
        _complete_quality_gate(client, headers, project_id)
        response = client.post("/api/beautiful-ai/presentations", headers=headers, json=_beautiful_payload(sample_pptx_payload, project_id))
        assert response.status_code == expected_status
        body = response.json()
        serialized = str(body).lower()
        detail = body.get("detail") if isinstance(body.get("detail"), dict) else body
        assert detail["error_type"] == error_type
        assert "dummy-beautiful-ai-key" not in serialized
        assert "authorization" not in serialized


def test_beautiful_ai_extracts_nested_data_response() -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    result = service._extract_api_result(
        {
            "data": {
                "presentationId": "nested-presentation",
                "editorUrl": "https://www.beautiful.ai/editor/nested-presentation",
                "playerUrl": "https://www.beautiful.ai/player/nested-presentation",
                "status": "created",
                "title": "Nested response",
            }
        },
        "Fallback title",
    )
    assert result == {
        "presentation_id": "nested-presentation",
        "editor_url": "https://www.beautiful.ai/editor/nested-presentation",
        "player_url": "https://www.beautiful.ai/player/nested-presentation",
        "status": "created",
        "title": "Nested response",
    }


def test_beautiful_ai_payload_uses_sections_content_and_blocks(sample_pptx_payload: dict[str, Any]) -> None:
    mapper = importlib.import_module("app.beautiful_ai.presentation_mapper")
    schemas = importlib.import_module("app.beautiful_ai.schemas")
    request = schemas.BeautifulAiPresentationRequest(**_beautiful_payload(sample_pptx_payload, "payload-shape-project"))

    payload = mapper.map_to_beautiful_ai_payload(request).dict()

    assert payload["title"]
    assert "日本語" in payload["prompt"]
    assert "入力されていない数値" in payload["prompt"]
    assert payload["content"].startswith("#")
    assert payload["sections"]
    assert payload["sections"][0]["content"]["blocks"][0]["type"] == "paragraph"
    assert payload["slides"]
    assert payload["slides"][0]["sections"]
    assert payload["slides"][0]["content"]["blocks"]
    assert payload["slides"][0]["blocks"]
    assert "body" not in payload["slides"][0]


def test_beautiful_ai_clean_payload_removes_empty_optional_fields() -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")

    payload = service._clean_payload(
        {
            "title": "Proposal",
            "themeId": "",
            "workspaceId": "",
            "slides": [{"title": "Slide", "folderId": "", "blocks": [{"type": "heading", "content": "Slide"}]}],
        }
    )

    assert "themeId" not in payload
    assert "workspaceId" not in payload
    assert "folderId" not in payload["slides"][0]
    assert payload["slides"][0]["blocks"][0]["content"] == "Slide"


def test_beautiful_ai_prompt_api_resolves_official_url() -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    original_base = service.settings.beautiful_ai_base_url
    original_mode = service.settings.beautiful_ai_api_mode
    try:
        object.__setattr__(service.settings, "beautiful_ai_base_url", "https://beautiful.ai/api/v1/")
        object.__setattr__(service.settings, "beautiful_ai_api_mode", "prompt")
        assert service._endpoint() == "https://www.beautiful.ai/api/v1/generatePresentation"
    finally:
        object.__setattr__(service.settings, "beautiful_ai_base_url", original_base)
        object.__setattr__(service.settings, "beautiful_ai_api_mode", original_mode)


def test_beautiful_ai_structured_mode_uses_create_presentation() -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    original_base = service.settings.beautiful_ai_base_url
    original_mode = service.settings.beautiful_ai_api_mode
    try:
        object.__setattr__(service.settings, "beautiful_ai_base_url", "https://beautiful.ai/api/v1/createPresentation")
        object.__setattr__(service.settings, "beautiful_ai_api_mode", "structured")
        assert service._endpoint() == "https://www.beautiful.ai/api/v1/createPresentation"
    finally:
        object.__setattr__(service.settings, "beautiful_ai_base_url", original_base)
        object.__setattr__(service.settings, "beautiful_ai_api_mode", original_mode)


def test_beautiful_ai_prompt_request_uses_only_prompt_and_theme() -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    original_mode = service.settings.beautiful_ai_api_mode
    try:
        object.__setattr__(service.settings, "beautiful_ai_api_mode", "prompt")
        payload = service._api_request_payload(
            {
                "prompt": "Create a proposal deck",
                "themeId": "minimal",
                "workspaceId": "workspace-ignored",
                "slides": [{"title": "Ignored"}],
            }
        )
        assert payload == {"prompt": "Create a proposal deck", "themeId": "minimal"}
    finally:
        object.__setattr__(service.settings, "beautiful_ai_api_mode", original_mode)


def test_beautiful_ai_prompt_request_omits_empty_theme() -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    original_mode = service.settings.beautiful_ai_api_mode
    try:
        object.__setattr__(service.settings, "beautiful_ai_api_mode", "prompt")
        payload = service._api_request_payload({"prompt": "Create a proposal deck", "themeId": ""})
        assert payload == {"prompt": "Create a proposal deck"}
    finally:
        object.__setattr__(service.settings, "beautiful_ai_api_mode", original_mode)


def test_beautiful_ai_prompt_request_requires_prompt() -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    original_mode = service.settings.beautiful_ai_api_mode
    try:
        object.__setattr__(service.settings, "beautiful_ai_api_mode", "prompt")
        with pytest.raises(service.BeautifulAiServiceError) as exc_info:
            service._api_request_payload({"slides": [{"title": "Missing prompt"}]})
    finally:
        object.__setattr__(service.settings, "beautiful_ai_api_mode", original_mode)
    assert exc_info.value.error_type == "beautiful_ai_prompt_required"


@pytest.mark.anyio
async def test_beautiful_ai_post_payload_sends_bearer_prompt_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    captured: dict[str, Any] = {}
    original_key = service.settings.beautiful_ai_api_key
    original_mode = service.settings.beautiful_ai_api_mode

    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "application/json"}
        text = '{"presentationId":"prompt-created"}'

        def json(self) -> dict[str, Any]:
            return {"presentationId": "prompt-created", "status": "created"}

    class FakeClient:
        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_: Any) -> None:
            return None

        async def post(self, *_: Any, **kwargs: Any) -> FakeResponse:
            captured["headers"] = kwargs["headers"]
            captured["json"] = kwargs["json"]
            return FakeResponse()

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)
    try:
        object.__setattr__(service.settings, "beautiful_ai_api_key", "dummy-beautiful-ai-key")
        object.__setattr__(service.settings, "beautiful_ai_api_mode", "prompt")
        result = await service._post_payload({"prompt": "Create a proposal deck", "themeId": ""})
    finally:
        object.__setattr__(service.settings, "beautiful_ai_api_key", original_key)
        object.__setattr__(service.settings, "beautiful_ai_api_mode", original_mode)

    assert result["presentationId"] == "prompt-created"
    assert captured["headers"]["Authorization"] == "Bearer dummy-beautiful-ai-key"
    assert captured["json"] == {"prompt": "Create a proposal deck"}


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("external_status", "expected_error_type", "expected_service_status"),
    [
        (400, "beautiful_ai_bad_request", 400),
        (401, "beautiful_ai_invalid_api_key", 401),
        (403, "beautiful_ai_access_not_enabled", 403),
        (404, "beautiful_ai_endpoint_not_found", 502),
        (429, "beautiful_ai_rate_limit", 429),
        (500, "beautiful_ai_service_error", 502),
    ],
)
async def test_beautiful_ai_post_payload_maps_external_status(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    external_status: int,
    expected_error_type: str,
    expected_service_status: int,
) -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    caplog.set_level("ERROR")

    class FakeResponse:
        status_code = external_status
        headers = {"Retry-After": "30", "Content-Type": "application/json"} if external_status == 429 else {"Content-Type": "application/json"}
        text = '{"error":"validation failed"}'

        def json(self) -> dict[str, Any]:
            return {}

    class FakeClient:
        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_: Any) -> None:
            return None

        async def post(self, *_: Any, **__: Any) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)

    with pytest.raises(service.BeautifulAiServiceError) as exc_info:
        await service._post_payload({"prompt": "Create a proposal deck"})

    assert exc_info.value.error_type == expected_error_type
    assert exc_info.value.status_code == expected_service_status
    if external_status == 400:
        assert "validation failed" in caplog.text


@pytest.mark.anyio
async def test_beautiful_ai_post_payload_maps_redirect_and_logs_safe_diagnostics(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    service = importlib.import_module("app.services.beautiful_ai_service")
    original_key = service.settings.beautiful_ai_api_key
    caplog.set_level("ERROR")

    class FakeResponse:
        status_code = 301
        headers = {
            "Content-Type": "",
            "Location": "https://www.beautiful.ai/api/v1/generatePresentation",
            "Set-Cookie": "session=hidden",
        }
        text = ""

        def json(self) -> dict[str, Any]:
            return {}

    class FakeClient:
        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *_: Any) -> None:
            return None

        async def post(self, *_: Any, **__: Any) -> FakeResponse:
            return FakeResponse()

    monkeypatch.setattr(service.httpx, "AsyncClient", FakeClient)
    try:
        object.__setattr__(service.settings, "beautiful_ai_api_key", "dummy-beautiful-ai-key")
        with pytest.raises(service.BeautifulAiServiceError) as exc_info:
            await service._post_payload({"prompt": "Secret proposal prompt", "themeId": "minimal"})
    finally:
        object.__setattr__(service.settings, "beautiful_ai_api_key", original_key)

    assert exc_info.value.error_type == "beautiful_ai_redirect"
    assert exc_info.value.status_code == 502
    assert "request_json_safe" in caplog.text
    assert "request_headers_safe" in caplog.text
    assert "response_headers_safe" in caplog.text
    assert "<empty response body>" in caplog.text
    assert "Secret proposal prompt" not in caplog.text
    assert "dummy-beautiful-ai-key" not in caplog.text
    assert "session=hidden" not in caplog.text


def test_beautiful_ai_api_key_is_not_returned_or_stored(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    api_key_placeholder = "dummy-beautiful-ai-secret"
    with _client_with_env(
        monkeypatch,
        tmp_path,
        BEAUTIFUL_AI_ENABLED="true",
        BEAUTIFUL_AI_MOCK="true",
        BEAUTIFUL_AI_API_KEY="dummy-beautiful-ai-secret",
    ) as client:
        headers = _login(client)
        project_id = "secret-safety-project"
        _complete_quality_gate(client, headers, project_id)
        create_response = client.post("/api/beautiful-ai/presentations", headers=headers, json=_beautiful_payload(sample_pptx_payload, project_id))
        list_response = client.get(f"/api/beautiful-ai/presentations/{project_id}", headers=headers)
        audit_response = client.get("/api/logs/audit", headers=headers)
        combined = f"{create_response.text}\n{list_response.text}\n{audit_response.text}".lower()
        assert create_response.status_code == 200
        assert api_key_placeholder.lower() not in combined
        assert "authorization" not in combined
