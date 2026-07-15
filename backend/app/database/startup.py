from __future__ import annotations

from typing import Any

from app.config import settings
from app.database.connection import ENGINE_DIALECT, get_db
from app.database.schema import _schema_statements


def create_tables() -> None:
    with get_db() as db:
        for statement in _schema_statements():
            db.execute(statement)


_CONTEXT_TABLES = (
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
    "presentation_reviews",
    "presentation_revisions",
    "presentation_revision_history",
    "proposal_improvement_backlog",
    "proposal_best_practices",
)


def _ensure_context_indexes(db: Any) -> None:
    for table_name in _CONTEXT_TABLES:
        if not _table_exists(db, table_name):
            continue
        db.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_org_workspace ON {table_name}(organization_id, workspace_id)")
    if _table_exists(db, "quality_gates"):
        db.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_quality_gates_scope_project_unique
            ON quality_gates(organization_id, workspace_id, project_id)
            """
        )


def add_missing_columns() -> None:
    with get_db() as db:
        _ensure_column(db, "users", "current_organization_id", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "users", "current_workspace_id", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "organizations", "is_active", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "workspaces", "is_active", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "users", "auth_version", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "users", "pilot_enabled", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "users", "pilot_started_at", "TEXT")
        _ensure_column(db, "users", "pilot_last_used_at", "TEXT")
        _ensure_column(db, "users", "pilot_completed", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "users", "pilot_note", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "audit_logs", "actor_role", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "audit_logs", "request_id", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "pilot_issues", "source_feedback_id", "INTEGER")
        _ensure_column(db, "pilot_issues", "resolution_note", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "pilot_issues", "resolved_at", "TEXT")
        _ensure_column(db, "integration_settings", "allowed_roles", "TEXT NOT NULL DEFAULT 'admin,manager,member'")
        _ensure_column(db, "integration_settings", "requires_admin_approval", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "integration_settings", "data_retention_days", "INTEGER NOT NULL DEFAULT 90")
        _ensure_column(db, "integration_settings", "last_security_review_at", "TEXT")
        _ensure_column(db, "integration_settings", "security_note", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "external_intake_items", "security_flags", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "external_intake_items", "reviewed_by", "INTEGER")
        _ensure_column(db, "external_intake_items", "reviewed_at", "TEXT")
        _ensure_column(db, "external_intake_items", "review_comment", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "action_queue", "reason", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "action_queue", "result_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "action_queue", "error_type", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "action_queue", "created_by", "INTEGER")
        _ensure_column(db, "learning_runs", "metrics_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "learning_runs", "release_candidate_version", "TEXT NOT NULL DEFAULT '13.6候補'")
        _ensure_column(db, "learning_runs", "release_candidate_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "learning_improvements", "recommendation", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "learning_improvements", "simulation", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "learning_improvements", "status", "TEXT NOT NULL DEFAULT 'candidate'")
        _ensure_column(db, "prompt_versions", "description", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "prompt_versions", "target_agent", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "prompt_versions", "prompt_template", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "prompt_versions", "status", "TEXT NOT NULL DEFAULT 'draft'")
        _ensure_column(db, "prompt_versions", "scope_type", "TEXT NOT NULL DEFAULT 'workspace'")
        _ensure_column(db, "prompt_versions", "scope_id", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "experiments", "traffic_ratio", "INTEGER NOT NULL DEFAULT 50")
        _ensure_column(db, "experiments", "status", "TEXT NOT NULL DEFAULT 'draft'")
        _ensure_column(db, "experiments", "winner", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "experiments", "updated_at", "TEXT")
        _ensure_column(db, "experiments", "scope_type", "TEXT NOT NULL DEFAULT 'workspace'")
        _ensure_column(db, "experiments", "scope_id", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "prompt_experiment_metrics", "outcome", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "prompt_experiment_metrics", "review_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "prompt_experiment_metrics", "quality_gate_passed", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "prompt_experiment_metrics", "proposal_time_seconds", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "prompt_experiment_metrics", "user_rating", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_knowledge", "approval_status", "TEXT NOT NULL DEFAULT 'draft'")
        _ensure_column(db, "proposal_knowledge", "quality_score", "INTEGER NOT NULL DEFAULT 50")
        _ensure_column(db, "proposal_knowledge", "confidential_risk", "TEXT NOT NULL DEFAULT 'low'")
        _ensure_column(db, "proposal_knowledge", "confidential_flags", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_knowledge", "source_type", "TEXT NOT NULL DEFAULT 'admin_created'")
        _ensure_column(db, "proposal_knowledge", "source_note", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "beautiful_ai_presentations", "theme_id", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "beautiful_ai_presentations", "request_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "beautiful_ai_presentations", "error_type", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "beautiful_ai_presentations", "http_status", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "beautiful_ai_presentations", "response_text", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "beautiful_ai_presentations", "request_json_safe", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "beautiful_ai_presentations", "endpoint", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "beautiful_ai_presentations", "api_mode", "TEXT NOT NULL DEFAULT 'prompt'")
        _ensure_column(db, "beautiful_ai_presentations", "workspace_config_id", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_reviews", "actions_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_reviews", "outline_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_reviews", "unresolved_issue_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "presentation_reviews", "score_schema_version", "TEXT NOT NULL DEFAULT '19.1'")
        _ensure_column(db, "presentation_revisions", "status", "TEXT NOT NULL DEFAULT 'draft'")
        _ensure_column(db, "presentation_revisions", "selected_actions_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revisions", "outline_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revisions", "diff_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revisions", "editor_url", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revisions", "player_url", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revisions", "generation_error_type", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revisions", "generated_at", "TEXT")
        _ensure_column(db, "presentation_revisions", "approved_by", "INTEGER")
        _ensure_column(db, "presentation_revisions", "approved_at", "TEXT")
        _ensure_column(db, "presentation_revision_history", "change_reason", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revision_history", "before_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revision_history", "after_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revision_history", "field_name", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revision_history", "human_action", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "presentation_revision_history", "action_id", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "project_id", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "category", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "title", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "priority", "TEXT NOT NULL DEFAULT 'Medium'")
        _ensure_column(db, "proposal_improvement_backlog", "impact", "REAL NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_improvement_backlog", "confidence", "REAL NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_improvement_backlog", "expected_improvement", "REAL NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_improvement_backlog", "effort", "INTEGER NOT NULL DEFAULT 3")
        _ensure_column(db, "proposal_improvement_backlog", "importance", "INTEGER NOT NULL DEFAULT 3")
        _ensure_column(db, "proposal_improvement_backlog", "adoption_rate", "REAL NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_improvement_backlog", "predicted_win_rate_delta", "REAL NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_improvement_backlog", "composite_score", "REAL NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_improvement_backlog", "status", "TEXT NOT NULL DEFAULT 'suggested'")
        _ensure_column(db, "proposal_improvement_backlog", "owner", "INTEGER")
        _ensure_column(db, "proposal_improvement_backlog", "source_type", "TEXT NOT NULL DEFAULT 'optimization_engine'")
        _ensure_column(db, "proposal_improvement_backlog", "explanation", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "simulation_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "evidence_type", "TEXT NOT NULL DEFAULT 'insufficient_data'")
        _ensure_column(db, "proposal_improvement_backlog", "sample_size", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_improvement_backlog", "is_estimate", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "proposal_improvement_backlog", "calculation_method", "TEXT NOT NULL DEFAULT 'weighted_score_v20_1'")
        _ensure_column(db, "proposal_improvement_backlog", "predicted_effect_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "measured_effect_json", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "measurement_status", "TEXT NOT NULL DEFAULT 'pending'")
        _ensure_column(db, "proposal_improvement_backlog", "measured_at", "TEXT")
        _ensure_column(db, "proposal_improvement_backlog", "measurement_period", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "outcome_type", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "requires_human_review", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "proposal_improvement_backlog", "evidence_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "evidence_period", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_improvement_backlog", "created_by", "INTEGER")
        _ensure_column(db, "proposal_improvement_backlog", "approved_by", "INTEGER")
        _ensure_column(db, "proposal_improvement_backlog", "approved_at", "TEXT")
        _ensure_column(db, "proposal_best_practices", "category", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "title", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "pattern_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "source_type", "TEXT NOT NULL DEFAULT 'learning'")
        _ensure_column(db, "proposal_best_practices", "success_metric", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "confidence", "REAL NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_best_practices", "adoption_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_best_practices", "status", "TEXT NOT NULL DEFAULT 'pending_review'")
        _ensure_column(db, "proposal_best_practices", "normalized_title", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "tags", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "structure_summary", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "cta_type", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "slide_order_pattern", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "evidence_count", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_best_practices", "evidence_period", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "confidential_risk", "TEXT NOT NULL DEFAULT 'low'")
        _ensure_column(db, "proposal_best_practices", "quality_score", "INTEGER NOT NULL DEFAULT 50")
        _ensure_column(db, "proposal_best_practices", "has_prediction", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "proposal_best_practices", "approved_by", "INTEGER")
        _ensure_column(db, "proposal_best_practices", "approved_at", "TEXT")
        _ensure_column(db, "proposal_best_practices", "approval_reason", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "rejection_reason", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "archived_reason", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "proposal_best_practices", "merged_into_id", "INTEGER")
        for table_name in _CONTEXT_TABLES:
            _ensure_column(db, table_name, "organization_id", "INTEGER NOT NULL DEFAULT 1")
            _ensure_column(db, table_name, "workspace_id", "INTEGER NOT NULL DEFAULT 1")
        _ensure_context_indexes(db)
        if _table_exists(db, "presentation_revisions"):
            db.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_presentation_revisions_scope_number_unique
                ON presentation_revisions(organization_id, workspace_id, project_id, revision_number)
                """
            )
        seed_default_organization(db)


