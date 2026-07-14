from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db
from app.orchestrator import (
    build_orchestrator_analytics,
    enqueue_project_orchestration,
    get_project_orchestrator_status,
    list_action_queue,
    retry_queue_action,
    run_project_orchestrator,
)
from app.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])


@router.get("/queue")
async def get_queue(
    status: str = Query("", max_length=40),
    limit: int = Query(100, ge=1, le=200),
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        return {"queue": list_action_queue(db, status=status, limit=limit, user_id=int(user["id"]))}


@router.get("/analytics")
async def get_analytics(user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"orchestrator": build_orchestrator_analytics(db, int(user["id"]))}


@router.get("/projects/{project_id}/status")
async def get_project_status(project_id: int, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return {"orchestrator": get_project_orchestrator_status(db, project_id, int(user["id"]))}


@router.post("/projects/{project_id}/start")
async def start_project_orchestrator(
    project_id: int,
    user: dict = Depends(require_roles("admin", "manager", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        result = enqueue_project_orchestration(db, project_id=project_id, user_id=int(user["id"]))
        if not result.get("queue") and not result.get("created"):
            raise HTTPException(status_code=404, detail="Project not found.")
        return {"orchestrator": result}


@router.post("/projects/{project_id}/run")
async def run_project(
    project_id: int,
    user: dict = Depends(require_roles("admin", "manager", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        enqueue_project_orchestration(db, project_id=project_id, user_id=int(user["id"]))
        result = run_project_orchestrator(db, project_id=project_id, user_id=int(user["id"]))
        if not result.get("queue"):
            raise HTTPException(status_code=404, detail="Project not found.")
        return {"orchestrator": result}


@router.post("/actions/{action_id}/retry")
async def retry_action(
    action_id: int,
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        action = retry_queue_action(db, action_id=action_id, user_id=int(user["id"]))
    if not action:
        raise HTTPException(status_code=404, detail="Action not found.")
    return {"action": action}
