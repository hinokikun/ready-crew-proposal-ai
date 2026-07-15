from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]


def _login(client: TestClient, email: str, password: str = "test-password") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _create_user(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    response = client.post("/api/users", headers=admin_headers, json={"email": email, "password": "test-password", "role": role})
    assert response.status_code == 200
    return _login(client, email)


def _create_org_and_switch(client: TestClient, headers: dict[str, str], name: str, slug: str) -> tuple[int, int]:
    response = client.post("/api/organizations", headers=headers, json={"name": name, "slug": slug})
    assert response.status_code == 200
    organization_id = int(response.json()["organization"]["id"])
    context = client.get("/api/organizations/context", headers=headers)
    assert context.status_code == 200
    workspace_id = next(item["workspace_id"] for item in context.json()["available"] if item["organization_id"] == organization_id)
    switched = client.patch("/api/organizations/context", headers=headers, json={"organization_id": organization_id, "workspace_id": workspace_id})
    assert switched.status_code == 200
    return organization_id, int(workspace_id)


def test_admin_aggregations_default_to_workspace_and_require_system_scope(client: TestClient, admin_headers: dict[str, str]) -> None:
    first = client.post(
        "/api/analytics/events",
        headers=admin_headers,
        json={"session_id": "acceptance-a1", "event_name": "proposal_generated", "feature_name": "proposal", "status": "success"},
    )
    assert first.status_code == 200

    _create_org_and_switch(client, admin_headers, "Acceptance Org B", "acceptance-b")
    second = client.post(
        "/api/analytics/events",
        headers=admin_headers,
        json={"session_id": "acceptance-b1", "event_name": "summary_ppt_download", "feature_name": "summary_ppt", "status": "success"},
    )
    assert second.status_code == 200

    workspace_dashboard = client.get("/api/analytics/dashboard", headers=admin_headers)
    assert workspace_dashboard.status_code == 200
    assert workspace_dashboard.json()["dashboard"]["scope"]["scope"] == "workspace"
    assert workspace_dashboard.json()["dashboard"]["summary"]["total_events"] == 1

    system_dashboard = client.get("/api/analytics/dashboard?scope=system", headers=admin_headers)
    assert system_dashboard.status_code == 200
    assert system_dashboard.json()["dashboard"]["summary"]["total_events"] == 2


def test_non_admin_cannot_request_cross_system_scope(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user(client, admin_headers, "acceptance-member@example.com", "member")
    manager_headers = _create_user(client, admin_headers, "acceptance-manager@example.com", "manager")

    member_logs = client.get("/api/logs?scope=system", headers=member_headers)
    assert member_logs.status_code == 403

    manager_analytics = client.get("/api/analytics/dashboard?scope=system", headers=manager_headers)
    assert manager_analytics.status_code == 403


def _clear_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _alembic_upgrade(monkeypatch, db_path: Path) -> None:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("APP_AUTH_SECRET", "migration-test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("USE_MOCK_AI", "true")
    _clear_app_modules()
    importlib.invalidate_caches()
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")


def test_alembic_upgrade_empty_sqlite_creates_workspace_schema(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "empty.db"
    _alembic_upgrade(monkeypatch, db_path)
    with sqlite3.connect(db_path) as db:
        columns = {row[1] for row in db.execute("PRAGMA table_info(projects)").fetchall()}
        assert {"organization_id", "workspace_id"}.issubset(columns)
        user_columns = {row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()}
        assert {"display_name", "last_login_at", "password_change_required", "deleted_at"}.issubset(user_columns)
        version = db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert version == "20260715_2400"


def test_alembic_migrates_legacy_quality_gate_unique(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as db:
        db.executescript(
            """
            CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY);
            INSERT INTO alembic_version (version_num) VALUES ('20260711_1701');
            CREATE TABLE organizations (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, slug TEXT NOT NULL UNIQUE);
            CREATE TABLE workspaces (id INTEGER PRIMARY KEY AUTOINCREMENT, organization_id INTEGER NOT NULL, name TEXT NOT NULL, slug TEXT NOT NULL);
            CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE organization_memberships (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, organization_id INTEGER NOT NULL, workspace_id INTEGER NOT NULL, membership_role TEXT NOT NULL, UNIQUE(user_id, organization_id, workspace_id));
            CREATE TABLE quality_gates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL UNIQUE,
                user_id INTEGER,
                checklist_items TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT,
                bypassed INTEGER NOT NULL DEFAULT 0,
                bypass_reason TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users (email, password_hash, role, is_active) VALUES ('admin@example.com', 'x', 'admin', 1);
            INSERT INTO quality_gates (project_id, checklist_items, completed) VALUES ('shared-project', 'company', 1);
            """
        )
    _alembic_upgrade(monkeypatch, db_path)
    with sqlite3.connect(db_path) as db:
        count = db.execute("SELECT COUNT(*) FROM quality_gates").fetchone()[0]
        assert count == 1
        indexes = db.execute("PRAGMA index_list(quality_gates)").fetchall()
        unique_columns = []
        for index in indexes:
            if not int(index[2] or 0):
                continue
            unique_columns.append([row[2] for row in db.execute(f"PRAGMA index_info({index[1]})").fetchall()])
        assert ["project_id"] not in unique_columns
        assert ["organization_id", "workspace_id", "project_id"] in unique_columns
