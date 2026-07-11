from __future__ import annotations

import json
import re
from sqlite3 import Connection
from typing import Any

from app.repositories import create_audit_log, get_or_create_customer, get_or_create_project, row_to_dict
from app.workspace.repositories import save_workspace_bundle


INTEGRATION_PROVIDERS = [
    ("gmail", "Gmail"),
    ("outlook", "Outlook"),
    ("google_calendar", "Google Calendar"),
    ("google_drive", "Google Drive"),
    ("slack", "Slack"),
    ("teams", "Teams"),
    ("notion", "Notion"),
    ("kintone", "kintone"),
    ("hubspot", "HubSpot"),
    ("salesforce", "Salesforce"),
]

INTEGRATION_STATUSES = {"未接続", "接続準備中", "接続済み", "エラー"}
INTAKE_STATUSES = {"received", "pending_review", "approved", "rejected", "converted", "archived"}
SOURCE_TYPES = {"email", "calendar", "chat", "document"}
SAFE_METADATA_KEYS = {
    "company_name",
    "industry",
    "source_url",
    "sender_domain",
    "channel",
    "workspace",
    "calendar_name",
    "document_type",
    "provider_item_id",
    "owner_hint",
}
BLOCKED_METADATA_HINTS = {
    "token",
    "refresh",
    "api_key",
    "apikey",
    "secret",
    "password",
    "credential",
    "body",
    "content",
    "attachment",
    "file",
    "raw",
}
SECURITY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email_address", re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")),
    ("phone_number", re.compile(r"\b(?:\+?\d[\d\s().-]{8,}\d)\b")),
    ("api_key_like", re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret)\s*[:=]\s*[A-Za-z0-9_\-./+=]{8,}")),
    ("password_like", re.compile(r"(?i)(password|pass|pwd)\s*[:=]\s*[^\s,;]{4,}")),
    ("url", re.compile(r"https?://[^\s)]+")),
    ("personal_name_like", re.compile(r"(担当者|氏名|お名前|name|contact_person)\s*[:：]\s*[^\s,;]{2,40}", re.IGNORECASE)),
)
ATTACHMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".zip", ".eml")
DRY_RUN_PROVIDERS = {"gmail", "outlook", "slack", "teams", "google_calendar", "google_drive"}
DRY_RUN_TEMPLATE_LABELS = {
    "case_email": "案件相談メール",
    "meeting_schedule": "商談予定",
    "slack_consultation": "Slack相談",
    "teams_request": "Teams依頼",
    "proposal_request_memo": "提案依頼書メモ",
    "document_share_memo": "資料共有メモ",
}


def _dry_run_template_payload(provider: str, template_type: str) -> dict[str, Any]:
    label = DRY_RUN_TEMPLATE_LABELS.get(template_type, "案件相談メール")
    source_type = {
        "case_email": "email",
        "meeting_schedule": "calendar",
        "slack_consultation": "chat",
        "teams_request": "chat",
        "proposal_request_memo": "document",
        "document_share_memo": "document",
    }.get(template_type, "email")
    return {
        "source_provider": provider,
        "source_type": source_type,
        "title": f"Dry Run: {label}",
        "summary": (
            "Webサイトリニューアルの相談。問い合わせ導線、CMS運用、SEO改善が主な論点。"
            "連絡先 sample@example.com と参考URL https://example.com はセキュリティスキャン確認用。"
        ),
        "received_at": "",
        "metadata": {
            "company_name": "Dry Run サンプル株式会社",
            "industry": "Web制作テスト",
            "source_url": "https://example.com/dry-run",
            "provider_item_id": f"dry-run-{provider}-{template_type}",
            "channel": "dry-run",
            "api_key": "dry-run-api-key-should-not-save",
            "attachment": "request-summary.pdf",
        },
    }


def _row(row: Any) -> dict[str, Any]:
    return row_to_dict(row) or {}


def _normalise_provider(provider: str) -> str:
    value = provider.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "googlecalendar": "google_calendar",
        "google_calendar": "google_calendar",
        "googledrive": "google_drive",
        "google_drive": "google_drive",
        "ms_teams": "teams",
        "microsoft_teams": "teams",
    }
    return aliases.get(value, value)


