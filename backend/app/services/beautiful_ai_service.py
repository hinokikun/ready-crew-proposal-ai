from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Any
from urllib.parse import urlparse

import httpx

from app.beautiful_ai.presentation_mapper import build_request_summary, map_to_beautiful_ai_payload
from app.beautiful_ai.schemas import (
    BeautifulAiPresentationRecord,
    BeautifulAiPresentationRequest,
    BeautifulAiPresentationResponse,
    BeautifulAiStatusResponse,
)
from app.config import settings
from app.quality_gates import get_quality_gate
from app.repositories import create_audit_log


class BeautifulAiServiceError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        error_type: str,
        message: str,
        retry_after_seconds: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message)


def get_beautiful_ai_status() -> BeautifulAiStatusResponse:
    configured = bool(settings.beautiful_ai_api_key) or settings.beautiful_ai_mock
    enabled = settings.beautiful_ai_enabled and configured
    if settings.beautiful_ai_mock and settings.beautiful_ai_enabled:
        message = "Beautiful.ai連携はモックモードで利用可能です。"
    elif enabled:
        message = "Beautiful.ai連携は利用可能です。"
    elif not settings.beautiful_ai_enabled:
        message = "Beautiful.ai連携は未設定です。既存PPTXをご利用ください。"
    else:
        message = "Beautiful.ai APIキーを設定してください。"
    return BeautifulAiStatusResponse(enabled=enabled, configured=configured, mock=settings.beautiful_ai_mock, message=message)


def list_presentations_by_project(db: Connection, project_id: str) -> list[BeautifulAiPresentationRecord]:
    rows = db.execute(
        """
        SELECT id, project_id, presentation_id, title, editor_url, player_url, status, theme_id, provider, error_type, created_at, updated_at
        FROM beautiful_ai_presentations
        WHERE project_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 20
        """,
        (project_id[:120],),
    ).fetchall()
    return [BeautifulAiPresentationRecord(**dict(row)) for row in rows]


