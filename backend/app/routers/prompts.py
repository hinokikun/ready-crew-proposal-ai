from fastapi import APIRouter, Depends, HTTPException

from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db
from app.models import (
    ExperimentCreateRequest,
    PromptMetricRequest,
    PromptRollbackRequest,
    PromptRouteRequest,
    PromptVersionCreateRequest,
    PromptVersionStatusRequest,
)
from app.prompts.services import (
    create_experiment_from_learning,
    create_experiment_from_payload,
    create_prompt_version_from_payload,
    get_prompt_studio_dashboard,
    judge_experiment,
    record_prompt_metric_from_payload,
    rollback_prompt_from_payload,
    route_prompt_from_payload,
    update_prompt_status_from_payload,
)
from app.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"dashboard": get_prompt_studio_dashboard(db, int(user["id"]))}


@router.post("/versions")
async def post_prompt_version(payload: PromptVersionCreateRequest, user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        try:
            prompt_version = create_prompt_version_from_payload(db, payload=payload, user_id=int(user["id"]))
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return {"prompt_version": prompt_version, "dashboard": get_prompt_studio_dashboard(db, int(user["id"]))}


@router.patch("/versions/{version_id}/status")
async def patch_prompt_version_status(
    version_id: int,
    payload: PromptVersionStatusRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        prompt_version = update_prompt_status_from_payload(db, version_id=version_id, payload=payload, user_id=int(user["id"]))
        if not prompt_version:
            raise HTTPException(status_code=404, detail="Prompt version not found.")
        return {"prompt_version": prompt_version, "dashboard": get_prompt_studio_dashboard(db, int(user["id"]))}


@router.post("/rollback")
async def post_prompt_rollback(payload: PromptRollbackRequest, user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        prompt_version = rollback_prompt_from_payload(db, payload=payload, user_id=int(user["id"]))
        if not prompt_version:
            raise HTTPException(status_code=404, detail="Prompt version not found.")
        return {"prompt_version": prompt_version, "dashboard": get_prompt_studio_dashboard(db, int(user["id"]))}


@router.post("/experiments")
async def post_experiment(
    payload: ExperimentCreateRequest,
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        experiment = create_experiment_from_payload(db, payload=payload, user_id=int(user["id"]))
        return {"experiment": experiment, "dashboard": get_prompt_studio_dashboard(db, int(user["id"]))}


@router.post("/experiments/{experiment_id}/judge")
async def post_experiment_judgement(
    experiment_id: int,
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    with get_db() as db:
        recommendation = judge_experiment(db, experiment_id=experiment_id, user_id=int(user["id"]))
        if not recommendation:
            raise HTTPException(status_code=404, detail="Experiment not found or not enough data.")
        return {"recommendation": recommendation, "dashboard": get_prompt_studio_dashboard(db, int(user["id"]))}


@router.post("/from-learning/{improvement_id}")
async def post_from_learning(
    improvement_id: int,
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        result = create_experiment_from_learning(db, improvement_id=improvement_id, user_id=int(user["id"]))
        if not result:
            raise HTTPException(status_code=404, detail="Learning improvement not found.")
        return {"result": result, "dashboard": get_prompt_studio_dashboard(db, int(user["id"]))}


@router.post("/route")
async def post_prompt_route(
    payload: PromptRouteRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> dict:
    with get_db() as db:
        return {"routing": route_prompt_from_payload(db, payload=payload, user_id=int(user["id"]))}


@router.post("/metrics")
async def post_prompt_metric(
    payload: PromptMetricRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
    __: None = Depends(rate_limit_dependency("generation")),
) -> dict:
    with get_db() as db:
        metric = record_prompt_metric_from_payload(db, payload=payload, user_id=int(user["id"]))
        return {"metric": metric, "analytics": get_prompt_studio_dashboard(db, int(user["id"]))["analytics"]}
