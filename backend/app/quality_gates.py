import json
from sqlite3 import Connection
from typing import Any

from fastapi import HTTPException

from app.repositories import create_audit_log, get_user_context_ids
from app.scoping.service import attach_project_scope
from app.workspace.services import sanitize_workspace_text


MAX_CHECKLIST_ITEMS = 20
MAX_ITEM_LENGTH = 140


def _safe_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items[:MAX_CHECKLIST_ITEMS]:
        value = sanitize_workspace_text(item, MAX_ITEM_LENGTH)
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return cleaned


def _row_to_gate(row: Any | None) -> dict[str, Any] | None:
    if not row:
        return None
    gate = dict(row)
    try:
        gate["checklist_items"] = json.loads(gate.get("checklist_items") or "[]")
    except json.JSONDecodeError:
        gate["checklist_items"] = []
    gate["completed"] = bool(gate.get("completed"))
    gate["bypassed"] = bool(gate.get("bypassed"))
    gate["download_unlocked"] = bool(gate["completed"] or gate["bypassed"])
    return gate


def _gate_scope(db: Connection, project_id: str, user_id: int | None) -> tuple[int, int]:
    fallback_org, fallback_workspace = get_user_context_ids(db, user_id)
    return attach_project_scope(db, project_id=project_id, fallback_context=(fallback_org, fallback_workspace))


def get_quality_gate(db: Connection, project_id: str, user_id: int | None = None) -> dict[str, Any] | None:
    if user_id is None:
        row = db.execute("SELECT * FROM quality_gates WHERE project_id = ?", (project_id,)).fetchone()
    else:
        organization_id, workspace_id = _gate_scope(db, project_id, user_id)
        row = db.execute(
            "SELECT * FROM quality_gates WHERE project_id = ? AND organization_id = ? AND workspace_id = ?",
            (project_id, organization_id, workspace_id),
        ).fetchone()
    return _row_to_gate(row)


def save_quality_gate(db: Connection, project_id: str, user_id: int, checklist_items: list[str]) -> dict[str, Any]:
    items = _safe_items(checklist_items)
    encoded_items = json.dumps(items, ensure_ascii=False)
    organization_id, workspace_id = _gate_scope(db, project_id, user_id)
    existing = get_quality_gate(db, project_id, user_id)
    if existing:
        db.execute(
            """
            UPDATE quality_gates
            SET user_id = ?, checklist_items = ?, updated_at = CURRENT_TIMESTAMP
            WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
            """,
            (user_id, encoded_items, project_id, organization_id, workspace_id),
        )
    else:
        db.execute(
            """
            INSERT INTO quality_gates (project_id, user_id, checklist_items, organization_id, workspace_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, user_id, encoded_items, organization_id, workspace_id),
        )
        create_audit_log(db, user_id, "quality_gate_start", "quality_gate", project_id, "success", "started")
    return get_quality_gate(db, project_id, user_id) or {}


def complete_quality_gate(db: Connection, project_id: str, user_id: int, checklist_items: list[str]) -> dict[str, Any]:
    items = _safe_items(checklist_items)
    if not items:
        raise HTTPException(status_code=400, detail="提出前確認項目をチェックしてください。")
    encoded_items = json.dumps(items, ensure_ascii=False)
    organization_id, workspace_id = _gate_scope(db, project_id, user_id)
    if get_quality_gate(db, project_id, user_id):
        db.execute(
            """
            UPDATE quality_gates
            SET user_id = ?,
                checklist_items = ?,
                completed = 1,
                completed_at = CURRENT_TIMESTAMP,
                bypassed = 0,
                bypass_reason = '',
                updated_at = CURRENT_TIMESTAMP
            WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
            """,
            (user_id, encoded_items, project_id, organization_id, workspace_id),
        )
    else:
        db.execute(
            """
            INSERT INTO quality_gates (project_id, user_id, checklist_items, completed, completed_at, organization_id, workspace_id)
            VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, ?, ?)
            """,
            (project_id, user_id, encoded_items, organization_id, workspace_id),
        )
        create_audit_log(db, user_id, "quality_gate_start", "quality_gate", project_id, "success", "started")
    create_audit_log(db, user_id, "quality_gate_complete", "quality_gate", project_id, "success", f"items={len(items)}")
    return get_quality_gate(db, project_id, user_id) or {}


def bypass_quality_gate(db: Connection, project_id: str, user_id: int, bypass_reason: str) -> dict[str, Any]:
    reason = sanitize_workspace_text(bypass_reason, 240)
    if not reason:
        raise HTTPException(status_code=400, detail="管理者バイパスには理由が必要です。")
    organization_id, workspace_id = _gate_scope(db, project_id, user_id)
    if get_quality_gate(db, project_id, user_id):
        db.execute(
            """
            UPDATE quality_gates
            SET user_id = ?,
                bypassed = 1,
                completed = 0,
                completed_at = CURRENT_TIMESTAMP,
                bypass_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
            """,
            (user_id, reason, project_id, organization_id, workspace_id),
        )
    else:
        db.execute(
            """
            INSERT INTO quality_gates (project_id, user_id, bypassed, completed_at, bypass_reason, organization_id, workspace_id)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP, ?, ?, ?)
            """,
            (project_id, user_id, reason, organization_id, workspace_id),
        )
        create_audit_log(db, user_id, "quality_gate_start", "quality_gate", project_id, "success", "started")
    create_audit_log(db, user_id, "quality_gate_bypass", "quality_gate", project_id, "success", "admin_override")
    create_audit_log(db, user_id, "quality_gate_bypass_reason", "quality_gate", project_id, "success", "reason_recorded")
    return get_quality_gate(db, project_id, user_id) or {}
