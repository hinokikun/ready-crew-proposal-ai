from __future__ import annotations

import logging
from threading import Lock
from pathlib import Path
import re
from typing import Any

from sqlalchemy.engine import make_url

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

_PSYCOPG_IMPLEMENTATIONS = frozenset({"python", "c", "binary"})
_DATABASE_URL_QUERY_KEYS = (
    "sslmode",
    "sslrootcert",
    "connect_timeout",
    "target_session_attrs",
)
_PREFLIGHT_STATUSES = frozenset({"success", "failure", "not_run"})
_PREFLIGHT_EXCEPTION_CLASSES = frozenset({
    "AssertionError",
    "OperationalError",
    "ProgrammingError",
    "InterfaceError",
    "DatabaseError",
    "Error",
    "OSError",
    "TimeoutError",
    "gaierror",
})
_conninfo_preflight_cache: dict[str, Any] | None = None
_conninfo_preflight_lock = Lock()


def _disabled_conninfo_preflight() -> dict[str, Any]:
    return {
        "enabled": False,
        "executed": False,
        "conninfo_parse_status": "not_run",
        "timeout_status": "not_run",
        "conninfo_attempts_status": "not_run",
        "attempts_count": "unknown",
        "dns_resolution_status": "unknown",
        "exception_class": "unknown",
    }


def _safe_preflight_exception_class(error: BaseException) -> str:
    name = type(error).__name__
    return name if name in _PREFLIGHT_EXCEPTION_CLASSES else "unknown"


def _preflight_result(enabled: bool) -> dict[str, Any]:
    result = _disabled_conninfo_preflight()
    result["enabled"] = enabled
    if enabled:
        result["dns_resolution_status"] = "unknown"
    return result


def _dns_not_required(params: dict[str, Any]) -> bool:
    host = params.get("host")
    if not host or params.get("hostaddr"):
        return True
    if isinstance(host, str) and (host.startswith("/") or host[1:2] == ":"):
        return True
    try:
        import ipaddress

        return all(ipaddress.ip_address(item.strip("[]")) for item in str(host).split(","))
    except Exception:
        return False


def _run_conninfo_preflight(database_url: str) -> dict[str, Any]:
    result = _preflight_result(True)
    # Reaching this function means the enabled preflight has executed, even
    # when parsing or a later diagnostic step fails.
    result["executed"] = True
    try:
        from psycopg.conninfo import conninfo_attempts, conninfo_to_dict, timeout_from_conninfo
    except Exception as exc:
        result["conninfo_parse_status"] = "failure"
        result["exception_class"] = _safe_preflight_exception_class(exc)
        return result

    try:
        params = conninfo_to_dict(database_url)
        result["conninfo_parse_status"] = "success"
    except Exception as exc:
        result["conninfo_parse_status"] = "failure"
        result["exception_class"] = _safe_preflight_exception_class(exc)
        return result

    try:
        timeout_from_conninfo(params)
        result["timeout_status"] = "success"
    except Exception as exc:
        result["timeout_status"] = "failure"
        result["exception_class"] = _safe_preflight_exception_class(exc)
        return result

    try:
        attempts = conninfo_attempts(params)
        result["conninfo_attempts_status"] = "success"
        result["attempts_count"] = len(attempts) if len(attempts) >= 0 else "unknown"
        result["dns_resolution_status"] = "not_required" if _dns_not_required(params) else "success"
    except Exception as exc:
        result["conninfo_attempts_status"] = "failure"
        result["exception_class"] = _safe_preflight_exception_class(exc)
        return result
    return result


def run_conninfo_preflight_once() -> dict[str, Any]:
    """Run the opt-in conninfo/DNS preflight at most once per process."""
    global _conninfo_preflight_cache
    enabled = bool(getattr(settings, "enable_db_conninfo_preflight", False))
    if not enabled:
        return _disabled_conninfo_preflight()
    with _conninfo_preflight_lock:
        if _conninfo_preflight_cache is None:
            try:
                _conninfo_preflight_cache = _run_conninfo_preflight(settings.database_url)
            except Exception as exc:
                _conninfo_preflight_cache = _preflight_result(True)
                _conninfo_preflight_cache["executed"] = True
                _conninfo_preflight_cache["exception_class"] = _safe_preflight_exception_class(exc)
            _conninfo_preflight_cache["executed"] = True
        return dict(_conninfo_preflight_cache)


def get_conninfo_preflight_diagnostic() -> dict[str, Any]:
    if _conninfo_preflight_cache is None:
        enabled = bool(getattr(settings, "enable_db_conninfo_preflight", False))
        return _preflight_result(enabled)
    return dict(_conninfo_preflight_cache)


def _database_url_scheme(database_url: str) -> str:
    try:
        drivername = make_url(database_url).drivername
    except Exception:
        return "unknown"
    if drivername == "postgresql+psycopg":
        return "postgresql_psycopg"
    if drivername == "postgresql":
        return "postgresql"
    if drivername == "postgres":
        return "postgres"
    if drivername:
        return "other"
    return "unknown"


def _unknown_database_diagnostic() -> dict[str, Any]:
    return {
        "psycopg_implementation": "unknown",
        "libpq_version": "unknown",
        "database_url_scheme": "unknown",
        "database_url_host_present": False,
        "database_url_port_present": False,
        "database_url_username_present": False,
        "database_url_password_present": False,
        **{f"{key}_present": False for key in _DATABASE_URL_QUERY_KEYS},
    }


def get_database_diagnostic() -> dict[str, Any]:
    """Return bounded PostgreSQL metadata without connecting or exposing URL values."""
    diagnostic = _unknown_database_diagnostic()
    diagnostic["conninfo_preflight"] = get_conninfo_preflight_diagnostic()
    if ENGINE_DIALECT != "postgresql":
        return diagnostic

    diagnostic["database_url_scheme"] = _database_url_scheme(settings.database_url)
    try:
        url = make_url(settings.database_url)
        diagnostic.update({
            "database_url_host_present": url.host is not None,
            "database_url_port_present": url.port is not None,
            "database_url_username_present": url.username is not None,
            "database_url_password_present": url.password is not None,
            **{f"{key}_present": key in url.query for key in _DATABASE_URL_QUERY_KEYS},
        })
    except Exception:
        pass

    try:
        import psycopg

        implementation = getattr(psycopg.pq, "__impl__", None)
        if implementation in _PSYCOPG_IMPLEMENTATIONS:
            diagnostic["psycopg_implementation"] = implementation
        version = psycopg.pq.version()
        if isinstance(version, int) and not isinstance(version, bool) and version >= 0:
            diagnostic["libpq_version"] = version
    except Exception:
        pass
    return diagnostic


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
        "database_diagnostic": get_database_diagnostic(),
        **migration_state,
    }
