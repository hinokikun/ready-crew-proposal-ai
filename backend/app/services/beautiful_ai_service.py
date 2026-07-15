from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Any
from urllib.parse import urlparse, urlunparse

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
from app.repositories import create_audit_log, get_user_context_ids


logger = logging.getLogger(__name__)


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


def _get_beautiful_ai_runtime_summary(db: Connection | None) -> dict[str, str]:
    if db is None:
        return {"last_success_at": "", "last_error_type": ""}
    last_success = db.execute(
        """
        SELECT updated_at
        FROM beautiful_ai_presentations
        WHERE status IN ('created', 'succeeded', 'completed', 'mock')
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    last_error = db.execute(
        """
        SELECT error_type
        FROM beautiful_ai_presentations
        WHERE status = 'failed' AND error_type != ''
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    return {
        "last_success_at": str(last_success["updated_at"] if last_success else ""),
        "last_error_type": str(last_error["error_type"] if last_error else ""),
    }


def get_beautiful_ai_status(db: Connection | None = None) -> BeautifulAiStatusResponse:
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
    runtime_summary = _get_beautiful_ai_runtime_summary(db)
    return BeautifulAiStatusResponse(
        enabled=enabled,
        configured=configured,
        mock=settings.beautiful_ai_mock,
        api_mode=_api_mode(),
        resolved_endpoint=_endpoint(),
        api_reachable=True,
        route_found=True,
        backend_version=settings.app_version,
        last_success_at=runtime_summary["last_success_at"],
        last_error_type=runtime_summary["last_error_type"],
        message=message,
    )


def list_presentations_by_project(
    db: Connection,
    project_id: str,
    *,
    organization_id: int | None = None,
    workspace_id: int | None = None,
) -> list[BeautifulAiPresentationRecord]:
    context_org_id = int(organization_id or 1)
    context_workspace_id = int(workspace_id or 1)
    rows = db.execute(
        """
        SELECT id, project_id, presentation_id, title, editor_url, player_url, status, theme_id, provider, error_type, created_at, updated_at
        FROM beautiful_ai_presentations
        WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 20
        """,
        (project_id[:120], context_org_id, context_workspace_id),
    ).fetchall()
    return [BeautifulAiPresentationRecord(**dict(row)) for row in rows]


def _latest_success(db: Connection, project_id: str, *, organization_id: int, workspace_id: int) -> dict[str, Any] | None:
    row = db.execute(
        """
        SELECT *
        FROM beautiful_ai_presentations
        WHERE project_id = ? AND organization_id = ? AND workspace_id = ? AND status IN ('created', 'succeeded', 'completed', 'mock')
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
        (project_id[:120], organization_id, workspace_id),
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
    organization_id: int = 1,
    workspace_id: int = 1,
) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO beautiful_ai_presentations
            (project_id, user_id, presentation_id, title, editor_url, player_url, status, theme_id, provider, request_summary, error_type, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            organization_id,
            workspace_id,
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
    suffix = hashlib.sha256(f"{project_id}:{title}".encode("utf-8")).hexdigest()[:12]
    presentation_id = f"mock-{suffix}"
    return {
        "presentation_id": presentation_id,
        "editor_url": f"https://www.beautiful.ai/editor/{presentation_id}",
        "player_url": f"https://www.beautiful.ai/player/{presentation_id}",
        "status": "mock",
        "title": title,
    }


def _extract_api_result(data: dict[str, Any], fallback_title: str) -> dict[str, str]:
    sources: list[dict[str, Any]] = [data]
    for key in ("data", "presentation", "result"):
        nested_value = data.get(key)
        if isinstance(nested_value, dict):
            sources.append(nested_value)
            nested_presentation = nested_value.get("presentation")
            if isinstance(nested_presentation, dict):
                sources.append(nested_presentation)
    source: dict[str, Any] = {}
    for item in sources:
        source.update(item)
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


def _api_mode() -> str:
    return "structured" if settings.beautiful_ai_api_mode == "structured" else "prompt"


def _normalise_base_url() -> str:
    raw = (settings.beautiful_ai_base_url or "https://www.beautiful.ai/api/v1").strip().rstrip("/")
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    parsed = urlparse(raw)
    scheme = parsed.scheme or "https"
    netloc = parsed.netloc.lower()
    if netloc == "beautiful.ai":
        netloc = "www.beautiful.ai"
    path = parsed.path.rstrip("/") or "/api/v1"
    for suffix in ("/createPresentation", "/generatePresentation"):
        if path.endswith(suffix):
            path = path[: -len(suffix)] or "/api/v1"
    return urlunparse((scheme, netloc, path, "", "", "")).rstrip("/")


def _endpoint() -> str:
    action = "createPresentation" if _api_mode() == "structured" else "generatePresentation"
    return f"{_normalise_base_url()}/{action}"


def _clean_payload(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            cleaned_item = _clean_payload(item)
            if cleaned_item in ("", None, [], {}):
                continue
            cleaned[key] = cleaned_item
        return cleaned
    if isinstance(value, list):
        return [item for item in (_clean_payload(item) for item in value) if item not in ("", None, [], {})]
    return value


def _response_text_for_log(response: httpx.Response) -> str:
    text = response.text.strip()
    return text[:4000] if text else "<empty response body>"


def _safe_headers_for_log(headers: dict[str, str] | httpx.Headers) -> dict[str, str]:
    safe: dict[str, str] = {}
    for key, value in dict(headers).items():
        lower_key = key.lower()
        if lower_key in {"authorization", "cookie", "set-cookie", "x-api-key"}:
            safe[key] = "<redacted>"
            continue
        safe[key] = str(value)[:500]
    return safe


def _safe_request_payload_for_log(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in payload.items():
        lower_key = key.lower()
        if lower_key in {"apikey", "api_key", "authorization", "password", "secret", "token"}:
            safe[key] = "<redacted>"
        elif key == "prompt":
            safe[key] = f"<redacted prompt length={len(str(value or ''))}>"
        elif isinstance(value, list):
            safe[key] = f"<redacted list length={len(value)}>"
        elif isinstance(value, dict):
            safe[key] = f"<redacted object keys={','.join(list(value.keys())[:10])}>"
        elif isinstance(value, str):
            safe[key] = value[:500]
        elif isinstance(value, (int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = f"<redacted {type(value).__name__}>"
    return safe


def _api_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = _clean_payload(payload)
    if _api_mode() == "structured":
        return cleaned
    prompt = str(cleaned.get("prompt") or "").strip()
    if not prompt:
        raise BeautifulAiServiceError(
            status_code=400,
            error_type="beautiful_ai_prompt_required",
            message="Beautiful.ai prompt APIに送信するpromptを作成できませんでした。",
        )
    prompt_payload: dict[str, Any] = {"prompt": prompt}
    theme_id = str(cleaned.get("themeId") or "").strip()
    if theme_id:
        prompt_payload["themeId"] = theme_id
    return prompt_payload


def _log_beautiful_ai_error_response(response: httpx.Response, request_payload: dict[str, Any], request_headers: dict[str, str]) -> None:
    logger.error(
        "beautiful_ai_api_error status=%s endpoint=%s content_type=%s request_json_safe=%s request_headers_safe=%s response_headers_safe=%s response_text=%s prompt_length=%s theme_id_present=%s",
        response.status_code,
        _endpoint(),
        response.headers.get("Content-Type", ""),
        json.dumps(_safe_request_payload_for_log(request_payload), ensure_ascii=False),
        json.dumps(_safe_headers_for_log(request_headers), ensure_ascii=False),
        json.dumps(_safe_headers_for_log(response.headers), ensure_ascii=False),
        _response_text_for_log(response),
        len(str(request_payload.get("prompt") or "")),
        bool(request_payload.get("themeId")),
    )


async def _post_payload(payload: dict[str, Any]) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {settings.beautiful_ai_api_key}",
        "Content-Type": "application/json",
    }
    request_payload = _api_request_payload(payload)
    async with httpx.AsyncClient(timeout=settings.beautiful_ai_timeout_seconds) as client:
        response = await client.post(_endpoint(), headers=headers, json=request_payload)
    if 300 <= response.status_code < 400:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise BeautifulAiServiceError(
            status_code=502,
            error_type="beautiful_ai_redirect",
            message="Beautiful.ai APIがリダイレクトを返しました。BackendのBeautiful.ai接続先を確認してください。",
        )
    if response.status_code == 400:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise BeautifulAiServiceError(
            status_code=400,
            error_type="beautiful_ai_bad_request",
            message="Beautiful.aiへ送信した内容を受け付けられませんでした。入力内容を確認してください。",
        )
    if response.status_code == 401:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise BeautifulAiServiceError(status_code=401, error_type="beautiful_ai_invalid_api_key", message="Beautiful.ai APIキーを確認してください。")
    if response.status_code == 403:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise BeautifulAiServiceError(status_code=403, error_type="beautiful_ai_access_not_enabled", message="Beautiful.ai APIの利用権限が有効になっていません。")
    if response.status_code == 404:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise BeautifulAiServiceError(
            status_code=502,
            error_type="beautiful_ai_endpoint_not_found",
            message="Beautiful.ai外部APIのエンドポイントが見つかりません。BackendのBeautiful.ai接続先を確認してください。",
        )
    if response.status_code == 429:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        retry_after = response.headers.get("Retry-After")
        raise BeautifulAiServiceError(
            status_code=429,
            error_type="beautiful_ai_rate_limit",
            message="Beautiful.aiの利用上限に達しました。時間を置くか既存PPTXをご利用ください",
            retry_after_seconds=int(retry_after) if retry_after and retry_after.isdigit() else None,
        )
    if response.status_code >= 500:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise BeautifulAiServiceError(status_code=502, error_type="beautiful_ai_service_error", message="Beautiful.ai側で処理に失敗しました。既存PPTXをご利用ください。")
    if response.status_code >= 400:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise BeautifulAiServiceError(status_code=502, error_type="beautiful_ai_service_error", message="Beautiful.ai連携で処理に失敗しました。既存PPTXをご利用ください。")
    try:
        parsed = response.json()
    except ValueError as exc:
        raise BeautifulAiServiceError(status_code=502, error_type="beautiful_ai_service_error", message="Beautiful.ai APIの応答を解析できませんでした。") from exc
    return parsed if isinstance(parsed, dict) else {}


def _ensure_quality_gate_unlocked(db: Connection, project_id: str, user_id: int) -> None:
    gate = get_quality_gate(db, project_id, user_id)
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

    organization_id, workspace_id = get_user_context_ids(db, user_id)
    _ensure_quality_gate_unlocked(db, request.project_id, user_id)
    if not request.force_new:
        existing = _latest_success(db, request.project_id, organization_id=organization_id, workspace_id=workspace_id)
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
            organization_id=organization_id,
            workspace_id=workspace_id,
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
            organization_id=organization_id,
            workspace_id=workspace_id,
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
        organization_id=organization_id,
        workspace_id=workspace_id,
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
