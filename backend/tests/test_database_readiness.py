import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _table_names() -> set[str]:
    from app.db import get_db

    with get_db() as db:
        rows = db.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return {row["name"] for row in rows}


def test_sqlite_initialization_creates_core_tables(client: TestClient) -> None:
    tables = _table_names()

    assert "users" in tables
    assert "customers" in tables
    assert "projects" in tables
    assert "proposal_knowledge" in tables
    assert "analytics_sessions" in tables
    assert "analytics_events" in tables
    assert "feedback_entries" in tables
    assert "workspace_conversations" in tables
    assert "workspace_work_logs" in tables
    assert "proposal_reviews" in tables
    assert "proposal_review_revisions" in tables
    assert "quality_gates" in tables
    assert "release_records" in tables


def test_user_can_be_created_after_db_initialization(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "db-readiness-member@example.com", "password": "test-password", "role": "member"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["role"] == "member"


def test_database_url_unset_uses_safe_sqlite_default(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "test-password")
    monkeypatch.chdir(tmp_path)

    _reload_app_modules()
    main = importlib.import_module("app.main")
    with TestClient(main.app) as test_client:
        response = test_client.get("/health")

    body = response.json()
    assert response.status_code == 200
    assert body["db_connected"] is True
    assert body["db_type"] == "sqlite"
    assert body["db_tables_count"] >= 10
    assert (tmp_path / "app.db").exists()
