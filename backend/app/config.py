import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _as_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    use_mock_ai: bool = _as_bool(os.getenv("USE_MOCK_AI"), False)
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    )
    cors_origin_regex: str | None = os.getenv("CORS_ORIGIN_REGEX", "").strip() or None
    request_timeout_seconds: float = _as_float(os.getenv("REQUEST_TIMEOUT_SECONDS"), 60.0)
    app_access_password: str = os.getenv("APP_ACCESS_PASSWORD", "")
    app_auth_secret: str = os.getenv("APP_AUTH_SECRET", "") or os.getenv("APP_ACCESS_PASSWORD", "")
    app_auth_token_ttl_seconds: int = _as_int(os.getenv("APP_AUTH_TOKEN_TTL_SECONDS"), 60 * 60 * 12)


settings = Settings()


