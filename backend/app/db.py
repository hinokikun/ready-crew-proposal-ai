from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.config import settings


def _normalise_database_url(database_url: str) -> str:
    url = (database_url or "sqlite:///app.db").strip() or "sqlite:///app.db"
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database_path() -> str:
    if settings.database_url.startswith("sqlite:///"):
        return settings.database_url.replace("sqlite:///", "", 1)
    return "app.db"


def _engine_url() -> str:
    url = _normalise_database_url(settings.database_url)
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        if path != ":memory:":
            parent = Path(path).parent
            if parent != Path("."):
                parent.mkdir(parents=True, exist_ok=True)
    return url


ENGINE_URL = _engine_url()
ENGINE_DIALECT = make_url(ENGINE_URL).get_backend_name()


def _connect_args() -> dict[str, Any]:
    if ENGINE_DIALECT == "sqlite":
        return {"check_same_thread": False}
    if ENGINE_DIALECT == "postgresql":
        try:
            from psycopg.rows import dict_row

            return {"row_factory": dict_row}
        except Exception:
            return {}
    return {}


engine = create_engine(
    ENGINE_URL,
    connect_args=_connect_args(),
    pool_pre_ping=True,
)


class _CursorAdapter:
    def __init__(self, cursor: Any, lastrowid: int | None = None):
        self._cursor = cursor
        self.lastrowid = lastrowid

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()


class _PostgresConnectionAdapter:
    """Small compatibility layer for the existing SQLite-style repositories.

    The current repositories use `?` placeholders and `cursor.lastrowid`.
    This adapter keeps that surface stable while the project moves toward
    a proper SQLAlchemy/Alembic repository implementation.
    """

    def __init__(self, connection: Any):
        self._connection = connection

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> _CursorAdapter:
        cursor = self._connection.cursor()
        statement = _postgres_sql(sql)
        values = tuple(params or ())
        is_insert_with_id = statement.lstrip().upper().startswith("INSERT INTO") and " RETURNING " not in statement.upper()
        if is_insert_with_id:
            statement = statement.rstrip().rstrip(";") + " RETURNING id"
        cursor.execute(statement, values)
        lastrowid = None
        if is_insert_with_id:
            try:
                row = cursor.fetchone()
                if isinstance(row, dict):
                    lastrowid = int(row.get("id") or 0)
                elif row:
                    lastrowid = int(row[0])
            except Exception:
                lastrowid = None
        return _CursorAdapter(cursor, lastrowid)

    def executescript(self, script: str) -> None:
        for statement in _split_sql_script(script):
            self.execute(statement)


def _postgres_sql(sql: str) -> str:
    statement = sql.replace("?", "%s")
    statement = re.sub(
        r"CAST\(\(JULIANDAY\(CURRENT_TIMESTAMP\)\s*-\s*JULIANDAY\(started_at\)\)\s*\*\s*86400\s+AS\s+INTEGER\)",
        "CAST(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at::timestamp)) AS INTEGER)",
        statement,
        flags=re.IGNORECASE,
    )
    statement = re.sub(r"DATE\(created_at\)\s*=\s*DATE\('now'\)", "DATE(created_at::timestamp) = CURRENT_DATE", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DATETIME\('now',\s*'-7 days'\)", "CURRENT_TIMESTAMP - INTERVAL '7 days'", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DATETIME\('now'\)", "CURRENT_TIMESTAMP", statement, flags=re.IGNORECASE)
    return statement


def _split_sql_script(script: str) -> list[str]:
    return [part.strip() for part in script.split(";") if part.strip()]


@contextmanager
def get_db():
    raw_connection = engine.raw_connection()
    connection = raw_connection.driver_connection if hasattr(raw_connection, "driver_connection") else raw_connection
    if ENGINE_DIALECT == "sqlite":
        connection.row_factory = sqlite3.Row
        db = connection
    elif ENGINE_DIALECT == "postgresql":
        db = _PostgresConnectionAdapter(connection)
    else:
        db = connection
    try:
        yield db
        raw_connection.commit()
    finally:
        raw_connection.close()


def get_db_type() -> str:
    if ENGINE_DIALECT == "sqlite":
        return "sqlite"
    if ENGINE_DIALECT == "postgresql":
        return "postgresql"
    return ENGINE_DIALECT or "unknown"


def _id_column() -> str:
    return "SERIAL PRIMARY KEY" if ENGINE_DIALECT == "postgresql" else "INTEGER PRIMARY KEY AUTOINCREMENT"


