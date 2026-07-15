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
from app.repository_parts.shared import _count_rows, _count_rows_in_scope, _feedback_score_metrics, _scope_filter, _scope_label, _scope_value

def row_to_dict(row: Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def ensure_initial_admin(db: Connection) -> None:
    if not settings.initial_admin_email or not settings.initial_admin_password:
        return
    existing = db.execute("SELECT id FROM users WHERE email = ?", (settings.initial_admin_email,)).fetchone()
    if existing:
        return
    db.execute(
        "INSERT INTO users (display_name, email, password_hash, role, is_active) VALUES (?, ?, ?, 'admin', 1)",
        ("Initial Admin", settings.initial_admin_email, hash_password(settings.initial_admin_password)),
    )


def authenticate_user(db: Connection, email: str, password: str) -> dict[str, Any] | None:
    user = db.execute(
        "SELECT * FROM users WHERE email = ? AND is_active = 1 AND deleted_at IS NULL",
        (email.strip().lower(),),
    ).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return row_to_dict(user)


def get_user_by_id(db: Connection, user_id: int) -> dict[str, Any] | None:
    return add_role_display_fields(row_to_dict(
        db.execute(
            """
            SELECT
                u.id,
                u.display_name,
                u.email,
                u.role,
                u.current_organization_id,
                u.current_workspace_id,
                COALESCE(o.name, '') AS organization_name,
                COALESCE(w.name, '') AS workspace_name,
                u.is_active,
                u.auth_version,
                u.pilot_enabled,
                u.pilot_started_at,
                u.pilot_last_used_at,
                u.pilot_completed,
                u.pilot_note,
                u.last_login_at,
                u.password_change_required,
                u.deleted_at,
                u.created_at,
                u.updated_at
            FROM users u
            LEFT JOIN organizations o ON o.id = u.current_organization_id
            LEFT JOIN workspaces w ON w.id = u.current_workspace_id
            WHERE u.id = ?
            """,
            (user_id,),
        ).fetchone()
    ))


def list_users(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT
            u.id,
            u.display_name,
            u.email,
            u.role,
            u.current_organization_id,
            u.current_workspace_id,
            COALESCE(o.name, '') AS organization_name,
            COALESCE(w.name, '') AS workspace_name,
            u.is_active,
            u.auth_version,
            u.pilot_enabled,
            u.pilot_started_at,
            u.pilot_last_used_at,
            u.pilot_completed,
            u.pilot_note,
            u.last_login_at,
            u.password_change_required,
            u.deleted_at,
            u.created_at,
            u.updated_at
        FROM users u
        LEFT JOIN organizations o ON o.id = u.current_organization_id
        LEFT JOIN workspaces w ON w.id = u.current_workspace_id
        WHERE u.deleted_at IS NULL
        ORDER BY u.id DESC
        """
    ).fetchall()
    return [add_role_display_fields(dict(row)) for row in rows]


def _pilot_days_remaining() -> int | None:
    if not settings.pilot_end_date:
        return None
    try:
        end_date = date.fromisoformat(settings.pilot_end_date[:10])
    except ValueError:
        return None
    return max(0, (end_date - date.today()).days)


def get_pilot_status() -> dict[str, Any]:
    return {
        "pilot_mode": settings.pilot_mode,
        "maintenance_mode": settings.maintenance_mode,
        "pilot_start_date": settings.pilot_start_date,
        "pilot_end_date": settings.pilot_end_date,
        "pilot_max_users": settings.pilot_max_users,
        "days_remaining": _pilot_days_remaining(),
        "notice": "社内試験利用中です。AI作成内容は社外提出前に必ず人が確認してください。",
    }


def build_pilot_dashboard(db: Connection, scope: Any | None = None) -> dict[str, Any]:
    from app.repository_parts.operations import (
        _safe_pilot_text,
        calculate_pilot_judgment,
        detect_pilot_incidents,
        get_pilot_data_retention_preview,
        get_runtime_maintenance_mode,
        list_pilot_issues,
    )

    enabled_count = _count_rows(db, "users", "pilot_enabled = 1 AND is_active = 1")
    started_count = _count_rows(db, "users", "pilot_enabled = 1 AND pilot_started_at IS NOT NULL")
    active_week_count = _count_rows(db, "users", "pilot_enabled = 1 AND pilot_last_used_at >= DATETIME('now', '-7 days')")
    proposal_count = _count_rows_in_scope(db, "pilot_events", scope, "event_type = 'proposal_generation'")
    proposal_success_count = _count_rows_in_scope(db, "pilot_events", scope, "event_type = 'proposal_generation' AND status = 'success'")
    successful_count = _count_rows_in_scope(db, "pilot_events", scope, "status = 'success'")
    failed_count = _count_rows_in_scope(db, "pilot_events", scope, "status != 'success'")
    total_events = _count_rows_in_scope(db, "pilot_events", scope)
    download_count = _count_rows_in_scope(db, "pilot_events", scope, "event_type = 'download'")
    feedback_count = _count_rows_in_scope(db, "feedback_entries", scope)
    success_rate = round((proposal_success_count / proposal_count) * 100) if proposal_count else 0
    issue_count = _count_rows_in_scope(db, "pilot_issues", scope)
    unresolved_issue_count = _count_rows_in_scope(db, "pilot_issues", scope, "status NOT IN ('resolved', 'deferred')")
    critical_issue_count = _count_rows_in_scope(db, "pilot_issues", scope, "severity = 'critical' AND status NOT IN ('resolved', 'deferred')")
    avg_duration_row = db.execute("SELECT AVG(duration_ms) AS average_ms FROM pilot_events WHERE duration_ms > 0").fetchone()
    average_processing_ms = round(float(avg_duration_row["average_ms"] or 0)) if avg_duration_row else 0
    unused_users = [
        dict(row)
        for row in db.execute(
            """
            SELECT id, email, role, pilot_note
            FROM users
            WHERE pilot_enabled = 1 AND is_active = 1 AND pilot_last_used_at IS NULL
            ORDER BY email
            """
        ).fetchall()
    ]
    users = [
        dict(row)
        for row in db.execute(
            """
            SELECT
                u.id,
                u.email,
                u.role,
                u.pilot_enabled,
                u.pilot_started_at,
                u.pilot_last_used_at,
                u.pilot_completed,
                u.pilot_note,
                COUNT(e.id) AS usage_count,
                SUM(CASE WHEN e.status = 'success' THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN e.status != 'success' THEN 1 ELSE 0 END) AS failure_count
            FROM users u
            LEFT JOIN pilot_events e ON e.user_id = u.id
            WHERE u.pilot_enabled = 1 OR u.role = 'admin'
            GROUP BY u.id, u.email, u.role, u.pilot_enabled, u.pilot_started_at, u.pilot_last_used_at, u.pilot_completed, u.pilot_note
            ORDER BY u.pilot_enabled DESC, u.email
            """
        ).fetchall()
    ]
    target_usage_rate = round((started_count / enabled_count) * 100) if enabled_count else 0
    feedback_metrics = _feedback_score_metrics(db)
    incidents = detect_pilot_incidents(db)
    judgment = calculate_pilot_judgment(db)
    runtime_maintenance = get_runtime_maintenance_mode(db)
    maintenance = {
        "env_enabled": settings.maintenance_mode,
        "runtime_enabled": runtime_maintenance["enabled"],
        "effective": settings.maintenance_mode or runtime_maintenance["enabled"],
        "reason": "環境変数でMaintenance Modeが有効です。" if settings.maintenance_mode else runtime_maintenance["reason"],
        "updated_at": runtime_maintenance["updated_at"],
        "updated_by": runtime_maintenance["updated_by"],
    }
    recent_feedback = [
        {
            "id": int(row["id"]),
            "rating": str(row["rating"]),
            "comment_summary": _safe_pilot_text(str(row["comment"] or ""), 180),
            "feature_name": str(row["feature_name"] or ""),
            "user_role": str(row["user_role"] or ""),
            "created_at": str(row["created_at"] or ""),
        }
        for row in db.execute(
            """
            SELECT id, rating, comment, feature_name, user_role, created_at
            FROM feedback_entries
            ORDER BY created_at DESC
            LIMIT 20
            """
        ).fetchall()
    ]
    return {
        "scope": _scope_label(scope),
        "status": get_pilot_status(),
        "summary": {
            "enabled_users": enabled_count,
            "started_users": started_count,
            "active_this_week": active_week_count,
            "usage_rate": target_usage_rate,
            "proposal_count": proposal_count,
            "proposal_generations": proposal_count,
            "downloads": download_count,
            "success_rate": success_rate,
            "error_count": failed_count,
            "feedback_count": feedback_count,
            "feedback_average": feedback_metrics["average_usability"],
            "critical_issue_count": critical_issue_count,
            "unresolved_issue_count": unresolved_issue_count,
            "issue_count": issue_count,
            "average_processing_ms": average_processing_ms,
            "unused_users": len(unused_users),
            "max_users": settings.pilot_max_users,
            "days_remaining": _pilot_days_remaining(),
            "days_to_end": _pilot_days_remaining(),
        },
        "users": users,
        "unused_users": unused_users,
        "success_criteria": judgment["criteria"],
        "feedback_metrics": feedback_metrics,
        "issues": list_pilot_issues(db),
        "incidents": incidents,
        "judgment": judgment,
        "maintenance": maintenance,
        "recent_feedback": recent_feedback,
        "retention_preview": get_pilot_data_retention_preview(db),
    }


def build_pilot_end_report(db: Connection, admin_comment: str = "", scope: Any | None = None) -> dict[str, Any]:
    from app.repository_parts.operations import summarize_feedback_entries

    dashboard = build_pilot_dashboard(db, scope)
    feedback_summary = summarize_feedback_entries(db, scope)
    issues = dashboard.get("issues", [])
    unresolved_issues = [issue for issue in issues if issue["status"] not in {"resolved", "deferred"}]
    resolved_issues = [issue for issue in issues if issue["status"] == "resolved"]
    next_improvements = []
    if dashboard["summary"]["error_count"] > 0:
        next_improvements.append("エラー分類を確認し、PPT/PDF作成と認証まわりの復旧手順を更新する")
    if unresolved_issues:
        next_improvements.append("未解決Issueを担当者へ割り当て、Pilot継続可否を判断する")
    if dashboard["summary"]["feedback_count"] < max(3, int(dashboard["summary"]["enabled_users"])):
        next_improvements.append("未回答ユーザーへフィードバック入力を依頼する")
    if dashboard["summary"]["started_users"] < dashboard["summary"]["enabled_users"]:
        next_improvements.append("未利用ユーザーへ利用案内を再送する")
    if not next_improvements:
        next_improvements.append("正式運用前にPilot結果を上長確認し、対象部署を段階的に広げる")
    markdown = "\n".join(
        [
            "# AI営業秘書 Pilot 終了レポート",
            "",
            f"- 期間: {settings.pilot_start_date or '未設定'} - {settings.pilot_end_date or '未設定'}",
            f"- 有効な試験利用者数: {dashboard['summary']['enabled_users']}",
            f"- 利用開始済み人数: {dashboard['summary']['started_users']}",
            f"- 利用率: {dashboard['summary']['usage_rate']}%",
            f"- 今週利用人数: {dashboard['summary']['active_this_week']}",
            f"- 提案書作成数: {dashboard['summary']['proposal_generations']}",
            f"- PPT/PDFダウンロード数: {dashboard['summary']['downloads']}",
            f"- 成功率: {dashboard['summary']['success_rate']}%",
            f"- 平均処理時間: {dashboard['summary']['average_processing_ms']}ms",
            f"- エラー件数: {dashboard['summary']['error_count']}",
            f"- フィードバック件数: {dashboard['summary']['feedback_count']}",
            f"- Pilot終了判定: {dashboard['judgment']['result']}",
            "",
            "## フィードバック集計",
            f"- 使えそう: {feedback_summary.get('usable', 0)}",
            f"- 修正すれば使えそう: {feedback_summary.get('needs_revision', 0)}",
            f"- 使いにくい: {feedback_summary.get('hard_to_use', 0)}",
            f"- 使いやすさ平均: {dashboard['feedback_metrics']['average_usability']}/5",
            f"- 継続利用意向: {dashboard['feedback_metrics']['continue_intent_rate']}%",
            "",
            "## 発生Issue一覧",
            *[f"- [{issue['severity']}/{issue['status']}] {issue['issue_id']}: {issue['title']}" for issue in issues[:30]],
            "",
            "## 解決済みIssue",
            *([f"- {issue['issue_id']}: {issue['title']}" for issue in resolved_issues[:20]] or ["- なし"]),
            "",
            "## 未解決Issue",
            *([f"- {issue['issue_id']}: {issue['title']}" for issue in unresolved_issues[:20]] or ["- なし"]),
            "",
            "## 次回改善項目",
            *[f"- {item}" for item in next_improvements],
            "",
            "## 正式導入可否",
            dashboard["judgment"]["result"],
            "",
            "## 判断理由",
            *[f"- {reason}" for reason in dashboard["judgment"]["reasons"]],
            "",
            "## 管理者コメント",
            admin_comment[:1000] or "未入力",
            "",
            "> 顧客本文、生成本文、APIキー、パスワード、トークンは含めていません。",
        ]
    )
    return {
        "dashboard": dashboard,
        "feedback_summary": feedback_summary,
        "next_improvements": next_improvements,
        "issues": issues,
        "resolved_issues": resolved_issues,
        "unresolved_issues": unresolved_issues,
        "judgment": dashboard["judgment"],
        "markdown": markdown,
    }


def create_user(db: Connection, email: str, password: str, role: str, display_name: str = "") -> dict[str, Any]:
    storage_role = normalize_role_for_storage(role)
    db.execute(
        "INSERT INTO users (display_name, email, password_hash, role, is_active, auth_version) VALUES (?, ?, ?, ?, 1, 1)",
        (display_name.strip()[:160], email.strip().lower(), hash_password(password), storage_role),
    )
    user = db.execute(
        """
        SELECT id
        FROM users
        WHERE email = ?
        """,
        (email.strip().lower(),),
    ).fetchone()
    result = get_user_by_id(db, int(user["id"])) if user else None
    if result:
        db.execute(
            """
            INSERT INTO organization_memberships (user_id, organization_id, workspace_id, membership_role)
            VALUES (?, 1, 1, ?)
            """,
            (int(result["id"]), "organization_admin" if result["role"] in {"admin", "manager"} else "member"),
        )
    return result or {}


def set_user_display_name(db: Connection, user_id: int, display_name: str) -> dict[str, Any] | None:
    db.execute(
        "UPDATE users SET display_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (display_name.strip()[:160], user_id),
    )
    return get_user_by_id(db, user_id)


def set_user_active(db: Connection, user_id: int, is_active: bool) -> dict[str, Any] | None:
    db.execute(
        "UPDATE users SET is_active = ?, auth_version = auth_version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (1 if is_active else 0, user_id),
    )
    return get_user_by_id(db, user_id)


def set_user_role(db: Connection, user_id: int, role: str) -> dict[str, Any] | None:
    storage_role = normalize_role_for_storage(role)
    db.execute(
        "UPDATE users SET role = ?, auth_version = auth_version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (storage_role, user_id),
    )
    return get_user_by_id(db, user_id)


def set_user_password(db: Connection, user_id: int, password: str, password_change_required: bool = False) -> dict[str, Any] | None:
    db.execute(
        """
        UPDATE users
        SET password_hash = ?,
            password_change_required = ?,
            auth_version = auth_version + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (hash_password(password), 1 if password_change_required else 0, user_id),
    )
    return get_user_by_id(db, user_id)


def set_user_password_change_required(db: Connection, user_id: int, required: bool) -> dict[str, Any] | None:
    db.execute(
        """
        UPDATE users
        SET password_change_required = ?,
            auth_version = auth_version + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (1 if required else 0, user_id),
    )
    return get_user_by_id(db, user_id)


def soft_delete_user(db: Connection, user_id: int) -> dict[str, Any] | None:
    db.execute(
        """
        UPDATE users
        SET is_active = 0,
            deleted_at = CURRENT_TIMESTAMP,
            auth_version = auth_version + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (user_id,),
    )
    return get_user_by_id(db, user_id)


def mark_user_login(db: Connection, user_id: int) -> None:
    db.execute(
        "UPDATE users SET last_login_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (user_id,),
    )


def count_active_admin_users(db: Connection) -> int:
    row = db.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'admin' AND is_active = 1 AND deleted_at IS NULL").fetchone()
    return int(row["count"] if row else 0)


def count_pilot_enabled_users(db: Connection) -> int:
    row = db.execute("SELECT COUNT(*) AS count FROM users WHERE pilot_enabled = 1 AND is_active = 1").fetchone()
    return int(row["count"] if row else 0)


def set_user_pilot_settings(
    db: Connection,
    user_id: int,
    pilot_enabled: bool,
    pilot_completed: bool | None = None,
    pilot_note: str = "",
) -> dict[str, Any] | None:
    db.execute(
        """
        UPDATE users
        SET pilot_enabled = ?,
            pilot_completed = COALESCE(?, pilot_completed),
            pilot_note = ?,
            auth_version = auth_version + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (1 if pilot_enabled else 0, None if pilot_completed is None else (1 if pilot_completed else 0), pilot_note[:500], user_id),
    )
    return get_user_by_id(db, user_id)


def mark_pilot_login(db: Connection, user_id: int) -> None:
    db.execute(
        """
        UPDATE users
        SET pilot_started_at = COALESCE(pilot_started_at, CURRENT_TIMESTAMP),
            pilot_last_used_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (user_id,),
    )
    record_pilot_event(db, user_id, "login", "success")


def mark_pilot_checklist_confirmed(db: Connection, user_id: int) -> dict[str, Any] | None:
    db.execute(
        """
        UPDATE users
        SET pilot_started_at = COALESCE(pilot_started_at, CURRENT_TIMESTAMP),
            pilot_last_used_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (user_id,),
    )
    record_pilot_event(db, user_id, "checklist_confirmed", "success")
    return get_user_by_id(db, user_id)


def record_pilot_event(
    db: Connection,
    user_id: int | None,
    event_type: str,
    status: str = "success",
    duration_ms: int = 0,
    metadata: str = "",
) -> None:
    if not settings.pilot_mode:
        return
    db.execute(
        """
        INSERT INTO pilot_events (user_id, event_type, status, duration_ms, metadata)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, event_type[:80], status[:40], max(0, duration_ms), metadata[:300]),
    )
    if user_id:
        db.execute("UPDATE users SET pilot_last_used_at = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))


def get_user_context_ids(db: Connection, user_id: int | None) -> tuple[int, int]:
    if not user_id:
        return 1, 1
    row = db.execute(
        "SELECT COALESCE(current_organization_id, 1) AS organization_id, COALESCE(current_workspace_id, 1) AS workspace_id FROM users WHERE id = ?",
        (int(user_id),),
    ).fetchone()
    if not row:
        return 1, 1
    return int(row["organization_id"] or 1), int(row["workspace_id"] or 1)
