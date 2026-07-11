from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import Request

from app.security import verify_auth_token

SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "password",
    "api_key",
    "apikey",
    "openai_api_key",
    "token",
    "secret",
    "database_url",
    "project_brief",
    "generated_text",
    "input_text",
    "output_text",
}


def is_sensitive_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized in SENSITIVE_KEYS or any(
        marker in normalized
        for marker in ("authorization", "cookie", "password", "apikey", "token", "secret", "databaseurl")
    )


def new_request_id() -> str:
    return uuid4().hex


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def get_request_role(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return "anonymous"
    payload = verify_auth_token(token)
    if not payload:
        return "invalid"
    return str(payload.get("role") or "authenticated")


def sanitize_log_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if is_sensitive_key(key) else sanitize_log_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_log_value(item) for item in value[:20]]
    if isinstance(value, str) and len(value) > 500:
        return f"{value[:500]}..."
    return value


def log_structured(logger: logging.Logger, level: str, message: str, **fields: Any) -> None:
    payload = {
        "timestamp": utc_timestamp(),
        "level": level.upper(),
        "message": message,
        **sanitize_log_value(fields),
    }
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))


def report_error(error: BaseException, context: dict[str, Any] | None = None, logger: logging.Logger | None = None) -> None:
    target_logger = logger or logging.getLogger("app.error")
    safe_context = sanitize_log_value(context or {})
    log_structured(
        target_logger,
        "error",
        "application_error",
        error_type=error.__class__.__name__,
        context=safe_context,
    )


def perf_counter_ms(start: float) -> int:
    return max(0, round((time.perf_counter() - start) * 1000))
