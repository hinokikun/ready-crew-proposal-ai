"""Workspace isolation acceptance migration.

Revision ID: 20260713_1820
Revises: 20260711_1701
Create Date: 2026-07-13
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260713_1820"
down_revision = "20260711_1701"
branch_labels = None
depends_on = None


CONTEXT_TABLES = (
    "customers",
    "projects",
    "project_lifecycle_events",
    "project_outcomes",
    "project_handoffs",
    "project_retrospectives",
    "proposal_histories",
    "meeting_memos",
    "usage_logs",
    "audit_logs",
    "feedback_entries",
    "analytics_events",
    "analytics_sessions",
    "analytics_errors",
    "daily_briefing_events",
    "ai_notifications",
    "proposal_knowledge",
    "proposal_templates",
    "prompt_versions",
    "experiments",
    "prompt_experiment_metrics",
    "beautiful_ai_presentations",
    "proposal_reviews",
    "proposal_review_revisions",
    "quality_gates",
    "learning_runs",
    "learning_improvements",
    "pilot_events",
    "pilot_issues",
    "workspace_conversations",
    "workspace_work_logs",
    "action_queue",
    "integration_settings",
    "external_intake_items",
    "dry_run_logs",
    "release_records",
    "release_notes",
)


def _dialect() -> str:
    return op.get_bind().dialect.name


def _has_table(table_name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _add_int_column(table_name: str, column_name: str, default: int = 1) -> None:
    if _has_table(table_name) and not _has_column(table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, sa.Integer(), nullable=False, server_default=str(default)))


def _add_text_column(table_name: str, column_name: str, default: str = "") -> None:
    if _has_table(table_name) and not _has_column(table_name, column_name):
        op.add_column(table_name, sa.Column(column_name, sa.Text(), nullable=False, server_default=default))


def _exec(sql: str) -> None:
    op.get_bind().exec_driver_sql(sql)


def _seed_default_org_workspace() -> None:
    if not _has_table("organizations") or not _has_table("workspaces"):
        return
    if _dialect() == "postgresql":
        _exec("INSERT INTO organizations (id, name, slug, is_active) VALUES (1, 'Ready Crew', 'ready-crew', 1) ON CONFLICT (slug) DO NOTHING")
        _exec("INSERT INTO workspaces (id, organization_id, name, slug, is_active) VALUES (1, 1, '営業部', 'sales', 1) ON CONFLICT (organization_id, slug) DO NOTHING")
    else:
        _exec("INSERT OR IGNORE INTO organizations (id, name, slug, is_active) VALUES (1, 'Ready Crew', 'ready-crew', 1)")
        _exec("INSERT OR IGNORE INTO workspaces (id, organization_id, name, slug, is_active) VALUES (1, 1, '営業部', 'sales', 1)")


def _backfill_users_and_memberships() -> None:
    if not _has_table("users"):
        return
    _exec("UPDATE users SET current_organization_id = 1 WHERE current_organization_id IS NULL OR current_organization_id = 0")
    _exec("UPDATE users SET current_workspace_id = 1 WHERE current_workspace_id IS NULL OR current_workspace_id = 0")
    if not _has_table("organization_memberships"):
        return
    rows = op.get_bind().exec_driver_sql("SELECT id, role FROM users").fetchall()
    for row in rows:
        user_id = int(row[0])
        role = str(row[1] or "")
        membership_role = "organization_admin" if role in {"admin", "manager"} else "member"
        if _dialect() == "postgresql":
            op.get_bind().exec_driver_sql(
                """
                INSERT INTO organization_memberships (user_id, organization_id, workspace_id, membership_role)
                VALUES (%s, 1, 1, %s)
                ON CONFLICT (user_id, organization_id, workspace_id) DO NOTHING
                """,
                (user_id, membership_role),
            )
        else:
            op.get_bind().exec_driver_sql(
                """
                INSERT OR IGNORE INTO organization_memberships (user_id, organization_id, workspace_id, membership_role)
                VALUES (?, 1, 1, ?)
                """,
                (user_id, membership_role),
            )


def _backfill_context_columns() -> None:
    for table_name in CONTEXT_TABLES:
        if not _has_table(table_name):
            continue
        _add_int_column(table_name, "organization_id", 1)
        _add_int_column(table_name, "workspace_id", 1)
        _exec(f"UPDATE {table_name} SET organization_id = 1 WHERE organization_id IS NULL OR organization_id = 0")
        _exec(f"UPDATE {table_name} SET workspace_id = 1 WHERE workspace_id IS NULL OR workspace_id = 0")
        op.create_index(f"idx_{table_name}_org_workspace", table_name, ["organization_id", "workspace_id"], unique=False, if_not_exists=True)


def _sqlite_quality_gate_has_legacy_project_unique() -> bool:
    if _dialect() != "sqlite" or not _has_table("quality_gates"):
        return False
    connection = op.get_bind()
    for index_row in connection.exec_driver_sql("PRAGMA index_list(quality_gates)").fetchall():
        if not int(index_row[2] or 0):
            continue
        index_name = str(index_row[1])
        columns = [str(info[2]) for info in connection.exec_driver_sql(f"PRAGMA index_info({index_name})").fetchall()]
        if columns == ["project_id"]:
            return True
    return False


def _rebuild_sqlite_quality_gates() -> None:
    if not _sqlite_quality_gate_has_legacy_project_unique():
        return
    _exec("PRAGMA foreign_keys=OFF")
    _exec(
        """
        CREATE TABLE quality_gates_1820_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            user_id INTEGER,
            checklist_items TEXT NOT NULL DEFAULT '',
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            bypassed INTEGER NOT NULL DEFAULT 0,
            bypass_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            organization_id INTEGER NOT NULL DEFAULT 1,
            workspace_id INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    _exec(
        """
        INSERT INTO quality_gates_1820_new
            (id, project_id, user_id, checklist_items, completed, completed_at, bypassed, bypass_reason, created_at, updated_at, organization_id, workspace_id)
        SELECT
            id,
            project_id,
            user_id,
            checklist_items,
            completed,
            completed_at,
            bypassed,
            bypass_reason,
            created_at,
            updated_at,
            COALESCE(NULLIF(organization_id, 0), 1),
            COALESCE(NULLIF(workspace_id, 0), 1)
        FROM quality_gates
        """
    )
    _exec("DROP TABLE quality_gates")
    _exec("ALTER TABLE quality_gates_1820_new RENAME TO quality_gates")
    _exec("PRAGMA foreign_keys=ON")


