from __future__ import annotations

from fastapi import Depends, Header

from app.auth import get_current_user
from app.context import RequestContext
from app.db import get_db
from app.organization import get_user_workspace_context


def get_request_context(user: dict = Depends(get_current_user), x_request_id: str | None = Header(default=None)) -> RequestContext:
    with get_db() as db:
        workspace = get_user_workspace_context(db, int(user["id"]))
    return RequestContext(
        user_id=int(user["id"]),
        role=str(user.get("role") or ""),
        organization_id=int(workspace.get("organization_id") or 1),
        workspace_id=int(workspace.get("workspace_id") or 1),
        membership_role=str(workspace.get("membership_role") or "member"),
        request_id=(x_request_id or "")[:120],
    )
