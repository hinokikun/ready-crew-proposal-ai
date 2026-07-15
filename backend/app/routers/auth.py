import hmac

from fastapi import APIRouter, Depends, HTTPException

from app.auth import ensure_pilot_user_allowed, get_current_user
from app.config import settings
from app.db import get_db
from app.models import AuthLoginRequest, AuthResponse, AuthStatusResponse
from app.repositories import authenticate_user, create_audit_log, create_user, get_user_by_id, mark_pilot_login, mark_user_login
from app.role_permissions import normalize_role_for_storage, role_group, role_label
from app.rate_limit import rate_limit_dependency
from app.security import create_auth_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])

ADMIN_LOGIN_ROLES = {"admin", "manager", "system_admin", "organization_admin"}
USER_LOGIN_ROLES = {"member", "user", "viewer"}
GENERIC_LOGIN_ERROR = "\u30e1\u30fc\u30eb\u30a2\u30c9\u30ec\u30b9\u307e\u305f\u306f\u30d1\u30b9\u30ef\u30fc\u30c9\u304c\u6b63\u3057\u304f\u3042\u308a\u307e\u305b\u3093"
INACTIVE_USER_ERROR = "\u3053\u306e\u30a2\u30ab\u30a6\u30f3\u30c8\u306f\u73fe\u5728\u7121\u52b9\u3067\u3059"
PILOT_DENIED_ERROR = "\u793e\u5185\u8a66\u9a13\u5229\u7528\u306e\u5bfe\u8c61\u5916\u3067\u3059"
USER_MODE_MISMATCH_ERROR = "\u3053\u306e\u30a2\u30ab\u30a6\u30f3\u30c8\u306f\u5229\u7528\u8005\u30ed\u30b0\u30a4\u30f3\u5bfe\u8c61\u3067\u306f\u3042\u308a\u307e\u305b\u3093\u3002\u7ba1\u7406\u8005\u30ed\u30b0\u30a4\u30f3\u304b\u3089\u30ed\u30b0\u30a4\u30f3\u3057\u3066\u304f\u3060\u3055\u3044"
ADMIN_MODE_MISMATCH_ERROR = "\u3053\u306e\u30a2\u30ab\u30a6\u30f3\u30c8\u306b\u306f\u7ba1\u7406\u8005\u6a29\u9650\u304c\u3042\u308a\u307e\u305b\u3093"


def _mask_email(email: str) -> str:
    value = (email or "").strip().lower()
    if "@" not in value:
        return "legacy" if not value else "masked"
    local, domain = value.split("@", 1)
    prefix = local[:2] if len(local) >= 2 else local[:1]
    return f"{prefix}***@{domain}"


def _role_allowed_for_login_mode(role: str, login_mode: str | None) -> bool:
    if not login_mode:
        return True
    raw_role = (role or "").strip().lower()
    storage_role = normalize_role_for_storage(raw_role)
    if login_mode == "admin":
        return raw_role in ADMIN_LOGIN_ROLES or storage_role in ADMIN_LOGIN_ROLES
    return raw_role in USER_LOGIN_ROLES or storage_role in USER_LOGIN_ROLES


def _role_mismatch_message(login_mode: str | None) -> str:
    if login_mode == "admin":
        return ADMIN_MODE_MISMATCH_ERROR
    return USER_MODE_MISMATCH_ERROR


def _audit_login(db, user_id: int | None, event_type: str, email: str, status: str, login_mode: str | None, metadata: str = "") -> None:
    mode = login_mode or "legacy"
    safe_meta = f"login_mode={mode};sanitized=true"
    if metadata:
        safe_meta = f"{safe_meta};{metadata[:180]}"
    create_audit_log(db, user_id, event_type, "auth", _mask_email(email), status, safe_meta)


