from fastapi import APIRouter, Depends, HTTPException

from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db
from app.integrations import (
    build_connector_readiness,
    convert_external_candidate_to_project,
    create_external_intake,
    execute_integration_dry_run,
    list_external_candidates,
    list_dry_run_logs,
    list_integration_settings,
    review_external_candidate,
    update_integration_setting,
)
from app.models import ExternalIntakeRequest, ExternalIntakeReviewRequest, IntegrationDryRunRequest, IntegrationSettingUpdateRequest
from app.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/settings")
async def get_integration_settings(_: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"settings": list_integration_settings(db)}


@router.patch("/settings/{provider}")
async def patch_integration_setting(
    provider: str,
    payload: IntegrationSettingUpdateRequest,
    user: dict = Depends(require_roles("admin")),
) -> dict:
    with get_db() as db:
        try:
            setting = update_integration_setting(
                db,
                provider=provider,
                status=payload.status,
                display_name=payload.display_name,
                enabled=payload.enabled,
                error_message=payload.error_message,
                allowed_roles=payload.allowed_roles,
                requires_admin_approval=payload.requires_admin_approval,
                data_retention_days=payload.data_retention_days,
                security_note=payload.security_note,
                user_id=int(user["id"]),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not setting:
        raise HTTPException(status_code=404, detail="外部連携設定が見つかりません。")
    return {"setting": setting}


@router.post("/intake")
async def post_external_intake(
    payload: ExternalIntakeRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        try:
            candidate = create_external_intake(db, user=user, payload=payload.dict())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"candidate": candidate}


@router.get("/candidates")
async def get_external_candidates(user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return {"candidates": list_external_candidates(db, user)}


@router.post("/dry-run")
async def post_integration_dry_run(
    payload: IntegrationDryRunRequest,
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    with get_db() as db:
        try:
            result = execute_integration_dry_run(db, user=user, provider=payload.provider, template_type=payload.template_type)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
    return result


@router.get("/dry-run/logs")
async def get_integration_dry_run_logs(_: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"logs": list_dry_run_logs(db)}


@router.get("/readiness")
async def get_connector_readiness(user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"readiness": build_connector_readiness(db, user_id=int(user["id"]))}


@router.patch("/candidates/{item_id}/review")
async def patch_external_candidate_review(
    item_id: int,
    payload: ExternalIntakeReviewRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        try:
            candidate = review_external_candidate(
                db,
                item_id=item_id,
                status=payload.status,
                review_comment=payload.review_comment,
                user=user,
            )
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"candidate": candidate}


@router.post("/candidates/{item_id}/convert")
async def post_external_candidate_convert(
    item_id: int,
    user: dict = Depends(require_roles("admin", "manager", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        try:
            candidate = convert_external_candidate_to_project(db, item_id=item_id, user=user)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"candidate": candidate}
