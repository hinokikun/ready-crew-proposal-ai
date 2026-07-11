from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from app.analytics.repositories import (
    build_product_analytics_dashboard,
    create_release_note,
    list_release_notes,
    record_analytics_event,
    update_error_resolved,
)


def record_event(
    db: Connection,
    *,
    user_id: int | None,
    session_key: str,
    event_name: str,
    feature_name: str = "",
    status: str = "success",
    duration_ms: int = 0,
    error_type: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return record_analytics_event(
        db,
        user_id=user_id,
        session_key=session_key,
        event_name=event_name,
        feature_name=feature_name,
        status=status,
        duration_ms=duration_ms,
        error_type=error_type,
        metadata=metadata,
    )


def get_dashboard(db: Connection, limit: int = 20, offset: int = 0) -> dict[str, Any]:
    return build_product_analytics_dashboard(db, limit, offset)


def set_error_resolved(db: Connection, error_id: int, resolved: bool) -> dict[str, Any] | None:
    return update_error_resolved(db, error_id, resolved)


def get_release_notes(db: Connection, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    return list_release_notes(db, limit, offset)


def add_release_note(
    db: Connection,
    *,
    user_id: int,
    version: str,
    release_date: str,
    title: str,
    improvements: str,
) -> dict[str, Any]:
    return create_release_note(
        db,
        user_id=user_id,
        version=version,
        release_date=release_date,
        title=title,
        improvements=improvements,
    )
