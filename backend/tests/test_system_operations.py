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
        "DATABASE_URL": f"sqlite:///{tmp_path / 'system-operations.db'}",
        "USE_MOCK_AI": "true",
        "OPENAI_API_KEY": "dummy-openai-secret",
        "APP_AUTH_SECRET": "dummy-auth-secret",
        "INITIAL_ADMIN_EMAIL": "admin@example.com",
        "INITIAL_ADMIN_PASSWORD": "test-password",
        "CORS_ORIGINS": "http://localhost:3000",
        "BEAUTIFUL_AI_ENABLED": "true",
        "BEAUTIFUL_AI_API_KEY": "dummy-beautiful-secret",
        "BEAUTIFUL_AI_MOCK": "true",
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


def _admin_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-password"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _member_headers(client: TestClient) -> dict[str, str]:
    from app.db import get_db
    from app.security import hash_password

    with get_db() as db:
        db.execute(
            """
            INSERT INTO users (display_name, email, password_hash, role, is_active, current_organization_id, current_workspace_id)
            VALUES ('Member', 'member@example.com', ?, 'member', 1, 1, 1)
            """,
            (hash_password("member-password"),),
        )
    response = client.post("/api/auth/login", json={"email": "member@example.com", "password": "member-password"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_self_check_connection_tests_and_environment_are_admin_only_and_safe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with _client_with_env(monkeypatch, tmp_path) as client:
        admin_headers = _admin_headers(client)
        member_headers = _member_headers(client)

        forbidden = client.post("/api/system/self-check", headers=member_headers)
        assert forbidden.status_code == 403

        self_check = client.post("/api/system/self-check", headers=admin_headers)
        assert self_check.status_code == 200
        self_body = self_check.json()
        assert self_body["summary"]["total"] >= 8
        assert {item["name"] for item in self_body["checks"]} >= {"database", "auth", "pptx_generation", "pdf_generation"}

        connection = client.post("/api/system/connection-tests", headers=admin_headers, json={"checks": ["database", "beautiful_ai"]})
        assert connection.status_code == 200
        assert {item["name"] for item in connection.json()["checks"]} == {"database", "beautiful_ai_connection"}

        environment = client.get("/api/system/environment", headers=admin_headers)
        assert environment.status_code == 200
        names = {item["name"] for item in environment.json()["items"]}
        assert {"OPENAI_API_KEY", "BEAUTIFUL_AI_API_KEY", "APP_AUTH_SECRET", "DATABASE_URL"} <= names

        serialized = str({"self": self_body, "connection": connection.json(), "environment": environment.json()}).lower()
        assert "dummy-openai-secret" not in serialized
        assert "dummy-beautiful-secret" not in serialized
        assert "dummy-auth-secret" not in serialized


def test_admin_ai_logs_and_proposal_history_reuse_existing_safe_records(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with _client_with_env(monkeypatch, tmp_path) as client:
        headers = _admin_headers(client)
        from app.db import get_db

        with get_db() as db:
            admin = db.execute("SELECT id FROM users WHERE email = 'admin@example.com'").fetchone()
            user_id = int(admin["id"])
            db.execute(
                """
                INSERT INTO usage_logs (user_id, feature_name, input_length, output_type, status, error_type, organization_id, workspace_id)
                VALUES (?, '提案書生成', 120, 'pptx', 'success', '', 1, 1)
                """,
                (user_id,),
            )
            db.execute(
                """
                INSERT INTO projects (id, name, summary, organization_id, workspace_id)
                VALUES (1001, '安全確認案件', 'summary', 1, 1)
                """,
            )
            db.execute(
                """
                INSERT INTO proposal_histories (user_id, project_id, feature_name, input_length, output_type, status, error_type, organization_id, workspace_id)
                VALUES (?, 1001, 'Beautiful.ai', 80, 'beautiful-ai', 'success', '', 1, 1)
                """,
                (user_id,),
            )
            db.execute(
                """
                INSERT INTO beautiful_ai_presentations
                (project_id, user_id, presentation_id, title, editor_url, player_url, status, response_text, organization_id, workspace_id)
                VALUES ('1001', ?, 'firebase-like-id', '安全確認案件', 'https://www.beautiful.ai/editor/firebase-like-id', '', 'created',
                        '{"playerUrl":"https://beautiful.ai/player/official-player"}', 1, 1)
                """,
                (user_id,),
            )

        ai_logs = client.get("/api/admin/ai-logs?page=1&page_size=5", headers=headers)
        assert ai_logs.status_code == 200
        log_body = ai_logs.json()
        assert log_body["total"] >= 1
        assert all("admin@example.com" not in str(item) for item in log_body["items"])

        history = client.get("/api/admin/proposal-generation-history?page=1&page_size=5", headers=headers)
        assert history.status_code == 200
        history_body = history.json()
        assert history_body["total"] >= 1
        beautiful_items = [item for item in history_body["items"] if item["output_type"] == "beautiful-ai"]
        assert beautiful_items
        assert beautiful_items[0]["open_url"] == "https://beautiful.ai/player/official-player"
        serialized = str(history_body).lower()
        assert "dummy-beautiful-secret" not in serialized
        assert "password" not in serialized
