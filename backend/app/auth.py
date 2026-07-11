from typing import Callable

from fastapi import Header, HTTPException

from app.config import settings
from app.db import get_db
from app.repositories import create_audit_log, get_runtime_maintenance_mode, get_user_by_id
from app.security import verify_auth_token


def ensure_pilot_user_allowed(user: dict) -> None:
    if not settings.pilot_mode:
        return
    if user["role"] == "admin":
        return
    if not bool(user.get("pilot_enabled")):
        raise HTTPException(
            status_code=403,
            detail="現在は社内試験利用中です。許可された試験利用者のみ利用できます。管理者へ確認してください。",
        )


def ensure_not_maintenance_mode() -> None:
    enabled = settings.maintenance_mode
    reason = "環境変数でMaintenance Modeが有効です。"
    if not enabled:
        try:
            with get_db() as db:
                runtime = get_runtime_maintenance_mode(db)
            enabled = bool(runtime["enabled"])
            reason = runtime.get("reason") or "管理者によりMaintenance Modeが有効です。"
        except Exception:
            enabled = False
    if enabled:
        try:
            with get_db() as db:
                create_audit_log(db, None, "maintenance_reject", "api", "", "failure", "sanitized=true")
        except Exception:
            pass
        raise HTTPException(
            status_code=503,
            detail={
                "error_type": "maintenance_mode",
                "message": "現在メンテナンス中のため、新規作成を停止しています。",
                "reason": reason,
                "request_id": "",
            },
        )


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="ログインが必要です。")
    payload = verify_auth_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="ログイン期限が切れています。再ログインしてください。")
    with get_db() as db:
        user = get_user_by_id(db, int(payload["id"]))
    if not user or not user["is_active"]:
        raise HTTPException(status_code=401, detail="ユーザーが無効です。管理者へ確認してください。")
    if int(payload.get("auth_version", 0)) != int(user.get("auth_version", 1)):
        raise HTTPException(status_code=401, detail="ログイン状態が更新されました。再ログインしてください。")
    if str(payload.get("role", "")) != str(user.get("role", "")):
        raise HTTPException(status_code=401, detail="権限が更新されました。再ログインしてください。")
    ensure_pilot_user_allowed(user)
    return user


def require_roles(*roles: str) -> Callable[[str | None], dict]:
    def dependency(authorization: str | None = Header(default=None)) -> dict:
        user = get_current_user(authorization)
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="この操作を行う権限がありません。")
        return user

    return dependency
