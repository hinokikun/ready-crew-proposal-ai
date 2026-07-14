from fastapi import APIRouter, Depends, Query

from app.auth import require_roles
from app.db import get_db
from app.models import WorkspaceConversationSaveRequest
from app.workspace.repositories import (
    get_workspace_conversation_bundle,
    get_workspace_summary,
    list_workspace_conversations,
    save_workspace_bundle,
)

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


@router.get("/conversations")
async def get_workspace_conversations(
    project_id: str = Query("", max_length=120),
    user: dict = Depends(require_roles("admin", "member", "viewer")),
) -> dict:
    with get_db() as db:
        if project_id:
            return get_workspace_conversation_bundle(db, project_id, int(user["id"]))
        return {"conversations": list_workspace_conversations(db, 100, int(user["id"]))}


@router.post("/conversations")
async def post_workspace_conversations(
    payload: WorkspaceConversationSaveRequest,
    user: dict = Depends(require_roles("admin", "member")),
) -> dict:
    with get_db() as db:
        result = save_workspace_bundle(
            db,
            int(user["id"]),
            payload.project_id,
            [item.dict() for item in payload.conversations],
            [item.dict() for item in payload.work_logs],
        )
    return {"ok": True, **result}


@router.get("/conversations/{project_id}")
async def get_workspace_conversation_by_project(
    project_id: str,
    user: dict = Depends(require_roles("admin", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return get_workspace_conversation_bundle(db, project_id, int(user["id"]))


@router.get("/summary/{project_id}")
async def get_workspace_summary_by_project(
    project_id: str,
    user: dict = Depends(require_roles("admin", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return {"summary": get_workspace_summary(db, project_id, int(user["id"]))}
