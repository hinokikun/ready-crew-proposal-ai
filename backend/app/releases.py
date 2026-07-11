import json
import re
from sqlite3 import Connection
from typing import Any

from app.repositories import create_audit_log
from app.workspace.services import sanitize_workspace_text

RELEASE_STATUSES = {"draft", "internal_test", "released", "archived"}


def _clean(value: str | None, max_length: int) -> str:
    text = sanitize_workspace_text(value or "", max_length)
    text = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[redacted-api-key]", text)
    text = re.sub(r"(?i)(api[_-]?key|password|secret)\s*[:=]\s*\S+", r"\1=[redacted]", text)
    return text


def _clean_checklist(items: list[str] | None) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in (items or [])[:30]:
        value = _clean(item, 120)
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return cleaned


def _decode_checklist(value: str) -> list[str]:
    try:
      decoded = json.loads(value or "[]")
    except json.JSONDecodeError:
      return []
    if not isinstance(decoded, list):
      return []
    return [str(item) for item in decoded[:30]]


def _row_to_release(row: Any | None) -> dict[str, Any] | None:
    if not row:
        return None
    release = dict(row)
    release["checklist"] = _decode_checklist(release.get("checklist", ""))
    return release


def list_releases(db: Connection, role: str, limit: int = 50) -> list[dict[str, Any]]:
    if role in {"admin", "manager"}:
        rows = db.execute(
            """
            SELECT r.*, cu.email AS created_by_email, ru.email AS released_by_email
            FROM release_records r
            LEFT JOIN users cu ON cu.id = r.created_by
            LEFT JOIN users ru ON ru.id = r.released_by
            ORDER BY r.release_date DESC, r.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT r.*, cu.email AS created_by_email, ru.email AS released_by_email
            FROM release_records r
            LEFT JOIN users cu ON cu.id = r.created_by
            LEFT JOIN users ru ON ru.id = r.released_by
            WHERE r.status = 'released'
            ORDER BY r.release_date DESC, r.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_row_to_release(row) for row in rows if row]


def create_release_record(db: Connection, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    status = payload.get("status") if payload.get("status") in RELEASE_STATUSES else "draft"
    checklist = json.dumps(_clean_checklist(payload.get("checklist")), ensure_ascii=False)
    cursor = db.execute(
        """
        INSERT INTO release_records (
            version, release_date, status, summary, changes, impact_scope,
            checklist, known_issues, rollback_note, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _clean(payload.get("version"), 40),
            _clean(payload.get("release_date"), 20),
            status,
            _clean(payload.get("summary"), 1000),
            _clean(payload.get("changes"), 3000),
            _clean(payload.get("impact_scope"), 1000),
            checklist,
            _clean(payload.get("known_issues"), 1500),
            _clean(payload.get("rollback_note"), 1500),
            user_id,
        ),
    )
    release_id = cursor.lastrowid
    create_audit_log(db, user_id, "release_create", "release_record", str(release_id), "success", f"version={payload.get('version', '')[:40]}")
    if status == "released":
        db.execute(
            "UPDATE release_records SET released_by = ?, released_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id, release_id),
        )
        create_audit_log(db, user_id, "release_publish", "release_record", str(release_id), "success", f"version={payload.get('version', '')[:40]}; comment=created_as_released")
    return get_release_record(db, int(release_id)) or {}


def get_release_record(db: Connection, release_id: int) -> dict[str, Any] | None:
    row = db.execute(
        """
        SELECT r.*, cu.email AS created_by_email, ru.email AS released_by_email
        FROM release_records r
        LEFT JOIN users cu ON cu.id = r.created_by
        LEFT JOIN users ru ON ru.id = r.released_by
        WHERE r.id = ?
        """,
        (release_id,),
    ).fetchone()
    return _row_to_release(row)


def update_release_record(db: Connection, release_id: int, user_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    existing = get_release_record(db, release_id)
    if not existing:
        return None
    next_values = {
        "version": _clean(payload.get("version", existing["version"]), 40),
        "release_date": _clean(payload.get("release_date", existing["release_date"]), 20),
        "status": payload.get("status", existing["status"]) if payload.get("status", existing["status"]) in RELEASE_STATUSES else existing["status"],
        "summary": _clean(payload.get("summary", existing["summary"]), 1000),
        "changes": _clean(payload.get("changes", existing["changes"]), 3000),
        "impact_scope": _clean(payload.get("impact_scope", existing["impact_scope"]), 1000),
        "checklist": json.dumps(_clean_checklist(payload.get("checklist", existing["checklist"])), ensure_ascii=False),
        "known_issues": _clean(payload.get("known_issues", existing["known_issues"]), 1500),
        "rollback_note": _clean(payload.get("rollback_note", existing["rollback_note"]), 1500),
    }
    db.execute(
        """
        UPDATE release_records
        SET version = ?, release_date = ?, status = ?, summary = ?, changes = ?,
            impact_scope = ?, checklist = ?, known_issues = ?, rollback_note = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            next_values["version"],
            next_values["release_date"],
            next_values["status"],
            next_values["summary"],
            next_values["changes"],
            next_values["impact_scope"],
            next_values["checklist"],
            next_values["known_issues"],
            next_values["rollback_note"],
            release_id,
        ),
    )
    create_audit_log(db, user_id, "release_update", "release_record", str(release_id), "success", f"status={next_values['status']}")
    if existing["status"] != "released" and next_values["status"] == "released":
        db.execute(
            "UPDATE release_records SET released_by = ?, released_at = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id, release_id),
        )
        create_audit_log(db, user_id, "release_publish", "release_record", str(release_id), "success", f"version={next_values['version']}; comment=status_update")
    return get_release_record(db, release_id)


def publish_release_record(db: Connection, release_id: int, user_id: int, comment: str = "") -> dict[str, Any] | None:
    existing = get_release_record(db, release_id)
    if not existing:
        return None
    db.execute(
        """
        UPDATE release_records
        SET status = 'released',
            released_by = ?,
            released_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (user_id, release_id),
    )
    metadata = f"version={existing['version']}; comment={_clean(comment, 180)}"
    create_audit_log(db, user_id, "release_publish", "release_record", str(release_id), "success", metadata)
    return get_release_record(db, release_id)
