import importlib.util
import os
from sqlite3 import Connection, Row
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
    return row_to_dict(db.execute("SELECT id, email, role, is_active, created_at, updated_at FROM users WHERE id = ?", (user_id,)).fetchone())


def list_users(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute("SELECT id, email, role, is_active, created_at, updated_at FROM users ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def create_user(db: Connection, email: str, password: str, role: str) -> dict[str, Any]:
    db.execute(
        "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
        (email.strip().lower(), hash_password(password), role),
    )
    user = db.execute("SELECT id, email, role, is_active, created_at, updated_at FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return dict(user)


def set_user_active(db: Connection, user_id: int, is_active: bool) -> dict[str, Any] | None:
    db.execute("UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (1 if is_active else 0, user_id))
    return get_user_by_id(db, user_id)


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
    project_name = name.strip() or "提案準備案件"
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
    if feature_name in {"提案書生成", "PowerPoint", "要約PowerPoint", "見積書PDF"}:
        create_audit_log(db, user_id, "generate", feature_name, "", status, f"output_type={output_type};error_type={error_type}")


def list_crm(db: Connection) -> dict[str, list[dict[str, Any]]]:
    customers = [dict(row) for row in db.execute("SELECT * FROM customers ORDER BY updated_at DESC LIMIT 100").fetchall()]
    projects = [
        dict(row)
        for row in db.execute(
            """
            SELECT p.*, c.company_name AS customer_name
            FROM projects p
            LEFT JOIN customers c ON c.id = p.customer_id
            ORDER BY p.updated_at DESC
            LIMIT 100
            """
        ).fetchall()
    ]
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


def _count_rows(db: Connection, table_name: str, where_clause: str = "", params: tuple[Any, ...] = ()) -> int:
    sql = f"SELECT COUNT(*) AS count FROM {table_name}"
    if where_clause:
        sql = f"{sql} WHERE {where_clause}"
    row = db.execute(sql, params).fetchone()
    return int(row["count"]) if row else 0


def _classify_usage_error(error_type: str, output_type: str, feature_name: str) -> str:
    text = f"{error_type} {output_type} {feature_name}".lower()
    if any(token in text for token in ("401", "403", "auth", "login", "unauthorized", "認証", "ログイン", "隱崎", "繝ｭ繧ｰ")):
        return "auth_error"
    if any(token in text for token in ("429", "rate", "quota", "openai", "api制限", "api蛻", "制限", "上限")):
        return "api_limit"
    if any(token in text for token in ("failed to fetch", "network", "cors", "timeout", "backend", "render", "通信", "接続", "騾壻", "謗･邯")):
        return "backend_unreachable"
    if any(token in text for token in ("400", "422", "validation", "min_length", "入力", "不足", "蜈･蜉", "荳崎")):
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
                "user_name": row.get("user_name") or "未登録ユーザー",
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
    proposal_params = ("%提案%",)
    summary_ppt_condition = "output_type = 'summary-pptx'"
    detail_ppt_condition = "output_type = 'pptx'"
    ppt_condition = "output_type IN ('pptx', 'summary-pptx')"
    estimate_pdf_condition = "output_type = 'estimate-pdf'"
    sample_condition = "(output_type = 'sample' OR feature_name LIKE ?)"
    sample_params = ("%サンプル%",)

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
                COALESCE(u.email, '未登録ユーザー') AS user_name,
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
                COALESCE(u.email, '未登録ユーザー') AS user_name,
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
                "feature_name": "提案書作成",
                "usage_count": _count_rows(db, "usage_logs", proposal_condition, proposal_params),
                "success_count": _count_rows(db, "usage_logs", f"{proposal_condition} AND status = 'success'", proposal_params),
                "failure_count": _count_rows(db, "usage_logs", f"{proposal_condition} AND status != 'success'", proposal_params),
            },
            {
                "feature_key": "summary_ppt",
                "feature_name": "要約PPT",
                "usage_count": _count_rows(db, "usage_logs", summary_ppt_condition),
                "success_count": _count_rows(db, "usage_logs", f"{summary_ppt_condition} AND status = 'success'"),
                "failure_count": _count_rows(db, "usage_logs", f"{summary_ppt_condition} AND status != 'success'"),
            },
            {
                "feature_key": "detail_ppt",
                "feature_name": "詳細PPT",
                "usage_count": _count_rows(db, "usage_logs", detail_ppt_condition),
                "success_count": _count_rows(db, "usage_logs", f"{detail_ppt_condition} AND status = 'success'"),
                "failure_count": _count_rows(db, "usage_logs", f"{detail_ppt_condition} AND status != 'success'"),
            },
            {
                "feature_key": "estimate_pdf",
                "feature_name": "見積PDF",
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
                "feature_name": "フィードバック送信",
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
    return start_label if start_label == end_label else f"{start_label}〜{end_label}"


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
        "> 注意: 本レポートには顧客本文、生成本文、APIキー、個人情報は含めていません。",
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
        good_points.append("提案書作成機能が実際に利用され、初稿作成の時間短縮に寄与しています。")
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
        issues.append("「修正すれば使えそう」の評価があり、出力内容の微調整や説明文の改善余地があります。")
    if hard_to_use > 0:
        issues.append("「使いにくい」の評価があるため、初期画面とダウンロード導線を重点的に確認します。")
    if errors["api_limit"] > 0:
        issues.append("API上限に関する失敗があるため、利用時間帯やモックモード案内の整備が必要です。")
    if errors["backend_unreachable"] > 0:
        issues.append("Backend接続エラーがあるため、Renderの起動状態とVercel側API URLを確認します。")
    if not issues:
        issues.append("現時点で大きな阻害要因は目立っていません。継続利用で追加データを確認します。")

    next_actions: list[str] = []
    if feedback_count < 5:
        next_actions.append("試験利用者を数名追加し、提案書作成後のフィードバックを集めます。")
    if error_count > 0:
        next_actions.append("エラー種別ごとの再現条件を確認し、利用者向けの案内文と復旧手順を整えます。")
    next_actions.append("提出前チェックリストの運用を徹底し、AI作成内容を人が確認するルールを周知します。")
    next_actions.append("要約PPTを中心に、研修発表・営業共有で使いやすい出力品質を確認します。")

    if total_usage == 0:
        rollout_opinion = "現時点では利用実績がないため、まずは少人数でサンプル体験を行う段階です。"
    elif hard_to_use > usable or (total_usage > 0 and error_count / max(total_usage, 1) >= 0.25):
        rollout_opinion = "全社展開前に、エラー対策と使いにくさの解消を優先した限定試験の継続が妥当です。"
    elif feedback_count >= 3 and usable >= needs_revision + hard_to_use:
        rollout_opinion = "小規模部門での継続利用または対象部署を広げた試験導入を検討できます。"
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
    lines.append("> 注意: 本チェックには顧客本文、生成本文、APIキー、パスワードは含めていません。")
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
    render_detected = bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID") or os.getenv("RENDER_EXTERNAL_URL"))
    sqlite_default = settings.database_url == "sqlite:///app.db"
    pptx_available = importlib.util.find_spec("pptx") is not None
    reportlab_available = importlib.util.find_spec("reportlab") is not None
    frontend_openai_env = [key for key in os.environ if key.startswith("NEXT_PUBLIC_") and "OPENAI" in key.upper()]

    checks = [
        _readiness_item("backend", "Backend接続", "ok", "管理者APIへ接続できています。"),
        _readiness_item(
            "openai",
            "OpenAI API設定",
            "ok" if settings.openai_api_key else ("warning" if settings.use_mock_ai else "missing"),
            "OPENAI_API_KEYが設定されています。" if settings.openai_api_key else ("モックモードで動作中です。" if settings.use_mock_ai else "OPENAI_API_KEYが未設定です。"),
            "" if settings.openai_api_key else "RenderのEnvironment VariablesでOPENAI_API_KEYとAPI上限を確認してください。",
        ),
        _readiness_item(
            "auth",
            "認証設定",
            "ok" if settings.app_auth_secret else "missing",
            "認証用シークレットが設定されています。" if settings.app_auth_secret else "APP_AUTH_SECRETまたはAPP_ACCESS_PASSWORDが未設定です。",
            "" if settings.app_auth_secret else "APP_AUTH_SECRETをRenderに設定してください。",
        ),
        _readiness_item(
            "initial_admin",
            "初期管理者設定",
            "ok" if settings.initial_admin_email and settings.initial_admin_password and has_admin else ("warning" if has_admin else "missing"),
            "初期管理者が有効です。" if has_admin else "有効なadminユーザーが確認できません。",
            "" if has_admin else "INITIAL_ADMIN_EMAILとINITIAL_ADMIN_PASSWORDを設定し、Backendを再起動してください。",
        ),
        _readiness_item(
            "db",
            "DB接続",
            "ok" if db_ok else "missing",
            f"DBへ接続できています。ユーザー登録数は{users_count}件です。" if db_ok and users_available else "DB接続またはusersテーブルを確認できません。",
            "" if db_ok else "DATABASE_URLを確認し、RenderでDBファイルまたは永続化設定を確認してください。",
        ),
        _readiness_item(
            "vercel_api_url",
            "Vercel API URL設定",
            "ok" if has_vercel_origin else "warning",
            "Vercelからの接続を許可するCORS設定があります。" if has_vercel_origin else "CORS_ORIGINSにVercel URLが見当たりません。",
            "" if has_vercel_origin else "VercelのNEXT_PUBLIC_API_URLとRenderのCORS_ORIGINSを確認してください。",
        ),
        _readiness_item(
            "render_env",
            "Render環境変数",
            "ok" if render_detected and settings.app_auth_secret and (settings.openai_api_key or settings.use_mock_ai) else "warning",
            "Render環境で主要な環境変数を確認できます。" if render_detected else "ローカルまたはRender検出外の環境です。",
            "" if render_detected else "Render上でOPENAI_API_KEY、APP_AUTH_SECRET、INITIAL_ADMIN_EMAIL、DATABASE_URLを確認してください。",
        ),
        _readiness_item(
            "pptx",
            "PPTX生成",
            "ok" if pptx_available else "missing",
            "python-pptxを利用できます。" if pptx_available else "python-pptxを確認できません。",
            "" if pptx_available else "backend/requirements.txtとRenderのビルドログを確認してください。",
        ),
        _readiness_item(
            "pdf",
            "PDF生成",
            "ok" if reportlab_available else "missing",
            "reportlabを利用できます。" if reportlab_available else "reportlabを確認できません。",
            "" if reportlab_available else "backend/requirements.txtにreportlabが入っているか確認してください。",
        ),
        _readiness_item(
            "permissions",
            "権限管理",
            "ok" if has_admin and has_member_or_viewer else ("warning" if has_admin else "missing"),
            "admin/member/viewerの運用準備ができています。" if has_admin and has_member_or_viewer else "adminはありますが、member/viewerの確認が未完了です。",
            "" if has_admin and has_member_or_viewer else "admin/member/viewerの権限確認をしてください。",
        ),
        _readiness_item(
            "audit_logs",
            "監査ログ",
            "ok" if audit_available else "missing",
            f"監査ログテーブルを確認しました。現在{audit_count}件です。" if audit_available else "監査ログテーブルを確認できません。",
            "" if audit_available else "DB初期化とaudit_logsテーブルを確認してください。",
        ),
        _readiness_item(
            "usage_logs",
            "利用ログ",
            "ok" if usage_available else "missing",
            f"利用ログテーブルを確認しました。現在{usage_count}件です。" if usage_available else "利用ログテーブルを確認できません。",
            "" if usage_available else "DB初期化とusage_logsテーブルを確認してください。",
        ),
        _readiness_item(
            "feedback",
            "フィードバック収集",
            "ok" if feedback_available else "missing",
            f"フィードバック収集を利用できます。現在{feedback_count}件です。" if feedback_available else "フィードバックテーブルを確認できません。",
            "" if feedback_available else "DB初期化とfeedback_entriesテーブルを確認してください。",
        ),
        _readiness_item(
            "trial_report",
            "試験導入レポート作成",
            "ok",
            "利用状況・エラー・フィードバックからレポートを作成できます。",
        ),
    ]

    security_checks = [
        _readiness_item(
            "frontend_api_key",
            "APIキーをFrontendに表示していない",
            "ok" if not frontend_openai_env else "warning",
            "公開Frontend向けのOpenAI環境変数は検出されていません。" if not frontend_openai_env else "NEXT_PUBLICにOpenAI関連の環境変数があります。",
            "" if not frontend_openai_env else "VercelのEnvironment VariablesからNEXT_PUBLIC_OPENAI系の値を削除してください。",
        ),
        _readiness_item("password_logs", "パスワードをログ保存していない", "ok", "利用ログ・監査ログにパスワード本文を保存しない設計です。"),
        _readiness_item("input_body_logs", "入力本文全文を利用ログに保存していない", "ok", "利用ログは入力文字数、機能名、出力種別、成功/失敗のみ保存します。"),
        _readiness_item("output_body_audit_logs", "生成本文全文を監査ログに保存していない", "ok", "監査ログはイベント種別と短いメタ情報のみ保存します。"),
        _readiness_item("admin_menu", "admin以外に管理者メニューを表示していない", "ok", "Frontend表示とBackend APIの両方でadmin権限を確認します。"),
    ]

    all_items = checks + security_checks
    score = _score_readiness_items(all_items)
    if score >= 85:
        score_label = "社内試験導入可能。ただし要確認項目は案内前に確認してください。"
    elif score >= 70:
        score_label = "限定的な試験導入は可能です。未設定・要確認項目を先に整理してください。"
    else:
        score_label = "社内案内前に設定・接続・権限の確認が必要です。"

    next_actions = []
    for item in all_items:
        if item["status"] != "ok" and item["next_action"] and item["next_action"] not in next_actions:
            next_actions.append(item["next_action"])
    if sqlite_default and not render_detected:
        next_actions.append("Renderへデプロイする場合は、SQLite永続化または将来のPostgreSQL移行方針を確認してください。")

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
    lines.extend(["## 改善ロードマップ"])
    roadmap_labels = {"now": "今すぐ対応", "this_month": "今月対応", "future": "将来対応"}
    for key, label in roadmap_labels.items():
        lines.append(f"### {label}")
        items = dashboard["roadmap"][key]
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- 現時点で該当項目はありません。")
        lines.append("")
    lines.append("> 注意: 本ダッシュボードには顧客本文、生成本文、APIキー、パスワードは含めていません。")
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
        improvements.append(
            _improvement_item(
                "高",
                "運用",
                "サンプル体験から利用ログを集める",
                "利用ログがまだなく、改善判断に必要な利用実績が不足しています。",
                "試験導入の効果とつまずき箇所を早く把握できます。",
                "低",
                "管理者がサンプル案件を使って操作手順を確認し、2〜3名に試験利用を依頼します。",
            )
        )

    if hard_to_use > 0 or (feedback_count > 0 and hard_to_use >= usable):
        improvements.append(
            _improvement_item(
                "高",
                "UI/UX",
                "初期画面とダウンロード導線をさらに簡単にする",
                f"「使いにくい」評価が{hard_to_use}件あります。",
                "初めて使う社員の迷いを減らし、要約PPTダウンロードまで到達しやすくなります。",
                "中",
                "完了後画面で要約PPT、提出前チェック、その他出力の順に見えるか確認します。",
            )
        )

    if needs_revision > 0:
        improvements.append(
            _improvement_item(
                "中",
                "AI精度",
                "提案書の出力品質をフィードバック基準で調整する",
                f"「修正すれば使えそう」評価が{needs_revision}件あります。",
                "営業担当が修正する時間を減らし、提出前レビューの負担を下げられます。",
                "中",
                "フィードバックの傾向を確認し、プロンプトと提出前チェック項目に反映します。",
            )
        )

    if error_count > 0:
        top_error_key = max(errors, key=lambda key: int(errors[key]))
        error_labels = {
            "api_limit": "API上限",
            "backend_unreachable": "Backend未接続",
            "input_missing": "入力不足",
            "ppt_generation_failed": "PPT生成失敗",
            "auth_error": "認証エラー",
        }
        improvements.append(
            _improvement_item(
                "高",
                "運用",
                "エラー発生時の案内と復旧手順を整える",
                f"エラーが{error_count}件発生しています。最多分類は{error_labels.get(top_error_key, top_error_key)}です。",
                "利用者が止まった時に自己解決しやすくなり、管理者への問い合わせを減らせます。",
                "低",
                "エラー分類ごとの対処文を確認し、Backend接続とAPI上限を重点的に点検します。",
            )
        )

    if errors.get("ppt_generation_failed", 0) > 0:
        improvements.append(
            _improvement_item(
                "高",
                "パフォーマンス",
                "PPT生成処理の失敗条件を確認する",
                f"PPT生成失敗が{errors['ppt_generation_failed']}件あります。",
                "営業資料のダウンロード失敗を減らし、実務利用の信頼性が上がります。",
                "中",
                "失敗時の入力サイズ、Renderログ、python-pptx依存関係を確認します。",
            )
        )

    if errors.get("api_limit", 0) > 0:
        improvements.append(
            _improvement_item(
                "中",
                "パフォーマンス",
                "OpenAI API上限とモックモード案内を整える",
                f"API上限関連の失敗が{errors['api_limit']}件あります。",
                "研修中や試験導入中にAI作成が止まるリスクを下げられます。",
                "低",
                "利用時間帯、API利用上限、USE_MOCK_AIでの代替確認手順を整理します。",
            )
        )

    if readiness_score < 85:
        missing_or_warning = [item for item in [*readiness["checks"], *readiness["security_checks"]] if item["status"] != "ok"]
        improvements.append(
            _improvement_item(
                "高",
                "セキュリティ",
                "運用準備チェックの要確認項目を解消する",
                f"運用準備スコアが{readiness_score}点で、要確認・未設定項目が{len(missing_or_warning)}件あります。",
                "社内案内前の設定漏れや権限ミスを減らし、安心して試験導入できます。",
                "中",
                "運用準備チェックの「次にやること」を上から順に確認します。",
            )
        )

    if feedback_count < 5:
        improvements.append(
            _improvement_item(
                "中",
                "運用",
                "試験利用後のフィードバック回収を増やす",
                f"フィードバック件数が{feedback_count}件で、判断材料がまだ少ない状態です。",
                "改善優先度を利用者の実感に基づいて判断できるようになります。",
                "低",
                "提案書作成後に3択評価とコメント入力を依頼する案内を追加します。",
            )
        )

    if summary["proposal_generation"] > 0 and summary["ppt_download"] == 0:
        improvements.append(
            _improvement_item(
                "中",
                "UI/UX",
                "作成完了後の要約PPTダウンロードを目立たせる",
                "提案書作成はされていますが、PPTダウンロードが確認できません。",
                "作成結果を営業資料として持ち出す流れが分かりやすくなります。",
                "低",
                "生成完了画面で要約PPTボタンが最初に見えるか確認します。",
            )
        )

    if not any(item["category"] == "連携" for item in improvements):
        improvements.append(
            _improvement_item(
                "低",
                "連携",
                "将来のGoogle Drive・Slack連携範囲を整理する",
                "現時点では外部連携は企画表示が中心で、実運用前に連携対象の優先順位を決める必要があります。",
                "過去提案書や社内ナレッジを安全に活用する準備ができます。",
                "高",
                "機密情報の扱いを確認したうえで、最初に連携するデータ元を1つに絞ります。",
            )
        )

    if not improvements:
        improvements.append(
            _improvement_item(
                "低",
                "運用",
                "少人数試験を継続して判断材料を増やす",
                "大きな問題は見えていませんが、継続利用データがあるほど改善判断が正確になります。",
                "本格展開前の判断精度が上がります。",
                "低",
                "1週間単位で利用状況とフィードバックを確認します。",
            )
        )

    priority_order = {"高": 0, "中": 1, "低": 2}
    improvements = sorted(improvements, key=lambda item: (priority_order.get(item["priority"], 9), item["category"]))[:10]

    roadmap = {
        "now": [item["title"] for item in improvements if item["priority"] == "高"][:4],
        "this_month": [item["title"] for item in improvements if item["priority"] == "中"][:4],
        "future": [item["title"] for item in improvements if item["priority"] == "低"][:4],
    }

    learned = (
        f"試験導入では総利用{total_usage}件、フィードバック{feedback_count}件が確認され、"
        f"使えそう評価は{usable}件でした。"
    )
    plan = (
        f"今後は優先度高の改善として「{roadmap['now'][0]}」を中心に、"
        "UI/UX、運用、セキュリティ面を順に整備します。"
        if roadmap["now"]
        else "今後はフィードバック回収と利用ログの蓄積を進め、改善判断の精度を上げます。"
    )
    next_action = (
        "次回は管理者が運用準備チェックとエラー分類を確認し、社内メンバーへ使い方と提出前確認ルールを案内します。"
    )
    executive_summary = f"{learned}{plan}{next_action}"[:320]

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
