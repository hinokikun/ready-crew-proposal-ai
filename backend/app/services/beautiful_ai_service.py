from __future__ import annotations

import json
import hashlib
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
    BeautifulAiConnectionTestResponse,
    BeautifulAiDiagnosticsResponse,
    BeautifulAiHistoryRecord,
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
        http_status: int = 0,
        response_text: str = "",
        request_json_safe: str = "",
    ) -> None:
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.retry_after_seconds = retry_after_seconds
        self.http_status = http_status
        self.response_text = response_text
        self.request_json_safe = request_json_safe
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


def get_beautiful_ai_diagnostics(
    db: Connection,
    *,
    organization_id: int,
    workspace_id: int,
) -> BeautifulAiDiagnosticsResponse:
    rows = db.execute(
        """
        SELECT id, project_id, title, status, theme_id, error_type, http_status, response_text, request_json_safe,
               endpoint, api_mode, workspace_config_id, created_at, updated_at
        FROM beautiful_ai_presentations
        WHERE organization_id = ? AND workspace_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 20
        """,
        (organization_id, workspace_id),
    ).fetchall()
    history = [_history_record_from_row(dict(row)) for row in rows]
    last = history[0] if history else None
    return BeautifulAiDiagnosticsResponse(
        enabled=bool(settings.beautiful_ai_enabled),
        configured=bool(settings.beautiful_ai_api_key or settings.beautiful_ai_mock),
        mock=bool(settings.beautiful_ai_mock),
        api_mode=_api_mode(),
        resolved_endpoint=_endpoint(),
        workspace_id=settings.beautiful_ai_workspace_id,
        theme_id=_effective_theme_id(),
        last_http_status=last.http_status if last else 0,
        last_error_type=last.error_type if last else "",
        last_response_text=last.response_text if last else "",
        last_request_json_safe=last.request_json_safe if last else "",
        last_run_at=last.updated_at if last else "",
        history=history,
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
    http_status: int = 0,
    response_text: str = "",
    request_json_safe: str = "",
    endpoint: str = "",
    api_mode: str = "",
    workspace_config_id: str = "",
    organization_id: int = 1,
    workspace_id: int = 1,
) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO beautiful_ai_presentations
            (project_id, user_id, presentation_id, title, editor_url, player_url, status, theme_id, provider, request_summary, error_type, http_status, response_text, request_json_safe, endpoint, api_mode, workspace_config_id, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            int(http_status or 0),
            _safe_log_text(response_text, 1000),
            _safe_log_text(request_json_safe, 1000),
            (endpoint or _endpoint())[:500],
            (api_mode or _api_mode())[:40],
            (workspace_config_id or settings.beautiful_ai_workspace_id)[:160],
            organization_id,
            workspace_id,
        ),
    )
    row = db.execute("SELECT * FROM beautiful_ai_presentations WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row) if row else {}


def _insert_diagnostic_record(
    db: Connection,
    *,
    user_id: int,
    title: str,
    status: str,
    error_type: str = "",
    http_status: int = 0,
    response_text: str = "",
    request_json_safe: str = "",
    organization_id: int = 1,
    workspace_id: int = 1,
) -> None:
    db.execute(
        """
        INSERT INTO beautiful_ai_presentations
            (project_id, user_id, presentation_id, title, editor_url, player_url, status, theme_id, provider,
             request_summary, error_type, http_status, response_text, request_json_safe, endpoint, api_mode, workspace_config_id,
             organization_id, workspace_id)
        VALUES (?, ?, '', ?, '', '', ?, ?, 'beautiful.ai', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "__diagnostic__",
            user_id,
            title[:240],
            status[:40],
            settings.beautiful_ai_default_theme_id[:160],
            "Beautiful.ai connection test",
            error_type[:80],
            int(http_status or 0),
            _safe_log_text(response_text, 1000),
            _safe_log_text(request_json_safe, 1000),
            _endpoint()[:500],
            _api_mode()[:40],
            settings.beautiful_ai_workspace_id[:160],
            organization_id,
            workspace_id,
        ),
    )


def _response_from_record(record: dict[str, Any]) -> BeautifulAiPresentationResponse:
    presentation_id = str(record.get("presentation_id") or "")
    urls = resolve_beautiful_ai_urls(
        stored_editor_url=str(record.get("editor_url") or ""),
        stored_player_url=str(record.get("player_url") or ""),
        response_text=str(record.get("response_text") or ""),
    )
    return BeautifulAiPresentationResponse(
        presentation_id=presentation_id,
        status=str(record.get("status") or "created"),
        title=str(record.get("title") or ""),
        editor_url=urls["editor_url"],
        player_url=urls["player_url"],
        created_at=str(record.get("created_at") or ""),
        provider=str(record.get("provider") or "beautiful.ai"),
        fallback_available=True,
    )


def _history_record_from_row(row: dict[str, Any]) -> BeautifulAiHistoryRecord:
    return BeautifulAiHistoryRecord(
        id=int(row.get("id") or 0),
        project_id=str(row.get("project_id") or ""),
        title=str(row.get("title") or ""),
        status=str(row.get("status") or ""),
        http_status=int(row.get("http_status") or 0),
        error_type=str(row.get("error_type") or ""),
        response_text=_safe_log_text(str(row.get("response_text") or ""), 300),
        request_json_safe=_safe_log_text(str(row.get("request_json_safe") or ""), 500),
        endpoint=str(row.get("endpoint") or ""),
        api_mode=str(row.get("api_mode") or "prompt"),
        theme_id=str(row.get("theme_id") or ""),
        workspace_config_id=str(row.get("workspace_config_id") or ""),
        created_at=str(row.get("created_at") or ""),
        updated_at=str(row.get("updated_at") or ""),
    )


def _safe_url(value: str) -> str:
    raw = (value or "").strip()[:2000]
    if not raw:
        return ""
    parsed = urlparse(raw)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        return ""
    return raw


def resolve_beautiful_ai_urls(
    source: dict[str, Any] | None = None,
    *,
    stored_editor_url: str = "",
    stored_player_url: str = "",
    response_text: str = "",
) -> dict[str, str]:
    """Resolve open URLs only from URLs returned by Beautiful.ai, never from IDs."""
    api_source = _extract_url_source(source)
    if api_source is None and response_text and response_text != "mock":
        try:
            parsed = json.loads(response_text)
        except ValueError:
            parsed = {}
        api_source = _extract_url_source(parsed) if isinstance(parsed, dict) else None

    if api_source is not None:
        editor_url = _safe_url(str(api_source.get("editor_url") or api_source.get("editorUrl") or api_source.get("editUrl") or ""))
        player_url = _safe_url(str(api_source.get("player_url") or api_source.get("playerUrl") or api_source.get("shareUrl") or api_source.get("viewUrl") or ""))
        return {
            "editor_url": editor_url,
            "player_url": player_url,
            "open_url": editor_url or player_url,
        }

    if response_text and response_text != "mock":
        return {"editor_url": "", "player_url": "", "open_url": ""}

    editor_url = _safe_url(stored_editor_url)
    player_url = _safe_url(stored_player_url)
    return {
        "editor_url": editor_url,
        "player_url": player_url,
        "open_url": editor_url or player_url,
    }


def _extract_url_source(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return None
    sources: list[dict[str, Any]] = [data]
    for key in ("data", "presentation", "result"):
        nested_value = data.get(key)
        if isinstance(nested_value, dict):
            sources.append(nested_value)
            nested_presentation = nested_value.get("presentation")
            if isinstance(nested_presentation, dict):
                sources.append(nested_presentation)
    merged: dict[str, Any] = {}
    for item in sources:
        merged.update(item)
    return merged


def _safe_log_text(value: str, limit: int = 1000) -> str:
    text = (value or "").replace("\x00", "").strip()
    return text[:limit]


def _make_mock_response(project_id: str, title: str) -> dict[str, str]:
    suffix = hashlib.sha256(f"{project_id}:{title}".encode("utf-8")).hexdigest()[:12]
    presentation_id = f"mock-{suffix}"
    return {
        "presentation_id": presentation_id,
        "editor_url": f"https://www.beautiful.ai/editor/mock-editor-{suffix}",
        "player_url": f"https://www.beautiful.ai/player/mock-player-{suffix}",
        "status": "mock",
        "title": title,
    }


def _extract_api_result(data: dict[str, Any], fallback_title: str) -> dict[str, str]:
    source = _extract_url_source(data) or {}
    presentation_id = str(source.get("presentation_id") or source.get("presentationId") or source.get("id") or "")
    urls = resolve_beautiful_ai_urls(source)
    status = str(source.get("status") or "created")
    title = str(source.get("title") or fallback_title)
    return {
        "presentation_id": presentation_id,
        "editor_url": urls["editor_url"],
        "player_url": urls["player_url"],
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


def _request_json_safe_text(payload: dict[str, Any], limit: int = 1000) -> str:
    return _safe_log_text(json.dumps(_safe_request_payload_for_log(payload), ensure_ascii=False), limit)


def _effective_theme_id(value: str = "") -> str:
    return (value or settings.beautiful_ai_default_theme_id or "minimal").strip()


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
    theme_id = _effective_theme_id(str(cleaned.get("themeId") or ""))
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


def _log_beautiful_ai_diagnostic_response(response: httpx.Response, request_payload: dict[str, Any], request_headers: dict[str, str], *, ok: bool) -> None:
    log = logger.info if ok else logger.error
    log(
        "beautiful_ai_diagnostic_response ok=%s status=%s endpoint=%s content_type=%s request_json_safe=%s request_headers_safe=%s response_headers_safe=%s response_text=%s prompt_length=%s theme_id_present=%s",
        ok,
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


def _external_service_error(
    response: httpx.Response,
    *,
    status_code: int,
    error_type: str,
    message: str,
    request_payload: dict[str, Any] | None = None,
    retry_after_seconds: int | None = None,
) -> BeautifulAiServiceError:
    return BeautifulAiServiceError(
        status_code=status_code,
        error_type=error_type,
        message=message,
        retry_after_seconds=retry_after_seconds,
        http_status=response.status_code,
        response_text=_response_text_for_log(response),
        request_json_safe=_request_json_safe_text(request_payload) if request_payload is not None else "",
    )


def _diagnostic_message_for_status(status_code: int) -> tuple[bool, str, str]:
    if status_code == 400:
        return True, "", "Beautiful.aiへの通信と認証を確認できました。診断用にpromptなしで送信したため、プレゼンは作成されていません。"
    if status_code == 401:
        return False, "beautiful_ai_invalid_api_key", "Beautiful.ai APIキーが無効、または期限切れの可能性があります。"
    if status_code == 403:
        return False, "beautiful_ai_access_not_enabled", "Beautiful.aiのWorkspaceまたはAPI利用権限にアクセスできません。"
    if status_code == 429:
        return False, "beautiful_ai_rate_limit", "Beautiful.aiのRate Limitです。時間を置いて再確認してください。"
    if 300 <= status_code < 400:
        return False, "beautiful_ai_redirect", "Beautiful.ai APIがリダイレクトを返しました。接続先URLを確認してください。"
    if status_code >= 500:
        return False, "beautiful_ai_service_error", "Beautiful.aiサーバー側でエラーが発生しています。"
    if 200 <= status_code < 300:
        return True, "", "Beautiful.ai APIから成功応答が返りました。プレゼン作成は要求していません。"
    return False, "beautiful_ai_service_error", "Beautiful.ai接続テストで予期しない応答が返りました。"


async def run_beautiful_ai_connection_test(
    db: Connection,
    *,
    user_id: int,
) -> BeautifulAiConnectionTestResponse:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    checked_at = datetime.now(timezone.utc).isoformat()

    if settings.beautiful_ai_mock:
        _insert_diagnostic_record(
            db,
            user_id=user_id,
            title="Beautiful.ai mock connection test",
            status="diagnostic_ok",
            http_status=200,
            response_text="mock",
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        create_audit_log(db, user_id, "beautiful_ai_connection_test", "beautiful_ai", "__diagnostic__", "success", "mock=true")
        return BeautifulAiConnectionTestResponse(ok=True, http_status=200, message="Beautiful.aiはモックモードで接続テスト済みです。", response_text="mock", checked_at=checked_at)

    if not settings.beautiful_ai_enabled:
        _insert_diagnostic_record(
            db,
            user_id=user_id,
            title="Beautiful.ai connection test",
            status="diagnostic_failed",
            error_type="beautiful_ai_disabled",
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        return BeautifulAiConnectionTestResponse(ok=False, error_type="beautiful_ai_disabled", message="Beautiful.ai連携が無効です。RenderのBEAUTIFUL_AI_ENABLEDを確認してください。", checked_at=checked_at)

    if not settings.beautiful_ai_api_key:
        _insert_diagnostic_record(
            db,
            user_id=user_id,
            title="Beautiful.ai connection test",
            status="diagnostic_failed",
            error_type="beautiful_ai_missing_api_key",
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        return BeautifulAiConnectionTestResponse(ok=False, error_type="beautiful_ai_missing_api_key", message="Beautiful.ai APIキーが未設定です。", checked_at=checked_at)

    headers = {
        "Authorization": f"Bearer {settings.beautiful_ai_api_key}",
        "Content-Type": "application/json",
    }
    request_payload: dict[str, Any] = {}
    try:
        async with httpx.AsyncClient(timeout=settings.beautiful_ai_timeout_seconds) as client:
            response = await client.post(_endpoint(), headers=headers, json=request_payload)
    except httpx.TimeoutException:
        _insert_diagnostic_record(
            db,
            user_id=user_id,
            title="Beautiful.ai connection test",
            status="diagnostic_failed",
            error_type="beautiful_ai_timeout",
            response_text="timeout",
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
        create_audit_log(db, user_id, "beautiful_ai_connection_test", "beautiful_ai", "__diagnostic__", "failure", "error_type=beautiful_ai_timeout")
        return BeautifulAiConnectionTestResponse(ok=False, error_type="beautiful_ai_timeout", message="Beautiful.aiへの通信がタイムアウトしました。", response_text="timeout", checked_at=checked_at)

    ok, error_type, message = _diagnostic_message_for_status(response.status_code)
    _log_beautiful_ai_diagnostic_response(response, request_payload, headers, ok=ok)
    response_text = _response_text_for_log(response)
    _insert_diagnostic_record(
        db,
        user_id=user_id,
        title="Beautiful.ai connection test",
        status="diagnostic_ok" if ok else "diagnostic_failed",
        error_type=error_type,
        http_status=response.status_code,
        response_text=response_text,
        request_json_safe=_request_json_safe_text(request_payload),
        organization_id=organization_id,
        workspace_id=workspace_id,
    )
    create_audit_log(
        db,
        user_id,
        "beautiful_ai_connection_test",
        "beautiful_ai",
        "__diagnostic__",
        "success" if ok else "failure",
        f"error_type={error_type or 'none'} http_status={response.status_code}",
    )
    return BeautifulAiConnectionTestResponse(
        ok=ok,
        http_status=response.status_code,
        error_type=error_type,
        message=message,
        response_text=_safe_log_text(response_text, 300),
        checked_at=checked_at,
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
        raise _external_service_error(
            response,
            status_code=502,
            error_type="beautiful_ai_redirect",
            request_payload=request_payload,
            message="Beautiful.ai APIがリダイレクトを返しました。BackendのBeautiful.ai接続先を確認してください。",
        )
    if response.status_code == 400:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise _external_service_error(
            response,
            status_code=400,
            error_type="beautiful_ai_bad_request",
            request_payload=request_payload,
            message="Beautiful.aiへ送信した内容が受け付けられませんでした。管理者はBeautiful.ai診断情報でResponse Textを確認してください。",
        )
    if response.status_code == 401:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise _external_service_error(response, status_code=401, error_type="beautiful_ai_invalid_api_key", message="Beautiful.ai APIキーが無効、または期限切れの可能性があります。管理者に確認してください。")
    if response.status_code == 403:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise _external_service_error(response, status_code=403, error_type="beautiful_ai_access_not_enabled", message="Beautiful.aiのWorkspaceまたはAPI利用権限にアクセスできません。管理者に確認してください。")
    if response.status_code == 404:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise _external_service_error(
            response,
            status_code=502,
            error_type="beautiful_ai_endpoint_not_found",
            request_payload=request_payload,
            message="Beautiful.ai外部APIのエンドポイントが見つかりません。BackendのBeautiful.ai接続先を確認してください。",
        )
    if response.status_code == 429:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        retry_after = response.headers.get("Retry-After")
        raise _external_service_error(
            response,
            status_code=429,
            error_type="beautiful_ai_rate_limit",
            request_payload=request_payload,
            message="Beautiful.aiの利用上限に達しました。時間を置くか既存PPTXをご利用ください",
            retry_after_seconds=int(retry_after) if retry_after and retry_after.isdigit() else None,
        )
    if response.status_code >= 500:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise _external_service_error(response, status_code=502, error_type="beautiful_ai_service_error", message="Beautiful.aiサーバー側でエラーが発生しました。時間を置くか既存PPTXをご利用ください。")
    if response.status_code >= 400:
        _log_beautiful_ai_error_response(response, request_payload, headers)
        raise _external_service_error(response, status_code=502, error_type="beautiful_ai_service_error", message="Beautiful.ai連携で通信エラーが発生しました。既存PPTXをご利用ください。")
    try:
        parsed = response.json()
    except ValueError as exc:
        raise BeautifulAiServiceError(status_code=502, error_type="beautiful_ai_service_error", message="Beautiful.ai APIの応答を解析できませんでした。") from exc
    if not isinstance(parsed, dict):
        return {"__http_status": response.status_code, "__response_text": _response_text_for_log(response), "__request_json_safe": _request_json_safe_text(request_payload)}
    parsed.setdefault("__http_status", response.status_code)
    parsed.setdefault("__response_text", _response_text_for_log(response))
    parsed.setdefault("__request_json_safe", _request_json_safe_text(request_payload))
    return parsed


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
    api_http_status = 200 if settings.beautiful_ai_mock else 0
    api_response_text = "mock" if settings.beautiful_ai_mock else ""
    api_request_json_safe = _request_json_safe_text(_api_request_payload(payload))

    create_audit_log(db, user_id, "beautiful_ai_generation_started", "beautiful_ai", request.project_id, "success", "fallback_available=true")
    try:
        if settings.beautiful_ai_mock:
            api_result = _make_mock_response(request.project_id, title)
        else:
            api_data = await _post_payload(payload)
            api_http_status = int(api_data.get("__http_status") or 0)
            api_response_text = str(api_data.get("__response_text") or "")
            api_request_json_safe = str(api_data.get("__request_json_safe") or api_request_json_safe)
            api_result = _extract_api_result(api_data, title)
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
            http_status=0,
            response_text="timeout",
            request_json_safe=api_request_json_safe,
            endpoint=_endpoint(),
            api_mode=_api_mode(),
            workspace_config_id=payload_model.workspaceId,
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
            http_status=exc.http_status,
            response_text=exc.response_text,
            request_json_safe=exc.request_json_safe or api_request_json_safe,
            endpoint=_endpoint(),
            api_mode=_api_mode(),
            workspace_config_id=payload_model.workspaceId,
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
        http_status=api_http_status,
        response_text=api_response_text,
        request_json_safe=api_request_json_safe,
        endpoint=_endpoint(),
        api_mode=_api_mode(),
        workspace_config_id=payload_model.workspaceId,
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
