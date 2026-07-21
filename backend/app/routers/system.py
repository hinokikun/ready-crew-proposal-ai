from __future__ import annotations

import os
import tempfile
import time
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Any, Literal
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.auth import require_roles
from app.config import settings
from app.db import get_db, get_db_health
from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest, WinProbability
from app.repositories import create_audit_log
from app.services.beautiful_ai_service import get_beautiful_ai_status, run_beautiful_ai_connection_test
from app.services.pdf_service import build_estimate_pdf_bytes
from app.services.presentation_engine_integration import build_pptx_bytes_for_engine


router = APIRouter(prefix="/api/system", tags=["system"])

CheckStatus = Literal["ok", "warning", "error", "skipped", "unknown"]
EnvironmentStatus = Literal["configured", "missing", "invalid", "disabled", "optional", "unknown"]


class ConnectionTestRequest(BaseModel):
    checks: list[str] = Field(default_factory=list, max_items=20)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _duration_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _check(name: str, status: CheckStatus, message: str, *, label: str | None = None, duration_ms: int = 0, action: str = "") -> dict[str, Any]:
    return {
        "name": name,
        "label": label or name,
        "status": status,
        "message": message,
        "duration_ms": duration_ms,
        "action": action,
    }


def _overall_status(checks: list[dict[str, Any]]) -> CheckStatus:
    statuses = {str(item["status"]) for item in checks}
    if "error" in statuses:
        return "error"
    if "warning" in statuses or "unknown" in statuses:
        return "warning"
    return "ok"


def _summary(checks: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total": len(checks),
        "ok": sum(1 for item in checks if item["status"] == "ok"),
        "warning": sum(1 for item in checks if item["status"] == "warning"),
        "error": sum(1 for item in checks if item["status"] == "error"),
        "skipped": sum(1 for item in checks if item["status"] == "skipped"),
        "unknown": sum(1 for item in checks if item["status"] == "unknown"),
    }


@router.get("/diagnostics")
async def get_system_diagnostics(request: Request) -> dict[str, Any]:
    db_health = _safe_db_health()
    database_connected = bool(db_health.get("db_connected"))
    auth_available = bool(settings.app_auth_secret)
    openai_configured = bool(settings.openai_api_key) or settings.use_mock_ai
    openai_enabled = bool(settings.openai_api_key) and not settings.use_mock_ai
    beautiful_status = _safe_beautiful_ai_status()
    frontend_api_base_url = request.headers.get("x-frontend-api-base-url", "")

    checks = [
        _check("backend", "ok", "Backendは応答しています。", label="Backend"),
        _check(
            "database",
            "ok" if database_connected else "error",
            "DB接続は正常です。" if database_connected else "DBに接続できません。BackendのDB設定を確認してください。",
            label="Database",
            action="" if database_connected else "backend/.env の DATABASE_URL とDB起動状態を確認してください。",
        ),
        _check(
            "auth",
            "ok" if auth_available else "warning",
            "認証設定は利用できます。" if auth_available else "認証Secretが未設定です。",
            label="Auth",
            action="" if auth_available else "APP_AUTH_SECRET を設定してください。",
        ),
        _check(
            "openai",
            "ok" if openai_configured else "warning",
            "OpenAI設定は利用できます。" if openai_configured else "OpenAI APIキーが設定されていません。",
            label="OpenAI",
            action="" if openai_configured else "OPENAI_API_KEY または USE_MOCK_AI を確認してください。",
        ),
        _check(
            "beautiful_ai",
            "ok" if beautiful_status["enabled"] and beautiful_status["configured"] else "warning",
            "Beautiful.ai設定は利用できます。" if beautiful_status["enabled"] and beautiful_status["configured"] else "Beautiful.aiの設定が不足しています。",
            label="Beautiful.ai",
            action="" if beautiful_status["enabled"] and beautiful_status["configured"] else "BEAUTIFUL_AI_ENABLED と BEAUTIFUL_AI_API_KEY を確認してください。",
        ),
        _check(
            "frontend",
            "ok" if frontend_api_base_url else "unknown",
            "FrontendのAPI Base URLを確認しました。" if frontend_api_base_url else "FrontendのAPI Base URLは未確認です。",
            label="Frontend API",
        ),
    ]

    return {
        "overall_status": _overall_status(checks),
        "backend": {"reachable": True, "version": settings.app_version},
        "database": {"connected": database_connected},
        "auth": {"available": auth_available},
        "openai": {"enabled": openai_enabled, "configured": openai_configured},
        "beautiful_ai": beautiful_status,
        "frontend": {"api_base_url": frontend_api_base_url},
        "checks": checks,
    }


