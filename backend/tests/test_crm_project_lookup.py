from __future__ import annotations

import sqlite3

from app.database.connection import _postgres_sql
from app.repository_parts.crm import get_or_create_project


PROJECTS_SCHEMA = """
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    name TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    win_probability INTEGER NOT NULL DEFAULT 0,
    next_action TEXT NOT NULL DEFAULT '',
    organization_id INTEGER NOT NULL,
    workspace_id INTEGER NOT NULL,
    updated_at TEXT
)
"""


def _db() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(PROJECTS_SCHEMA)
    return db


def test_get_or_create_project_preserves_null_safe_customer_and_scope_semantics() -> None:
    db = _db()
    try:
        db.execute(
            "INSERT INTO projects (customer_id, name, organization_id, workspace_id) VALUES (?, ?, ?, ?)",
            (None, "Null customer", 1, 1),
        )
        db.execute(
            "INSERT INTO projects (customer_id, name, organization_id, workspace_id) VALUES (?, ?, ?, ?)",
            (10, "Named customer", 1, 1),
        )
        db.execute(
            "INSERT INTO projects (customer_id, name, organization_id, workspace_id) VALUES (?, ?, ?, ?)",
            (10, "Scoped project", 2, 1),
        )
        db.execute(
            "INSERT INTO projects (customer_id, name, organization_id, workspace_id) VALUES (?, ?, ?, ?)",
            (10, "Scoped project", 1, 2),
        )
        db.commit()

        null_id = get_or_create_project(db, None, "Null customer", organization_id=1, workspace_id=1)
        assert null_id == 1

        existing_id = get_or_create_project(db, 10, "Named customer", organization_id=1, workspace_id=1)
        assert existing_id == 2

        different_customer_id = get_or_create_project(db, 11, "Named customer", organization_id=1, workspace_id=1)
        assert different_customer_id not in {1, 2}
        assert db.execute("SELECT customer_id FROM projects WHERE id = ?", (different_customer_id,)).fetchone()[0] == 11

        organization_scoped_id = get_or_create_project(db, 10, "Scoped project", organization_id=2, workspace_id=1)
        assert organization_scoped_id == 3

        workspace_scoped_id = get_or_create_project(db, 10, "Scoped project", organization_id=1, workspace_id=2)
        assert workspace_scoped_id == 4

        created_id = get_or_create_project(db, None, "New project", organization_id=1, workspace_id=1)
        created = db.execute(
            "SELECT name, customer_id, organization_id, workspace_id FROM projects WHERE id = ?",
            (created_id,),
        ).fetchone()
        assert tuple(created) == ("New project", None, 1, 1)
    finally:
        db.close()


def test_get_or_create_project_postgres_sql_has_no_parameter_after_is() -> None:
    sql = "SELECT id FROM projects WHERE name = ? AND ((customer_id IS NULL AND ? IS NULL) OR customer_id = ?) AND organization_id = ? AND workspace_id = ?"
    postgres_sql = _postgres_sql(sql)

    assert "customer_id IS %s" not in postgres_sql
    assert "customer_id IS $" not in postgres_sql
    assert "customer_id IS NULL" in postgres_sql
    assert "%s IS NULL" in postgres_sql
    assert postgres_sql.count("%s") == 5