def _ensure_quality_gate_uniqueness() -> None:
    if not _has_table("quality_gates"):
        return
    if _dialect() == "postgresql":
        _exec("ALTER TABLE quality_gates DROP CONSTRAINT IF EXISTS quality_gates_project_id_key")
        _exec("DROP INDEX IF EXISTS quality_gates_project_id_key")
    else:
        _rebuild_sqlite_quality_gates()
    op.create_index(
        "idx_quality_gates_scope_project_unique",
        "quality_gates",
        ["organization_id", "workspace_id", "project_id"],
        unique=True,
        if_not_exists=True,
    )
    op.create_index("idx_quality_gates_project", "quality_gates", ["project_id", "updated_at"], unique=False, if_not_exists=True)


def upgrade() -> None:
    if _has_table("organizations"):
        _add_int_column("organizations", "is_active", 1)
    if _has_table("workspaces"):
        _add_int_column("workspaces", "is_active", 1)
    if _has_table("users"):
        _add_int_column("users", "current_organization_id", 1)
        _add_int_column("users", "current_workspace_id", 1)
    if _has_table("audit_logs"):
        _add_text_column("audit_logs", "actor_role", "")
        _add_text_column("audit_logs", "request_id", "")
    if _has_table("prompt_versions"):
        _add_text_column("prompt_versions", "scope_type", "workspace")
        _add_int_column("prompt_versions", "scope_id", 1)
    if _has_table("experiments"):
        _add_text_column("experiments", "scope_type", "workspace")
        _add_int_column("experiments", "scope_id", 1)

    _seed_default_org_workspace()
    _backfill_users_and_memberships()
    _backfill_context_columns()
    _ensure_quality_gate_uniqueness()


def downgrade() -> None:
    raise RuntimeError("Workspace isolation migration downgrade is intentionally disabled to avoid data loss.")