def _display_name(provider: str) -> str:
    normalized = _normalise_provider(provider)
    return dict(INTEGRATION_PROVIDERS).get(normalized, provider.strip()[:40] or "External")


def _redact_sensitive_text(value: str, limit: int) -> str:
    text = (value or "").strip()
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[メールアドレス省略]", text)
    text = re.sub(r"\b(?:\+?\d[\d\s().-]{8,}\d)\b", "[電話番号省略]", text)
    text = re.sub(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[A-Za-z0-9_\-./+=]{8,}", r"\1=[省略]", text)
    return text[:limit]


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, str | int | float | bool | None]:
    safe: dict[str, str | int | float | bool | None] = {}
    if not metadata:
        return safe
    for key, value in metadata.items():
        normalized_key = str(key).strip().lower()
        if normalized_key not in SAFE_METADATA_KEYS:
            continue
        if any(hint in normalized_key for hint in BLOCKED_METADATA_HINTS):
            continue
        if not isinstance(value, (str, int, float, bool, type(None))):
            continue
        if isinstance(value, str):
            if any(hint in value.lower() for hint in ("api_key", "refresh_token", "access_token", "password=", "secret=")):
                continue
            safe[normalized_key] = _redact_sensitive_text(value, 200)
        else:
            safe[normalized_key] = value
    return safe


def scan_external_intake_security(payload: dict[str, Any]) -> list[dict[str, str]]:
    flags: list[dict[str, str]] = []
    text_targets = [
        ("title", str(payload.get("title") or "")),
        ("summary", str(payload.get("summary") or "")),
        ("received_at", str(payload.get("received_at") or "")),
    ]
    metadata = payload.get("metadata") or {}
    if isinstance(metadata, dict):
        for key, value in metadata.items():
            key_text = str(key)
            value_text = str(value) if isinstance(value, (str, int, float, bool)) else ""
            text_targets.append((f"metadata.{key_text}", value_text))
            key_lower = key_text.lower()
            if any(hint in key_lower for hint in ("token", "api_key", "apikey", "password", "secret", "refresh")):
                flags.append({"type": "credential_key", "field": f"metadata.{key_text}", "severity": "high"})
            if any(hint in key_lower for hint in ("attachment", "file", "filename")):
                flags.append({"type": "attachment_filename", "field": f"metadata.{key_text}", "severity": "medium"})
    for field, text in text_targets:
        for flag_type, pattern in SECURITY_PATTERNS:
            if pattern.search(text):
                severity = "high" if flag_type in {"api_key_like", "password_like"} else "medium"
                flags.append({"type": flag_type, "field": field, "severity": severity})
        lower_text = text.lower()
        if any(lower_text.endswith(extension) or extension in lower_text for extension in ATTACHMENT_EXTENSIONS):
            flags.append({"type": "attachment_filename", "field": field, "severity": "medium"})
    unique: dict[tuple[str, str], dict[str, str]] = {}
    for flag in flags:
        unique[(flag["type"], flag["field"])] = flag
    return list(unique.values())[:20]


def _security_flags_json(payload: dict[str, Any]) -> str:
    return json.dumps(scan_external_intake_security(payload), ensure_ascii=False)[:1200]


def _safe_metadata_json(metadata: dict[str, Any] | None) -> str:
    return json.dumps(sanitize_metadata(metadata), ensure_ascii=False)[:1200]


