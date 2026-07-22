import importlib
import logging
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _configure_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, email: str, password: str) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", email)
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", password)
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("RATE_LIMIT_LOGIN_LIMIT", "1000")
    monkeypatch.setenv("RATE_LIMIT_GENERATION_LIMIT", "1000")
    monkeypatch.setenv("RATE_LIMIT_ADMIN_LIMIT", "1000")
    monkeypatch.setenv("BEAUTIFUL_AI_ENABLED", "false")
    monkeypatch.setenv("BEAUTIFUL_AI_API_KEY", "")
    monkeypatch.setenv("BEAUTIFUL_AI_MOCK", "false")
    _reload_app_modules()


def test_initial_admin_created_on_startup_and_can_login(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _configure_env(monkeypatch, tmp_path, email="admin@example.com", password="test-password")
    main = importlib.import_module("app.main")
    with TestClient(main.app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "test-password", "login_mode": "admin"},
        )
        assert response.status_code == 200
        assert response.json()["user"]["role"] == "admin"

        from app.db import get_db

        with get_db() as db:
            user = db.execute("SELECT * FROM users WHERE email = ?", ("admin@example.com",)).fetchone()
            assert user is not None
            assert user["role"] == "admin"
            assert user["is_active"] == 1
            assert user["password_hash"]
            assert user["password_hash"] != "test-password"
            membership = db.execute(
                """
                SELECT membership_role
                FROM organization_memberships
                WHERE user_id = ? AND organization_id = 1 AND workspace_id = 1
                """,
                (int(user["id"]),),
            ).fetchone()
            assert membership is not None
            assert membership["membership_role"] == "organization_admin"


def test_initial_admin_seed_does_not_overwrite_existing_user(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _configure_env(monkeypatch, tmp_path, email="admin@example.com", password="new-password")
    from app.db import get_db, init_db
    from app.repositories import ensure_initial_admin
    from app.security import hash_password, verify_password

    init_db()
    original_hash = hash_password("old-password")
    with get_db() as db:
        db.execute(
            "INSERT INTO users (display_name, email, password_hash, role, is_active) VALUES (?, ?, ?, 'member', 1)",
            ("Existing User", "admin@example.com", original_hash),
        )
        ensure_initial_admin(db)
        rows = db.execute("SELECT * FROM users WHERE email = ?", ("admin@example.com",)).fetchall()
        assert len(rows) == 1
        user = rows[0]
        assert user["role"] == "member"
        assert verify_password("old-password", user["password_hash"])
        assert not verify_password("new-password", user["password_hash"])


def test_initial_admin_logs_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    email = "safe-admin@example.com"
    password = "secret-bootstrap-password"
    _configure_env(monkeypatch, tmp_path, email=email, password=password)
    from app.db import get_db, init_db
    from app.repositories import ensure_initial_admin

    init_db()
    caplog.set_level(logging.INFO, logger="app.repository_parts.users")
    with get_db() as db:
        ensure_initial_admin(db)

    logs = "\n".join(record.getMessage() for record in caplog.records)
    assert "initial_admin_created" in logs
    assert password not in logs
    assert email not in logs
    assert "s***n@example.com" in logs
