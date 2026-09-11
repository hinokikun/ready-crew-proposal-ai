from __future__ import annotations

import logging
from pathlib import Path
import re
from typing import Any

from app.config import settings
from app.database.connection import DB_CONNECT_STAGES, ENGINE_DIALECT, get_db, get_db_type
from app.database.migration import _existing_columns, _quality_gate_unique_state, _table_exists


logger = logging.getLogger(__name__)


_DB_FAILURE_CATEGORIES = frozenset({
    "authentication",
    "dns",
    "connection_refused",
    "timeout",
    "ssl",
    "database_unavailable",
    "unknown",
})


def _safe_sqlstate(error: BaseException) -> str | None:
    candidates: list[Any] = [error]
    try:
        original = getattr(error, "orig", None)
    except Exception:
        original = None
    if original is not None:
        candidates.append(original)
    for candidate in candidates:
        for attribute in ("sqlstate", "pgcode"):
            try:
                value = getattr(candidate, attribute, None)
            except Exception:
                continue
            if isinstance(value, str) and re.fullmatch(r"[0-9A-Za-z]{5}", value):
                return value
    return None


def _db_failure_category(error: BaseException, sqlstate: str | None) -> str:
    if sqlstate:
        if sqlstate.startswith("28"):
            return "authentication"
        if sqlstate.startswith("08"):
            return "database_unavailable"
    exception_class = type(error).__name__.lower()
    if exception_class in {"timeouterror", "connecttimeouterror"}:
        return "timeout"
    if exception_class in {"sslerror", "sslsyscallerror", "sslcertverificationerror"}:
        return "ssl"
    if exception_class in {"gaierror", "dnserror"}:
        return "dns"
    if exception_class == "connectionrefusederror":
        return "connection_refused"
    if exception_class in {"authenticationerror", "invalidpassworderror"}:
        return "authentication"
    if exception_class in {"operationalerror", "interfaceerror", "connectionerror"}:
        return "database_unavailable"
    return "unknown"


def _safe_connect_stage(error: BaseException) -> str | None:
    try:
        stage = getattr(error, "_db_connect_stage", None)
    except Exception:
        return None
    return stage if isinstance(stage, str) and stage in DB_CONNECT_STAGES else None


def get_schema_readiness() -> dict[str, Any]:
    required_columns = {
        "organizations": {"is_active"},
        "workspaces": {"organization_id", "is_active"},
        "organization_memberships": {"user_id", "organization_id", "workspace_id", "membership_role"},
        "users": {"current_organization_id", "current_workspace_id"},
        "projects": {"organization_id", "workspace_id"},
        "proposal_histories": {
            "project_name",
            "proposal_generation_duration_ms",
            "powerpoint_generation_duration_ms",
            "beautiful_ai_generation_duration_ms",
            "pdf_generation_duration_ms",
            "total_generation_duration_ms",
            "is_demo",
        },
        "business_improvement_reports": {
            "before_minutes",
            "ai_input_minutes",
            "ai_wait_minutes",
            "total_after_minutes",
            "saved_minutes",
            "reduction_rate",
            "quality_score",
            "is_demo",
            "organization_id",
            "workspace_id",
        },
        "proposal_agent_memories": {
            "project_id",
            "project_name",
            "hearing_notes",
            "confirmation_items",
            "proposal_content",
            "competitor_analysis",
            "improvement_history",
            "organization_id",
            "workspace_id",
        },
        "quality_gates": {"organization_id", "workspace_id", "project_id"},
        "prompt_versions": {"organization_id", "workspace_id", "scope_type", "scope_id"},
        "experiments": {"organization_id", "workspace_id", "scope_type", "scope_id"},
        "audit_logs": {"organization_id", "workspace_id", "actor_role", "request_id"},
    }
    missing: list[str] = []
    with get_db() as db:
        for table_name, expected_columns in required_columns.items():
            columns = _existing_columns(db, table_name)
            if not columns:
                missing.append(f"{table_name}.*")
                continue
            for column_name in sorted(expected_columns - columns):
                missing.append(f"{table_name}.{column_name}")
        quality_gate_unique = _quality_gate_unique_state(db)
    ready = not missing and bool(quality_gate_unique["scoped"]) and not bool(quality_gate_unique["legacy_project_unique"])
    return {
        "schema_ready": ready,
        "schema_missing": missing,
        "quality_gate_unique_scoped": bool(quality_gate_unique["scoped"]),
        "quality_gate_legacy_project_unique": bool(quality_gate_unique["legacy_project_unique"]),
    }


def get_migration_state() -> dict[str, Any]:
    current = ""
    head = ""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        alembic_config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        script = ScriptDirectory.from_config(alembic_config)
        head = str(script.get_current_head() or "")
    except Exception:
        head = ""

    try:
        with get_db() as db:
            if _table_exists(db, "alembic_version"):
                row = db.execute("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1").fetchone()
                current = str(row["version_num"] if row else "")
    except Exception:
        current = ""

    schema = get_schema_readiness() if check_db() else {
        "schema_ready": False,
        "schema_missing": ["database"],
        "quality_gate_unique_scoped": False,
        "quality_gate_legacy_project_unique": False,
    }
    revision_ready = bool(current and head and current == head)
    if not revision_ready and settings.allow_startup_schema_migration and not current and schema["schema_ready"]:
        # Local/dev databases may be patched by startup DDL before Alembic is introduced.
        revision_ready = True
        current = "startup_schema_patch"
    return {
        "migration_current": current,
        "migration_head": head,
        "migration_ready": bool(revision_ready and schema["schema_ready"]),
        **schema,
    }


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
    except Exception as exc:
        sqlstate = _safe_sqlstate(exc)
        failure_category = _db_failure_category(exc, sqlstate)
        connect_stage = _safe_connect_stage(exc)
        if failure_category not in _DB_FAILURE_CATEGORIES:
            failure_category = "unknown"
        fields: dict[str, str] = {
            "db_connect_stage": connect_stage or "unknown",
            "db_dialect": ENGINE_DIALECT,
            "exception_class": type(exc).__name__,
            "failure_category": failure_category,
        }
        if sqlstate is not None:
            fields["sqlstate"] = sqlstate
        message = "database_connectivity_failed db_connect_stage={db_connect_stage} db_dialect={db_dialect} exception_class={exception_class} failure_category={failure_category}".format(**fields)
        if sqlstate is not None:
            message += " sqlstate=" + sqlstate
        logger.warning(message)
        return False


def get_db_health() -> dict[str, Any]:
    connected = check_db()
    migration_state = get_migration_state() if connected else {
        "migration_current": "",
        "migration_head": "",
        "migration_ready": False,
        "schema_ready": False,
        "schema_missing": ["database"],
        "quality_gate_unique_scoped": False,
        "quality_gate_legacy_project_unique": False,
    }
    return {
        "db_connected": connected,
        "db_type": get_db_type(),
        "db_tables_count": get_tables_count() if connected else 0,
        "startup_schema_migration_enabled": settings.allow_startup_schema_migration,
        **migration_state,
    }
