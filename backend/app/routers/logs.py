from fastapi import APIRouter, Depends

from app.auth import require_roles
from app.db import get_db
from app.models import UsageLogCreateRequest
from app.repositories import create_history_log, list_audit_logs, list_usage_logs

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def get_logs(_: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        return {"logs": list_usage_logs(db, 100)}


@router.get("/audit")
async def get_audit_logs(_: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        return {"logs": list_audit_logs(db, 200)}


@router.post("")
async def post_log(payload: UsageLogCreateRequest, user: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        create_history_log(
            db,
            int(user["id"]),
            None,
            None,
            payload.feature_name,
            payload.input_length,
            payload.output_type,
            payload.status,
            payload.error_type,
        )
    return {"ok": True}
