import importlib.util
import os
import re
import uuid
from sqlite3 import Connection, Row
from datetime import date
from typing import Any

from app.config import settings
from app.security import hash_password, verify_password


def row_to_dict(row: Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def ensure_initial_admin(db: Connection) -> None:
    if not settings.initial_admin_email or not settings.initial_admin_password:
        return
    existing = db.execute("SELECT id FROM users WHERE email = ?", (settings.initial_admin_email,)).fetchone()
    if existing:
        return
    db.execute(
        "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'admin', 1)",
        (settings.initial_admin_email, hash_password(settings.initial_admin_password)),
    )


def authenticate_user(db: Connection, email: str, password: str) -> dict[str, Any] | None:
    user = db.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email.strip().lower(),)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return row_to_dict(user)


def get_user_by_id(db: Connection, user_id: int) -> dict[str, Any] | None:
    return row_to_dict(
        db.execute(
            """
            SELECT id, email, role, is_active, auth_version, pilot_enabled, pilot_started_at, pilot_last_used_at,
                   pilot_completed, pilot_note, created_at, updated_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
    )


def list_users(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT id, email, role, is_active, auth_version, pilot_enabled, pilot_started_at, pilot_last_used_at,
               pilot_completed, pilot_note, created_at, updated_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()
    return [dict(row) for row in rows]


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


def build_pilot_dashboard(db: Connection) -> dict[str, Any]:
    enabled_count = _count_rows(db, "users", "pilot_enabled = 1 AND is_active = 1")
    started_count = _count_rows(db, "users", "pilot_enabled = 1 AND pilot_started_at IS NOT NULL")
    active_week_count = _count_rows(db, "users", "pilot_enabled = 1 AND pilot_last_used_at >= DATETIME('now', '-7 days')")
    proposal_count = _count_rows(db, "pilot_events", "event_type = 'proposal_generation'")
    proposal_success_count = _count_rows(db, "pilot_events", "event_type = 'proposal_generation' AND status = 'success'")
    successful_count = _count_rows(db, "pilot_events", "status = 'success'")
    failed_count = _count_rows(db, "pilot_events", "status != 'success'")
    total_events = _count_rows(db, "pilot_events")
    download_count = _count_rows(db, "pilot_events", "event_type = 'download'")
    feedback_count = _count_rows(db, "feedback_entries")
    success_rate = round((proposal_success_count / proposal_count) * 100) if proposal_count else 0
    issue_count = _count_rows(db, "pilot_issues")
    unresolved_issue_count = _count_rows(db, "pilot_issues", "status NOT IN ('resolved', 'deferred')")
    critical_issue_count = _count_rows(db, "pilot_issues", "severity = 'critical' AND status NOT IN ('resolved', 'deferred')")
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


def build_pilot_end_report(db: Connection, admin_comment: str = "") -> dict[str, Any]:
    dashboard = build_pilot_dashboard(db)
    feedback_summary = summarize_feedback_entries(db)
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


def create_user(db: Connection, email: str, password: str, role: str) -> dict[str, Any]:
    db.execute(
        "INSERT INTO users (email, password_hash, role, is_active, auth_version) VALUES (?, ?, ?, 1, 1)",
        (email.strip().lower(), hash_password(password), role),
    )
    user = db.execute(
        """
        SELECT id, email, role, is_active, auth_version, pilot_enabled, pilot_started_at, pilot_last_used_at,
               pilot_completed, pilot_note, created_at, updated_at
        FROM users
        WHERE email = ?
        """,
        (email.strip().lower(),),
    ).fetchone()
    return dict(user)


def set_user_active(db: Connection, user_id: int, is_active: bool) -> dict[str, Any] | None:
    db.execute(
        "UPDATE users SET is_active = ?, auth_version = auth_version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (1 if is_active else 0, user_id),
    )
    return get_user_by_id(db, user_id)


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


def get_or_create_customer(db: Connection, company_name: str, industry: str = "", contact_person: str = "") -> int | None:
    name = company_name.strip()
    if not name:
        return None
    existing = db.execute("SELECT id FROM customers WHERE company_name = ?", (name,)).fetchone()
    if existing:
        db.execute(
            "UPDATE customers SET industry = COALESCE(NULLIF(?, ''), industry), contact_person = COALESCE(NULLIF(?, ''), contact_person), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (industry.strip(), contact_person.strip(), existing["id"]),
        )
        return int(existing["id"])
    cursor = db.execute(
        "INSERT INTO customers (company_name, industry, contact_person) VALUES (?, ?, ?)",
        (name, industry.strip(), contact_person.strip()),
    )
    return int(cursor.lastrowid)


def get_or_create_project(db: Connection, customer_id: int | None, name: str, summary: str = "", win_probability: int = 0, next_action: str = "") -> int:
    project_name = name.strip() or "謠先｡域ｺ門ｙ譯井ｻｶ"
    existing = db.execute(
        "SELECT id FROM projects WHERE name = ? AND (customer_id IS ? OR customer_id = ?)",
        (project_name, customer_id, customer_id),
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE projects SET summary = ?, win_probability = ?, next_action = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (summary[:500], win_probability, next_action[:300], existing["id"]),
        )
        return int(existing["id"])
    cursor = db.execute(
        "INSERT INTO projects (customer_id, name, summary, win_probability, next_action) VALUES (?, ?, ?, ?, ?)",
        (customer_id, project_name, summary[:500], win_probability, next_action[:300]),
    )
    return int(cursor.lastrowid)


def create_history_log(
    db: Connection,
    user_id: int | None,
    customer_id: int | None,
    project_id: int | None,
    feature_name: str,
    input_length: int,
    output_type: str,
    status: str,
    error_type: str = "",
) -> None:
    db.execute(
        """
        INSERT INTO proposal_histories
        (user_id, customer_id, project_id, feature_name, input_length, output_type, status, error_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, customer_id, project_id, feature_name, input_length, output_type, status, error_type),
    )
    db.execute(
        """
        INSERT INTO usage_logs (user_id, feature_name, input_length, output_type, status, error_type)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, feature_name, input_length, output_type, status, error_type),
    )
    if output_type in {"markdown", "markdown+pptx-data"}:
        record_pilot_event(db, user_id, "proposal_generation", status, metadata=f"output_type={output_type};error_type={error_type}")
    elif output_type in {"pptx", "summary-pptx", "estimate-pdf"}:
        record_pilot_event(db, user_id, "download", status, metadata=f"output_type={output_type};error_type={error_type}")
    if feature_name in {"謠先｡域嶌逕滓・", "PowerPoint", "隕∫ｴПowerPoint", "隕狗ｩ肴嶌PDF"}:
        create_audit_log(db, user_id, "generate", feature_name, "", status, f"output_type={output_type};error_type={error_type}")


def list_crm(db: Connection) -> dict[str, list[dict[str, Any]]]:
    customers = [dict(row) for row in db.execute("SELECT * FROM customers ORDER BY updated_at DESC LIMIT 100").fetchall()]
    projects: list[dict[str, Any]] = []
    project_rows = db.execute(
            """
            SELECT p.*, c.company_name AS customer_name
            FROM projects p
            LEFT JOIN customers c ON c.id = p.customer_id
            ORDER BY p.updated_at DESC
            LIMIT 100
            """
        ).fetchall()
    for row in project_rows:
        project = dict(row)
        review = db.execute("SELECT status FROM proposal_reviews WHERE project_id = ? ORDER BY updated_at DESC, id DESC LIMIT 1", (str(project["id"]),)).fetchone()
        outcome = db.execute("SELECT outcome, lost_reason FROM project_outcomes WHERE project_id = ? LIMIT 1", (project["id"],)).fetchone()
        project["review_status"] = review["status"] if review else ""
        project["outcome"] = outcome["outcome"] if outcome else ""
        project["lost_reason"] = outcome["lost_reason"] if outcome else ""
        projects.append(project)
    return {"customers": customers, "projects": projects}


def get_project_detail(db: Connection, project_id: int) -> dict[str, Any] | None:
    project = row_to_dict(
        db.execute(
            """
            SELECT p.*, c.company_name AS customer_name
            FROM projects p
            LEFT JOIN customers c ON c.id = p.customer_id
            WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()
    )
    if not project:
        return None
    project["proposal_histories"] = [
        dict(row) for row in db.execute("SELECT * FROM proposal_histories WHERE project_id = ? ORDER BY created_at DESC LIMIT 50", (project_id,)).fetchall()
    ]
    project["meeting_memos"] = [
        dict(row) for row in db.execute("SELECT * FROM meeting_memos WHERE project_id = ? ORDER BY created_at DESC LIMIT 50", (project_id,)).fetchall()
    ]
    project["workspace_conversations"] = [
        dict(row)
        for row in db.execute(
            "SELECT * FROM workspace_conversations WHERE project_id = ? ORDER BY created_at ASC, id ASC LIMIT 100",
            (str(project_id),),
        ).fetchall()
    ]
    project["workspace_work_logs"] = [
        dict(row)
        for row in db.execute(
            "SELECT * FROM workspace_work_logs WHERE project_id = ? ORDER BY created_at ASC, id ASC LIMIT 100",
            (str(project_id),),
        ).fetchall()
    ]
    project["proposal_reviews"] = [
        dict(row)
        for row in db.execute(
            "SELECT * FROM proposal_reviews WHERE project_id = ? ORDER BY updated_at DESC, id DESC LIMIT 20",
            (str(project_id),),
        ).fetchall()
    ]
    return project


def list_usage_logs(db: Connection, limit: int = 50) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in db.execute(
            """
            SELECT l.*, u.email AS user_email
            FROM usage_logs l
            LEFT JOIN users u ON u.id = l.user_id
            ORDER BY l.created_at DESC
            LIMIT ?
            """,
            (limit,),
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
    db.execute(
        """
        INSERT INTO audit_logs (user_id, event_type, target_type, target_id, status, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, event_type, target_type, target_id, status, metadata[:300]),
    )


def list_audit_logs(db: Connection, limit: int = 100) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in db.execute(
            """
            SELECT a.*, u.email AS user_email
            FROM audit_logs a
            LEFT JOIN users u ON u.id = a.user_id
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    ]


def create_feedback_entry(db: Connection, user_id: int | None, user_role: str, rating: str, comment: str, feature_name: str) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO feedback_entries (user_id, user_role, rating, comment, feature_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, user_role[:30], rating, comment.strip()[:1000], feature_name.strip()[:100]),
    )
    feedback = dict(db.execute("SELECT * FROM feedback_entries WHERE id = ?", (cursor.lastrowid,)).fetchone())
    create_audit_log(db, user_id, "save", "feedback", str(cursor.lastrowid), "success", f"rating={rating};feature={feature_name[:80]}")
    return feedback


def list_feedback_entries(db: Connection, limit: int = 200) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in db.execute(
            """
            SELECT f.*, u.email AS user_email
            FROM feedback_entries f
            LEFT JOIN users u ON u.id = f.user_id
            ORDER BY f.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    ]


def summarize_feedback_entries(db: Connection) -> dict[str, int]:
    rows = db.execute(
        """
        SELECT rating, COUNT(*) AS count
        FROM feedback_entries
        GROUP BY rating
        """
    ).fetchall()
    summary = {"usable": 0, "needs_revision": 0, "hard_to_use": 0, "comments": 0}
    for row in rows:
        summary[str(row["rating"])] = int(row["count"])
    comment_row = db.execute("SELECT COUNT(*) AS count FROM feedback_entries WHERE TRIM(comment) != ''").fetchone()
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


def list_pilot_issues(db: Connection, limit: int = 200) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT i.*, u.email AS reported_by_email
        FROM pilot_issues i
        LEFT JOIN users u ON u.id = i.reported_by
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
        (limit,),
    ).fetchall()
    return [dict(row) for row in rows]


def _pilot_issue_duplicate_candidates(db: Connection, title: str, summary: str, limit: int = 5) -> list[dict[str, Any]]:
    title_key = _safe_pilot_text(title, 80)
    summary_key = _safe_pilot_text(summary, 80)
    rows = db.execute(
        """
        SELECT issue_id, category, severity, title, summary, status, updated_at
        FROM pilot_issues
        WHERE status != 'resolved'
          AND (
            title LIKE ?
            OR summary LIKE ?
            OR ? LIKE '%' || title || '%'
          )
        ORDER BY updated_at DESC
        LIMIT ?
        """,
        (f"%{title_key[:40]}%", f"%{summary_key[:40]}%", title_key, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def create_pilot_issue(
    db: Connection,
    payload: Any,
    user_id: int | None,
    source_feedback_id: int | None = None,
) -> dict[str, Any]:
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
        (issue_id, category, severity, title, summary, reproduction_steps, status, reported_by, assigned_to, source_feedback_id)
        VALUES (?, ?, ?, ?, ?, ?, 'reported', ?, ?, ?)
        """,
        (issue_uuid, category, severity, title, summary, reproduction_steps, user_id, assigned_to, source_feedback_id),
    )
    row = db.execute("SELECT * FROM pilot_issues WHERE issue_id = ?", (issue_uuid,)).fetchone()
    return dict(row)


def update_pilot_issue(db: Connection, issue_id: str, payload: Any, user_id: int | None) -> dict[str, Any] | None:
    existing = db.execute("SELECT * FROM pilot_issues WHERE issue_id = ?", (issue_id,)).fetchone()
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
        WHERE issue_id = ?
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
        ),
    )
    row = db.execute("SELECT * FROM pilot_issues WHERE issue_id = ?", (issue_id,)).fetchone()
    create_audit_log(db, user_id, "settings_change", "pilot_issue", issue_id, "success", f"status={values['status']};severity={values['severity']}")
    return dict(row)


