from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from fastapi import HTTPException

from app.repositories import create_audit_log


DEFAULT_ORGANIZATION_ID = 1
DEFAULT_WORKSPACE_ID = 1


def ensure_user_default_membership(db: Connection, user: dict[str, Any]) -> None:
    membership_role = "organization_admin" if str(user.get("role")) in {"admin", "manager"} else "member"
    _upsert_membership(
        db,
        user_id=int(user["id"]),
        organization_id=DEFAULT_ORGANIZATION_ID,
        workspace_id=DEFAULT_WORKSPACE_ID,
        membership_role=membership_role,
    )
    if not int(user.get("current_organization_id") or 0) or not int(user.get("current_workspace_id") or 0):
        db.execute(
            """
            UPDATE users
            SET current_organization_id = ?, current_workspace_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (DEFAULT_ORGANIZATION_ID, DEFAULT_WORKSPACE_ID, int(user["id"])),
        )


def get_user_workspace_context(db: Connection, user_id: int) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT
            u.id AS user_id,
            u.role AS system_role,
            COALESCE(u.current_organization_id, 1) AS organization_id,
            COALESCE(u.current_workspace_id, 1) AS workspace_id,
            COALESCE(o.name, 'Ready Crew') AS organization_name,
            COALESCE(w.name, '営業部') AS workspace_name,
            COALESCE(m.membership_role, CASE WHEN u.role IN ('admin', 'manager') THEN 'organization_admin' ELSE 'member' END) AS membership_role
        FROM users u
        LEFT JOIN organizations o ON o.id = COALESCE(u.current_organization_id, 1)
        LEFT JOIN workspaces w ON w.id = COALESCE(u.current_workspace_id, 1)
        LEFT JOIN organization_memberships m
            ON m.user_id = u.id
            AND m.organization_id = COALESCE(u.current_organization_id, 1)
            AND m.workspace_id = COALESCE(u.current_workspace_id, 1)
        WHERE u.id = ?
        """,
        (user_id,),
    ).fetchone()
    if not row:
        return {
            "organization_id": DEFAULT_ORGANIZATION_ID,
            "workspace_id": DEFAULT_WORKSPACE_ID,
            "organization_name": "Ready Crew",
            "workspace_name": "営業部",
            "membership_role": "member",
            "scope": "user",
        }
    context = dict(row)
    context["scope"] = "admin" if context["system_role"] == "admin" else ("organization_admin" if context["membership_role"] == "organization_admin" else "user")
    return context


def add_context_fields(db: Connection, record: dict[str, Any], user_id: int | None = None) -> dict[str, Any]:
    if int(record.get("organization_id") or 0) and int(record.get("workspace_id") or 0):
        return record
    context = get_user_workspace_context(db, int(user_id or 0)) if user_id else {
        "organization_id": DEFAULT_ORGANIZATION_ID,
        "workspace_id": DEFAULT_WORKSPACE_ID,
    }
    record["organization_id"] = int(context.get("organization_id") or DEFAULT_ORGANIZATION_ID)
    record["workspace_id"] = int(context.get("workspace_id") or DEFAULT_WORKSPACE_ID)
    return record