@router.post("/self-check")
async def post_system_self_check(user: dict = Depends(require_roles("admin"))) -> dict[str, Any]:
    started = time.perf_counter()
    started_at = _now_iso()
    checks = [
        _run_check("backend"),
        _run_check("database"),
        _run_check("auth"),
        _run_check("openai_config"),
        _run_check("openai_connection"),
        _run_check("beautiful_ai_config"),
        await _run_async_check("beautiful_ai_connection", int(user["id"])),
        _run_check("pptx_generation"),
        _run_check("pdf_generation"),
        _run_check("storage_write"),
    ]
    completed_at = _now_iso()
    with get_db() as db:
        create_audit_log(db, int(user["id"]), "system_self_check", "system", "", _overall_status(checks), "sanitized=true")
    return {
        "overall_status": _overall_status(checks),
        "summary": _summary(checks),
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_ms": _duration_ms(started),
        "checks": checks,
    }


@router.post("/connection-tests")
async def post_connection_tests(payload: ConnectionTestRequest, user: dict = Depends(require_roles("admin"))) -> dict[str, Any]:
    requested = [item.strip().lower() for item in payload.checks if item.strip()]
    if not requested:
        requested = ["backend", "database", "auth", "openai", "beautiful_ai", "pptx", "pdf", "storage"]
    alias = {
        "openai": "openai_connection",
        "beautiful_ai": "beautiful_ai_connection",
        "pptx": "pptx_generation",
        "pdf": "pdf_generation",
        "storage": "storage_write",
    }
    started = time.perf_counter()
    checks: list[dict[str, Any]] = []
    for name in requested[:20]:
        check_name = alias.get(name, name)
        if check_name == "beautiful_ai_connection":
            checks.append(await _run_async_check(check_name, int(user["id"])))
        else:
            checks.append(_run_check(check_name))
    with get_db() as db:
        create_audit_log(db, int(user["id"]), "connection_test", "system", ",".join(requested)[:120], _overall_status(checks), "sanitized=true")
    return {
        "overall_status": _overall_status(checks),
        "summary": _summary(checks),
        "started_at": _now_iso(),
        "completed_at": _now_iso(),
        "duration_ms": _duration_ms(started),
        "checks": checks,
    }


