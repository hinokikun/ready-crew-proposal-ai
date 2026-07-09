from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_roles
from app.db import get_db
from app.repositories import get_project_detail, list_crm

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/crm")
async def get_crm(_: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        return list_crm(db)


@router.get("/{project_id}")
async def get_project(project_id: int, _: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        project = get_project_detail(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません。")
    return {"project": project}
