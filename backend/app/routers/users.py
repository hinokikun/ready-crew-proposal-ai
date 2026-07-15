from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, require_roles
from app.config import settings
from app.db import get_db
from app.models import PasswordChangeRequest, UserCreateRequest, UserUpdateRequest
from app.rate_limit import rate_limit_dependency
from app.repositories import (
    count_active_admin_users,
    count_pilot_enabled_users,
    create_audit_log,
    create_user,
    get_user_by_id,
    list_users,
    set_user_active,
    set_user_display_name,
    set_user_password,
    set_user_password_change_required,
    set_user_pilot_settings,
    set_user_role,
    soft_delete_user,
)
from app.role_permissions import normalize_role_for_storage, role_label
from app.security import verify_password

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
            user = create_user(db, payload.email, payload.password, payload.role, payload.display_name)
            create_audit_log(
                db,
                int(current_user["id"]),
                "user_created",
                "user",
                str(user["id"]),
                "success",
                f"role={user['role']};role_label={role_label(str(user['role']))};display_name_set={bool(payload.display_name)}",
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

        if payload.display_name is not None:
            user = set_user_display_name(db, user_id, payload.display_name)
            create_audit_log(
                db,
                int(current_user["id"]),
                "user_display_name_updated",
                "user",
                str(user_id),
                "success",
                "sanitized=true",
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
            user = set_user_password(db, user_id, payload.password, bool(payload.password_change_required))
            create_audit_log(
                db,
                int(current_user["id"]),
                "password_reset",
                "user",
                str(user_id),
                "success",
                f"password_stored=false;change_required={bool(payload.password_change_required)}",
            )
        elif payload.password_change_required is not None:
            user = set_user_password_change_required(db, user_id, payload.password_change_required)
            create_audit_log(
                db,
                int(current_user["id"]),
                "password_change_required_updated",
                "user",
                str(user_id),
                "success",
                f"required={bool(payload.password_change_required)}",
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
                f"pilot_completed={payload.pilot_completed};display_name_updated={payload.display_name is not None}"
            ),
        )
    return {"user": user}


@router.patch("/me/password")
async def change_my_password(
    payload: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    _: None = Depends(rate_limit_dependency("auth")),
) -> dict:
    if payload.new_password != payload.new_password_confirm:
        raise HTTPException(status_code=400, detail="新しいパスワードが一致しません。")
    with get_db() as db:
        row = db.execute("SELECT password_hash FROM users WHERE id = ? AND deleted_at IS NULL", (int(current_user["id"]),)).fetchone()
        if not row or not verify_password(payload.current_password, row["password_hash"]):
            create_audit_log(db, int(current_user["id"]), "password_change_failed", "user", str(current_user["id"]), "failure", "reason=current_password")
            raise HTTPException(status_code=400, detail="現在のパスワードが正しくありません。")
        user = set_user_password(db, int(current_user["id"]), payload.new_password, False)
        create_audit_log(db, int(current_user["id"]), "password_changed", "user", str(current_user["id"]), "success", "password_stored=false")
    return {"ok": True, "user": user, "message": "パスワードを変更しました。再ログインしてください。"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_roles("admin")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    with get_db() as db:
        user = get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません。")
        if user_id == int(current_user["id"]):
            raise HTTPException(status_code=400, detail="自分自身のアカウントは削除できません。")
        if user["role"] == "admin" and count_active_admin_users(db) <= 1:
            raise HTTPException(status_code=400, detail="最後の有効な管理者は削除できません。")
        deleted_user = soft_delete_user(db, user_id)
        create_audit_log(
            db,
            int(current_user["id"]),
            "user_deleted",
            "user",
            str(user_id),
            "success",
            "logical_delete=true",
        )
    return {"user": deleted_user}