def _schema_statements() -> list[str]:
    id_column = _id_column()
    return [
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id {id_column},
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'manager', 'member', 'viewer')),
            is_active INTEGER NOT NULL DEFAULT 1,
            auth_version INTEGER NOT NULL DEFAULT 1,
            pilot_enabled INTEGER NOT NULL DEFAULT 0,
            pilot_started_at TEXT,
            pilot_last_used_at TEXT,
            pilot_completed INTEGER NOT NULL DEFAULT 0,
            pilot_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS customers (
            id {id_column},
            company_name TEXT NOT NULL,
            industry TEXT NOT NULL DEFAULT '',
            contact_person TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS projects (
            id {id_column},
            customer_id INTEGER,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'draft',
            win_probability INTEGER NOT NULL DEFAULT 0,
            summary TEXT NOT NULL DEFAULT '',
            next_action TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS project_lifecycle_events (
            id {id_column},
            project_id INTEGER NOT NULL,
            user_id INTEGER,
            event_type TEXT NOT NULL DEFAULT '',
            from_status TEXT NOT NULL DEFAULT '',
            to_status TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_project_lifecycle_events_project ON project_lifecycle_events(project_id, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS project_outcomes (
            id {id_column},
            project_id INTEGER NOT NULL UNIQUE,
            outcome TEXT NOT NULL DEFAULT '',
            lost_reason TEXT NOT NULL DEFAULT '',
            note TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS project_handoffs (
            id {id_column},
            project_id INTEGER NOT NULL UNIQUE,
            handoff_text TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS project_retrospectives (
            id {id_column},
            project_id INTEGER NOT NULL UNIQUE,
            success_factors TEXT NOT NULL DEFAULT '',
            improvements TEXT NOT NULL DEFAULT '',
            next_learnings TEXT NOT NULL DEFAULT '',
            knowledge_candidate_id INTEGER,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS proposal_histories (
            id {id_column},
            user_id INTEGER,
            customer_id INTEGER,
            project_id INTEGER,
            feature_name TEXT NOT NULL,
            input_length INTEGER NOT NULL DEFAULT 0,
            output_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            error_type TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS meeting_memos (
            id {id_column},
            user_id INTEGER,
            project_id INTEGER,
            summary TEXT NOT NULL DEFAULT '',
            next_action TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id {id_column},
            user_id INTEGER,
            feature_name TEXT NOT NULL,
            input_length INTEGER NOT NULL DEFAULT 0,
            output_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            error_type TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id {id_column},
            user_id INTEGER,
            event_type TEXT NOT NULL,
            target_type TEXT NOT NULL DEFAULT '',
            target_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            metadata TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS pilot_events (
            id {id_column},
            user_id INTEGER,
            event_type TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            duration_ms INTEGER NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_pilot_events_user ON pilot_events(user_id, event_type, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS pilot_issues (
            id {id_column},
            issue_id TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT 'other',
            severity TEXT NOT NULL DEFAULT 'medium',
            title TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            reproduction_steps TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'reported',
            reported_by INTEGER,
            assigned_to TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT,
            resolution_note TEXT NOT NULL DEFAULT '',
            source_feedback_id INTEGER,
            FOREIGN KEY(reported_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_pilot_issues_status ON pilot_issues(status, severity, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS app_runtime_settings (
            key TEXT NOT NULL PRIMARY KEY,
            value TEXT NOT NULL DEFAULT '',
            updated_by INTEGER,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            note TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(updated_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS ai_notifications (
            id {id_column},
            notification_key TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            project_id INTEGER,
            agent_name TEXT NOT NULL DEFAULT '',
            priority TEXT NOT NULL DEFAULT '中',
            title TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '',
            recommended_action TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT '',
            source_id TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'unread',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            read_at TEXT,
            archived_at TEXT,
            actioned_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_ai_notifications_user_status ON ai_notifications(user_id, status, priority, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_ai_notifications_project ON ai_notifications(project_id, source_type)",
        f"""
        CREATE TABLE IF NOT EXISTS integration_settings (
            id {id_column},
            provider TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL DEFAULT '未接続',
            display_name TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 0,
            allowed_roles TEXT NOT NULL DEFAULT 'admin,manager,member',
            requires_admin_approval INTEGER NOT NULL DEFAULT 1,
            data_retention_days INTEGER NOT NULL DEFAULT 90,
            last_checked_at TEXT,
            last_security_review_at TEXT,
            error_message TEXT NOT NULL DEFAULT '',
            security_note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_integration_settings_status ON integration_settings(status, enabled, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS external_intake_items (
            id {id_column},
            source_provider TEXT NOT NULL,
            source_type TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            received_at TEXT NOT NULL DEFAULT '',
            metadata TEXT NOT NULL DEFAULT '',
            candidate_status TEXT NOT NULL DEFAULT 'pending_review',
            security_flags TEXT NOT NULL DEFAULT '',
            reviewed_by INTEGER,
            reviewed_at TEXT,
            review_comment TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            project_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id),
            FOREIGN KEY(reviewed_by) REFERENCES users(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_external_intake_provider ON external_intake_items(source_provider, candidate_status, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_external_intake_user ON external_intake_items(created_by, candidate_status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS dry_run_logs (
            id {id_column},
            provider TEXT NOT NULL,
            template_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'success',
            created_item_id INTEGER,
            result_summary TEXT NOT NULL DEFAULT '',
            security_flags_count INTEGER NOT NULL DEFAULT 0,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_item_id) REFERENCES external_intake_items(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_dry_run_logs_provider ON dry_run_logs(provider, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS action_queue (
            id {id_column},
            project_id INTEGER,
            action_type TEXT NOT NULL,
            agent TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            priority INTEGER NOT NULL DEFAULT 50,
            reason TEXT NOT NULL DEFAULT '',
            result_summary TEXT NOT NULL DEFAULT '',
            error_type TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            completed_at TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_action_queue_status_priority ON action_queue(status, priority, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_action_queue_project ON action_queue(project_id, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS learning_runs (
            id {id_column},
            triggered_by INTEGER,
            status TEXT NOT NULL DEFAULT 'success',
            analyzed_items_count INTEGER NOT NULL DEFAULT 0,
            metrics_summary TEXT NOT NULL DEFAULT '',
            release_candidate_version TEXT NOT NULL DEFAULT '13.6候補',
            release_candidate_summary TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(triggered_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS learning_improvements (
            id {id_column},
            run_id INTEGER,
            improvement_type TEXT NOT NULL DEFAULT 'prompt',
            agent TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT '',
            current_version TEXT NOT NULL DEFAULT '',
            suggested_prompt TEXT NOT NULL DEFAULT '',
            recommendation TEXT NOT NULL DEFAULT '',
            expected_effect TEXT NOT NULL DEFAULT '',
            confidence INTEGER NOT NULL DEFAULT 50,
            priority INTEGER NOT NULL DEFAULT 50,
            simulation TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'candidate',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(run_id) REFERENCES learning_runs(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_learning_improvements_run ON learning_improvements(run_id, priority, confidence)",
        "CREATE INDEX IF NOT EXISTS idx_learning_improvements_type ON learning_improvements(improvement_type, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id {id_column},
            prompt_name TEXT NOT NULL,
            version TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            target_agent TEXT NOT NULL DEFAULT '',
            prompt_template TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'draft',
            UNIQUE(prompt_name, version),
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_prompt_versions_name_status ON prompt_versions(prompt_name, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS experiments (
            id {id_column},
            experiment_name TEXT NOT NULL,
            target_prompt TEXT NOT NULL,
            control_version TEXT NOT NULL,
            candidate_version TEXT NOT NULL,
            traffic_ratio INTEGER NOT NULL DEFAULT 50,
            status TEXT NOT NULL DEFAULT 'draft',
            start_at TEXT,
            end_at TEXT,
            winner TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_experiments_prompt_status ON experiments(target_prompt, status, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS experiment_assignments (
            id {id_column},
            experiment_id INTEGER,
            project_id INTEGER,
            user_id INTEGER,
            selected_version TEXT NOT NULL,
            assignment_key TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id),
            FOREIGN KEY(project_id) REFERENCES projects(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_experiment_assignments_experiment ON experiment_assignments(experiment_id, selected_version)",
        f"""
        CREATE TABLE IF NOT EXISTS prompt_experiment_metrics (
            id {id_column},
            experiment_id INTEGER,
            prompt_name TEXT NOT NULL,
            prompt_version TEXT NOT NULL,
            project_id INTEGER,
            outcome TEXT NOT NULL DEFAULT '',
            review_count INTEGER NOT NULL DEFAULT 0,
            quality_gate_passed INTEGER NOT NULL DEFAULT 0,
            proposal_time_seconds INTEGER NOT NULL DEFAULT 0,
            user_rating TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(experiment_id) REFERENCES experiments(id),
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_prompt_metrics_prompt_version ON prompt_experiment_metrics(prompt_name, prompt_version, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS feedback_entries (
            id {id_column},
            user_id INTEGER,
            user_role TEXT NOT NULL DEFAULT '',
            rating TEXT NOT NULL CHECK(rating IN ('usable', 'needs_revision', 'hard_to_use')),
            comment TEXT NOT NULL DEFAULT '',
            feature_name TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS analytics_sessions (
            id {id_column},
            session_key TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ended_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            generation_count INTEGER NOT NULL DEFAULT 0,
            download_count INTEGER NOT NULL DEFAULT 0,
            error_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id {id_column},
            session_key TEXT NOT NULL,
            user_id INTEGER,
            event_name TEXT NOT NULL,
            feature_name TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'success',
            duration_ms INTEGER NOT NULL DEFAULT 0,
            metadata TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_session ON analytics_events(session_key, event_name, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_analytics_events_feature ON analytics_events(feature_name, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS analytics_errors (
            id {id_column},
            error_key TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL DEFAULT '',
            message TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL DEFAULT '',
            count INTEGER NOT NULL DEFAULT 1,
            first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved INTEGER NOT NULL DEFAULT 0
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS release_notes (
            id {id_column},
            version TEXT NOT NULL,
            release_date TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT '',
            improvements TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS release_records (
            id {id_column},
            version TEXT NOT NULL,
            release_date TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'draft',
            summary TEXT NOT NULL DEFAULT '',
            changes TEXT NOT NULL DEFAULT '',
            impact_scope TEXT NOT NULL DEFAULT '',
            checklist TEXT NOT NULL DEFAULT '',
            known_issues TEXT NOT NULL DEFAULT '',
            rollback_note TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            released_by INTEGER,
            released_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id),
            FOREIGN KEY(released_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_release_records_status ON release_records(status, release_date, id)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_knowledge (
            id {id_column},
            industry TEXT NOT NULL DEFAULT '',
            company_size TEXT NOT NULL DEFAULT '',
            project_summary TEXT NOT NULL DEFAULT '',
            adopted_proposal TEXT NOT NULL DEFAULT '',
            proposal_story TEXT NOT NULL DEFAULT '',
            adoption_reason TEXT NOT NULL DEFAULT '',
            lost_reason TEXT NOT NULL DEFAULT '',
            result TEXT NOT NULL DEFAULT '',
            owner_memo TEXT NOT NULL DEFAULT '',
            outcome TEXT NOT NULL DEFAULT 'unknown',
            rating INTEGER NOT NULL DEFAULT 3,
            evaluation_status TEXT NOT NULL DEFAULT 'effective',
            tags TEXT NOT NULL DEFAULT '',
            approval_status TEXT NOT NULL DEFAULT 'draft',
            quality_score INTEGER NOT NULL DEFAULT 50,
            confidential_risk TEXT NOT NULL DEFAULT 'low',
            confidential_flags TEXT NOT NULL DEFAULT '',
            source_type TEXT NOT NULL DEFAULT 'admin_created',
            source_note TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_knowledge_industry ON proposal_knowledge(industry, rating, outcome)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_templates (
            id {id_column},
            category TEXT NOT NULL DEFAULT 'other',
            title TEXT NOT NULL,
            template_summary TEXT NOT NULL DEFAULT '',
            structure TEXT NOT NULL DEFAULT '',
            recommended_for TEXT NOT NULL DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(created_by) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_templates_category ON proposal_templates(category, is_active)",
        f"""
        CREATE TABLE IF NOT EXISTS workspace_conversations (
            id {id_column},
            project_id TEXT NOT NULL,
            user_id INTEGER,
            client_message_id TEXT NOT NULL DEFAULT '',
            agent_name TEXT NOT NULL DEFAULT '',
            message_type TEXT NOT NULL DEFAULT 'normal',
            message_body TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_workspace_conversations_project ON workspace_conversations(project_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_workspace_conversations_client_id ON workspace_conversations(project_id, user_id, client_message_id)",
        f"""
        CREATE TABLE IF NOT EXISTS workspace_work_logs (
            id {id_column},
            project_id TEXT NOT NULL,
            user_id INTEGER,
            client_log_id TEXT NOT NULL DEFAULT '',
            agent_name TEXT NOT NULL DEFAULT '',
            action_summary TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_workspace_work_logs_project ON workspace_work_logs(project_id, created_at)",
        "CREATE INDEX IF NOT EXISTS idx_workspace_work_logs_client_id ON workspace_work_logs(project_id, user_id, client_log_id)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_reviews (
            id {id_column},
            project_id TEXT NOT NULL,
            project_name TEXT NOT NULL DEFAULT '',
            creator_user_id INTEGER,
            status TEXT NOT NULL DEFAULT 'draft',
            review_comment TEXT NOT NULL DEFAULT '',
            reviewer_user_id INTEGER,
            review_requested_at TEXT,
            reviewed_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(creator_user_id) REFERENCES users(id),
            FOREIGN KEY(reviewer_user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_reviews_project ON proposal_reviews(project_id, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_proposal_reviews_status ON proposal_reviews(status, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS proposal_review_revisions (
            id {id_column},
            review_id INTEGER NOT NULL,
            project_id TEXT NOT NULL,
            previous_status TEXT NOT NULL DEFAULT '',
            next_status TEXT NOT NULL DEFAULT '',
            review_comment TEXT NOT NULL DEFAULT '',
            ai_improvement_policy TEXT NOT NULL DEFAULT '',
            diff_summary TEXT NOT NULL DEFAULT '',
            executed_by_user_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(review_id) REFERENCES proposal_reviews(id),
            FOREIGN KEY(executed_by_user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_proposal_review_revisions_review ON proposal_review_revisions(review_id, created_at)",
        f"""
        CREATE TABLE IF NOT EXISTS quality_gates (
            id {id_column},
            project_id TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            checklist_items TEXT NOT NULL DEFAULT '',
            completed INTEGER NOT NULL DEFAULT 0,
            completed_at TEXT,
            bypassed INTEGER NOT NULL DEFAULT 0,
            bypass_reason TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_quality_gates_project ON quality_gates(project_id, updated_at)",
        f"""
        CREATE TABLE IF NOT EXISTS beautiful_ai_presentations (
            id {id_column},
            project_id TEXT NOT NULL,
            user_id INTEGER,
            presentation_id TEXT NOT NULL DEFAULT '',
            title TEXT NOT NULL DEFAULT '',
            editor_url TEXT NOT NULL DEFAULT '',
            player_url TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'created',
            theme_id TEXT NOT NULL DEFAULT '',
            provider TEXT NOT NULL DEFAULT 'beautiful.ai',
            request_summary TEXT NOT NULL DEFAULT '',
            error_type TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_beautiful_ai_presentations_project ON beautiful_ai_presentations(project_id, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_beautiful_ai_presentations_presentation ON beautiful_ai_presentations(presentation_id)",
    ]


def create_tables() -> None:
    with get_db() as db:
        for statement in _schema_statements():
            db.execute(statement)


def add_missing_columns() -> None:
    with get_db() as db:
        _ensure_column(db, "users", "auth_version", "INTEGER NOT NULL DEFAULT 1")
        _ensure_column(db, "users", "pilot_enabled", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "users", "pilot_started_at", "TEXT")
        _ensure_column(db, "users", "pilot_last_used_at", "TEXT")
        _ensure_column(db, "users", "pilot_completed", "INTEGER NOT NULL DEFAULT 0")
        _ensure_column(db, "users", "pilot_note", "TEXT NOT NULL DEFAULT ''")
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
        _ensure_column(db, "experiments", "traffic_ratio", "INTEGER NOT NULL DEFAULT 50")
        _ensure_column(db, "experiments", "status", "TEXT NOT NULL DEFAULT 'draft'")
        _ensure_column(db, "experiments", "winner", "TEXT NOT NULL DEFAULT ''")
        _ensure_column(db, "experiments", "updated_at", "TEXT")
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


def init_db() -> None:
    if not settings.allow_startup_schema_migration:
        return
    create_tables()
    add_missing_columns()


def _ensure_column(db: Any, table_name: str, column_name: str, column_definition: str) -> None:
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


def get_tables_count() -> int:
    with get_db() as db:
        if ENGINE_DIALECT == "sqlite":
            row = db.execute("SELECT COUNT(*) AS count FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'").fetchone()
        elif ENGINE_DIALECT == "postgresql":
            row = db.execute(
                """
                SELECT COUNT(*) AS count
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                """
            ).fetchone()
        else:
            return 0
    return int(row["count"] if row else 0)


def check_db() -> bool:
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return True
    except Exception:
        return False


def get_db_health() -> dict[str, Any]:
    connected = check_db()
    return {
        "db_connected": connected,
        "db_type": get_db_type(),
        "db_tables_count": get_tables_count() if connected else 0,
        "startup_schema_migration_enabled": settings.allow_startup_schema_migration,
    }
