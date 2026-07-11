from __future__ import annotations

import hashlib
from collections.abc import Callable

from fastapi import HTTPException, Request

from app.config import settings
from app.observability import new_request_id
from app.rate_limit.backend import InMemoryRateLimitBackend
from app.security import verify_auth_token


_backend = InMemoryRateLimitBackend()


def reset_rate_limits() -> None:
    _backend.reset()


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _client_key(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    raw_ip = forwarded_for.split(",", 1)[0].strip() or (request.client.host if request.client else "unknown")
    return f"ip:{_hash(raw_ip)}"


def _user_or_client_key(request: Request) -> str:
    scheme, _, token = (request.headers.get("authorization") or "").partition(" ")
    if scheme.lower() == "bearer" and token:
        payload = verify_auth_token(token)
        if payload and payload.get("id"):
            return f"user:{payload['id']}"
    return _client_key(request)


def _limit_config(scope: str) -> tuple[int, int]:
    if scope == "login":
        return settings.rate_limit_login_limit, settings.rate_limit_login_window_seconds
    if scope == "admin":
        return settings.rate_limit_admin_limit, settings.rate_limit_admin_window_seconds
    return settings.rate_limit_generation_limit, settings.rate_limit_generation_window_seconds


def rate_limit_dependency(scope: str) -> Callable[[Request], None]:
    def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        limit, window_seconds = _limit_config(scope)
        identity = _client_key(request) if scope == "login" else _user_or_client_key(request)
        result = _backend.check(f"{scope}:{identity}", limit, window_seconds)
        if result.allowed:
            return
        request_id = getattr(request.state, "request_id", "") or new_request_id()
        raise HTTPException(
            status_code=429,
            detail={
                "error_type": "rate_limit",
                "message": "短時間に操作が集中しています。少し時間を置いてから再実行してください。",
                "request_id": request_id,
                "retry_after_seconds": result.retry_after_seconds,
            },
            headers={"Retry-After": str(result.retry_after_seconds), "X-Request-ID": request_id},
        )

    return dependency
