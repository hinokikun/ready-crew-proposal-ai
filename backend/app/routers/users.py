from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_roles
from app.config import settings
from app.db import get_db
from app.models import UserCreateRequest, UserUpdateRequest
from app.rate_limit import rate_limit_dependency
from app.repositories import (
    count_pilot_enabled_users,
    create_audit_log,
    create_user,
    get_user_by_id,
    list_users,
    set_user_active,
    set_user_pilot_settings,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def get_users(_: dict = Depends(require_roles("admin"))) -> dict[str, list[dict]]:
    with get_db() as db:
        return {"users": list_users(db)}


@router.post("")
async def post_user(
    payload: UserCreateRequest,
    current_user: dict = Depends(require_roles("admin")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    try:
        with get_db() as db:
            user = create_user(db, payload.email, payload.password, payload.role)
            create_audit_log(db, int(current_user["id"]), "save", "user", str(user["id"]), "success", f"role={payload.role}")
        return {"user": user}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ユーザーを作成できませんでした。メールアドレスの重複や入力内容を確認してください。") from exc


@router.patch("/{user_id}")
async def patch_user(
    user_id: int,
    payload: UserUpdateRequest,
    current_user: dict = Depends(require_roles("admin")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    with get_db() as db:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません。")
        if payload.is_active is not None:
            user = set_user_active(db, user_id, payload.is_active)
        if payload.pilot_enabled is not None:
            already_enabled = bool(user.get("pilot_enabled")) if user else False
            if payload.pilot_enabled and not already_enabled and count_pilot_enabled_users(db) >= settings.pilot_max_users:
                raise HTTPException(status_code=400, detail=f"Pilot対象者は最大{settings.pilot_max_users}名までです。")
            user = set_user_pilot_settings(db, user_id, payload.pilot_enabled, payload.pilot_completed, payload.pilot_note)
        elif payload.pilot_completed is not None or payload.pilot_note:
            user = set_user_pilot_settings(
                db,
                user_id,
                bool(user.get("pilot_enabled")) if user else False,
                payload.pilot_completed,
                payload.pilot_note,
            )
        create_audit_log(
            db,
            int(current_user["id"]),
            "settings_change",
            "user",
            str(user_id),
            "success",
            f"is_active={payload.is_active};pilot_enabled={payload.pilot_enabled};pilot_completed={payload.pilot_completed}",
        )
    return {"user": user}
