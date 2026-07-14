from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db
from app.proposal_optimization import (
    approve_backlog_item,
    build_optimization_dashboard,
    build_recommendations,
    build_revision_actions,
    extract_best_practices,
    list_backlog,
    list_best_practices,
    mark_backlog_in_revision,
    record_backlog_measurement,
    run_optimization,
    update_backlog_status,
    update_best_practice_status,
)
from app.rate_limit import rate_limit_dependency
from app.scope_policy import resolve_scope

router = APIRouter(prefix="/api/proposal-optimization", tags=["proposal-optimization"])


class OptimizationRunRequest(BaseModel):
    project_id: str = Field("", max_length=120)


class BacklogStatusRequest(BaseModel):
    status: str = Field(..., max_length=40)


class BacklogRevisionRequest(BaseModel):
    backlog_ids: list[int] = Field(default_factory=list)


class MeasurementRequest(BaseModel):
    measurement_status: str = Field(..., max_length=40)
    measured_effect: dict[str, Any] = Field(default_factory=dict)
    measurement_period: str = Field("", max_length=120)
    outcome_type: str = Field("", max_length=80)


class BestPracticeStatusRequest(BaseModel):
    status: str = Field(..., max_length=40)
    reason: str = Field("", max_length=300)


@router.post("/run", dependencies=[Depends(rate_limit_dependency("generation"))])
async def post_optimization_run(
    payload: OptimizationRunRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        return run_optimization(db, user_id=int(user["id"]), project_id=payload.project_id)


@router.get("/recommendations")
async def get_recommendations(
    project_id: str = Query("", max_length=120),
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return build_recommendations(db, user_id=int(user["id"]), project_id=project_id)


@router.get("/backlog")
async def get_backlog(
    project_id: str = Query("", max_length=120),
    status: str = Query("", max_length=40),
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return {"backlog": list_backlog(db, user_id=int(user["id"]), project_id=project_id, status=status)}


@router.patch("/backlog/{backlog_id}/status")
async def patch_backlog_status(
    backlog_id: int,
    payload: BacklogStatusRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
) -> dict:
    if payload.status == "approved" and user.get("role") not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Only manager or admin can approve an improvement.")
    if payload.status in {"measured"} and user.get("role") not in {"admin", "manager"}:
        raise HTTPException(status_code=403, detail="Only manager or admin can mark measurement complete.")
    with get_db() as db:
        try:
            item = update_backlog_status(db, backlog_id=backlog_id, user_id=int(user["id"]), status=payload.status)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail="Invalid backlog status transition.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid backlog status.") from exc
    if not item:
        raise HTTPException(status_code=404, detail="Improvement backlog item was not found.")
    return {"item": item}


@router.patch("/backlog/{backlog_id}/approve")
async def patch_backlog_approved(
    backlog_id: int,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        try:
            item = approve_backlog_item(db, backlog_id=backlog_id, user_id=int(user["id"]))
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail="Invalid backlog status transition.") from exc
    if not item:
        raise HTTPException(status_code=404, detail="Improvement backlog item was not found.")
    return {"item": item}


@router.patch("/backlog/{backlog_id}/measurement")
async def patch_backlog_measurement(
    backlog_id: int,
    payload: MeasurementRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        try:
            item = record_backlog_measurement(
                db,
                backlog_id=backlog_id,
                user_id=int(user["id"]),
                measured_effect=payload.measured_effect,
                measurement_status=payload.measurement_status,
                measurement_period=payload.measurement_period,
                outcome_type=payload.outcome_type,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid measurement status.") from exc
    if not item:
        raise HTTPException(status_code=404, detail="Improvement backlog item was not found.")
    return {"item": item}


@router.post("/revision-actions")
async def post_backlog_revision_actions(
    payload: BacklogRevisionRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
) -> dict:
    with get_db() as db:
        items = mark_backlog_in_revision(db, backlog_ids=payload.backlog_ids, user_id=int(user["id"]))
    return {"items": items}


@router.get("/revision-actions")
async def get_backlog_revision_actions(
    project_id: str = Query("", max_length=120),
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return {"selected_actions": build_revision_actions(db, user_id=int(user["id"]), project_id=project_id)}


@router.get("/best-practices")
async def get_best_practices(user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        approved_only = str(user.get("role")) not in {"admin", "manager"}
        return {"best_practices": list_best_practices(db, user_id=int(user["id"]), approved_only=approved_only)}


@router.post("/best-practices/extract")
async def post_best_practices_extract(
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    with get_db() as db:
        return {"best_practices": extract_best_practices(db, user_id=int(user["id"]))}


@router.patch("/best-practices/{best_practice_id}/status")
async def patch_best_practice_status(
    best_practice_id: int,
    payload: BestPracticeStatusRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        try:
            item = update_best_practice_status(
                db,
                best_practice_id=best_practice_id,
                user_id=int(user["id"]),
                status=payload.status,
                reason=payload.reason,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid best practice status.") from exc
    if not item:
        raise HTTPException(status_code=404, detail="Best practice was not found.")
    return {"best_practice": item}


@router.get("/dashboard")
async def get_optimization_dashboard(
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = Query("workspace", pattern="^(workspace|organization|system)$"),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        return {"dashboard": build_optimization_dashboard(db, scope=resolved_scope)}
