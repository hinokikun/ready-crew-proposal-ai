from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_roles
from app.config import settings
from app.db import get_db
from app.models import UserCreateRequest, UserUpdateRequest
from app.rate_limit import rate_limit_dependency
from app.repositories import (
    count_active_admin_users,
    count_pilot_enabled_users,
    create_audit_log,
    create_user,
    get_user_by_id,
    list_users,
    set_user_active,
    set_user_password,
    set_user_pilot_settings,
    set_user_role,
)
from app.role_permissions import normalize_role_for_storage, role_label

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
            create_audit_log(
                db,
                int(current_user["id"]),
                "user_created",
                "user",
                str(user["id"]),
                "success",
                f"role={user['role']};role_label={role_label(str(user['role']))}",
            )
        return {"user": user}
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="ユーザーを作成できませんでした。メールアドレスの重複や入力内容を確認してください。",
        ) from exc


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

        if user_id == int(current_user["id"]) and payload.is_active is False:
            raise HTTPException(status_code=400, detail="自分自身のアカウントは無効化できません。")

        if payload.role is not None:
            next_role = normalize_role_for_storage(payload.role)
            if user_id == int(current_user["id"]) and next_role != "admin":
                raise HTTPException(status_code=400, detail="自分自身を一般利用者へ変更することはできません。")
            if user["role"] == "admin" and next_role != "admin" and count_active_admin_users(db) <= 1:
                raise HTTPException(status_code=400, detail="最後の管理者を一般利用者へ変更することはできません。")

        if payload.is_active is not None:
            if user["role"] == "admin" and not payload.is_active and count_active_admin_users(db) <= 1:
                raise HTTPException(status_code=400, detail="最後の管理者を無効化することはできません。")
            previous_active = bool(user.get("is_active"))
            user = set_user_active(db, user_id, payload.is_active)
            create_audit_log(
                db,
                int(current_user["id"]),
                "user_enabled" if payload.is_active else "user_disabled",
                "user",
                str(user_id),
                "success",
                f"previous_active={previous_active};new_active={bool(payload.is_active)}",
            )

        if payload.role is not None:
            previous_role = str(user.get("role")) if user else ""
            next_role = normalize_role_for_storage(payload.role)
            if previous_role != next_role:
                user = set_user_role(db, user_id, next_role)
                create_audit_log(
                    db,
                    int(current_user["id"]),
                    "role_changed",
                    "user",
                    str(user_id),
                    "success",
                    f"from={previous_role};to={next_role};to_label={role_label(next_role)}",
                )

        if payload.password:
            user = set_user_password(db, user_id, payload.password)
            create_audit_log(
                db,
                int(current_user["id"]),
                "password_reset",
                "user",
                str(user_id),
                "success",
                "password_stored=false",
            )

        if payload.pilot_enabled is not None:
            already_enabled = bool(user.get("pilot_enabled")) if user else False
            if payload.pilot_enabled and not already_enabled and count_pilot_enabled_users(db) >= settings.pilot_max_users:
                raise HTTPException(status_code=400, detail=f"Pilot対象者は最大{settings.pilot_max_users}名までです。")
            user = set_user_pilot_settings(db, user_id, payload.pilot_enabled, payload.pilot_completed, payload.pilot_note)
            create_audit_log(
                db,
                int(current_user["id"]),
                "pilot_target_changed",
                "user",
                str(user_id),
                "success",
                f"pilot_enabled={payload.pilot_enabled};pilot_completed={payload.pilot_completed}",
            )
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
                "pilot_target_changed",
                "user",
                str(user_id),
                "success",
                f"pilot_completed={payload.pilot_completed};pilot_note_updated={bool(payload.pilot_note)}",
            )

        create_audit_log(
            db,
            int(current_user["id"]),
            "user_updated",
            "user",
            str(user_id),
            "success",
            (
                f"is_active={payload.is_active};role_changed={payload.role is not None};"
                f"password_reset={bool(payload.password)};pilot_enabled={payload.pilot_enabled};"
                f"pilot_completed={payload.pilot_completed}"
            ),
        )
    return {"user": user}
