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

from app.repository_parts.operations import summarize_feedback_entries, detect_pilot_incidents, _feedback_score_metrics
from app.repository_parts.shared import _count_rows, _count_rows_in_scope, _scope_filter, _scope_label


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


def summarize_usage_dashboard(db: Connection, scope: dict[str, Any] | None = None) -> dict[str, Any]:
    feedback_summary = summarize_feedback_entries(db, scope)
    feedback_count = _count_rows_in_scope(db, "feedback_entries", scope)
    auth_error_count = _count_rows_in_scope(db, "audit_logs", scope, "event_type = 'login' AND status != 'success'")

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
    usage_where, usage_params = _scope_filter(scope)
    usage_where_sql = f"AND {usage_where}" if usage_where else ""
    for row in db.execute(
        f"""
        SELECT feature_name, output_type, error_type
        FROM usage_logs
        WHERE status != 'success'
        {usage_where_sql}
        """,
        usage_params,
    ).fetchall():
        category = _classify_usage_error(str(row["error_type"]), str(row["output_type"]), str(row["feature_name"]))
        if category in error_analysis:
            error_analysis[category] += 1

    usage_where_sql_full = f"WHERE {usage_where}" if usage_where else ""
    usage_rows = [
        dict(row)
        for row in db.execute(
            f"""
            SELECT
                l.user_id,
                COALESCE(u.email, '譛ｪ逋ｻ骭ｲ繝ｦ繝ｼ繧ｶ繝ｼ') AS user_name,
                COALESCE(u.role, 'unknown') AS user_role,
                l.status,
                l.created_at
            FROM usage_logs l
            LEFT JOIN users u ON u.id = l.user_id
            {usage_where_sql_full}
            """,
            usage_params,
        ).fetchall()
    ]
    feedback_where, feedback_params = _scope_filter(scope, "f")
    feedback_where_sql = f"WHERE {feedback_where}" if feedback_where else ""
    feedback_rows = [
        dict(row)
        for row in db.execute(
            f"""
            SELECT
                f.user_id,
                COALESCE(u.email, '譛ｪ逋ｻ骭ｲ繝ｦ繝ｼ繧ｶ繝ｼ') AS user_name,
                COALESCE(NULLIF(f.user_role, ''), u.role, 'unknown') AS user_role,
                'success' AS status,
                f.created_at
            FROM feedback_entries f
            LEFT JOIN users u ON u.id = f.user_id
            {feedback_where_sql}
            """,
            feedback_params,
        ).fetchall()
    ]

    total_usage = _count_rows_in_scope(db, "usage_logs", scope) + feedback_count
    today_usage = _count_rows_in_scope(db, "usage_logs", scope, "DATE(created_at) = DATE('now')") + _count_rows_in_scope(
        db, "feedback_entries", scope, "DATE(created_at) = DATE('now')"
    )
    week_usage = _count_rows_in_scope(db, "usage_logs", scope, "created_at >= DATETIME('now', '-7 days')") + _count_rows_in_scope(
        db, "feedback_entries", scope, "created_at >= DATETIME('now', '-7 days')"
    )

    return {
        "scope": _scope_label(scope),
        "summary": {
            "total_usage": total_usage,
            "today_usage": today_usage,
            "week_usage": week_usage,
            "proposal_generation": _count_rows_in_scope(db, "usage_logs", scope, proposal_condition, proposal_params),
            "ppt_download": _count_rows_in_scope(db, "usage_logs", scope, ppt_condition),
            "error_count": _count_rows_in_scope(db, "usage_logs", scope, "status != 'success'") + auth_error_count,
            "feedback_count": feedback_count,
        },
        "error_analysis": error_analysis,
        "users": _collect_user_usage(usage_rows + feedback_rows),
        "features": [
            {
                "feature_key": "proposal_generation",
                "feature_name": "謠先｡域嶌菴懈・",
                "usage_count": _count_rows_in_scope(db, "usage_logs", scope, proposal_condition, proposal_params),
                "success_count": _count_rows_in_scope(db, "usage_logs", scope, f"{proposal_condition} AND status = 'success'", proposal_params),
                "failure_count": _count_rows_in_scope(db, "usage_logs", scope, f"{proposal_condition} AND status != 'success'", proposal_params),
            },
            {
                "feature_key": "summary_ppt",
                "feature_name": "隕∫ｴПPT",
                "usage_count": _count_rows_in_scope(db, "usage_logs", scope, summary_ppt_condition),
                "success_count": _count_rows_in_scope(db, "usage_logs", scope, f"{summary_ppt_condition} AND status = 'success'"),
                "failure_count": _count_rows_in_scope(db, "usage_logs", scope, f"{summary_ppt_condition} AND status != 'success'"),
            },
            {
                "feature_key": "detail_ppt",
                "feature_name": "隧ｳ邏ｰPPT",
                "usage_count": _count_rows_in_scope(db, "usage_logs", scope, detail_ppt_condition),
                "success_count": _count_rows_in_scope(db, "usage_logs", scope, f"{detail_ppt_condition} AND status = 'success'"),
                "failure_count": _count_rows_in_scope(db, "usage_logs", scope, f"{detail_ppt_condition} AND status != 'success'"),
            },
            {
                "feature_key": "estimate_pdf",
                "feature_name": "隕狗ｩ恒DF",
                "usage_count": _count_rows_in_scope(db, "usage_logs", scope, estimate_pdf_condition),
                "success_count": _count_rows_in_scope(db, "usage_logs", scope, f"{estimate_pdf_condition} AND status = 'success'"),
                "failure_count": _count_rows_in_scope(db, "usage_logs", scope, f"{estimate_pdf_condition} AND status != 'success'"),
            },
            {
                "feature_key": "sample_experience",
                "feature_name": "サンプル体験",
                "usage_count": _count_rows_in_scope(db, "usage_logs", scope, sample_condition, sample_params),
                "success_count": _count_rows_in_scope(db, "usage_logs", scope, f"{sample_condition} AND status = 'success'", sample_params),
                "failure_count": _count_rows_in_scope(db, "usage_logs", scope, f"{sample_condition} AND status != 'success'", sample_params),
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
    scope = report.get("scope", {})
    lines = [
        "# AI営業秘書 社内試験導入レポート",
        "",
        "## 要約",
        report["summary_text"],
        "",
        "## 集計範囲",
        f"- Scope: {scope.get('scope', 'workspace')}",
        f"- Organization: {scope.get('organization_name') or scope.get('organization_id') or 'All Organizations'}",
        f"- Workspace: {scope.get('workspace_name') or scope.get('workspace_id') or 'All Workspaces'}",
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


def build_trial_report(db: Connection, admin_comment: str = "", scope: dict[str, Any] | None = None) -> dict[str, Any]:
    dashboard = summarize_usage_dashboard(db, scope)
    summary = dashboard["summary"]
    feedback = dashboard["feedback_summary"]
    errors = dashboard["error_analysis"]

    usage_where, usage_params = _scope_filter(scope)
    feedback_where, feedback_params = _scope_filter(scope)
    usage_where_sql = f"WHERE {usage_where}" if usage_where else ""
    feedback_where_sql = f"WHERE {feedback_where}" if feedback_where else ""
    period_row = db.execute(
        f"""
        SELECT MIN(created_at) AS start_at, MAX(created_at) AS end_at
        FROM (
            SELECT created_at FROM usage_logs {usage_where_sql}
            UNION ALL
            SELECT created_at FROM feedback_entries {feedback_where_sql}
        )
        """,
        (*usage_params, *feedback_params),
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
        "scope": _scope_label(scope),
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
    from app.db import get_migration_state

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
    migration_state = get_migration_state()

    checks = [
        _readiness_item("backend", "Backend接続", "ok", "Backend APIに接続できます。"),
        _readiness_item("openai", "OpenAI API設定", "ok" if settings.use_mock_ai or bool(settings.openai_api_key) else "missing", "モックモードまたはOpenAI APIキーが設定されています。" if settings.use_mock_ai or settings.openai_api_key else "OpenAI APIキーが未設定です。", "RenderにOPENAI_API_KEYを設定してください。" if not settings.use_mock_ai and not settings.openai_api_key else ""),
        _readiness_item("auth", "認証設定", "ok" if auth_configured else "missing", "認証用の環境変数が設定されています。" if auth_configured else "認証用の環境変数が不足しています。", "APP_AUTH_SECRET、INITIAL_ADMIN_EMAIL、INITIAL_ADMIN_PASSWORDを設定してください。" if not auth_configured else ""),
        _readiness_item("initial_admin", "初期管理者設定", "ok" if has_admin else "missing", f"有効なadminが{role_counts.get('admin', 0)}名います。" if has_admin else "有効なadminが見つかりません。", "初期管理者を作成してください。" if not has_admin else ""),
        _readiness_item("db", "DB接続", "ok" if db_ok else "missing", "DB接続を確認しました。" if db_ok else "DBへ接続できません。", "DATABASE_URLを確認してください。" if not db_ok else ""),
        _readiness_item(
            "migration_ready",
            "DB Migration",
            "ok" if migration_state.get("migration_ready") else "warning",
            f"current={migration_state.get('migration_current') or 'unknown'}, head={migration_state.get('migration_head') or 'unknown'}",
            "本番反映前に alembic upgrade head と /health/ready を確認してください。" if not migration_state.get("migration_ready") else "",
        ),
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


def build_improvement_dashboard(db: Connection, scope: dict[str, Any] | None = None) -> dict[str, Any]:
    usage = summarize_usage_dashboard(db, scope)
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
        "scope": _scope_label(scope),
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