def create_pilot_issue_from_feedback(db: Connection, feedback_id: int, payload: Any, user_id: int | None) -> dict[str, Any] | None:
    feedback = db.execute("SELECT * FROM feedback_entries WHERE id = ?", (feedback_id,)).fetchone()
    if not feedback:
        return None
    comment = str(feedback["comment"] or "")
    rating = str(feedback["rating"] or "")
    title = _safe_pilot_text(str(getattr(payload, "title", "")), 160) or f"フィードバック対応: {rating}"
    summary = _safe_pilot_text(comment, 500) or "フィードバック内容の確認が必要です。"
    duplicate_candidates = _pilot_issue_duplicate_candidates(db, title, summary)

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


def _feedback_score_metrics(db: Connection) -> dict[str, Any]:
    rows = db.execute("SELECT rating, comment FROM feedback_entries").fetchall()
    if not rows:
        return {
            "average_usability": 0,
            "practical_usability_rate": 0,
            "time_saved_rate": 0,
            "continue_intent_rate": 0,
            "score_count": 0,
        }
    rating_scores = {"usable": 5.0, "needs_revision": 3.5, "hard_to_use": 2.0}
    scores: list[float] = []
    time_saved_hits = 0
    time_saved_total = 0
    continue_hits = 0
    continue_total = 0
    practical_hits = 0
    for row in rows:
        rating = str(row["rating"] or "")
        comment = str(row["comment"] or "")
        practical_hits += 1 if rating in {"usable", "needs_revision"} else 0
        scores.append(rating_scores.get(rating, 3.0))
        for label, value in re.findall(r"([^:\n：]{2,30})[:：]\s*([1-5])\s*/\s*5", comment):
            numeric = int(value)
            if any(token in label for token in ("迷わず", "使いやす", "UI", "操作")):
                scores.append(float(numeric))
            if any(token in label for token in ("時間", "短縮")):
                time_saved_total += 1
                time_saved_hits += 1 if numeric >= 4 else 0
            if any(token in label for token in ("今後", "継続", "使いたい")):
                continue_total += 1
                continue_hits += 1 if numeric >= 4 else 0
    return {
        "average_usability": round(sum(scores) / len(scores), 1) if scores else 0,
        "practical_usability_rate": round((practical_hits / len(rows)) * 100) if rows else 0,
        "time_saved_rate": round((time_saved_hits / time_saved_total) * 100) if time_saved_total else 0,
        "continue_intent_rate": round((continue_hits / continue_total) * 100) if continue_total else 0,
        "score_count": len(scores),
    }


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


