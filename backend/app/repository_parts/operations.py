import importlib.util
import os
import re
import uuid
from sqlite3 import Connection, Row
from datetime import date
from typing import Any

from app.config import settings
from app.role_permissions import add_role_display_fields, normalize_role_for_storage
from app.security import hash_password, verify_password

from app.repository_parts.users import row_to_dict, get_user_context_ids, get_pilot_status
from app.repository_parts.shared import _count_rows, _feedback_score_metrics, _scope_filter, _scope_label

def list_usage_logs(db: Connection, limit: int = 50) -> list[dict[str, Any]]:
    return list_usage_logs_scoped(db, limit=limit)


def list_usage_logs_scoped(db: Connection, limit: int = 50, scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    where, params = _scope_filter(scope, "l")
    where_sql = f"WHERE {where}" if where else ""
    return [
        dict(row)
        for row in db.execute(
            f"""
            SELECT l.*, u.email AS user_email
            FROM usage_logs l
            LEFT JOIN users u ON u.id = l.user_id
            {where_sql}
            ORDER BY l.created_at DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    ]


def create_audit_log(
    db: Connection,
    user_id: int | None,
    event_type: str,
    target_type: str = "",
    target_id: str = "",
    status: str = "success",
    metadata: str = "",
) -> None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    actor_role = ""
    if user_id:
        row = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        actor_role = str(row["role"] if row else "")
    request_id = ""
    match = re.search(r"request_id=([^;]+)", metadata or "")
    if match:
        request_id = match.group(1)[:80]
    try:
        db.execute(
            """
            INSERT INTO audit_logs (user_id, actor_role, event_type, target_type, target_id, status, metadata, organization_id, workspace_id, request_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, actor_role, event_type, target_type, target_id, status, metadata[:300], organization_id, workspace_id, request_id),
        )
    except Exception:
        db.execute(
            """
            INSERT INTO audit_logs (user_id, event_type, target_type, target_id, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, event_type, target_type, target_id, status, metadata[:300]),
        )


def list_audit_logs(db: Connection, limit: int = 100, scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    where, params = _scope_filter(scope, "a")
    where_sql = f"WHERE {where}" if where else ""
    return [
        dict(row)
        for row in db.execute(
            f"""
            SELECT a.*, u.email AS user_email
            FROM audit_logs a
            LEFT JOIN users u ON u.id = a.user_id
            {where_sql}
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    ]


def create_feedback_entry(db: Connection, user_id: int | None, user_role: str, rating: str, comment: str, feature_name: str) -> dict[str, Any]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    cursor = db.execute(
        """
        INSERT INTO feedback_entries (user_id, user_role, rating, comment, feature_name, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, user_role[:30], rating, comment.strip()[:1000], feature_name.strip()[:100], organization_id, workspace_id),
    )
    feedback = dict(db.execute("SELECT * FROM feedback_entries WHERE id = ?", (cursor.lastrowid,)).fetchone())
    create_audit_log(db, user_id, "save", "feedback", str(cursor.lastrowid), "success", f"rating={rating};feature={feature_name[:80]}")
    return feedback


def list_feedback_entries(db: Connection, limit: int = 200, scope: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    where, params = _scope_filter(scope, "f")
    where_sql = f"WHERE {where}" if where else ""
    return [
        dict(row)
        for row in db.execute(
            f"""
            SELECT f.*, u.email AS user_email
            FROM feedback_entries f
            LEFT JOIN users u ON u.id = f.user_id
            {where_sql}
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
    ]


def summarize_feedback_entries(db: Connection, scope: dict[str, Any] | None = None) -> dict[str, int]:
    where, params = _scope_filter(scope)
    where_sql = f"WHERE {where}" if where else ""
    rows = db.execute(
        f"""
        SELECT rating, COUNT(*) AS count
        FROM feedback_entries
        {where_sql}
        GROUP BY rating
        """,
        params,
    ).fetchall()
    summary = {"usable": 0, "needs_revision": 0, "hard_to_use": 0, "comments": 0}
    for row in rows:
        summary[str(row["rating"])] = int(row["count"])
    comment_where = "TRIM(comment) != ''"
    if where:
        comment_where = f"{where} AND {comment_where}"
    comment_row = db.execute(f"SELECT COUNT(*) AS count FROM feedback_entries WHERE {comment_where}", params).fetchone()
    summary["comments"] = int(comment_row["count"]) if comment_row else 0
    return summary


PILOT_ISSUE_CATEGORIES = {"操作方法", "UI表示", "AI出力", "PPT/PDF", "認証", "権限", "Backend", "DB", "その他"}
PILOT_ISSUE_SEVERITIES = {"critical", "high", "medium", "low"}
PILOT_ISSUE_STATUSES = {"reported", "investigating", "fixing", "resolved", "deferred"}


def _safe_pilot_text(value: str, limit: int = 800) -> str:
    text = (value or "").strip()
    replacements = [
        (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]"),
        (r"https?://[^\s]+", "[url]"),
        (r"(?:\+?\d[\d\s\-()]{8,}\d)", "[phone]"),
        (r"sk-[A-Za-z0-9_\-]{12,}", "[api_key]"),
        (r"(?i)(password|passwd|api[_-]?key|token|secret)\s*[:=]\s*\S+", "[secret]"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    return text[:limit]


def _normalise_issue_category(category: str) -> str:
    value = (category or "その他").strip()
    return value if value in PILOT_ISSUE_CATEGORIES else "その他"


def _normalise_issue_severity(severity: str) -> str:
    value = (severity or "medium").strip()
    return value if value in PILOT_ISSUE_SEVERITIES else "medium"


def _normalise_issue_status(status: str) -> str:
    value = (status or "reported").strip()
    return value if value in PILOT_ISSUE_STATUSES else "reported"


def list_pilot_issues(db: Connection, limit: int = 200, user_id: int | None = None) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    rows = db.execute(
        """
        SELECT i.*, u.email AS reported_by_email
        FROM pilot_issues i
        LEFT JOIN users u ON u.id = i.reported_by
        WHERE i.organization_id = ? AND i.workspace_id = ?
        ORDER BY
            CASE i.severity
                WHEN 'critical' THEN 0
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            CASE i.status
                WHEN 'reported' THEN 0
                WHEN 'investigating' THEN 1
                WHEN 'fixing' THEN 2
                WHEN 'resolved' THEN 3
                ELSE 4
            END,
            i.updated_at DESC
        LIMIT ?
        """,
        (organization_id, workspace_id, limit),
    ).fetchall()
    return [add_role_display_fields(dict(row)) for row in rows]


def _pilot_issue_duplicate_candidates(db: Connection, title: str, summary: str, limit: int = 5, user_id: int | None = None) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    title_key = _safe_pilot_text(title, 80)
    summary_key = _safe_pilot_text(summary, 80)
    rows = db.execute(
        """
        SELECT issue_id, category, severity, title, summary, status, updated_at
        FROM pilot_issues
        WHERE status != 'resolved'
          AND organization_id = ? AND workspace_id = ?
          AND (
            title LIKE ?
            OR summary LIKE ?
            OR ? LIKE '%' || title || '%'
          )
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (organization_id, workspace_id, f"%{title_key[:40]}%", f"%{summary_key[:40]}%", title_key, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def create_pilot_issue(
    db: Connection,
    payload: Any,
    user_id: int | None,
    source_feedback_id: int | None = None,
) -> dict[str, Any]:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    issue_uuid = f"PILOT-{uuid.uuid4().hex[:10].upper()}"
    category = _normalise_issue_category(str(getattr(payload, "category", "その他")))
    severity = _normalise_issue_severity(str(getattr(payload, "severity", "medium")))
    title = _safe_pilot_text(str(getattr(payload, "title", "")), 160) or "Pilot課題"
    summary = _safe_pilot_text(str(getattr(payload, "summary", "")), 800)
    reproduction_steps = _safe_pilot_text(str(getattr(payload, "reproduction_steps", "")), 1000)
    assigned_to = _safe_pilot_text(str(getattr(payload, "assigned_to", "")), 120)
    db.execute(
        """
        INSERT INTO pilot_issues
        (issue_id, category, severity, title, summary, reproduction_steps, status, reported_by, assigned_to, source_feedback_id, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, 'reported', ?, ?, ?, ?, ?)
        """,
        (issue_uuid, category, severity, title, summary, reproduction_steps, user_id, assigned_to, source_feedback_id, organization_id, workspace_id),
    )
    row = db.execute(
        "SELECT * FROM pilot_issues WHERE issue_id = ? AND organization_id = ? AND workspace_id = ?",
        (issue_uuid, organization_id, workspace_id),
    ).fetchone()
    return dict(row)


def update_pilot_issue(db: Connection, issue_id: str, payload: Any, user_id: int | None) -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    existing = db.execute(
        "SELECT * FROM pilot_issues WHERE issue_id = ? AND organization_id = ? AND workspace_id = ?",
        (issue_id, organization_id, workspace_id),
    ).fetchone()
    if not existing:
        return None
    values = dict(existing)
    if getattr(payload, "category", None) is not None:
        values["category"] = _normalise_issue_category(str(payload.category))
    if getattr(payload, "severity", None) is not None:
        values["severity"] = _normalise_issue_severity(str(payload.severity))
    if getattr(payload, "title", None) is not None:
        values["title"] = _safe_pilot_text(str(payload.title), 160) or values["title"]
    if getattr(payload, "summary", None) is not None:
        values["summary"] = _safe_pilot_text(str(payload.summary), 800)
    if getattr(payload, "reproduction_steps", None) is not None:
        values["reproduction_steps"] = _safe_pilot_text(str(payload.reproduction_steps), 1000)
    if getattr(payload, "status", None) is not None:
        values["status"] = _normalise_issue_status(str(payload.status))
    if getattr(payload, "assigned_to", None) is not None:
        values["assigned_to"] = _safe_pilot_text(str(payload.assigned_to), 120)
    if getattr(payload, "resolution_note", None) is not None:
        values["resolution_note"] = _safe_pilot_text(str(payload.resolution_note), 1000)
    resolved_at_sql = "CURRENT_TIMESTAMP" if values["status"] == "resolved" and not values.get("resolved_at") else "resolved_at"
    db.execute(
        f"""
        UPDATE pilot_issues
        SET category = ?,
            severity = ?,
            title = ?,
            summary = ?,
            reproduction_steps = ?,
            status = ?,
            assigned_to = ?,
            resolution_note = ?,
            resolved_at = {resolved_at_sql},
            updated_at = CURRENT_TIMESTAMP
        WHERE issue_id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (
            values["category"],
            values["severity"],
            values["title"],
            values["summary"],
            values["reproduction_steps"],
            values["status"],
            values["assigned_to"],
            values["resolution_note"],
            issue_id,
            organization_id,
            workspace_id,
        ),
    )
    row = db.execute(
        "SELECT * FROM pilot_issues WHERE issue_id = ? AND organization_id = ? AND workspace_id = ?",
        (issue_id, organization_id, workspace_id),
    ).fetchone()
    create_audit_log(db, user_id, "settings_change", "pilot_issue", issue_id, "success", f"status={values['status']};severity={values['severity']}")
    return dict(row)


def create_pilot_issue_from_feedback(db: Connection, feedback_id: int, payload: Any, user_id: int | None) -> dict[str, Any] | None:
    organization_id, workspace_id = get_user_context_ids(db, user_id)
    feedback = db.execute(
        "SELECT * FROM feedback_entries WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (feedback_id, organization_id, workspace_id),
    ).fetchone()
    if not feedback:
        return None
    comment = str(feedback["comment"] or "")
    rating = str(feedback["rating"] or "")
    title = _safe_pilot_text(str(getattr(payload, "title", "")), 160) or f"フィードバック対応: {rating}"
    summary = _safe_pilot_text(comment, 500) or "フィードバック内容の確認が必要です。"
    duplicate_candidates = _pilot_issue_duplicate_candidates(db, title, summary, user_id=user_id)

    class _Payload:
        category = getattr(payload, "category", "その他")
        severity = getattr(payload, "severity", "medium")
        assigned_to = getattr(payload, "assigned_to", "")
        reproduction_steps = "フィードバック一覧から登録"

        def __init__(self, title: str, summary: str):
            self.title = title
            self.summary = summary

    issue = create_pilot_issue(db, _Payload(title, summary), user_id, source_feedback_id=feedback_id)
    create_audit_log(db, user_id, "save", "pilot_issue_from_feedback", str(feedback_id), "success", f"issue_id={issue['issue_id']}")
    return {"issue": issue, "duplicate_candidates": duplicate_candidates}


def get_runtime_maintenance_mode(db: Connection) -> dict[str, Any]:
    row = db.execute("SELECT value, updated_by, updated_at, note FROM app_runtime_settings WHERE key = 'maintenance_mode'").fetchone()
    if not row:
        return {"enabled": False, "reason": "", "updated_by": None, "updated_at": ""}
    return {
        "enabled": str(row["value"]).lower() in {"1", "true", "yes", "on"},
        "reason": str(row["note"] or ""),
        "updated_by": row["updated_by"],
        "updated_at": str(row["updated_at"] or ""),
    }


def set_runtime_maintenance_mode(db: Connection, enabled: bool, reason: str, user_id: int | None) -> dict[str, Any]:
    safe_reason = _safe_pilot_text(reason, 300)
    existing = db.execute("SELECT key FROM app_runtime_settings WHERE key = 'maintenance_mode'").fetchone()
    if existing:
        db.execute(
            """
            UPDATE app_runtime_settings
            SET value = ?, updated_by = ?, note = ?, updated_at = CURRENT_TIMESTAMP
            WHERE key = 'maintenance_mode'
            """,
            ("1" if enabled else "0", user_id, safe_reason),
        )
    else:
        db.execute(
            "INSERT INTO app_runtime_settings (key, value, updated_by, note) VALUES ('maintenance_mode', ?, ?, ?)",
            ("1" if enabled else "0", user_id, safe_reason),
        )
    create_audit_log(db, user_id, "settings_change", "maintenance_mode", "runtime", "success", f"enabled={enabled};reason={safe_reason[:120]}")
    return get_runtime_maintenance_mode(db)


def _latest_failure_streak(db: Connection, event_type: str, metadata_like: str = "%") -> int:
    rows = db.execute(
        """
        SELECT status
        FROM pilot_events
        WHERE event_type = ? AND metadata LIKE ?
        ORDER BY created_at DESC, id DESC
        LIMIT 3
        """,
        (event_type, metadata_like),
    ).fetchall()
    streak = 0
    for row in rows:
        if str(row["status"]) == "success":
            break
        streak += 1
    return streak


def detect_pilot_incidents(db: Connection) -> list[dict[str, Any]]:
    incidents: list[dict[str, Any]] = []
    login_failures = _count_rows(db, "audit_logs", "event_type = 'login' AND status != 'success'")
    if login_failures >= 3:
        incidents.append({"key": "login_failure", "severity": "critical", "title": "ログイン不能の可能性", "detail": f"ログイン失敗が{login_failures}件あります。"})
    try:
        db.execute("SELECT 1")
    except Exception:
        incidents.append({"key": "db_down", "severity": "critical", "title": "DB接続不能", "detail": "DB接続確認に失敗しました。"})
    if _latest_failure_streak(db, "proposal_generation") >= 3:
        incidents.append({"key": "proposal_failures", "severity": "critical", "title": "提案書作成が連続失敗", "detail": "提案書作成が直近3回連続で失敗しています。"})
    if _latest_failure_streak(db, "download") >= 3:
        incidents.append({"key": "download_failures", "severity": "critical", "title": "PPT/PDF生成が連続失敗", "detail": "PPT/PDF生成が直近3回連続で失敗しています。"})
    unauthorized_admin = _count_rows(db, "audit_logs", "status != 'success' AND (target_type LIKE '%admin%' OR metadata LIKE '%403%')")
    if unauthorized_admin > 0:
        incidents.append({"key": "unauthorized_admin", "severity": "high", "title": "管理機能への権限外アクセス候補", "detail": f"権限外アクセス候補が{unauthorized_admin}件あります。"})
    secret_candidates = 0
    for table_name, column_name in (("audit_logs", "metadata"), ("pilot_events", "metadata"), ("usage_logs", "error_type")):
        secret_candidates += _count_rows(db, table_name, f"{column_name} LIKE ? OR {column_name} LIKE ? OR {column_name} LIKE ?", ("%sk-%", "%password%", "%api_key%"))
    if secret_candidates > 0:
        incidents.append({"key": "secret_leak_candidate", "severity": "critical", "title": "機密情報がログへ保存された可能性", "detail": f"機密情報らしきログ候補が{secret_candidates}件あります。"})
    unresolved_critical = _count_rows(db, "pilot_issues", "severity = 'critical' AND status NOT IN ('resolved', 'deferred')")
    if unresolved_critical > 0:
        incidents.append({"key": "critical_issue", "severity": "critical", "title": "未解決の重大Issue", "detail": f"critical Issueが{unresolved_critical}件あります。"})
    enabled_count = _count_rows(db, "users", "pilot_enabled = 1 AND is_active = 1")
    started_count = _count_rows(db, "users", "pilot_enabled = 1 AND pilot_started_at IS NOT NULL")
    failed_count = _count_rows(db, "pilot_events", "status != 'success'")
    if enabled_count > 0 and started_count == 0 and failed_count > 0:
        incidents.append({"key": "all_pilot_users_blocked", "severity": "critical", "title": "Pilotユーザー全員が利用不能の可能性", "detail": "Pilot対象者の利用開始が確認できず、失敗イベントがあります。"})
    return incidents


def calculate_pilot_judgment(db: Connection) -> dict[str, Any]:
    enabled_count = _count_rows(db, "users", "pilot_enabled = 1 AND is_active = 1")
    started_count = _count_rows(db, "users", "pilot_enabled = 1 AND pilot_started_at IS NOT NULL")
    proposal_total = _count_rows(db, "pilot_events", "event_type = 'proposal_generation'")
    proposal_success = _count_rows(db, "pilot_events", "event_type = 'proposal_generation' AND status = 'success'")
    critical_issues = _count_rows(db, "pilot_issues", "severity = 'critical' AND status NOT IN ('resolved', 'deferred')")
    feedback_metrics = _feedback_score_metrics(db)
    usage_rate = round((started_count / enabled_count) * 100) if enabled_count else 0
    proposal_success_rate = round((proposal_success / proposal_total) * 100) if proposal_total else 0
    criteria = [
        {"key": "usage", "label": "対象者の80%以上が利用", "value": usage_rate, "target": 80, "met": enabled_count > 0 and usage_rate >= 80, "unit": "%"},
        {"key": "proposal_success", "label": "提案書作成成功率90%以上", "value": proposal_success_rate, "target": 90, "met": proposal_total > 0 and proposal_success_rate >= 90, "unit": "%"},
        {"key": "critical", "label": "critical障害0件", "value": critical_issues, "target": 0, "met": critical_issues == 0, "unit": "件"},
        {"key": "usability", "label": "使いやすさ平均4.0以上", "value": feedback_metrics["average_usability"], "target": 4.0, "met": feedback_metrics["average_usability"] >= 4.0, "unit": "/5"},
        {"key": "practical", "label": "実務利用可能評価70%以上", "value": feedback_metrics["practical_usability_rate"], "target": 70, "met": feedback_metrics["practical_usability_rate"] >= 70, "unit": "%"},
        {"key": "time_saved", "label": "時間短縮実感70%以上", "value": feedback_metrics["time_saved_rate"], "target": 70, "met": feedback_metrics["time_saved_rate"] >= 70, "unit": "%"},
    ]
    met_count = sum(1 for item in criteria if item["met"])
    if critical_issues > 0 or (proposal_total >= 3 and proposal_success_rate < 50):
        result = "中止推奨"
    elif met_count == len(criteria):
        result = "合格"
    elif met_count >= 4:
        result = "条件付き合格"
    else:
        result = "延長推奨"
    reasons = [f"{item['label']}: {item['value']}{item['unit']}" for item in criteria if not item["met"]]
    if not reasons:
        reasons = ["主要な成功基準を満たしています。正式導入へ進める判断材料があります。"]
    return {"result": result, "criteria": criteria, "reasons": reasons, "feedback_metrics": feedback_metrics}


def get_pilot_data_retention_preview(db: Connection) -> dict[str, int]:
    return {
        "pilot_events": _count_rows(db, "pilot_events"),
        "pilot_feedback": _count_rows(db, "feedback_entries"),
        "pilot_users": _count_rows(db, "users", "pilot_enabled = 1 OR pilot_started_at IS NOT NULL OR pilot_completed = 1"),
        "pilot_issues": _count_rows(db, "pilot_issues"),
        "production_projects": _count_rows(db, "projects"),
        "knowledge_entries": _count_rows(db, "proposal_knowledge"),
        "audit_logs": _count_rows(db, "audit_logs"),
    }


def apply_pilot_data_retention(db: Connection, action: str, confirm_text: str, user_id: int | None) -> dict[str, Any]:
    if confirm_text != "PILOT":
        raise ValueError("confirm_text must be PILOT")
    before = get_pilot_data_retention_preview(db)
    if action == "keep_summary_only":
        db.execute("UPDATE pilot_events SET user_id = NULL, metadata = 'summary_only' WHERE metadata != 'summary_only'")
    elif action == "anonymize_events":
        db.execute("UPDATE pilot_events SET user_id = NULL, metadata = 'anonymized'")
    elif action == "delete_events":
        db.execute("DELETE FROM pilot_events")
    elif action == "anonymize_feedback":
        db.execute("UPDATE feedback_entries SET user_id = NULL, user_role = 'pilot', comment = '[anonymized]'")
    elif action == "disable_test_users":
        db.execute("UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE role != 'admin' AND (pilot_enabled = 1 OR pilot_started_at IS NOT NULL OR pilot_completed = 1)")
    else:
        raise ValueError("unknown action")
    create_audit_log(db, user_id, "settings_change", "pilot_data_retention", action, "success", "sanitized=true;production_data_untouched=true")
    after = get_pilot_data_retention_preview(db)
    return {"action": action, "before": before, "after": after}