def list_user_contexts(db: Connection, user: dict[str, Any]) -> dict[str, Any]:
    if str(user.get("role")) == "admin":
        rows = db.execute(
            """
            SELECT
                o.id AS organization_id,
                o.name AS organization_name,
                w.id AS workspace_id,
                w.name AS workspace_name,
                'system_admin' AS membership_role
            FROM organizations o
            INNER JOIN workspaces w ON w.organization_id = o.id
            ORDER BY o.id, w.id
            """
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT
                o.id AS organization_id,
                o.name AS organization_name,
                w.id AS workspace_id,
                w.name AS workspace_name,
                m.membership_role
            FROM organization_memberships m
            INNER JOIN organizations o ON o.id = m.organization_id
            INNER JOIN workspaces w ON w.id = m.workspace_id
            WHERE m.user_id = ?
            ORDER BY o.id, w.id
            """,
            (int(user["id"]),),
        ).fetchall()
    return {
        "current": get_user_workspace_context(db, int(user["id"])),
        "available": [dict(row) for row in rows],
    }


def switch_workspace_context(db: Connection, *, user: dict[str, Any], organization_id: int, workspace_id: int) -> dict[str, Any]:
    workspace = db.execute(
        """
        SELECT w.id
        FROM workspaces w
        INNER JOIN organizations o ON o.id = w.organization_id
        WHERE w.id = ? AND w.organization_id = ? AND w.is_active = 1 AND o.is_active = 1
        """,
        (workspace_id, organization_id),
    ).fetchone()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspaceが見つかりません。")
    if str(user.get("role")) != "admin":
        membership = db.execute(
            """
            SELECT id FROM organization_memberships
            WHERE user_id = ? AND organization_id = ? AND workspace_id = ?
            """,
            (int(user["id"]), organization_id, workspace_id),
        ).fetchone()
        if not membership:
            create_audit_log(db, int(user["id"]), "organization_cross_access_denied", "workspace", str(workspace_id), "failure", f"organization_id={organization_id}")
            raise HTTPException(status_code=403, detail="このOrganization / Workspaceへアクセスする権限がありません。")
    db.execute(
        """
        UPDATE users
        SET current_organization_id = ?, current_workspace_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (organization_id, workspace_id, int(user["id"])),
    )
    create_audit_log(db, int(user["id"]), "workspace_context_switched", "workspace", str(workspace_id), "success", f"organization_id={organization_id}")
    return get_user_workspace_context(db, int(user["id"]))


def create_organization(db: Connection, *, name: str, slug: str, created_by: int) -> dict[str, Any]:
    cursor = db.execute(
        "INSERT INTO organizations (name, slug) VALUES (?, ?)",
        (name.strip()[:160], slug.strip().lower()[:80]),
    )
    organization_id = int(cursor.lastrowid)
    create_workspace(db, organization_id=organization_id, name="営業", slug="sales", created_by=created_by)
    create_audit_log(db, created_by, "organization_created", "organization", str(organization_id), "success", f"slug={slug[:80]}")
    row = db.execute("SELECT * FROM organizations WHERE id = ?", (organization_id,)).fetchone()
    return dict(row)


def create_workspace(db: Connection, *, organization_id: int, name: str, slug: str, created_by: int) -> dict[str, Any]:
    cursor = db.execute(
        "INSERT INTO workspaces (organization_id, name, slug) VALUES (?, ?, ?)",
        (organization_id, name.strip()[:160], slug.strip().lower()[:80]),
    )
    workspace_id = int(cursor.lastrowid)
    create_audit_log(db, created_by, "workspace_created", "workspace", str(workspace_id), "success", f"organization_id={organization_id}")
    row = db.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    return dict(row)


def add_user_to_workspace(
    db: Connection,
    *,
    user_id: int,
    organization_id: int,
    workspace_id: int,
    membership_role: str,
    actor_id: int,
) -> dict[str, Any]:
    if membership_role not in {"organization_admin", "member", "viewer"}:
        membership_role = "member"
    workspace = db.execute(
        """
        SELECT w.id
        FROM workspaces w
        INNER JOIN organizations o ON o.id = w.organization_id
        WHERE w.id = ? AND w.organization_id = ? AND w.is_active = 1 AND o.is_active = 1
        """,
        (workspace_id, organization_id),
    ).fetchone()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspaceが見つかりません。")
    _upsert_membership(db, user_id=user_id, organization_id=organization_id, workspace_id=workspace_id, membership_role=membership_role)
    create_audit_log(db, actor_id, "workspace_membership_changed", "user", str(user_id), "success", f"organization_id={organization_id};workspace_id={workspace_id};role={membership_role}")
    row = db.execute(
        """
        SELECT * FROM organization_memberships
        WHERE user_id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (user_id, organization_id, workspace_id),
    ).fetchone()
    return dict(row)


def _upsert_membership(db: Connection, *, user_id: int, organization_id: int, workspace_id: int, membership_role: str) -> None:
    existing = db.execute(
        """
        SELECT id
        FROM organization_memberships
        WHERE user_id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (user_id, organization_id, workspace_id),
    ).fetchone()
    if existing:
        db.execute(
            """
            UPDATE organization_memberships
            SET membership_role = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (membership_role, int(existing["id"])),
        )
        return
    db.execute(
        """
        INSERT INTO organization_memberships (user_id, organization_id, workspace_id, membership_role)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, organization_id, workspace_id, membership_role),
    )