def seed_default_templates() -> None:
    default_templates = [
        ("web", "Webサイト制作 提案テンプレート", "企業サイト・サービスサイトの標準構成", "提案サマリー, 現状理解, 課題, Web戦略, KPI, 制作方針, 費用, 今後の進め方", "Webリニューアル"),
        ("recruiting", "採用サイト 提案テンプレート", "採用強化案件向けの構成", "採用課題, ターゲット, コンテンツ設計, 導線, KPI, 運用", "採用サイト"),
        ("lp", "LP制作 提案テンプレート", "問い合わせ・資料請求獲得向けのLP構成", "訴求軸, ファーストビュー, CTA, FAQ, CV導線, 改善計画", "LP制作"),
    ]
    with get_db() as db:
        row = db.execute("SELECT COUNT(*) AS count FROM proposal_templates").fetchone()
        if int(row["count"] if row else 0) > 0:
            return
        for category, title, summary, structure, recommended_for in default_templates:
            db.execute(
                """
                INSERT INTO proposal_templates (category, title, template_summary, structure, recommended_for, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (category, title, summary, structure, recommended_for),
            )


def seed_default_organization(db: Any) -> tuple[int, int]:
    if ENGINE_DIALECT == "postgresql":
        db.execute("INSERT INTO organizations (id, name, slug) VALUES (1, 'Ready Crew', 'ready-crew') ON CONFLICT (slug) DO NOTHING")
        db.execute("INSERT INTO workspaces (id, organization_id, name, slug) VALUES (1, 1, '営業部', 'sales') ON CONFLICT (organization_id, slug) DO NOTHING")
    else:
        db.execute("INSERT OR IGNORE INTO organizations (id, name, slug) VALUES (1, 'Ready Crew', 'ready-crew')")
        db.execute("INSERT OR IGNORE INTO workspaces (id, organization_id, name, slug) VALUES (1, 1, '営業部', 'sales')")
    users = db.execute("SELECT id, role FROM users").fetchall()
    for user in users:
        membership_role = "organization_admin" if str(user["role"]) in {"admin", "manager"} else "member"
        if ENGINE_DIALECT == "postgresql":
            db.execute(
                """
                INSERT INTO organization_memberships (user_id, organization_id, workspace_id, membership_role)
                VALUES (?, 1, 1, ?)
                ON CONFLICT (user_id, organization_id, workspace_id) DO NOTHING
                """,
                (int(user["id"]), membership_role),
            )
        else:
            db.execute(
                """
                INSERT OR IGNORE INTO organization_memberships (user_id, organization_id, workspace_id, membership_role)
                VALUES (?, 1, 1, ?)
                """,
                (int(user["id"]), membership_role),
            )
    db.execute("UPDATE users SET current_organization_id = COALESCE(NULLIF(current_organization_id, 0), 1), current_workspace_id = COALESCE(NULLIF(current_workspace_id, 0), 1)")
    for table_name in _CONTEXT_TABLES:
        if not _table_exists(db, table_name):
            continue
        db.execute(f"UPDATE {table_name} SET organization_id = COALESCE(NULLIF(organization_id, 0), 1), workspace_id = COALESCE(NULLIF(workspace_id, 0), 1)")
    return 1, 1


def init_db() -> None:
    if not settings.allow_startup_schema_migration:
        return
    create_tables()
    add_missing_columns()


def _table_exists(db: Any, table_name: str) -> bool:
    if ENGINE_DIALECT == "sqlite":
        row = db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        ).fetchone()
        return bool(row)

    if ENGINE_DIALECT == "postgresql":
        row = db.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = ?
            """,
            (table_name,),
        ).fetchone()
        return bool(row)

    return False