def _inactive_user_matches_password(db, email: str, password: str) -> dict | None:
    if not email:
        return None
    row = db.execute("SELECT * FROM users WHERE email = ? AND is_active = 0", (email.strip().lower(),)).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        return None
    return dict(row)


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "display_name": user.get("display_name") or "",
        "email": user["email"],
        "role": user["role"],
        "role_group": role_group(str(user["role"])),
        "role_label": role_label(str(user["role"])),
        "current_organization_id": int(user.get("current_organization_id") or 1),
        "current_workspace_id": int(user.get("current_workspace_id") or 1),
        "is_active": bool(user["is_active"]),
        "auth_version": int(user.get("auth_version", 1)),
        "pilot_enabled": bool(user.get("pilot_enabled", False)),
        "pilot_started_at": user.get("pilot_started_at") or "",
        "pilot_last_used_at": user.get("pilot_last_used_at") or "",
        "pilot_completed": bool(user.get("pilot_completed", False)),
        "pilot_note": user.get("pilot_note") or "",
        "last_login_at": user.get("last_login_at") or "",
        "password_change_required": bool(user.get("password_change_required", False)),
    }


@router.post("/login", response_model=AuthResponse)
async def login(payload: AuthLoginRequest, _: None = Depends(rate_limit_dependency("login"))) -> AuthResponse:
    return _login_with_mode(payload)


def _login_with_mode(payload: AuthLoginRequest) -> AuthResponse:
    if not settings.app_auth_secret:
        raise HTTPException(status_code=503, detail="\u8a8d\u8a3c\u8a2d\u5b9a\u304c\u672a\u5b8c\u4e86\u3067\u3059\u3002\u7ba1\u7406\u8005\u306fAPP_AUTH_SECRET\u3092\u78ba\u8a8d\u3057\u3066\u304f\u3060\u3055\u3044\u3002")
    email = (payload.email or "").strip().lower()
    login_mode = payload.login_mode
    with get_db() as db:
        user = authenticate_user(db, email, payload.password) if email else None
        if not user and not email and settings.app_access_password and hmac.compare_digest(payload.password, settings.app_access_password):
            fallback_email = settings.initial_admin_email or "legacy-admin@example.local"
            existing = db.execute("SELECT * FROM users WHERE email = ?", (fallback_email,)).fetchone()
            user = dict(existing) if existing else create_user(db, fallback_email, payload.password, "admin")
            email = fallback_email
        if not user:
            inactive_user = _inactive_user_matches_password(db, email, payload.password)
            if inactive_user:
                _audit_login(db, int(inactive_user["id"]), "inactive_user_attempt", email, "failure", login_mode)
                raise HTTPException(status_code=403, detail=INACTIVE_USER_ERROR)
            _audit_login(db, None, "login_failure", email or "legacy", "failure", login_mode)
            raise HTTPException(status_code=401, detail=GENERIC_LOGIN_ERROR)
        if not _role_allowed_for_login_mode(str(user.get("role", "")), login_mode):
            _audit_login(db, int(user["id"]), "role_mismatch", email, "failure", login_mode)
            raise HTTPException(status_code=403, detail=_role_mismatch_message(login_mode))
        try:
            ensure_pilot_user_allowed(user)
        except HTTPException:
            _audit_login(db, int(user["id"]), "login_failure", email, "pilot_denied", login_mode)
            raise HTTPException(status_code=403, detail=PILOT_DENIED_ERROR)
        mark_user_login(db, int(user["id"]))
        mark_pilot_login(db, int(user["id"]))
        current = get_user_by_id(db, int(user["id"])) or user
        _audit_login(db, int(user["id"]), "login_success", email, "success", login_mode)
    return AuthResponse(
        authenticated=True,
        token=create_auth_token(int(current["id"]), current["email"], current["role"], int(current.get("auth_version", 1))),
        expires_in_seconds=settings.app_auth_token_ttl_seconds,
        message="\u30ed\u30b0\u30a4\u30f3\u3057\u307e\u3057\u305f\u3002",
        user=_public_user(current),
        login_mode=login_mode,
    )

@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(user: dict = Depends(get_current_user)) -> AuthStatusResponse:
    with get_db() as db:
        current = get_user_by_id(db, int(user["id"]))
    return AuthStatusResponse(
        authenticated=True,
        auth_configured=bool(settings.app_auth_secret),
        user=_public_user(current) if current else None,
    )


@router.post("/logout")
async def logout(user: dict = Depends(get_current_user)) -> dict:
    with get_db() as db:
        create_audit_log(db, int(user["id"]), "logout", "auth", str(user["id"]), "success", "sanitized=true")
    return {"ok": True}