def _parse_metadata(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _parse_security_flags(value: str) -> list[dict[str, str]]:
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _provider_allowed_roles(db: Connection, provider: str) -> list[str]:
    seed_integration_settings(db)
    row = db.execute("SELECT allowed_roles FROM integration_settings WHERE provider = ?", (provider,)).fetchone()
    if not row:
        return ["admin", "manager", "member"]
    roles = [role for role in str(row["allowed_roles"] or "").split(",") if role]
    return roles or ["admin", "manager", "member"]


def seed_integration_settings(db: Connection) -> None:
    for provider, display_name in INTEGRATION_PROVIDERS:
        db.execute(
            """
            INSERT INTO integration_settings (provider, display_name)
            VALUES (?, ?)
            ON CONFLICT(provider) DO NOTHING
            """,
            (provider, display_name),
        )


def list_integration_settings(db: Connection) -> list[dict[str, Any]]:
    seed_integration_settings(db)
    rows = db.execute(
        """
        SELECT
            id, provider, status, display_name, enabled, allowed_roles, requires_admin_approval,
            data_retention_days, last_checked_at, last_security_review_at, error_message,
            security_note, created_at, updated_at
        FROM integration_settings
        ORDER BY id ASC
        """
    ).fetchall()
    result = [_row(row) for row in rows]
    for item in result:
        item["enabled"] = bool(item.get("enabled"))
        item["requires_admin_approval"] = bool(item.get("requires_admin_approval"))
        item["allowed_roles"] = [role for role in str(item.get("allowed_roles") or "").split(",") if role]
    return result


def update_integration_setting(
    db: Connection,
    *,
    provider: str,
    status: str,
    display_name: str,
    enabled: bool,
    error_message: str,
    allowed_roles: list[str],
    requires_admin_approval: bool,
    data_retention_days: int,
    security_note: str,
    user_id: int,
) -> dict[str, Any] | None:
    normalized = _normalise_provider(provider)
    if status not in INTEGRATION_STATUSES:
        raise ValueError("Invalid integration status.")
    normalized_roles = [role for role in allowed_roles if role in {"admin", "manager", "member", "viewer"}] or ["admin", "manager", "member"]
    seed_integration_settings(db)
    db.execute(
        """
        UPDATE integration_settings
        SET status = ?, display_name = COALESCE(NULLIF(?, ''), display_name), enabled = ?,
            error_message = ?, allowed_roles = ?, requires_admin_approval = ?,
            data_retention_days = ?, security_note = ?, last_checked_at = CURRENT_TIMESTAMP,
            last_security_review_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE provider = ?
        """,
        (
            status,
            _redact_sensitive_text(display_name, 80),
            1 if enabled else 0,
            _redact_sensitive_text(error_message, 300),
            ",".join(normalized_roles),
            1 if requires_admin_approval else 0,
            max(1, min(int(data_retention_days or 90), 3650)),
            _redact_sensitive_text(security_note, 1000),
            normalized,
        ),
    )
    setting = _row(
        db.execute(
            """
            SELECT
                id, provider, status, display_name, enabled, allowed_roles, requires_admin_approval,
                data_retention_days, last_checked_at, last_security_review_at, error_message,
                security_note, created_at, updated_at
            FROM integration_settings
            WHERE provider = ?
            """,
            (normalized,),
        ).fetchone()
    )
    if setting:
        setting["enabled"] = bool(setting.get("enabled"))
        setting["requires_admin_approval"] = bool(setting.get("requires_admin_approval"))
        setting["allowed_roles"] = [role for role in str(setting.get("allowed_roles") or "").split(",") if role]
        create_audit_log(
            db,
            user_id,
            "integration_setting_change",
            "integration_setting",
            normalized,
            "success",
            f"status={status};enabled={enabled};roles={','.join(setting['allowed_roles'])}",
        )
        if not enabled:
            create_audit_log(db, user_id, "integration_disabled", "integration_setting", normalized, "success", "enabled=false")
    return setting or None


def create_external_intake(db: Connection, *, user: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    provider = _normalise_provider(str(payload.get("source_provider") or ""))
    source_type = str(payload.get("source_type") or "").strip().lower()
    if source_type not in SOURCE_TYPES:
        raise ValueError("Invalid external source type.")
    if str(user.get("role") or "") not in _provider_allowed_roles(db, provider):
        raise PermissionError("This role is not allowed to use the integration provider.")
    metadata = sanitize_metadata(payload.get("metadata") or {})
    security_flags = _security_flags_json(payload)
    title = _redact_sensitive_text(str(payload.get("title") or ""), 160) or f"{_display_name(provider)}からの案件候補"
    summary = _redact_sensitive_text(str(payload.get("summary") or ""), 800)
    received_at = _redact_sensitive_text(str(payload.get("received_at") or ""), 80)
    cursor = db.execute(
        """
        INSERT INTO external_intake_items
        (source_provider, source_type, title, summary, received_at, metadata, candidate_status, security_flags, created_by)
        VALUES (?, ?, ?, ?, ?, ?, 'pending_review', ?, ?)
        """,
        (provider, source_type, title, summary, received_at, json.dumps(metadata, ensure_ascii=False)[:1200], security_flags, int(user["id"])),
    )
    candidate = get_external_candidate(db, int(cursor.lastrowid))
    create_audit_log(
        db,
        int(user["id"]),
        "external_intake_received",
        "external_intake",
        str(candidate["id"]),
        "success",
        f"provider={provider};source_type={source_type};flags={len(candidate.get('security_flags') or [])}",
    )
    return candidate


def get_external_candidate(db: Connection, item_id: int) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT i.*, u.email AS created_by_email
        FROM external_intake_items i
        LEFT JOIN users u ON u.id = i.created_by
        WHERE i.id = ?
        """,
        (item_id,),
    ).fetchone()
    candidate = _row(row)
    if candidate:
        candidate["metadata"] = _parse_metadata(str(candidate.get("metadata") or ""))
        candidate["security_flags"] = _parse_security_flags(str(candidate.get("security_flags") or ""))
    return candidate


def list_external_candidates(db: Connection, user: dict[str, Any]) -> list[dict[str, Any]]:
    role = str(user.get("role") or "")
    params: tuple[Any, ...] = ()
    where = ""
    if role not in {"admin", "manager"}:
        where = "WHERE i.created_by = ?"
        params = (int(user["id"]),)
    rows = db.execute(
        f"""
        SELECT i.*, u.email AS created_by_email, p.name AS project_name
        FROM external_intake_items i
        LEFT JOIN users u ON u.id = i.created_by
        LEFT JOIN projects p ON p.id = i.project_id
        {where}
        ORDER BY i.created_at DESC, i.id DESC
        LIMIT 100
        """,
        params,
    ).fetchall()
    candidates = [_row(row) for row in rows]
    for candidate in candidates:
        candidate["metadata"] = _parse_metadata(str(candidate.get("metadata") or ""))
        candidate["security_flags"] = _parse_security_flags(str(candidate.get("security_flags") or ""))
    return candidates


def review_external_candidate(
    db: Connection,
    *,
    item_id: int,
    status: str,
    review_comment: str,
    user: dict[str, Any],
) -> dict[str, Any]:
    if status not in {"approved", "rejected", "archived"}:
        raise ValueError("Invalid external intake review status.")
    candidate = get_external_candidate(db, item_id)
    if not candidate:
        raise LookupError("External intake candidate was not found.")
    if candidate.get("candidate_status") == "converted":
        raise ValueError("Converted external intake cannot be reviewed again.")
    db.execute(
        """
        UPDATE external_intake_items
        SET candidate_status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
            review_comment = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, int(user["id"]), _redact_sensitive_text(review_comment, 800), item_id),
    )
    event_type = {
        "approved": "external_intake_approved",
        "rejected": "external_intake_rejected",
        "archived": "external_intake_archived",
    }[status]
    create_audit_log(db, int(user["id"]), event_type, "external_intake", str(item_id), "success", f"status={status}")
    return get_external_candidate(db, item_id)


