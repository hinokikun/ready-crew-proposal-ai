from fastapi import APIRouter, Depends, HTTPException

from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db
from app.models import (
    ProjectCompleteRequest,
    ProjectCreateRequest,
    ProjectHandoffRequest,
    ProjectOutcomeRequest,
    ProjectStatusUpdateRequest,
)
from app.orchestrator import enqueue_project_orchestration, run_project_orchestrator
from app.project_lifecycle import (
    build_project_lifecycle_analytics,
    build_production_handoff,
    complete_project_with_retrospective,
    create_project_record,
    get_project_lifecycle,
    register_project_outcome,
    update_project_status,
)
from app.rate_limit import rate_limit_dependency
from app.repositories import get_project_detail, list_crm
from app.organization import get_user_workspace_context

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _can_access_project(db, user: dict, project_id: int) -> bool:
    if user["role"] == "admin":
        return True
    project = db.execute("SELECT organization_id, workspace_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        return False
    context = get_user_workspace_context(db, int(user["id"]))
    same_context = int(project["organization_id"]) == int(context["organization_id"]) and int(project["workspace_id"]) == int(context["workspace_id"])
    if user["role"] == "manager":
        return same_context
    row = db.execute(
        "SELECT 1 FROM project_lifecycle_events WHERE project_id = ? AND user_id = ? LIMIT 1",
        (project_id, int(user["id"])),
    ).fetchone()
    return bool(row) and same_context


def _ensure_project_access(db, user: dict, project_id: int) -> None:
    if not _can_access_project(db, user, project_id):
        raise HTTPException(status_code=403, detail="この案件を閲覧・操作する権限がありません。")


@router.get("/crm")
async def get_crm(user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        context = get_user_workspace_context(db, int(user["id"]))
        return list_crm(
            db,
            None if user["role"] in {"admin", "manager"} else int(user["id"]),
            organization_id=int(context["organization_id"]),
            workspace_id=int(context["workspace_id"]),
        )


@router.post("")
async def post_project(
    payload: ProjectCreateRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        lifecycle = create_project_record(
            db,
            user_id=int(user["id"]),
            customer_name=payload.customer_name,
            project_name=payload.project_name,
            summary=payload.summary,
            win_probability=payload.win_probability,
            next_action=payload.next_action,
        )
        project_id = int((lifecycle.get("project") or {}).get("id") or 0)
        if project_id:
            enqueue_project_orchestration(db, project_id=project_id, user_id=int(user["id"]))
            lifecycle["orchestrator"] = run_project_orchestrator(db, project_id=project_id, user_id=int(user["id"]))
    return {"lifecycle": lifecycle}


@router.get("/lifecycle/analytics")
async def get_lifecycle_analytics(_: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"lifecycle_analytics": build_project_lifecycle_analytics(db)}


@router.get("/{project_id}")
async def get_project(project_id: int, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        project = get_project_detail(db, project_id)
        if project:
            _ensure_project_access(db, user, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="案件が見つかりません。")
    return {"project": project}


@router.get("/{project_id}/lifecycle")
async def get_project_lifecycle_detail(project_id: int, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        lifecycle = get_project_lifecycle(db, project_id)
        if lifecycle:
            _ensure_project_access(db, user, project_id)
    if not lifecycle:
        raise HTTPException(status_code=404, detail="案件が見つかりません。")
    return {"lifecycle": lifecycle}


@router.patch("/{project_id}/status")
async def patch_project_status(project_id: int, payload: ProjectStatusUpdateRequest, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        _ensure_project_access(db, user, project_id)
        try:
            lifecycle = update_project_status(db, project_id=project_id, user_id=int(user["id"]), status=payload.status, note=payload.note)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not lifecycle:
        raise HTTPException(status_code=404, detail="案件が見つかりません。")
    return {"lifecycle": lifecycle}


@router.post("/{project_id}/outcome")
async def post_project_outcome(project_id: int, payload: ProjectOutcomeRequest, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        _ensure_project_access(db, user, project_id)
        try:
            lifecycle = register_project_outcome(
                db,
                project_id=project_id,
                user_id=int(user["id"]),
                outcome=payload.outcome,
                lost_reason=payload.lost_reason,
                note=payload.note,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not lifecycle:
        raise HTTPException(status_code=404, detail="案件が見つかりません。")
    return {"lifecycle": lifecycle}


@router.post("/{project_id}/handoff")
async def post_project_handoff(project_id: int, payload: ProjectHandoffRequest, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        _ensure_project_access(db, user, project_id)
        lifecycle = build_production_handoff(db, project_id=project_id, user_id=int(user["id"]), payload=payload.dict())
    if not lifecycle:
        raise HTTPException(status_code=404, detail="案件が見つかりません。")
    return {"lifecycle": lifecycle}


@router.post("/{project_id}/complete")
async def post_project_complete(project_id: int, payload: ProjectCompleteRequest, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        _ensure_project_access(db, user, project_id)
        lifecycle = complete_project_with_retrospective(db, project_id=project_id, user_id=int(user["id"]), payload=payload.dict())
    if not lifecycle:
        raise HTTPException(status_code=404, detail="案件が見つかりません。")
    return {"lifecycle": lifecycle}
