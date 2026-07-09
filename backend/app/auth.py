from typing import Callable

from fastapi import Header, HTTPException

from app.db import get_db
from app.repositories import get_user_by_id
from app.security import verify_auth_token


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
        raise HTTPException(status_code=401, detail="ユーザーが無効です。管理者に確認してください。")
    return user


def require_roles(*roles: str) -> Callable[[str | None], dict]:
    def dependency(authorization: str | None = Header(default=None)) -> dict:
        user = get_current_user(authorization)
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail="この操作を行う権限がありません。")
        return user

    return dependency