@router.get("/environment")
async def get_environment_checks(request: Request, user: dict = Depends(require_roles("admin"))) -> dict[str, Any]:
    with get_db() as db:
        user_count = int(db.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"] or 0)
    frontend_api_base_url = request.headers.get("x-frontend-api-base-url", "")
    items = [
        _env_item("OPENAI_API_KEY", bool(settings.openai_api_key), True, "required", "OpenAI APIキーを設定してください。"),
        _env_item("OPENAI_MODEL", bool(settings.openai_model), False, "recommended", "未設定時は既定モデルを利用します。"),
        _env_item("BEAUTIFUL_AI_ENABLED", settings.beautiful_ai_enabled, False, "recommended", "Beautiful.aiを利用する場合は true にしてください."),
        _env_item("BEAUTIFUL_AI_API_KEY", bool(settings.beautiful_ai_api_key), settings.beautiful_ai_enabled and not settings.beautiful_ai_mock, "required", "Beautiful.aiを利用する場合はAPIキーを設定してください。"),
        _env_item("BEAUTIFUL_AI_API_MODE", settings.beautiful_ai_api_mode in {"prompt", "structured"}, False, "recommended", "prompt または structured を指定してください。", invalid=bool(settings.beautiful_ai_api_mode and settings.beautiful_ai_api_mode not in {"prompt", "structured"})),
        _url_item("BEAUTIFUL_AI_BASE_URL", settings.beautiful_ai_base_url, False, "recommended"),
        _env_item("BEAUTIFUL_AI_WORKSPACE_ID", bool(settings.beautiful_ai_workspace_id), False, "optional", "未設定の場合はBeautiful.ai側の既定Workspaceを利用します。"),
        _env_item("BEAUTIFUL_AI_DEFAULT_THEME_ID", bool(settings.beautiful_ai_default_theme_id), False, "optional", "未設定の場合はthemeIdを送信しません。"),
        _env_item("APP_AUTH_SECRET", bool(settings.app_auth_secret), True, "required", "ログイン用Secretを設定してください。"),
        _url_item("DATABASE_URL", settings.database_url, True, "required"),
        _env_item("CORS_ORIGINS", bool(settings.cors_origins or settings.cors_origin_regex), True, "required", "FrontendのURLを許可してください。"),
        _env_item("FRONTEND_API_BASE_URL", bool(frontend_api_base_url), False, "recommended", "Frontendから送信されたAPI Base URLを確認してください。"),
        _env_item("INITIAL_ADMIN_EMAIL", bool(settings.initial_admin_email) or user_count > 0, user_count == 0, "required", "DBが空の場合は初期管理者メールが必要です。"),
        _env_item("INITIAL_ADMIN_PASSWORD", bool(settings.initial_admin_password) or user_count > 0, user_count == 0, "required", "DBが空の場合は初期管理者パスワードが必要です。"),
    ]
    summary = {
        "total": len(items),
        "configured": sum(1 for item in items if item["status"] == "configured"),
        "missing": sum(1 for item in items if item["status"] == "missing"),
        "invalid": sum(1 for item in items if item["status"] == "invalid"),
        "optional": sum(1 for item in items if item["status"] == "optional"),
    }
    with get_db() as db:
        create_audit_log(db, int(user["id"]), "environment_check", "system", "", "success", "sanitized=true")
    return {"items": items, "summary": summary}


def _run_check(name: str) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        if name == "backend":
            return _check("backend", "ok", "Backendは正常です。", label="Backend", duration_ms=_duration_ms(start))
        if name == "database":
            db_health = _safe_db_health()
            ok = bool(db_health.get("db_connected"))
            return _check("database", "ok" if ok else "error", "DB接続は正常です。" if ok else "DB接続に失敗しました。", label="Database", duration_ms=_duration_ms(start), action="" if ok else "DATABASE_URLとDBの起動状態を確認してください。")
        if name == "auth":
            ok = bool(settings.app_auth_secret)
            return _check("auth", "ok" if ok else "warning", "認証機能は利用できます。" if ok else "認証Secretが未設定です。", label="Auth", duration_ms=_duration_ms(start), action="" if ok else "APP_AUTH_SECRETを設定してください。")
        if name == "openai_config":
            ok = bool(settings.openai_api_key) or settings.use_mock_ai
            return _check("openai_config", "ok" if ok else "warning", "OpenAI設定は利用できます。" if ok else "OpenAI APIキーが未設定です。", label="OpenAI設定", duration_ms=_duration_ms(start), action="" if ok else "OPENAI_API_KEYを設定してください。")
        if name == "openai_connection":
            if settings.use_mock_ai:
                return _check("openai_connection", "ok", "Mock AIモードのためOpenAI疎通は不要です。", label="OpenAI疎通", duration_ms=_duration_ms(start))
            if not settings.openai_api_key:
                return _check("openai_connection", "skipped", "OpenAI APIキーが未設定のため疎通確認をスキップしました。", label="OpenAI疎通", duration_ms=_duration_ms(start), action="OPENAI_API_KEYを設定してください。")
            return _check("openai_connection", "skipped", "生成コスト防止のため、OpenAI実通信は設定確認に留めました。", label="OpenAI疎通", duration_ms=_duration_ms(start), action="本番前に低コストの疎通確認を手動で実施してください。")
        if name == "beautiful_ai_config":
            status = _safe_beautiful_ai_status()
            ok = bool(status["enabled"] and status["configured"])
            return _check("beautiful_ai_config", "ok" if ok else "warning", "Beautiful.ai設定は利用できます。" if ok else "Beautiful.ai設定が不足しています。", label="Beautiful.ai設定", duration_ms=_duration_ms(start), action="" if ok else "BEAUTIFUL_AI_ENABLEDとBEAUTIFUL_AI_API_KEYを確認してください。")
        if name == "pptx_generation":
            payload = _sample_pptx_payload()
            result = build_pptx_bytes_for_engine(payload)
            ok = bool(result.pptx_bytes and len(result.pptx_bytes) > 1000)
            return _check("pptx_generation", "ok" if ok else "error", "PPTX一時生成に成功しました。" if ok else "PPTX生成結果が空です。", label="PPTX生成", duration_ms=_duration_ms(start), action="" if ok else "PPTX生成サービスを確認してください。")
        if name == "pdf_generation":
            pdf_bytes = build_estimate_pdf_bytes(_sample_pptx_payload())
            ok = bool(pdf_bytes and len(pdf_bytes) > 1000)
            return _check("pdf_generation", "ok" if ok else "error", "PDF一時生成に成功しました。" if ok else "PDF生成結果が空です。", label="PDF生成", duration_ms=_duration_ms(start), action="" if ok else "PDF生成サービスを確認してください。")
        if name == "storage_write":
            with tempfile.NamedTemporaryFile(prefix="ready-crew-self-check-", suffix=".tmp", delete=True) as tmp:
                tmp.write(b"ok")
                tmp.flush()
            return _check("storage_write", "ok", "一時ファイル書き込みは正常です。", label="一時Storage", duration_ms=_duration_ms(start))
        return _check(name, "unknown", "未対応のチェック項目です。", label=name, duration_ms=_duration_ms(start))
    except Exception:
        return _check(name, "error", "チェック中にエラーが発生しました。", label=name, duration_ms=_duration_ms(start), action="Backendログのrequest_id付近を確認してください。")


async def _run_async_check(name: str, user_id: int) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        if name != "beautiful_ai_connection":
            return _run_check(name)
        status = _safe_beautiful_ai_status()
        if not (status["enabled"] and status["configured"]):
            return _check("beautiful_ai_connection", "skipped", "Beautiful.ai設定が不足しているため疎通確認をスキップしました。", label="Beautiful.ai疎通", duration_ms=_duration_ms(start), action="backend/.envのBeautiful.ai設定を確認してください。")
        with get_db() as db:
            result = await run_beautiful_ai_connection_test(db, user_id=user_id)
        return _check(
            "beautiful_ai_connection",
            "ok" if result.ok else "error",
            result.message if result.message else ("Beautiful.ai疎通は正常です。" if result.ok else "Beautiful.ai疎通に失敗しました。"),
            label="Beautiful.ai疎通",
            duration_ms=_duration_ms(start),
            action="" if result.ok else "Beautiful.ai管理画面のAPIキー、Workspace、利用権限を確認してください。",
        )
    except Exception:
        return _check("beautiful_ai_connection", "error", "Beautiful.ai疎通確認中にエラーが発生しました。", label="Beautiful.ai疎通", duration_ms=_duration_ms(start), action="Beautiful.ai設定とBackendログを確認してください。")


def _safe_db_health() -> dict[str, Any]:
    try:
        return get_db_health()
    except Exception:
        return {"db_connected": False}


def _safe_beautiful_ai_status() -> dict[str, Any]:
    try:
        with get_db() as db:
            status = get_beautiful_ai_status(db)
        return {
            "enabled": bool(status.enabled),
            "configured": bool(status.configured),
            "mock": bool(status.mock),
            "api_reachable": bool(status.api_reachable),
            "api_mode": status.api_mode,
        }
    except Exception:
        return {"enabled": False, "configured": False, "mock": False, "api_reachable": False, "api_mode": "unknown"}


def _env_item(name: str, configured: bool, required: bool, category: str, action: str, *, invalid: bool = False) -> dict[str, Any]:
    if invalid:
        status: EnvironmentStatus = "invalid"
        message = "設定値の形式を確認してください。"
    elif configured:
        status = "configured"
        message = "設定済みです。"
    elif required:
        status = "missing"
        message = "必須設定が未設定です。"
    elif category == "optional":
        status = "optional"
        message = "任意設定です。未設定でも起動できます。"
    else:
        status = "missing"
        message = "推奨設定が未設定です。"
    return {"name": name, "status": status, "required": required, "category": category, "source": "environment" if os.getenv(name) is not None else "default", "message": message, "action": "" if status == "configured" else action}


def _url_item(name: str, value: str, required: bool, category: str) -> dict[str, Any]:
    parsed = urlparse(value or "")
    valid = bool(parsed.scheme and (parsed.netloc or parsed.scheme == "sqlite"))
    return _env_item(name, valid, required, category, f"{name} のURL形式を確認してください。", invalid=bool(value and not valid))


def _sample_pptx_payload() -> PptxDownloadRequest:
    data = PowerPointData(
        deck_title="自己診断用テスト提案書",
        client_name="テスト株式会社",
        slides=[
            PowerPointSlide(
                slide_no=1,
                layout="summary",
                title="自己診断",
                bullets=["このデータは一時生成確認のみで使用します。", "DBには保存しません。"],
                speaker_notes="自己診断用の一時データです。",
                visual_suggestion="シンプルなカード",
            )
        ],
    )
    win = WinProbability(
        rank="B",
        probability=60,
        label="Bランク",
        reason="自己診断用の固定値です。",
        risk_score=3,
        risk_label="中",
        positive_factors=["設定確認"],
        risk_factors=["本番データではありません"],
        recommended_next_actions=["管理者が結果を確認する"],
        improvement_actions=["必要に応じて設定を見直す"],
        projected_probability_after_actions=70,
    )
    return PptxDownloadRequest(
        powerpoint_generation_data=data,
        win_probability=win,
        project_brief="自己診断用の一時案件です。",
        client_company_info="テスト株式会社",
        desired_launch_timing="未定",
        budget_range="未定",
        own_service_info="ProposalPilot",
    )
