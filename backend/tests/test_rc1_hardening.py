import importlib
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _client_with_env(monkeypatch, tmp_path: Path, **overrides: str) -> TestClient:
    db_path = tmp_path / "rc1.db"
    defaults = {
        "DATABASE_URL": f"sqlite:///{db_path}",
        "USE_MOCK_AI": "true",
        "APP_AUTH_SECRET": "test-secret",
        "INITIAL_ADMIN_EMAIL": "admin@example.com",
        "INITIAL_ADMIN_PASSWORD": "test-password",
        "CORS_ORIGINS": "http://localhost:3000",
        "RATE_LIMIT_LOGIN_LIMIT": "1000",
        "RATE_LIMIT_GENERATION_LIMIT": "1000",
        "RATE_LIMIT_ADMIN_LIMIT": "1000",
    }
    defaults.update(overrides)
    for key, value in defaults.items():
        monkeypatch.setenv(key, value)
    _reload_app_modules()
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def _login(client: TestClient, email: str = "admin@example.com", password: str = "test-password") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_runtime_maintenance_blocks_generation_but_allows_read(client: TestClient, admin_headers: dict[str, str], sample_proposal_payload: dict) -> None:
    enabled = client.patch(
        "/api/pilot/maintenance",
        headers=admin_headers,
        json={"enabled": True, "reason": "RC1 hardening test"},
    )
    assert enabled.status_code == 200

    blocked = client.post("/api/analyze", headers=admin_headers, json=sample_proposal_payload)
    assert blocked.status_code == 503
    body = blocked.json()
    assert body["error_type"] == "maintenance_mode"
    assert body["request_id"]

    health = client.get("/health")
    assert health.status_code == 200
    crm = client.get("/api/projects/crm", headers=admin_headers)
    assert crm.status_code == 200

    audits = client.get("/api/logs/audit", headers=admin_headers)
    assert audits.status_code == 200
    assert any(log["event_type"] == "maintenance_reject" for log in audits.json()["logs"])


def test_env_maintenance_cannot_be_disabled_from_screen(monkeypatch, tmp_path: Path) -> None:
    with _client_with_env(monkeypatch, tmp_path, MAINTENANCE_MODE="true") as client:
        headers = _login(client)
        response = client.patch(
            "/api/pilot/maintenance",
            headers=headers,
            json={"enabled": False, "reason": "try disable from screen"},
        )
        assert response.status_code == 409


def test_rate_limit_returns_429_and_retry_after(monkeypatch, tmp_path: Path) -> None:
    with _client_with_env(monkeypatch, tmp_path, RATE_LIMIT_LOGIN_LIMIT="2", RATE_LIMIT_LOGIN_WINDOW_SECONDS="60") as client:
        for _ in range(2):
            response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"})
            assert response.status_code == 401
        limited = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "wrong"})
        assert limited.status_code == 429
        assert limited.headers.get("Retry-After")
        assert limited.json()["error_type"] == "rate_limit"


def test_auth_version_rejects_old_token_after_role_change(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "member@example.com", "password": "member-password", "role": "member"},
    )
    assert create_response.status_code == 200
    member_headers = _login(client, "member@example.com", "member-password")

    from app.db import get_db

    with get_db() as db:
        db.execute("UPDATE users SET role = 'viewer', auth_version = auth_version + 1 WHERE email = ?", ("member@example.com",))

    status = client.get("/api/auth/status", headers=member_headers)
    assert status.status_code == 401


def test_disabled_user_token_is_rejected(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "disabled@example.com", "password": "member-password", "role": "member"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["id"]
    member_headers = _login(client, "disabled@example.com", "member-password")
    patch = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"is_active": False})
    assert patch.status_code == 200

    status = client.get("/api/auth/status", headers=member_headers)
    assert status.status_code == 401


def test_alembic_migration_applies_to_empty_sqlite(monkeypatch, tmp_path: Path) -> None:
    from alembic import command
    from alembic.config import Config

    db_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "test-password")
    _reload_app_modules()

    config = Config(str(Path.cwd() / "alembic.ini"))
    command.upgrade(config, "head")

    import sqlite3

    with sqlite3.connect(db_path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()}
        assert "users" in tables
        assert "projects" in tables
        assert "quality_gates" in tables
        assert "alembic_version" in tables