def convert_external_candidate_to_project(db: Connection, *, item_id: int, user: dict[str, Any]) -> dict[str, Any]:
    candidate = get_external_candidate(db, item_id)
    if not candidate:
        raise LookupError("External intake candidate was not found.")
    role = str(user.get("role") or "")
    if role not in {"admin", "manager"} and int(candidate.get("created_by") or 0) != int(user["id"]):
        raise PermissionError("This candidate is not assigned to the current user.")
    if candidate.get("candidate_status") == "converted" and candidate.get("project_id"):
        return candidate
    if candidate.get("candidate_status") != "approved":
        raise ValueError("External intake must be approved before conversion.")

    metadata = candidate.get("metadata") if isinstance(candidate.get("metadata"), dict) else {}
    company_name = str(metadata.get("company_name") or "").strip() or str(candidate.get("title") or "外部連携案件候補")[:80]
    industry = str(metadata.get("industry") or "").strip()
    customer_id = get_or_create_customer(db, company_name, industry=industry)
    project_id = get_or_create_project(
        db,
        customer_id,
        str(candidate.get("title") or "外部連携案件候補"),
        summary=str(candidate.get("summary") or ""),
        win_probability=40,
        next_action="外部連携から案件化しました。営業担当が内容を確認してください。",
    )
    db.execute(
        """
        UPDATE external_intake_items
        SET candidate_status = 'converted', project_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (project_id, item_id),
    )
    save_workspace_bundle(
        db,
        int(user["id"]),
        str(project_id),
        [
            {
                "client_message_id": f"external-intake-{item_id}",
                "agent_name": "AI秘書",
                "message_type": "system",
                "message_body": "外部連携から案件候補を受け取りました。",
                "status": "done",
            }
        ],
        [
            {
                "client_log_id": f"external-intake-log-{item_id}",
                "agent_name": "AI秘書",
                "action_summary": "外部入力を案件化し、AI Workspaceへ引き継ぎました。",
                "status": "done",
            }
        ],
    )
    create_audit_log(db, int(user["id"]), "external_intake_converted", "external_intake", str(item_id), "success", f"project_id={project_id}")
    return get_external_candidate(db, item_id)


def execute_integration_dry_run(db: Connection, *, user: dict[str, Any], provider: str, template_type: str) -> dict[str, Any]:
    normalized_provider = _normalise_provider(provider)
    if normalized_provider not in DRY_RUN_PROVIDERS:
        raise ValueError("Unsupported dry run provider.")
    if template_type not in DRY_RUN_TEMPLATE_LABELS:
        raise ValueError("Unsupported dry run template.")

    payload = _dry_run_template_payload(normalized_provider, template_type)
    try:
        candidate = create_external_intake(db, user=user, payload=payload)
        flags_count = len(candidate.get("security_flags") or [])
        result_summary = (
            f"外部入力ID {candidate['id']} を pending_review として登録。"
            f"セキュリティフラグ {flags_count} 件。承認後に案件化できます。"
        )
        db.execute(
            """
            INSERT INTO dry_run_logs
            (provider, template_type, status, created_item_id, result_summary, security_flags_count, created_by)
            VALUES (?, ?, 'success', ?, ?, ?, ?)
            """,
            (normalized_provider, template_type, candidate["id"], result_summary[:500], flags_count, int(user["id"])),
        )
        create_audit_log(
            db,
            int(user["id"]),
            "integration_dry_run_executed",
            "integration_dry_run",
            normalized_provider,
            "success",
            f"template={template_type};item_id={candidate['id']};flags={flags_count}",
        )
        return {
            "candidate": candidate,
            "dry_run": {
                "provider": normalized_provider,
                "template_type": template_type,
                "status": "success",
                "created_item_id": candidate["id"],
                "result_summary": result_summary,
                "security_flags_count": flags_count,
                "checks": {
                    "registered": True,
                    "security_scanned": True,
                    "pending_review": candidate.get("candidate_status") == "pending_review",
                    "can_convert_after_approval": True,
                    "workspace_handoff_after_conversion": True,
                },
            },
        }
    except Exception as exc:
        result_summary = f"Dry Run failed: {type(exc).__name__}"
        db.execute(
            """
            INSERT INTO dry_run_logs
            (provider, template_type, status, created_item_id, result_summary, security_flags_count, created_by)
            VALUES (?, ?, 'failure', NULL, ?, 0, ?)
            """,
            (normalized_provider, template_type, result_summary[:500], int(user["id"])),
        )
        create_audit_log(
            db,
            int(user["id"]),
            "integration_dry_run_failed",
            "integration_dry_run",
            normalized_provider,
            "failure",
            f"template={template_type};error={type(exc).__name__}",
        )
        raise


def list_dry_run_logs(db: Connection, limit: int = 20) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT l.*, u.email AS created_by_email
        FROM dry_run_logs l
        LEFT JOIN users u ON u.id = l.created_by
        ORDER BY l.created_at DESC, l.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_row(row) for row in rows]


def build_connector_readiness(db: Connection, *, user_id: int | None = None) -> list[dict[str, Any]]:
    settings = {item["provider"]: item for item in list_integration_settings(db)}
    output: list[dict[str, Any]] = []
    for provider, display_name in INTEGRATION_PROVIDERS:
        setting = settings.get(provider)
        dry_run_success = db.execute(
            "SELECT id, created_at FROM dry_run_logs WHERE provider = ? AND status = 'success' ORDER BY created_at DESC, id DESC LIMIT 1",
            (provider,),
        ).fetchone()
        audit = db.execute(
            """
            SELECT id FROM audit_logs
            WHERE event_type = 'integration_dry_run_executed' AND target_id = ?
            ORDER BY created_at DESC, id DESC LIMIT 1
            """,
            (provider,),
        ).fetchone()
        checks = {
            "setting_exists": bool(setting),
            "allowed_roles_configured": bool(setting and setting.get("allowed_roles")),
            "retention_configured": bool(setting and int(setting.get("data_retention_days") or 0) > 0),
            "security_reviewed": bool(setting and setting.get("last_security_review_at")),
            "dry_run_success": bool(dry_run_success),
            "audit_log_confirmed": bool(audit),
        }
        score = round((sum(1 for passed in checks.values() if passed) / len(checks)) * 100)
        output.append(
            {
                "provider": provider,
                "display_name": display_name,
                "score": score,
                "status": "ready" if score >= 80 else "needs_review",
                "checks": checks,
                "last_dry_run_at": dry_run_success["created_at"] if dry_run_success else "",
            }
        )
    if user_id is not None:
        create_audit_log(db, user_id, "connector_readiness_checked", "integration_readiness", "", "success", "providers=10")
    return output


def build_integration_analytics(db: Connection) -> dict[str, Any]:
    total_inputs = int(db.execute("SELECT COUNT(*) AS count FROM external_intake_items").fetchone()["count"])
    candidate_count = int(
        db.execute(
            """
            SELECT COUNT(*) AS count
            FROM external_intake_items
            WHERE candidate_status IN ('received', 'pending_review', 'approved')
            """
        ).fetchone()["count"]
    )
    converted_count = int(
        db.execute("SELECT COUNT(*) AS count FROM external_intake_items WHERE candidate_status = 'converted'").fetchone()["count"]
    )
    rows = db.execute(
        """
        SELECT source_provider AS provider, COUNT(*) AS count
        FROM external_intake_items
        GROUP BY source_provider
        ORDER BY count DESC, source_provider ASC
        """
    ).fetchall()
    dry_run_total = int(db.execute("SELECT COUNT(*) AS count FROM dry_run_logs").fetchone()["count"])
    dry_run_rows = db.execute(
        """
        SELECT provider, COUNT(*) AS total, SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count
        FROM dry_run_logs
        GROUP BY provider
        ORDER BY total DESC, provider ASC
        """
    ).fetchall()
    provider_dry_run_success_rates = []
    for row in dry_run_rows:
        total = int(row["total"] or 0)
        success_count = int(row["success_count"] or 0)
        provider_dry_run_success_rates.append(
            {
                "provider": row["provider"],
                "total": total,
                "success_count": success_count,
                "success_rate": round((success_count / total) * 100, 1) if total else 0,
            }
        )
    readiness = build_connector_readiness(db)
    average_readiness_score = round(sum(item["score"] for item in readiness) / len(readiness), 1) if readiness else 0
    return {
        "external_input_count": total_inputs,
        "candidate_count": candidate_count,
        "converted_count": converted_count,
        "conversion_rate": round((converted_count / total_inputs) * 100, 1) if total_inputs else 0,
        "provider_counts": [_row(row) for row in rows],
        "dry_run_count": dry_run_total,
        "provider_dry_run_success_rates": provider_dry_run_success_rates,
        "average_readiness_score": average_readiness_score,
    }
