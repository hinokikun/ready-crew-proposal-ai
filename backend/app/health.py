from typing import Any

from fastapi import FastAPI

from app.config import settings
from app.db import get_db_health
from app.deployment_info import get_git_metadata
from app.observability import utc_timestamp
from app.services.beautiful_ai_service import _api_mode, _endpoint


def build_health_payload(app: FastAPI) -> dict[str, Any]:
    db_health = get_db_health()
    auth_configured = bool(settings.app_auth_secret and (settings.initial_admin_email or settings.app_access_password))
    db_connected = bool(db_health["db_connected"])
    db_ready = db_connected and int(db_health.get("db_tables_count", 0)) > 0
    migration_ready = bool(db_health.get("migration_ready", False))
    ai_api = "mock" if settings.use_mock_ai else ("configured" if settings.openai_api_key else "missing")
    ready = auth_configured and db_ready and migration_ready and ai_api != "missing"
    beautiful_ai_status_route_registered = any(
        getattr(route, "path", "") == "/api/beautiful-ai/status" and "GET" in getattr(route, "methods", set())
        for route in app.routes
    )
    return {
        "status": "ok" if ready else "degraded",
        "app_version": settings.app_version,
        "environment": settings.environment,
        "git": get_git_metadata(),
        "routes": {
            "beautiful_ai_status": "/api/beautiful-ai/status",
            "beautiful_ai_status_registered": beautiful_ai_status_route_registered,
            "beautiful_ai_docs_tag": "beautiful-ai",
        },
        "beautiful_ai": {
            "enabled": bool(settings.beautiful_ai_enabled),
            "configured": bool(settings.beautiful_ai_api_key or settings.beautiful_ai_mock),
            "mock": bool(settings.beautiful_ai_mock),
            "api_mode": _api_mode(),
            "resolved_endpoint": _endpoint(),
            "route_registered": beautiful_ai_status_route_registered,
        },
        "auth_configured": auth_configured,
        "pilot_mode": settings.pilot_mode,
        "pilot_start_date": settings.pilot_start_date,
        "pilot_end_date": settings.pilot_end_date,
        "pilot_max_users": settings.pilot_max_users,
        "maintenance_mode": settings.maintenance_mode,
        "mock_ai": settings.use_mock_ai,
        "ai_api": ai_api,
        "pptx": "available",
        "pdf": "available",
        "db": "connected" if db_connected else "error",
        "db_connected": db_connected,
        "db_type": db_health["db_type"],
        "db_tables_count": db_health["db_tables_count"],
        "startup_schema_migration_enabled": db_health.get("startup_schema_migration_enabled", False),
        "migration_current": db_health.get("migration_current", ""),
        "migration_head": db_health.get("migration_head", ""),
        "migration_ready": migration_ready,
        "schema_ready": db_health.get("schema_ready", False),
        "schema_missing": db_health.get("schema_missing", []),
        "quality_gate_unique_scoped": db_health.get("quality_gate_unique_scoped", False),
        "quality_gate_legacy_project_unique": db_health.get("quality_gate_legacy_project_unique", False),
        "timestamp": utc_timestamp(),
    }