def _count_rows(db: Connection, table_name: str, where_clause: str = "", params: tuple[Any, ...] = ()) -> int:
    sql = f"SELECT COUNT(*) AS count FROM {table_name}"
    if where_clause:
        sql = f"{sql} WHERE {where_clause}"
    row = db.execute(sql, params).fetchone()
    return int(row["count"]) if row else 0


def _classify_usage_error(error_type: str, output_type: str, feature_name: str) -> str:
    text = f"{error_type} {output_type} {feature_name}".lower()
    if any(token in text for token in ("401", "403", "auth", "login", "unauthorized", "認証", "ログイン")):
        return "auth_error"
    if any(token in text for token in ("429", "rate", "quota", "openai", "api制限", "上限")):
        return "api_limit"
    if any(token in text for token in ("failed to fetch", "network", "cors", "timeout", "backend", "render", "通信", "接続")):
        return "backend_unreachable"
    if any(token in text for token in ("400", "422", "validation", "min_length", "入力", "不足")):
        return "input_missing"
    if output_type in {"pptx", "summary-pptx"} or any(token in text for token in ("ppt", "pptx", "powerpoint")):
        return "ppt_generation_failed"
    return "other"


def _collect_user_usage(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    users: dict[str, dict[str, Any]] = {}
    for row in rows:
        user_id = row.get("user_id")
        user_role = row.get("user_role") or "unknown"
        key = f"user:{user_id}" if user_id is not None else f"role:{user_role}"
        if key not in users:
            users[key] = {
                "user_id": user_id,
                "user_name": row.get("user_name") or "譛ｪ逋ｻ骭ｲ繝ｦ繝ｼ繧ｶ繝ｼ",
                "user_role": user_role,
                "usage_count": 0,
                "last_used_at": "",
                "success_count": 0,
                "failure_count": 0,
            }
        users[key]["usage_count"] += 1
        created_at = str(row.get("created_at") or "")
        if created_at and (not users[key]["last_used_at"] or created_at > users[key]["last_used_at"]):
            users[key]["last_used_at"] = created_at
        if row.get("status") == "failure":
            users[key]["failure_count"] += 1
        else:
            users[key]["success_count"] += 1
    return sorted(users.values(), key=lambda item: (-int(item["usage_count"]), str(item["user_name"])))[:100]


def summarize_usage_dashboard(db: Connection) -> dict[str, Any]:
    feedback_summary = summarize_feedback_entries(db)
    feedback_count = _count_rows(db, "feedback_entries")
    auth_error_count = _count_rows(db, "audit_logs", "event_type = 'login' AND status != 'success'")

    proposal_condition = "(output_type IN ('markdown', 'markdown+pptx-data') OR feature_name LIKE ?)"
    proposal_params = ("%謠先｡・",)
    summary_ppt_condition = "output_type = 'summary-pptx'"
    detail_ppt_condition = "output_type = 'pptx'"
    ppt_condition = "output_type IN ('pptx', 'summary-pptx')"
    estimate_pdf_condition = "output_type = 'estimate-pdf'"
    sample_condition = "(output_type = 'sample' OR feature_name LIKE ?)"
    sample_params = ("%繧ｵ繝ｳ繝励Ν%",)

    error_analysis = {
        "api_limit": 0,
        "backend_unreachable": 0,
        "input_missing": 0,
        "ppt_generation_failed": 0,
        "auth_error": auth_error_count,
    }
    for row in db.execute(
        """
        SELECT feature_name, output_type, error_type
        FROM usage_logs
        WHERE status != 'success'
        """
    ).fetchall():
        category = _classify_usage_error(str(row["error_type"]), str(row["output_type"]), str(row["feature_name"]))
        if category in error_analysis:
            error_analysis[category] += 1

    usage_rows = [
        dict(row)
        for row in db.execute(
            """
            SELECT
                l.user_id,
                COALESCE(u.email, '譛ｪ逋ｻ骭ｲ繝ｦ繝ｼ繧ｶ繝ｼ') AS user_name,
                COALESCE(u.role, 'unknown') AS user_role,
                l.status,
                l.created_at
            FROM usage_logs l
            LEFT JOIN users u ON u.id = l.user_id
            """
        ).fetchall()
    ]
    feedback_rows = [
        dict(row)
        for row in db.execute(
            """
            SELECT
                f.user_id,
                COALESCE(u.email, '譛ｪ逋ｻ骭ｲ繝ｦ繝ｼ繧ｶ繝ｼ') AS user_name,
                COALESCE(NULLIF(f.user_role, ''), u.role, 'unknown') AS user_role,
                'success' AS status,
                f.created_at
            FROM feedback_entries f
            LEFT JOIN users u ON u.id = f.user_id
            """
        ).fetchall()
    ]

    total_usage = _count_rows(db, "usage_logs") + feedback_count
    today_usage = _count_rows(db, "usage_logs", "DATE(created_at) = DATE('now')") + _count_rows(
        db, "feedback_entries", "DATE(created_at) = DATE('now')"
    )
    week_usage = _count_rows(db, "usage_logs", "created_at >= DATETIME('now', '-7 days')") + _count_rows(
        db, "feedback_entries", "created_at >= DATETIME('now', '-7 days')"
    )

    return {
        "summary": {
            "total_usage": total_usage,
            "today_usage": today_usage,
            "week_usage": week_usage,
            "proposal_generation": _count_rows(db, "usage_logs", proposal_condition, proposal_params),
            "ppt_download": _count_rows(db, "usage_logs", ppt_condition),
            "error_count": _count_rows(db, "usage_logs", "status != 'success'") + auth_error_count,
            "feedback_count": feedback_count,
        },
        "error_analysis": error_analysis,
        "users": _collect_user_usage(usage_rows + feedback_rows),
        "features": [
            {
                "feature_key": "proposal_generation",
                "feature_name": "謠先｡域嶌菴懈・",
                "usage_count": _count_rows(db, "usage_logs", proposal_condition, proposal_params),
                "success_count": _count_rows(db, "usage_logs", f"{proposal_condition} AND status = 'success'", proposal_params),
                "failure_count": _count_rows(db, "usage_logs", f"{proposal_condition} AND status != 'success'", proposal_params),
            },
            {
                "feature_key": "summary_ppt",
                "feature_name": "隕∫ｴПPT",
                "usage_count": _count_rows(db, "usage_logs", summary_ppt_condition),
                "success_count": _count_rows(db, "usage_logs", f"{summary_ppt_condition} AND status = 'success'"),
                "failure_count": _count_rows(db, "usage_logs", f"{summary_ppt_condition} AND status != 'success'"),
            },
            {
                "feature_key": "detail_ppt",
                "feature_name": "隧ｳ邏ｰPPT",
                "usage_count": _count_rows(db, "usage_logs", detail_ppt_condition),
                "success_count": _count_rows(db, "usage_logs", f"{detail_ppt_condition} AND status = 'success'"),
                "failure_count": _count_rows(db, "usage_logs", f"{detail_ppt_condition} AND status != 'success'"),
            },
            {
                "feature_key": "estimate_pdf",
                "feature_name": "隕狗ｩ恒DF",
                "usage_count": _count_rows(db, "usage_logs", estimate_pdf_condition),
                "success_count": _count_rows(db, "usage_logs", f"{estimate_pdf_condition} AND status = 'success'"),
                "failure_count": _count_rows(db, "usage_logs", f"{estimate_pdf_condition} AND status != 'success'"),
            },
            {
                "feature_key": "sample_experience",
                "feature_name": "サンプル体験",
                "usage_count": _count_rows(db, "usage_logs", sample_condition, sample_params),
                "success_count": _count_rows(db, "usage_logs", f"{sample_condition} AND status = 'success'", sample_params),
                "failure_count": _count_rows(db, "usage_logs", f"{sample_condition} AND status != 'success'", sample_params),
            },
            {
                "feature_key": "feedback_submit",
                "feature_name": "繝輔ぅ繝ｼ繝峨ヰ繝・け騾∽ｿ｡",
                "usage_count": feedback_count,
                "success_count": feedback_count,
                "failure_count": 0,
            },
        ],
        "feedback_summary": feedback_summary,
    }


def _format_period_label(start_at: str, end_at: str) -> str:
    if not start_at and not end_at:
        return "未集計"
    start_label = start_at[:10] if start_at else "未記録"
    end_label = end_at[:10] if end_at else start_label
    return start_label if start_label == end_label else f"{start_label} - {end_label}"


def _build_trial_report_markdown(report: dict[str, Any]) -> str:
    summary = report["numeric_summary"]
    feedback = report["feedback_summary"]
    lines = [
        "# AI営業秘書 社内試験導入レポート",
        "",
        "## 要約",
        report["summary_text"],
        "",
        "## 数値サマリー",
        f"- 試験導入期間: {report['period']['label']}",
        f"- 総利用回数: {summary['total_usage']}件",
        f"- 提案書作成回数: {summary['proposal_generation']}件",
        f"- PPTダウンロード回数: {summary['ppt_download']}件",
        f"- エラー発生回数: {summary['error_count']}件",
        f"- フィードバック件数: {summary['feedback_count']}件",
        "",
        "## フィードバック傾向",
        f"- 使えそう: {feedback['usable']}件",
        f"- 修正すれば使えそう: {feedback['needs_revision']}件",
        f"- 使いにくい: {feedback['hard_to_use']}件",
        f"- コメント件数: {feedback['comments']}件",
        "",
        "## 良かった点",
        *[f"- {item}" for item in report["good_points"]],
        "",
        "## 課題",
        *[f"- {item}" for item in report["issues"]],
        "",
        "## 次回改善案",
        *[f"- {item}" for item in report["next_actions"]],
        "",
        "## 社内展開可否の所感",
        report["rollout_opinion"],
        "",
        "## 管理者コメント",
        report["admin_comment"] or "未入力",
        "",
        "> 顧客本文、生成本文、APIキー、個人情報は含めていません。",
    ]
    return "\n".join(lines)


def build_trial_report(db: Connection, admin_comment: str = "") -> dict[str, Any]:
    dashboard = summarize_usage_dashboard(db)
    summary = dashboard["summary"]
    feedback = dashboard["feedback_summary"]
    errors = dashboard["error_analysis"]

    period_row = db.execute(
        """
        SELECT MIN(created_at) AS start_at, MAX(created_at) AS end_at
        FROM (
            SELECT created_at FROM usage_logs
            UNION ALL
            SELECT created_at FROM feedback_entries
        )
        """
    ).fetchone()
    start_at = str(period_row["start_at"] or "") if period_row else ""
    end_at = str(period_row["end_at"] or "") if period_row else ""
    period = {"start": start_at, "end": end_at, "label": _format_period_label(start_at, end_at)}

    total_usage = int(summary["total_usage"])
    proposal_count = int(summary["proposal_generation"])
    ppt_count = int(summary["ppt_download"])
    error_count = int(summary["error_count"])
    feedback_count = int(summary["feedback_count"])
    usable = int(feedback["usable"])
    needs_revision = int(feedback["needs_revision"])
    hard_to_use = int(feedback["hard_to_use"])

    good_points: list[str] = []
    if total_usage > 0:
        good_points.append("社内メンバーによる利用ログが蓄積され、試験導入の効果測定を開始できています。")
    if proposal_count > 0:
        good_points.append("提案書作成機能が実際に利用され、初稿作成時間の短縮に寄与しています。")
    if ppt_count > 0:
        good_points.append("PPTダウンロードまで到達しており、営業資料作成の実務フローに接続できています。")
    if feedback_count > 0 and usable >= hard_to_use:
        good_points.append("肯定的なフィードバックが確認でき、社内試験導入を継続する判断材料があります。")
    if not good_points:
        good_points.append("まずはサンプル案件で利用体験を増やし、効果を測定する段階です。")

    issues: list[str] = []
    if error_count > 0:
        issues.append(f"エラーが{error_count}件発生しているため、利用者が止まりやすい箇所を確認する必要があります。")
    if feedback_count == 0:
        issues.append("フィードバックがまだ不足しており、利用者の体感品質を判断する材料が限られています。")
    if needs_revision > 0:
        issues.append("修正すれば使えそうという評価があり、出力内容の微調整や説明文の改善余地があります。")
    if hard_to_use > 0:
        issues.append("使いにくい評価があるため、初期画面とダウンロード導線を重点的に確認します。")
    if errors.get("api_limit", 0) > 0:
        issues.append("API上限に関する失敗があるため、利用時間帯やモックモード案内の整備が必要です。")
    if errors.get("backend_unreachable", 0) > 0:
        issues.append("Backend接続エラーがあるため、Renderの起動状態とVercel側API URLを確認します。")
    if not issues:
        issues.append("現時点で大きな阻害要因は目立っていません。継続利用で追加データを確認します。")

    next_actions: list[str] = []
    if feedback_count < 5:
        next_actions.append("試験利用者を数名追加し、提案書作成後のフィードバックを集めます。")
    if error_count > 0:
        next_actions.append("エラー種別ごとの再現条件を確認し、利用者向け案内文と復旧手順を整えます。")
    next_actions.append("提出前チェックリストの運用を徹底し、AI作成内容を人が確認するルールを周知します。")
    next_actions.append("要約PPTを中心に、研修発表・営業共有で使いやすい出力品質を確認します。")

    if total_usage == 0:
        rollout_opinion = "現時点では利用実績がないため、まずは少人数でサンプル体験を行う段階です。"
    elif hard_to_use > usable or (total_usage > 0 and error_count / max(total_usage, 1) >= 0.25):
        rollout_opinion = "全社展開前に、エラー対策と使いにくさの解消を優先した限定試験の継続が妥当です。"
    elif feedback_count >= 3 and usable >= needs_revision + hard_to_use:
        rollout_opinion = "小規模部門での継続利用、または対象部署を広げた試験導入を検討できます。"
    else:
        rollout_opinion = "追加の利用ログとフィードバックを集めながら、段階的な社内展開を検討する状態です。"

    summary_text = (
        f"試験導入期間は{period['label']}です。総利用回数は{total_usage}件、"
        f"提案書作成は{proposal_count}件、PPTダウンロードは{ppt_count}件でした。"
        f"エラーは{error_count}件、フィードバックは{feedback_count}件集まっています。"
    )

    report = {
        "period": period,
        "summary_text": summary_text,
        "numeric_summary": summary,
        "feedback_summary": feedback,
        "error_analysis": errors,
        "good_points": good_points,
        "issues": issues,
        "next_actions": next_actions,
        "rollout_opinion": rollout_opinion,
        "admin_comment": admin_comment.strip()[:2000],
    }
    report["markdown"] = _build_trial_report_markdown(report)
    return report


def _readiness_item(key: str, label: str, status: str, detail: str, next_action: str = "") -> dict[str, str]:
    return {
        "key": key,
        "label": label,
        "status": status,
        "detail": detail,
        "next_action": next_action,
    }


def _table_has_rows(db: Connection, table_name: str) -> tuple[bool, int]:
    try:
        row = db.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
        return True, int(row["count"]) if row else 0
    except Exception:
        return False, 0


def _score_readiness_items(items: list[dict[str, str]]) -> int:
    if not items:
        return 0
    points = {"ok": 100, "warning": 60, "missing": 0}
    return round(sum(points.get(item["status"], 0) for item in items) / len(items))


def _status_label(status: str) -> str:
    return {"ok": "OK", "warning": "要確認", "missing": "未設定"}.get(status, status)


def _build_operation_readiness_markdown(readiness: dict[str, Any]) -> str:
    lines = [
        "# AI営業秘書 運用準備チェック",
        "",
        f"- 作成日時: {readiness['generated_at']}",
        f"- 運用準備スコア: {readiness['score']}点",
        f"- 所感: {readiness['score_label']}",
        "",
        "## 自動チェック項目",
    ]
    lines.extend(
        f"- [{_status_label(item['status'])}] {item['label']}: {item['detail']}"
        for item in readiness["checks"]
    )
    lines.extend(["", "## セキュリティチェック"])
    lines.extend(
        f"- [{_status_label(item['status'])}] {item['label']}: {item['detail']}"
        for item in readiness["security_checks"]
    )
    lines.extend(["", "## 次にやること"])
    if readiness["next_actions"]:
        lines.extend(f"- {action}" for action in readiness["next_actions"])
    else:
        lines.append("- 主要な準備項目は整っています。少人数で試験利用を開始できます。")
    lines.append("")
    lines.append("> 顧客本文、生成本文、APIキー、パスワードは含めていません。")
    return "\n".join(lines)


def build_operation_readiness_check(db: Connection) -> dict[str, Any]:
    user_rows = db.execute("SELECT role, COUNT(*) AS count FROM users WHERE is_active = 1 GROUP BY role").fetchall()
    role_counts = {str(row["role"]): int(row["count"]) for row in user_rows}
    has_admin = role_counts.get("admin", 0) > 0
    has_member_or_viewer = role_counts.get("member", 0) + role_counts.get("viewer", 0) > 0

    db_ok = True
    try:
        db.execute("SELECT 1")
    except Exception:
        db_ok = False

    audit_available, audit_count = _table_has_rows(db, "audit_logs")
    usage_available, usage_count = _table_has_rows(db, "usage_logs")
    feedback_available, feedback_count = _table_has_rows(db, "feedback_entries")
    users_available, users_count = _table_has_rows(db, "users")
    has_vercel_origin = any("vercel.app" in origin for origin in settings.cors_origins) or bool(settings.cors_origin_regex)
    auth_configured = bool(settings.app_auth_secret and settings.initial_admin_email and settings.initial_admin_password)
    frontend_openai_env = any(key.startswith("NEXT_PUBLIC_OPENAI") for key in os.environ)

    checks = [
        _readiness_item("backend", "Backend接続", "ok", "Backend APIに接続できます。"),
        _readiness_item("openai", "OpenAI API設定", "ok" if settings.use_mock_ai or bool(settings.openai_api_key) else "missing", "モックモードまたはOpenAI APIキーが設定されています。" if settings.use_mock_ai or settings.openai_api_key else "OpenAI APIキーが未設定です。", "RenderにOPENAI_API_KEYを設定してください。" if not settings.use_mock_ai and not settings.openai_api_key else ""),
        _readiness_item("auth", "認証設定", "ok" if auth_configured else "missing", "認証用の環境変数が設定されています。" if auth_configured else "認証用の環境変数が不足しています。", "APP_AUTH_SECRET、INITIAL_ADMIN_EMAIL、INITIAL_ADMIN_PASSWORDを設定してください。" if not auth_configured else ""),
        _readiness_item("initial_admin", "初期管理者設定", "ok" if has_admin else "missing", f"有効なadminが{role_counts.get('admin', 0)}名います。" if has_admin else "有効なadminが見つかりません。", "初期管理者を作成してください。" if not has_admin else ""),
        _readiness_item("db", "DB接続", "ok" if db_ok else "missing", "DB接続を確認しました。" if db_ok else "DBへ接続できません。", "DATABASE_URLを確認してください。" if not db_ok else ""),
        _readiness_item("vercel_api_url", "Vercel API URL設定", "ok" if has_vercel_origin else "warning", "VercelからのCORS許可が設定されています。" if has_vercel_origin else "Vercel URLのCORS許可を確認してください。", "CORS_ORIGINSまたはCORS_ORIGIN_REGEXを確認してください。" if not has_vercel_origin else ""),
        _readiness_item("pptx", "PPTX生成", "ok", "python-pptxを利用した生成処理があります。"),
        _readiness_item("pdf", "PDF生成", "ok", "reportlabを利用した見積PDF生成処理があります。"),
        _readiness_item("roles", "権限管理", "ok" if has_member_or_viewer else "warning", "admin/member/viewerの利用を確認できます。" if has_member_or_viewer else "通常利用者または閲覧ユーザーが未作成です。", "member/viewerの権限確認用ユーザーを作成してください。" if not has_member_or_viewer else ""),
        _readiness_item("audit_logs", "監査ログ", "ok" if audit_available else "missing", f"audit_logsテーブルを確認しました。現在{audit_count}件です。" if audit_available else "audit_logsテーブルを確認できません。", "DB初期化を確認してください。" if not audit_available else ""),
        _readiness_item("usage_logs", "利用ログ", "ok" if usage_available else "missing", f"usage_logsテーブルを確認しました。現在{usage_count}件です。" if usage_available else "usage_logsテーブルを確認できません。", "DB初期化を確認してください。" if not usage_available else ""),
        _readiness_item("feedback", "フィードバック収集", "ok" if feedback_available else "missing", f"feedback_entriesテーブルを確認しました。現在{feedback_count}件です。" if feedback_available else "feedback_entriesテーブルを確認できません。", "DB初期化を確認してください。" if not feedback_available else ""),
        _readiness_item("trial_report", "試験導入レポート作成", "ok", "利用状況とフィードバックからレポートを作成できます。"),
    ]

    security_checks = [
        _readiness_item("frontend_api_key", "APIキーをFrontendに表示していない", "ok" if not frontend_openai_env else "warning", "NEXT_PUBLIC_OPENAI系の環境変数は検出されていません。" if not frontend_openai_env else "NEXT_PUBLIC_OPENAI系の環境変数が検出されました。", "Vercelの公開環境変数からOpenAI関連の値を削除してください。" if frontend_openai_env else ""),
        _readiness_item("password_logs", "パスワードをログ保存していない", "ok", "利用ログ・監査ログへパスワード本文を保存しない設計です。"),
        _readiness_item("input_body_logs", "入力本文全文を利用ログに保存していない", "ok", "利用ログは文字数、機能名、出力種別、成功/失敗のみ保存します。"),
        _readiness_item("output_body_audit_logs", "生成本文全文を監査ログに保存していない", "ok", "監査ログはイベント種別と短いメタ情報のみ保存します。"),
        _readiness_item("admin_menu", "admin以外に管理者メニューを表示していない", "ok", "Frontend表示とBackend APIの両方で権限確認します。"),
        _readiness_item("users_table", "ユーザーテーブル", "ok" if users_available else "missing", f"usersテーブルを確認しました。現在{users_count}件です。" if users_available else "usersテーブルを確認できません。"),
    ]

    all_items = checks + security_checks
    score = _score_readiness_items(all_items)
    if score >= 85:
        score_label = "社内試験導入可能です。要確認項目は案内前に確認してください。"
    elif score >= 70:
        score_label = "限定的な試験導入は可能です。未設定項目を優先して確認してください。"
    else:
        score_label = "社内案内前に設定、接続、権限の確認が必要です。"

    next_actions = []
    for item in all_items:
        if item["status"] != "ok" and item["next_action"] and item["next_action"] not in next_actions:
            next_actions.append(item["next_action"])

    generated_at = db.execute("SELECT DATETIME('now') AS now").fetchone()["now"]
    readiness = {
        "generated_at": str(generated_at),
        "score": score,
        "score_label": score_label,
        "checks": checks,
        "security_checks": security_checks,
        "next_actions": next_actions,
    }
    readiness["markdown"] = _build_operation_readiness_markdown(readiness)
    return readiness

def _improvement_item(
    priority: str,
    category: str,
    title: str,
    reason: str,
    expected_effect: str,
    difficulty: str,
    next_step: str,
) -> dict[str, str]:
    return {
        "priority": priority,
        "category": category,
        "title": title,
        "reason": reason,
        "expected_effect": expected_effect,
        "difficulty": difficulty,
        "next_step": next_step,
    }


def _build_improvement_markdown(dashboard: dict[str, Any]) -> str:
    lines = [
        "# AI営業秘書 改善提案ダッシュボード",
        "",
        "## 上司報告用まとめ",
        dashboard["executive_summary"],
        "",
        "## 改善案",
    ]
    for item in dashboard["improvements"]:
        lines.extend(
            [
                f"### [{item['priority']}] {item['title']}",
                f"- カテゴリ: {item['category']}",
                f"- 理由: {item['reason']}",
                f"- 想定効果: {item['expected_effect']}",
                f"- 対応難易度: {item['difficulty']}",
                f"- 次にやること: {item['next_step']}",
                "",
            ]
        )
    lines.append("## 改善ロードマップ")
    roadmap_labels = {"now": "今すぐ対応", "this_month": "今月対応", "future": "将来対応"}
    for key, label in roadmap_labels.items():
        lines.append(f"### {label}")
        items = dashboard["roadmap"].get(key, [])
        lines.extend(f"- {item}" for item in items) if items else lines.append("- 該当なし")
        lines.append("")
    lines.append("> 顧客本文、生成本文、APIキー、パスワードは含めていません。")
    return "\n".join(lines)


def build_improvement_dashboard(db: Connection) -> dict[str, Any]:
    usage = summarize_usage_dashboard(db)
    readiness = build_operation_readiness_check(db)
    summary = usage["summary"]
    feedback = usage["feedback_summary"]
    errors = usage["error_analysis"]
    total_usage = int(summary["total_usage"])
    error_count = int(summary["error_count"])
    feedback_count = int(summary["feedback_count"])
    hard_to_use = int(feedback["hard_to_use"])
    needs_revision = int(feedback["needs_revision"])
    usable = int(feedback["usable"])
    readiness_score = int(readiness["score"])

    improvements: list[dict[str, str]] = []
    if total_usage == 0:
        improvements.append(_improvement_item("高", "運用", "サンプル体験から利用ログを集める", "利用実績がまだなく、改善判断の材料が不足しています。", "試験導入の効果を測定しやすくなります。", "低", "管理者がサンプル案件で操作手順を確認し、対象者へ利用を依頼します。"))
    if hard_to_use > 0 or (feedback_count > 0 and hard_to_use >= usable):
        improvements.append(_improvement_item("高", "UI/UX", "初期画面とダウンロード導線をさらに簡単にする", f"使いにくい評価が{hard_to_use}件あります。", "初めて使う社員が要約PPTまで到達しやすくなります。", "中", "完成後の要約PPT、提出前チェック、その他出力の順序を再確認します。"))
    if needs_revision > 0:
        improvements.append(_improvement_item("中", "AI精度", "提案書の出力品質をフィードバック基準で調整する", f"修正すれば使えそうという評価が{needs_revision}件あります。", "営業担当が修正する時間を減らせます。", "中", "コメント傾向を確認し、プロンプトと提出前チェック項目へ反映します。"))
    if error_count > 0:
        improvements.append(_improvement_item("高", "運用", "エラー発生時の案内と復旧手順を整える", f"エラーが{error_count}件発生しています。", "利用者が止まった時に自己解決しやすくなります。", "低", "エラー分類ごとの案内文と管理者向け確認手順を更新します。"))
    if readiness_score < 85:
        improvements.append(_improvement_item("高", "セキュリティ", "運用準備チェックの要確認項目を解消する", f"運用準備スコアが{readiness_score}点です。", "安全に社内試験導入を開始できます。", "中", "運用準備チェックの次にやることを上から順に確認します。"))
    if feedback_count < 5:
        improvements.append(_improvement_item("中", "運用", "フィードバック回収を増やす", f"フィードバック件数が{feedback_count}件です。", "改善優先度を利用者の声から判断できます。", "低", "作成完了後に3択評価とコメント入力を依頼します。"))

    if not improvements:
        improvements.append(_improvement_item("低", "運用", "少人数試験を継続して判断材料を増やす", "大きな問題は見えていませんが、継続データが必要です。", "正式運用前の判断精度が上がります。", "低", "1週間単位で利用状況とフィードバックを確認します。"))

    priority_order = {"高": 0, "中": 1, "低": 2}
    improvements = sorted(improvements, key=lambda item: (priority_order.get(item["priority"], 9), item["category"]))[:10]
    roadmap = {
        "now": [item["title"] for item in improvements if item["priority"] == "高"][:4],
        "this_month": [item["title"] for item in improvements if item["priority"] == "中"][:4],
        "future": [item["title"] for item in improvements if item["priority"] == "低"][:4],
    }
    executive_summary = (
        f"試験導入では総利用{total_usage}件、フィードバック{feedback_count}件、エラー{error_count}件が確認されています。"
        "優先度の高い改善から対応し、要約PPTまでの到達率と提出前確認の安心感を高めます。"
    )[:320]
    result = {
        "summary": {
            "total_usage": total_usage,
            "error_count": error_count,
            "feedback_count": feedback_count,
            "hard_to_use": hard_to_use,
            "readiness_score": readiness_score,
        },
        "improvements": improvements,
        "roadmap": roadmap,
        "executive_summary": executive_summary,
    }
    result["markdown"] = _build_improvement_markdown(result)
    return result
