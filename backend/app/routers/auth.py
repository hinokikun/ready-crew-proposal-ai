import hmac

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.config import settings
from app.db import get_db
from app.models import AuthLoginRequest, AuthResponse, AuthStatusResponse
from app.repositories import authenticate_user, create_audit_log, create_user, get_user_by_id
from app.security import create_auth_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthLoginRequest) -> AuthResponse:
    email = (payload.email or "").strip().lower()
    with get_db() as db:
        user = authenticate_user(db, email, payload.password) if email else None
        if not user and not email and settings.app_access_password and hmac.compare_digest(payload.password, settings.app_access_password):
            fallback_email = settings.initial_admin_email or "legacy-admin@example.local"
            existing = db.execute("SELECT * FROM users WHERE email = ?", (fallback_email,)).fetchone()
            user = dict(existing) if existing else create_user(db, fallback_email, payload.password, "admin")
        if not user:
            create_audit_log(db, None, "login", "user", email or "legacy", "failure")
            raise HTTPException(status_code=401, detail="メールアドレスまたはパスワードが正しくありません。")
        create_audit_log(db, int(user["id"]), "login", "user", str(user["id"]), "success")
    return AuthResponse(
        authenticated=True,
        token=create_auth_token(int(user["id"]), user["email"], user["role"]),
        expires_in_seconds=settings.app_auth_token_ttl_seconds,
        message="ログインしました。",
        user={"id": user["id"], "email": user["email"], "role": user["role"], "is_active": bool(user["is_active"])},
    )


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(user: dict = Depends(get_current_user)) -> AuthStatusResponse:
    with get_db() as db:
        current = get_user_by_id(db, int(user["id"]))
    return AuthStatusResponse(
        authenticated=True,
        auth_configured=bool(settings.app_auth_secret),
        user=current,
    )
