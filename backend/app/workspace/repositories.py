from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from app.repositories import create_audit_log, get_user_context_ids
from app.scoping.service import attach_project_scope
from app.workspace.services import (
    build_workspace_summary,
    normalize_agent_name,
    normalize_message_type,
    normalize_status,
    sanitize_workspace_text,
)


def _row_to_dicts(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def save_workspace_bundle(
    db: Connection,
    user_id: int,
    project_id: str,
    conversations: list[dict[str, Any]],
    work_logs: list[dict[str, Any]],
) -> dict[str, int | str]:
    safe_project_id = sanitize_workspace_text(project_id, 120) or "default"
    fallback_org, fallback_workspace = get_user_context_ids(db, user_id)
    organization_id, workspace_id = attach_project_scope(
        db,
        project_id=safe_project_id,
        fallback_context=(fallback_org, fallback_workspace),
    )
    saved_conversations = 0
    saved_logs = 0

    for item in conversations[:80]:
        client_message_id = sanitize_workspace_text(str(item.get("client_message_id") or item.get("id") or ""), 120)
        if not client_message_id:
            continue
        agent_name = normalize_agent_name(str(item.get("agent_name") or ""))
        message_type = normalize_message_type(str(item.get("message_type") or "normal"))
        message_body = sanitize_workspace_text(str(item.get("message_body") or ""))
        status = normalize_status(str(item.get("status") or "active"))
        existing = db.execute(
            """
            SELECT id FROM workspace_conversations
            WHERE project_id = ? AND user_id = ? AND client_message_id = ?
              AND organization_id = ? AND workspace_id = ?
            """,
            (safe_project_id, user_id, client_message_id, organization_id, workspace_id),
        ).fetchone()
        if existing:
            db.execute(
                """
                UPDATE workspace_conversations
                SET agent_name = ?, message_type = ?, message_body = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND organization_id = ? AND workspace_id = ?
                """,
                (agent_name, message_type, message_body, status, existing["id"], organization_id, workspace_id),
            )
        else:
            db.execute(
                """
                INSERT INTO workspace_conversations
                (project_id, user_id, client_message_id, agent_name, message_type, message_body, status, organization_id, workspace_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    safe_project_id,
                    user_id,
                    client_message_id,
                    agent_name,
                    message_type,
                    message_body,
                    status,
                    organization_id,
                    workspace_id,
                ),
            )
        saved_conversations += 1

    for item in work_logs[:80]:
        client_log_id = sanitize_workspace_text(str(item.get("client_log_id") or item.get("id") or ""), 120)
        if not client_log_id:
            continue
        agent_name = normalize_agent_name(str(item.get("agent_name") or ""))
        action_summary = sanitize_workspace_text(str(item.get("action_summary") or ""))
        status = normalize_status(str(item.get("status") or "active"))
        existing = db.execute(
            """
            SELECT id FROM workspace_work_logs
            WHERE project_id = ? AND user_id = ? AND client_log_id = ?
              AND organization_id = ? AND workspace_id = ?
            """,
            (safe_project_id, user_id, client_log_id, organization_id, workspace_id),
        ).fetchone()
        if existing:
            db.execute(
                """
                UPDATE workspace_work_logs
                SET agent_name = ?, action_summary = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND organization_id = ? AND workspace_id = ?
                """,
                (agent_name, action_summary, status, existing["id"], organization_id, workspace_id),
            )
        else:
            db.execute(
                """
                INSERT INTO workspace_work_logs
                (project_id, user_id, client_log_id, agent_name, action_summary, status, organization_id, workspace_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (safe_project_id, user_id, client_log_id, agent_name, action_summary, status, organization_id, workspace_id),
            )
        saved_logs += 1

    if saved_conversations or saved_logs:
        create_audit_log(
            db,
            user_id,
            "save",
            "workspace_conversation",
            safe_project_id,
            "success",
            f"messages={saved_conversations};logs={saved_logs}",
        )

    return {"project_id": safe_project_id, "saved_conversations": saved_conversations, "saved_logs": saved_logs}


def list_workspace_conversations(db: Connection, limit: int = 100, user_id: int | None = None) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    rows = db.execute(
        """
        SELECT c.*, u.email AS user_email
        FROM workspace_conversations c
        LEFT JOIN users u ON u.id = c.user_id
        WHERE c.organization_id = ? AND c.workspace_id = ?
        ORDER BY c.created_at DESC
        LIMIT ?
        """,
        (organization_id, workspace_id, limit),
    ).fetchall()
    return _row_to_dicts(rows)


def get_workspace_conversation_bundle(db: Connection, project_id: str, user_id: int | None = None) -> dict[str, Any]:
    safe_project_id = sanitize_workspace_text(project_id, 120) or "default"
    fallback_org, fallback_workspace = get_user_context_ids(db, user_id)
    organization_id, workspace_id = attach_project_scope(
        db,
        project_id=safe_project_id,
        fallback_context=(fallback_org, fallback_workspace),
    )
    conversation_rows = db.execute(
        """
        SELECT c.*, u.email AS user_email
        FROM workspace_conversations c
        LEFT JOIN users u ON u.id = c.user_id
        WHERE c.project_id = ? AND c.organization_id = ? AND c.workspace_id = ?
        ORDER BY c.created_at ASC, c.id ASC
        """,
        (safe_project_id, organization_id, workspace_id),
    ).fetchall()
    log_rows = db.execute(
        """
        SELECT l.*, u.email AS user_email
        FROM workspace_work_logs l
        LEFT JOIN users u ON u.id = l.user_id
        WHERE l.project_id = ? AND l.organization_id = ? AND l.workspace_id = ?
        ORDER BY l.created_at ASC, l.id ASC
        """,
        (safe_project_id, organization_id, workspace_id),
    ).fetchall()
    return {
        "project_id": safe_project_id,
        "conversations": _row_to_dicts(conversation_rows),
        "work_logs": _row_to_dicts(log_rows),
    }


def get_workspace_summary(db: Connection, project_id: str, user_id: int | None = None) -> dict[str, Any]:
    bundle = get_workspace_conversation_bundle(db, project_id, user_id)
    return build_workspace_summary(str(bundle["project_id"]), bundle["conversations"], bundle["work_logs"])
