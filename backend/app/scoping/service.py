from __future__ import annotations

from sqlite3 import Connection
from typing import Any

from fastapi import HTTPException

from app.context import RequestContext
from app.repositories import create_audit_log


def scoped_where(alias: str = "") -> str:
    prefix = f"{alias}." if alias else ""
    return f"{prefix}organization_id = ? AND {prefix}workspace_id = ?"


def scoped_params(context: RequestContext) -> tuple[int, int]:
    return context.organization_id, context.workspace_id


def ensure_table_scope(
    db: Connection,
    *,
    table_name: str,
    row_id: int | str,
    context: RequestContext,
    id_column: str = "id",
    target_type: str = "",
) -> dict[str, Any]:
    row = db.execute(
        f"""
        SELECT id, organization_id, workspace_id
        FROM {table_name}
        WHERE {id_column} = ?
        """,
        (row_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="対象データが見つかりません。")
    if int(row["organization_id"] or 0) != context.organization_id or int(row["workspace_id"] or 0) != context.workspace_id:
        create_audit_log(
            db,
            context.user_id,
            "workspace_scope_denied",
            target_type or table_name,
            str(row_id),
            "failure",
            f"organization_id={context.organization_id};workspace_id={context.workspace_id};request_id={context.request_id}",
        )
        raise HTTPException(status_code=404, detail="対象データが見つかりません。")
    return dict(row)


def get_project_scope(db: Connection, project_id: int | str) -> dict[str, Any] | None:
    row = db.execute(
        """
        SELECT id, organization_id, workspace_id
        FROM projects
        WHERE id = ?
        """,
        (project_id,),
    ).fetchone()
    return dict(row) if row else None


def ensure_project_scope(db: Connection, *, project_id: int | str, context: RequestContext) -> dict[str, Any]:
    row = get_project_scope(db, project_id)
    if not row:
        raise HTTPException(status_code=404, detail="対象案件が見つかりません。")
    if int(row["organization_id"] or 0) != context.organization_id or int(row["workspace_id"] or 0) != context.workspace_id:
        create_audit_log(
            db,
            context.user_id,
            "workspace_scope_denied",
            "project",
            str(project_id),
            "failure",
            f"organization_id={context.organization_id};workspace_id={context.workspace_id};request_id={context.request_id}",
        )
        raise HTTPException(status_code=404, detail="対象案件が見つかりません。")
    return row


def attach_project_scope(
    db: Connection,
    *,
    project_id: int | str,
    fallback_context: RequestContext | tuple[int, int] | None = None,
) -> tuple[int, int]:
    row = get_project_scope(db, project_id)
    if row:
        return int(row["organization_id"] or 1), int(row["workspace_id"] or 1)
    if fallback_context:
        if isinstance(fallback_context, tuple):
            return int(fallback_context[0] or 1), int(fallback_context[1] or 1)
        return fallback_context.organization_id, fallback_context.workspace_id
    return 1, 1
