from __future__ import annotations

from dataclasses import dataclass
from sqlite3 import Connection
from typing import Any, Literal

from fastapi import HTTPException

from app.repositories import get_user_context_ids


ScopeName = Literal["workspace", "organization", "system"]


@dataclass(frozen=True)
class ScopeContext:
    scope: ScopeName
    organization_id: int
    workspace_id: int | None
    organization_name: str
    workspace_name: str

    @property
    def response_meta(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "organization_name": self.organization_name,
            "workspace_name": self.workspace_name,
        }


def _row_value(row: Any, key: str, fallback: Any = "") -> Any:
    if not row:
        return fallback
    try:
        return row[key]
    except Exception:
        return fallback


def resolve_scope(db: Connection, user: dict[str, Any], requested_scope: str | None = None) -> ScopeContext:
    """Resolve an explicit aggregation scope from the current authenticated user.

    Default scope is always the smallest useful scope: current workspace.
    Only system admin (`role=admin`) can use `system`.
    Organization-level scope is limited to admin and manager.
    """

    role = str(user.get("role") or "")
    scope = (requested_scope or "workspace").strip().lower()
    if scope not in {"workspace", "organization", "system"}:
        raise HTTPException(status_code=400, detail="scope must be workspace, organization, or system.")
    if scope == "system" and role != "admin":
        raise HTTPException(status_code=403, detail="system scope is available only to system admin.")
    if scope == "organization" and role not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="organization scope is available only to admin or manager.")

    organization_id, workspace_id = get_user_context_ids(db, int(user.get("id") or 0))
    row = db.execute(
        """
        SELECT
            COALESCE(o.name, 'Ready Crew') AS organization_name,
            COALESCE(w.name, '営業部') AS workspace_name
        FROM users u
        LEFT JOIN organizations o ON o.id = COALESCE(u.current_organization_id, ?)
        LEFT JOIN workspaces w ON w.id = COALESCE(u.current_workspace_id, ?)
        WHERE u.id = ?
        """,
        (organization_id, workspace_id, int(user.get("id") or 0)),
    ).fetchone()

    if scope == "system":
        return ScopeContext("system", organization_id, None, "All Organizations", "All Workspaces")
    if scope == "organization":
        return ScopeContext(
            "organization",
            organization_id,
            None,
            str(_row_value(row, "organization_name", "Ready Crew")),
            "All Workspaces",
        )
    return ScopeContext(
        "workspace",
        organization_id,
        workspace_id,
        str(_row_value(row, "organization_name", "Ready Crew")),
        str(_row_value(row, "workspace_name", "営業部")),
    )


def scope_where(scope: ScopeContext, alias: str = "") -> tuple[str, tuple[Any, ...]]:
    prefix = f"{alias}." if alias else ""
    if scope.scope == "system":
        return "1 = 1", ()
    if scope.scope == "organization":
        return f"{prefix}organization_id = ?", (scope.organization_id,)
    return f"{prefix}organization_id = ? AND {prefix}workspace_id = ?", (
        scope.organization_id,
        int(scope.workspace_id or 1),
    )


def scoped_count(db: Connection, table_name: str, scope: ScopeContext, extra_where: str = "", params: tuple[Any, ...] = ()) -> int:
    where, scope_params = scope_where(scope)
    clauses = [where]
    if extra_where:
        clauses.append(f"({extra_where})")
    row = db.execute(
        f"SELECT COUNT(*) AS count FROM {table_name} WHERE {' AND '.join(clauses)}",
        (*scope_params, *params),
    ).fetchone()
    return int(row["count"]) if row else 0