def _ensure_column(db: Any, table_name: str, column_name: str, column_definition: str) -> None:
    if not _table_exists(db, table_name):
        return
    if ENGINE_DIALECT == "sqlite":
        columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()}
        if column_name not in columns:
            db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        return

    if ENGINE_DIALECT == "postgresql":
        row = db.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ? AND column_name = ?
            """,
            (table_name, column_name),
        ).fetchone()
        if not row:
            db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")


def _existing_columns(db: Any, table_name: str) -> set[str]:
    if not _table_exists(db, table_name):
        return set()
    if ENGINE_DIALECT == "sqlite":
        return {str(row["name"]) for row in db.execute(f"PRAGMA table_info({table_name})").fetchall()}
    if ENGINE_DIALECT == "postgresql":
        rows = db.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = ?
            """,
            (table_name,),
        ).fetchall()
        return {str(row["column_name"]) for row in rows}
    return set()


def _quality_gate_unique_state(db: Any) -> dict[str, Any]:
    if not _table_exists(db, "quality_gates"):
        return {"scoped": False, "legacy_project_unique": False}
    if ENGINE_DIALECT == "sqlite":
        scoped = False
        legacy = False
        for index_row in db.execute("PRAGMA index_list(quality_gates)").fetchall():
            if not int(index_row["unique"] or 0):
                continue
            columns = [str(info["name"]) for info in db.execute(f"PRAGMA index_info({index_row['name']})").fetchall()]
            if columns == ["project_id"]:
                legacy = True
            if columns == ["organization_id", "workspace_id", "project_id"]:
                scoped = True
        return {"scoped": scoped, "legacy_project_unique": legacy}
    if ENGINE_DIALECT == "postgresql":
        rows = db.execute(
            """
            SELECT indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = 'quality_gates'
            """
        ).fetchall()
        index_defs = [str(row["indexdef"]).lower() for row in rows]
        scoped = any("unique" in item and "organization_id" in item and "workspace_id" in item and "project_id" in item for item in index_defs)
        legacy = any("unique" in item and "(project_id)" in item and "organization_id" not in item for item in index_defs)
        return {"scoped": scoped, "legacy_project_unique": legacy}
    return {"scoped": False, "legacy_project_unique": False}