def _latest_success(db: Connection, project_id: str) -> dict[str, Any] | None:
    row = db.execute(
        """
        SELECT *
        FROM beautiful_ai_presentations
        WHERE project_id = ? AND status IN ('created', 'succeeded', 'completed', 'mock')
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
        (project_id[:120],),
    ).fetchone()
    return dict(row) if row else None


def _insert_presentation_record(
    db: Connection,
    *,
    request: BeautifulAiPresentationRequest,
    user_id: int,
    presentation_id: str = "",
    title: str,
    editor_url: str = "",
    player_url: str = "",
    status: str,
    theme_id: str = "",
    provider: str = "beautiful.ai",
    request_summary: str = "",
    error_type: str = "",
) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO beautiful_ai_presentations
            (project_id, user_id, presentation_id, title, editor_url, player_url, status, theme_id, provider, request_summary, error_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request.project_id[:120],
            user_id,
            presentation_id[:240],
            title[:240],
            _safe_url(editor_url),
            _safe_url(player_url),
            status[:40],
            theme_id[:160],
            provider[:80],
            request_summary[:500],
            error_type[:80],
        ),
    )
    row = db.execute("SELECT * FROM beautiful_ai_presentations WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row) if row else {}


def _response_from_record(record: dict[str, Any]) -> BeautifulAiPresentationResponse:
    return BeautifulAiPresentationResponse(
        presentation_id=str(record.get("presentation_id") or ""),
        status=str(record.get("status") or "created"),
        title=str(record.get("title") or ""),
        editor_url=str(record.get("editor_url") or ""),
        player_url=str(record.get("player_url") or ""),
        created_at=str(record.get("created_at") or ""),
        provider=str(record.get("provider") or "beautiful.ai"),
        fallback_available=True,
    )


def _safe_url(value: str) -> str:
    raw = (value or "").strip()[:2000]
    if not raw:
        return ""
    parsed = urlparse(raw)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return ""
    return raw


def _make_mock_response(project_id: str, title: str) -> dict[str, str]:
    suffix = hashlib.sha256(project_id.encode("utf-8")).hexdigest()[:12]
    presentation_id = f"mock-{suffix}"
    return {
        "presentation_id": presentation_id,
        "editor_url": f"https://www.beautiful.ai/editor/{presentation_id}",
        "player_url": f"https://www.beautiful.ai/player/{presentation_id}",
        "status": "mock",
        "title": title,
    }


def _extract_api_result(data: dict[str, Any], fallback_title: str) -> dict[str, str]:
    nested = data.get("presentation") if isinstance(data.get("presentation"), dict) else {}
    source = {**data, **nested}
    presentation_id = str(source.get("presentation_id") or source.get("presentationId") or source.get("id") or "")
    editor_url = str(source.get("editor_url") or source.get("editorUrl") or source.get("editUrl") or source.get("url") or "")
    player_url = str(source.get("player_url") or source.get("playerUrl") or source.get("shareUrl") or source.get("viewUrl") or "")
    status = str(source.get("status") or "created")
    title = str(source.get("title") or fallback_title)
    return {
        "presentation_id": presentation_id,
        "editor_url": _safe_url(editor_url),
        "player_url": _safe_url(player_url),
        "status": status,
        "title": title,
    }


def _endpoint() -> str:
    base = settings.beautiful_ai_base_url.rstrip("/")
    if base.endswith("/createPresentation") or base.endswith("/generatePresentation"):
        return base
    return f"{base}/createPresentation"


async def _post_payload(payload: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {settings.beautiful_ai_api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=settings.beautiful_ai_timeout_seconds) as client:
        response = await client.post(_endpoint(), headers=headers, json=payload)
    if response.status_code == 401:
        raise BeautifulAiServiceError(status_code=401, error_type="beautiful_ai_unauthorized", message="Beautiful.ai APIキーを確認してください")
    if response.status_code == 403:
        raise BeautifulAiServiceError(status_code=403, error_type="beautiful_ai_forbidden", message="Beautiful.ai APIの利用権限が有効になっていません")
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After")
        raise BeautifulAiServiceError(
            status_code=429,
            error_type="beautiful_ai_rate_limit",
            message="Beautiful.aiの利用上限に達しました。時間を置くか既存PPTXをご利用ください",
            retry_after_seconds=int(retry_after) if retry_after and retry_after.isdigit() else None,
        )
    if response.status_code >= 400:
        raise BeautifulAiServiceError(status_code=502, error_type="beautiful_ai_service_error", message="Beautiful.ai側で処理に失敗しました。既存PPTXをご利用ください")
    parsed = response.json()
    return parsed if isinstance(parsed, dict) else {}


def _ensure_quality_gate_unlocked(db: Connection, project_id: str) -> None:
    gate = get_quality_gate(db, project_id)
    if not gate or not bool(gate.get("download_unlocked")):
        raise BeautifulAiServiceError(
            status_code=409,
            error_type="quality_gate_incomplete",
            message="提出前確認ゲートを完了すると、Beautiful.ai提案書を作成できます。",
        )


async def create_beautiful_ai_presentation(
    db: Connection,
    *,
    request: BeautifulAiPresentationRequest,
    user_id: int,
) -> BeautifulAiPresentationResponse:
    status = get_beautiful_ai_status()
    if not status.enabled:
        raise BeautifulAiServiceError(status_code=503, error_type="beautiful_ai_disabled", message=status.message)

    _ensure_quality_gate_unlocked(db, request.project_id)
    if not request.force_new:
        existing = _latest_success(db, request.project_id)
        if existing:
            return _response_from_record(existing)

    payload_model = map_to_beautiful_ai_payload(request)
    payload = payload_model.dict()
    request_summary = build_request_summary(request, len(payload_model.slides))
    title = payload_model.title

    create_audit_log(db, user_id, "beautiful_ai_generation_started", "beautiful_ai", request.project_id, "success", "fallback_available=true")
    try:
        if settings.beautiful_ai_mock:
            api_result = _make_mock_response(request.project_id, title)
        else:
            api_result = _extract_api_result(await _post_payload(payload), title)
    except httpx.TimeoutException as exc:
        _insert_presentation_record(
            db,
            request=request,
            user_id=user_id,
            title=title,
            status="failed",
            theme_id=payload_model.themeId,
            request_summary=request_summary,
            error_type="beautiful_ai_timeout",
        )
        create_audit_log(db, user_id, "beautiful_ai_generation_failed", "beautiful_ai", request.project_id, "failure", "error_type=beautiful_ai_timeout")
        raise BeautifulAiServiceError(
            status_code=504,
            error_type="beautiful_ai_timeout",
            message="Beautiful.aiの処理に時間がかかっています。既存PPTXも利用できます",
        ) from exc
    except BeautifulAiServiceError as exc:
        _insert_presentation_record(
            db,
            request=request,
            user_id=user_id,
            title=title,
            status="failed",
            theme_id=payload_model.themeId,
            request_summary=request_summary,
            error_type=exc.error_type,
        )
        create_audit_log(db, user_id, "beautiful_ai_generation_failed", "beautiful_ai", request.project_id, "failure", f"error_type={exc.error_type}")
        raise

    if not api_result.get("presentation_id"):
        api_result["presentation_id"] = f"beautiful-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    record = _insert_presentation_record(
        db,
        request=request,
        user_id=user_id,
        presentation_id=api_result["presentation_id"],
        title=api_result.get("title") or title,
        editor_url=api_result.get("editor_url") or "",
        player_url=api_result.get("player_url") or "",
        status=api_result.get("status") or "created",
        theme_id=payload_model.themeId,
        request_summary=request_summary,
    )
    create_audit_log(db, user_id, "beautiful_ai_generation_succeeded", "beautiful_ai", request.project_id, "success", "fallback_available=true")
    return _response_from_record(record)


def record_editor_opened(db: Connection, *, presentation_id: str, user_id: int) -> None:
    row = db.execute(
        "SELECT project_id FROM beautiful_ai_presentations WHERE presentation_id = ? ORDER BY updated_at DESC, id DESC LIMIT 1",
        (presentation_id[:240],),
    ).fetchone()
    create_audit_log(
        db,
        user_id,
        "beautiful_ai_editor_opened",
        "beautiful_ai",
        str(row["project_id"] if row else ""),
        "success",
        "url_opened=true",
    )
