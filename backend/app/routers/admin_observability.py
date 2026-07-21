from __future__ import annotations

import re
from datetime import datetime
from sqlite3 import Connection
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Query

from app.auth import require_roles
from app.db import get_db
from app.repositories import create_audit_log, get_user_context_ids
from app.services.beautiful_ai_service import resolve_beautiful_ai_urls


router = APIRouter(prefix="/api/admin", tags=["admin-observability"])


@router.get("/ai-logs")
async def get_admin_ai_logs(
    date_from: str = "",
    date_to: str = "",
    provider: str = "",
    operation: str = "",
    status: str = "",
    user_id: int | None = None,
    project_id: str = "",
    request_id: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_roles("admin")),
) -> dict[str, Any]:
    with get_db() as db:
        organization_id, workspace_id = get_user_context_ids(db, int(user["id"]))
        items = _collect_ai_logs(db, organization_id, workspace_id)
        filtered = _filter_rows(
            items,
            date_from=date_from,
            date_to=date_to,
            provider=provider,
            operation=operation,
            status=status,
            user_id=user_id,
            project_id=project_id,
            request_id=request_id,
        )
        page_items, total = _paginate(filtered, page, page_size)
        create_audit_log(db, int(user["id"]), "view_ai_logs", "admin_ai_logs", "", "success", "sanitized=true")
    return {"items": page_items, "total": total, "page": page, "page_size": page_size}


@router.get("/proposal-generation-history")
async def get_admin_proposal_generation_history(
    date_from: str = "",
    date_to: str = "",
    user_id: int | None = None,
    project_id: str = "",
    output_type: str = "",
    provider: str = "",
    status: str = "",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: dict = Depends(require_roles("admin")),
) -> dict[str, Any]:
    with get_db() as db:
        organization_id, workspace_id = get_user_context_ids(db, int(user["id"]))
        items = _collect_proposal_history(db, organization_id, workspace_id)
        filtered = _filter_rows(
            items,
            date_from=date_from,
            date_to=date_to,
            provider=provider,
            operation=output_type,
            status=status,
            user_id=user_id,
            project_id=project_id,
        )
        page_items, total = _paginate(filtered, page, page_size)
        create_audit_log(db, int(user["id"]), "view_proposal_generation_history", "proposal_histories", "", "success", "sanitized=true")
    return {"items": page_items, "total": total, "page": page, "page_size": page_size}


