from fastapi import APIRouter, Depends, HTTPException

from app.ai_watch import archive_notification, mark_notification_actioned, mark_notification_read, run_ai_watch_engine
from app.auth import require_roles
from app.db import get_db

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
async def get_notifications(user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return run_ai_watch_engine(db, int(user["id"]))


@router.post("/run-watch")
async def run_watch(user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return run_ai_watch_engine(db, int(user["id"]))


@router.patch("/{notification_id}/read")
async def patch_notification_read(notification_id: int, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        notification = mark_notification_read(db, notification_id, int(user["id"]))
    if not notification:
        raise HTTPException(status_code=404, detail="通知が見つかりません。")
    return {"notification": notification}


@router.patch("/{notification_id}/actioned")
async def patch_notification_actioned(notification_id: int, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        notification = mark_notification_actioned(db, notification_id, int(user["id"]))
    if not notification:
        raise HTTPException(status_code=404, detail="通知が見つかりません。")
    return {"notification": notification}


@router.patch("/{notification_id}/archive")
async def patch_notification_archive(notification_id: int, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        notification = archive_notification(db, notification_id, int(user["id"]))
    if not notification:
        raise HTTPException(status_code=404, detail="通知が見つかりません。")
    return {"notification": notification}
