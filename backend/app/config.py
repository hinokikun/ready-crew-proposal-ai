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
    app_version: str = os.getenv("APP_VERSION", "17.1-rc1")
    environment: str = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "local"))
    pilot_mode: bool = _as_bool(os.getenv("PILOT_MODE"), False)
    pilot_start_date: str = os.getenv("PILOT_START_DATE", "")
    pilot_end_date: str = os.getenv("PILOT_END_DATE", "")
    pilot_max_users: int = _as_int(os.getenv("PILOT_MAX_USERS"), 5)
    maintenance_mode: bool = _as_bool(os.getenv("MAINTENANCE_MODE"), False)
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
    app_auth_secret: str = os.getenv("APP_AUTH_SECRET", "")
    app_auth_token_ttl_seconds: int = _as_int(os.getenv("APP_AUTH_TOKEN_TTL_SECONDS"), 60 * 60 * 12)
    initial_admin_email: str = os.getenv("INITIAL_ADMIN_EMAIL", "").strip().lower()
    initial_admin_password: str = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///app.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    allow_startup_schema_migration: bool = _as_bool(
        os.getenv("AUTO_SCHEMA_PATCH"),
        _as_bool(
            os.getenv("ALLOW_STARTUP_SCHEMA_MIGRATION"),
            os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "local")).strip().lower() not in {"production", "prod"},
        ),
    )
    rate_limit_enabled: bool = _as_bool(os.getenv("RATE_LIMIT_ENABLED"), True)
    rate_limit_login_limit: int = _as_int(os.getenv("RATE_LIMIT_LOGIN_LIMIT"), 10)
    rate_limit_login_window_seconds: int = _as_int(os.getenv("RATE_LIMIT_LOGIN_WINDOW_SECONDS"), 60)
    rate_limit_generation_limit: int = _as_int(os.getenv("RATE_LIMIT_GENERATION_LIMIT"), 20)
    rate_limit_generation_window_seconds: int = _as_int(os.getenv("RATE_LIMIT_GENERATION_WINDOW_SECONDS"), 60)
    rate_limit_admin_limit: int = _as_int(os.getenv("RATE_LIMIT_ADMIN_LIMIT"), 60)
    rate_limit_admin_window_seconds: int = _as_int(os.getenv("RATE_LIMIT_ADMIN_WINDOW_SECONDS"), 60)
    beautiful_ai_api_key: str = os.getenv("BEAUTIFUL_AI_API_KEY", "")
    beautiful_ai_enabled: bool = _as_bool(os.getenv("BEAUTIFUL_AI_ENABLED"), False)
    beautiful_ai_mock: bool = _as_bool(os.getenv("BEAUTIFUL_AI_MOCK"), False)
    beautiful_ai_api_mode: str = os.getenv("BEAUTIFUL_AI_API_MODE", "prompt").strip().lower()
    beautiful_ai_base_url: str = os.getenv("BEAUTIFUL_AI_BASE_URL", "https://www.beautiful.ai/api/v1").rstrip("/")
    beautiful_ai_default_theme_id: str = os.getenv("BEAUTIFUL_AI_DEFAULT_THEME_ID", "")
    beautiful_ai_workspace_id: str = os.getenv("BEAUTIFUL_AI_WORKSPACE_ID", "")
    beautiful_ai_folder_id: str = os.getenv("BEAUTIFUL_AI_FOLDER_ID", "")
    beautiful_ai_image_source: str = os.getenv("BEAUTIFUL_AI_IMAGE_SOURCE", "ai")
    beautiful_ai_image_style: str = os.getenv("BEAUTIFUL_AI_IMAGE_STYLE", "clean corporate proposal")
    beautiful_ai_timeout_seconds: int = _as_int(os.getenv("BEAUTIFUL_AI_TIMEOUT_SECONDS"), 120)
    presentation_max_revisions: int = _as_int(os.getenv("PRESENTATION_MAX_REVISIONS"), 3)
    optimization_min_sample_size: int = _as_int(os.getenv("OPTIMIZATION_MIN_SAMPLE_SIZE"), 10)
    optimization_weight_impact: float = _as_float(os.getenv("OPTIMIZATION_WEIGHT_IMPACT"), 0.30)
    optimization_weight_confidence: float = _as_float(os.getenv("OPTIMIZATION_WEIGHT_CONFIDENCE"), 0.25)
    optimization_weight_urgency: float = _as_float(os.getenv("OPTIMIZATION_WEIGHT_URGENCY"), 0.20)
    optimization_weight_adoption: float = _as_float(os.getenv("OPTIMIZATION_WEIGHT_ADOPTION"), 0.15)
    optimization_weight_effort: float = _as_float(os.getenv("OPTIMIZATION_WEIGHT_EFFORT"), 0.10)


settings = Settings()


