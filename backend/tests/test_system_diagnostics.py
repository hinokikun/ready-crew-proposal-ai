import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _client_with_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **overrides: str) -> TestClient:
    env = {
        "DATABASE_URL": f"sqlite:///{tmp_path / 'diagnostics-test.db'}",
        "USE_MOCK_AI": "false",
        "OPENAI_API_KEY": "dummy-openai-key",
        "APP_AUTH_SECRET": "test-secret",
        "INITIAL_ADMIN_EMAIL": "admin@example.com",
        "INITIAL_ADMIN_PASSWORD": "test-password",
        "CORS_ORIGINS": "http://localhost:3000",
        "RATE_LIMIT_LOGIN_LIMIT": "1000",
        "RATE_LIMIT_GENERATION_LIMIT": "1000",
        "RATE_LIMIT_ADMIN_LIMIT": "1000",
        "BEAUTIFUL_AI_ENABLED": "true",
        "BEAUTIFUL_AI_API_KEY": "dummy-beautiful-key",
        "BEAUTIFUL_AI_MOCK": "false",
        "BEAUTIFUL_AI_API_MODE": "prompt",
    }
    env.update(overrides)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    _reload_app_modules()
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def test_system_diagnostics_reports_core_dependencies_without_secrets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with _client_with_env(monkeypatch, tmp_path) as client:
        response = client.get("/api/system/diagnostics", headers={"X-Frontend-Api-Base-Url": "http://localhost:8000"})

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "ok"
    assert body["backend"]["reachable"] is True
    assert body["database"]["connected"] is True
    assert body["auth"]["available"] is True
    assert body["openai"]["enabled"] is True
    assert body["openai"]["configured"] is True
    assert body["beautiful_ai"]["enabled"] is True
    assert body["beautiful_ai"]["configured"] is True
    assert body["beautiful_ai"]["mock"] is False
    assert body["beautiful_ai"]["api_mode"] == "prompt"
    assert body["frontend"]["api_base_url"] == "http://localhost:8000"
    assert {item["name"] for item in body["checks"]} >= {"backend", "database", "auth", "openai", "beautiful_ai", "frontend"}
    serialized = str(body).lower()
    assert "dummy-openai-key" not in serialized
    assert "dummy-beautiful-key" not in serialized
    assert "test-secret" not in serialized


def test_system_diagnostics_warns_when_beautiful_ai_is_not_configured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with _client_with_env(
        monkeypatch,
        tmp_path,
        BEAUTIFUL_AI_ENABLED="false",
        BEAUTIFUL_AI_API_KEY="",
        OPENAI_API_KEY="",
        USE_MOCK_AI="false",
    ) as client:
        response = client.get("/api/system/diagnostics")

    assert response.status_code == 200
    body = response.json()
    assert body["overall_status"] == "warning"
    assert body["beautiful_ai"]["enabled"] is False
    assert body["beautiful_ai"]["configured"] is False
    assert body["openai"]["configured"] is False
    assert any(item["name"] == "beautiful_ai" and item["status"] == "warning" for item in body["checks"])