def _collect_ai_logs(db: Connection, organization_id: int, workspace_id: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    items.extend(_usage_log_rows(db, organization_id, workspace_id))
    items.extend(_audit_log_rows(db, organization_id, workspace_id))
    items.extend(_analytics_event_rows(db, organization_id, workspace_id))
    items.extend(_beautiful_ai_rows(db, organization_id, workspace_id))
    return sorted(items, key=lambda item: str(item.get("created_at") or ""), reverse=True)


def _usage_log_rows(db: Connection, organization_id: int, workspace_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT l.id, l.created_at, l.user_id, COALESCE(u.email, '') AS user_email,
               l.feature_name, l.output_type, l.status, l.error_type
        FROM usage_logs l
        LEFT JOIN users u ON u.id = l.user_id
        WHERE l.organization_id = ? AND l.workspace_id = ?
        ORDER BY l.created_at DESC, l.id DESC
        LIMIT 500
        """,
        (organization_id, workspace_id),
    ).fetchall()
    return [
        {
            "id": f"usage-{row['id']}",
            "source": "usage_logs",
            "created_at": str(row["created_at"] or ""),
            "provider": _provider_from_output(str(row["output_type"] or "")),
            "operation": str(row["feature_name"] or row["output_type"] or ""),
            "status": _status_label(str(row["status"] or "")),
            "user_id": row["user_id"],
            "user": _mask_email(str(row["user_email"] or "")),
            "project_id": "",
            "project": "",
            "duration_ms": 0,
            "request_id": "",
            "error_type": _safe_token(str(row["error_type"] or "")),
            "retry_count": 0,
            "summary": f"output_type={_safe_token(str(row['output_type'] or ''))}",
        }
        for row in rows
    ]


def _audit_log_rows(db: Connection, organization_id: int, workspace_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT a.id, a.created_at, a.user_id, COALESCE(u.email, '') AS user_email,
               a.event_type, a.target_type, a.target_id, a.status, a.request_id, a.error_type, a.http_status
        FROM audit_logs a
        LEFT JOIN users u ON u.id = a.user_id
        WHERE a.organization_id = ? AND a.workspace_id = ?
        ORDER BY a.created_at DESC, a.id DESC
        LIMIT 500
        """,
        (organization_id, workspace_id),
    ).fetchall()
    return [
        {
            "id": f"audit-{row['id']}",
            "source": "audit_logs",
            "created_at": str(row["created_at"] or ""),
            "provider": "system",
            "operation": str(row["event_type"] or ""),
            "status": _status_label(str(row["status"] or "")),
            "user_id": row["user_id"],
            "user": _mask_email(str(row["user_email"] or "")),
            "project_id": str(row["target_id"] or "") if str(row["target_type"] or "") in {"project", "proposal", "proposal_histories"} else "",
            "project": "",
            "duration_ms": 0,
            "request_id": _safe_token(str(row["request_id"] or "")),
            "error_type": _safe_token(str(row["error_type"] or "")),
            "retry_count": 0,
            "summary": f"target={_safe_token(str(row['target_type'] or ''))};http_status={int(row['http_status'] or 0)}",
        }
        for row in rows
    ]


def _analytics_event_rows(db: Connection, organization_id: int, workspace_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT e.id, e.created_at, e.user_id, COALESCE(u.email, '') AS user_email,
               e.event_name, e.feature_name, e.status, e.duration_ms
        FROM analytics_events e
        LEFT JOIN users u ON u.id = e.user_id
        WHERE e.organization_id = ? AND e.workspace_id = ?
        ORDER BY e.created_at DESC, e.id DESC
        LIMIT 500
        """,
        (organization_id, workspace_id),
    ).fetchall()
    return [
        {
            "id": f"analytics-{row['id']}",
            "source": "analytics_events",
            "created_at": str(row["created_at"] or ""),
            "provider": "frontend",
            "operation": str(row["feature_name"] or row["event_name"] or ""),
            "status": _status_label(str(row["status"] or "")),
            "user_id": row["user_id"],
            "user": _mask_email(str(row["user_email"] or "")),
            "project_id": "",
            "project": "",
            "duration_ms": int(row["duration_ms"] or 0),
            "request_id": "",
            "error_type": "",
            "retry_count": 0,
            "summary": _safe_text(str(row["event_name"] or ""), 120),
        }
        for row in rows
    ]


def _beautiful_ai_rows(db: Connection, organization_id: int, workspace_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT b.id, b.created_at, b.updated_at, b.user_id, COALESCE(u.email, '') AS user_email,
               b.project_id, b.title, b.status, b.error_type, b.http_status, b.api_mode, b.endpoint
        FROM beautiful_ai_presentations b
        LEFT JOIN users u ON u.id = b.user_id
        WHERE b.organization_id = ? AND b.workspace_id = ?
        ORDER BY b.updated_at DESC, b.id DESC
        LIMIT 500
        """,
        (organization_id, workspace_id),
    ).fetchall()
    return [
        {
            "id": f"beautiful-ai-{row['id']}",
            "source": "beautiful_ai_presentations",
            "created_at": str(row["updated_at"] or row["created_at"] or ""),
            "provider": "beautiful.ai",
            "operation": "beautiful_ai_generation",
            "status": _status_label(str(row["status"] or "")),
            "user_id": row["user_id"],
            "user": _mask_email(str(row["user_email"] or "")),
            "project_id": str(row["project_id"] or ""),
            "project": _safe_text(str(row["title"] or ""), 120),
            "duration_ms": 0,
            "request_id": "",
            "error_type": _safe_token(str(row["error_type"] or "")),
            "retry_count": 0,
            "summary": f"api_mode={_safe_token(str(row['api_mode'] or ''))};http_status={int(row['http_status'] or 0)}",
        }
        for row in rows
    ]


def _collect_proposal_history(db: Connection, organization_id: int, workspace_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT
            h.id, h.created_at, h.user_id, COALESCE(u.email, '') AS user_email,
            h.project_id, COALESCE(p.name, '') AS project_title, h.feature_name,
            h.output_type, h.status, h.error_type,
            (
                SELECT editor_url FROM beautiful_ai_presentations b
                WHERE b.organization_id = h.organization_id
                  AND b.workspace_id = h.workspace_id
                  AND COALESCE(b.project_id, '') = COALESCE(CAST(h.project_id AS TEXT), '')
                ORDER BY b.updated_at DESC, b.id DESC
                LIMIT 1
            ) AS editor_url,
            (
                SELECT player_url FROM beautiful_ai_presentations b
                WHERE b.organization_id = h.organization_id
                  AND b.workspace_id = h.workspace_id
                  AND COALESCE(b.project_id, '') = COALESCE(CAST(h.project_id AS TEXT), '')
                ORDER BY b.updated_at DESC, b.id DESC
                LIMIT 1
            ) AS player_url,
            (
                SELECT response_text FROM beautiful_ai_presentations b
                WHERE b.organization_id = h.organization_id
                  AND b.workspace_id = h.workspace_id
                  AND COALESCE(b.project_id, '') = COALESCE(CAST(h.project_id AS TEXT), '')
                ORDER BY b.updated_at DESC, b.id DESC
                LIMIT 1
            ) AS response_text
        FROM proposal_histories h
        LEFT JOIN users u ON u.id = h.user_id
        LEFT JOIN projects p ON p.id = h.project_id
        WHERE h.organization_id = ? AND h.workspace_id = ?
        ORDER BY h.created_at DESC, h.id DESC
        LIMIT 600
        """,
        (organization_id, workspace_id),
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        resolved = resolve_beautiful_ai_urls(
            stored_editor_url=str(row["editor_url"] or ""),
            stored_player_url=str(row["player_url"] or ""),
            response_text=str(row["response_text"] or ""),
        )
        output_type = str(row["output_type"] or "")
        open_url = resolved["editor_url"] or resolved["player_url"]
        items.append(
            {
                "id": int(row["id"]),
                "created_at": str(row["created_at"] or ""),
                "user_id": row["user_id"],
                "user": _mask_email(str(row["user_email"] or "")),
                "project_id": str(row["project_id"] or ""),
                "project_title": _safe_text(str(row["project_title"] or ""), 120),
                "output_type": _safe_token(output_type),
                "provider": _provider_from_output(output_type),
                "status": _status_label(str(row["status"] or "")),
                "duration_ms": 0,
                "error_type": _safe_token(str(row["error_type"] or "")),
                "downloadable": False,
                "external_url_available": bool(open_url),
                "open_url": open_url if _is_safe_external_url(open_url) else "",
                "summary": _safe_text(str(row["feature_name"] or ""), 120),
            }
        )
    return items


def _filter_rows(
    rows: list[dict[str, Any]],
    *,
    date_from: str = "",
    date_to: str = "",
    provider: str = "",
    operation: str = "",
    status: str = "",
    user_id: int | None = None,
    project_id: str = "",
    request_id: str = "",
) -> list[dict[str, Any]]:
    provider_key = provider.strip().lower()
    operation_key = operation.strip().lower()
    status_key = status.strip().lower()
    project_key = project_id.strip()
    request_key = request_id.strip()
    filtered = []
    for row in rows:
        created_at = str(row.get("created_at") or "")
        if date_from and created_at < date_from[:30]:
            continue
        if date_to and created_at > date_to[:30]:
            continue
        if provider_key and provider_key not in str(row.get("provider", "")).lower():
            continue
        if operation_key:
            haystack = f"{row.get('operation', '')} {row.get('output_type', '')}".lower()
            if operation_key not in haystack:
                continue
        if status_key and status_key != str(row.get("status", "")).lower():
            continue
        if user_id is not None and row.get("user_id") != user_id:
            continue
        if project_key and project_key not in str(row.get("project_id", "")):
            continue
        if request_key and request_key not in str(row.get("request_id", "")):
            continue
        filtered.append(row)
    return filtered


def _paginate(rows: list[dict[str, Any]], page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    return rows[start:end], total


def _provider_from_output(output_type: str) -> str:
    value = output_type.lower()
    if "beautiful" in value:
        return "beautiful.ai"
    if "pptx" in value or "pdf" in value:
        return "proposalpilot"
    return "proposalpilot"


def _status_label(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in {"created", "succeeded", "completed", "mock"}:
        return "success"
    if lowered in {"failed", "failure", "error"}:
        return "failure"
    if lowered in {"success", "start"}:
        return lowered
    return lowered or "unknown"


def _safe_token(value: str, limit: int = 80) -> str:
    return re.sub(r"[^A-Za-z0-9_.:/@-]", "", value)[:limit]


def _safe_text(value: str, limit: int = 160) -> str:
    text = re.sub(r"(?i)(api[_-]?key|authorization|password|token|secret)\s*[:=]\s*\S+", "[secret]", value or "")
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", text)
    return text[:limit]


def _mask_email(email: str) -> str:
    if "@" not in email:
        return ""
    local, domain = email.split("@", 1)
    if not local:
        return f"***@{domain}"
    return f"{local[:1]}***@{domain}"


def _is_safe_external_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme == "https" and bool(parsed.netloc)
