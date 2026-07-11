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
    assert "backend_version" in body
    assert "last_success_at" in body
    assert "last_error_type" in body
    assert "api_key" not in str(body).lower()


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
        (401, "beautiful_ai_unauthorized", 401),
        (403, "beautiful_ai_forbidden", 403),
        (429, "beautiful_ai_rate_limit", 429),
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
        BEAUTIFUL_AI_API_KEY="test-beautiful-key",
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
        assert "test-beautiful-key" not in serialized
        assert "authorization" not in serialized


def test_beautiful_ai_api_key_is_not_returned_or_stored(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    secret = "sk-beautiful-secret"
    with _client_with_env(
        monkeypatch,
        tmp_path,
        BEAUTIFUL_AI_ENABLED="true",
        BEAUTIFUL_AI_MOCK="true",
        BEAUTIFUL_AI_API_KEY=secret,
    ) as client:
        headers = _login(client)
        project_id = "secret-safety-project"
        _complete_quality_gate(client, headers, project_id)
        create_response = client.post("/api/beautiful-ai/presentations", headers=headers, json=_beautiful_payload(sample_pptx_payload, project_id))
        list_response = client.get(f"/api/beautiful-ai/presentations/{project_id}", headers=headers)
        audit_response = client.get("/api/logs/audit", headers=headers)
        combined = f"{create_response.text}\n{list_response.text}\n{audit_response.text}".lower()
        assert create_response.status_code == 200
        assert secret.lower() not in combined
        assert "authorization" not in combined
