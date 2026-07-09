from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_roles
from app.db import get_db
from app.models import UserCreateRequest, UserUpdateRequest
from app.repositories import create_audit_log, create_user, list_users, set_user_active

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("")
async def get_users(_: dict = Depends(require_roles("admin"))) -> dict[str, list[dict]]:
    with get_db() as db:
        return {"users": list_users(db)}


@router.post("")
async def post_user(payload: UserCreateRequest, current_user: dict = Depends(require_roles("admin"))) -> dict:
    try:
        with get_db() as db:
            user = create_user(db, payload.email, payload.password, payload.role)
            create_audit_log(db, int(current_user["id"]), "save", "user", str(user["id"]), "success", f"role={payload.role}")
        return {"user": user}
    except Exception as exc:
        raise HTTPException(status_code=400, detail="ユーザーを作成できませんでした。メールアドレスの重複や入力内容を確認してください。") from exc


@router.patch("/{user_id}")
async def patch_user(user_id: int, payload: UserUpdateRequest, current_user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        user = set_user_active(db, user_id, payload.is_active)
        create_audit_log(
            db,
            int(current_user["id"]),
            "settings_change",
            "user",
            str(user_id),
            "success" if user else "failure",
            f"is_active={payload.is_active}",
        )
    if not user:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません。")
    return {"user": user}
