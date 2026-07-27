import csv
from io import StringIO
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.auth import require_roles
from app.db import get_db
from app.models import BusinessImprovementReportRequest, TrialReportRequest, UsageLogCreateRequest
from app.repositories import (
    build_operation_readiness_check,
    build_improvement_dashboard,
    build_trial_report,
    create_audit_log,
    create_history_log,
    list_creation_history,
    list_audit_logs,
    list_usage_logs_scoped,
    summarize_usage_dashboard,
)
from app.scope_policy import ScopeName, resolve_scope

router = APIRouter(prefix="/api/logs", tags=["logs"])


def _scope_query(default: ScopeName = "workspace") -> Query:
    return Query(default, pattern="^(workspace|organization|system)$")


@router.get("")
async def get_logs(
    user: dict = Depends(require_roles("admin", "member", "viewer")),
    scope: str = _scope_query(),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        return {"logs": list_usage_logs_scoped(db, 100, resolved_scope), "scope": resolved_scope.response_meta}


@router.get("/audit")
async def get_audit_logs(
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = _scope_query("organization"),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        return {"logs": list_audit_logs(db, 200, resolved_scope), "scope": resolved_scope.response_meta}


@router.get("/usage-dashboard")
async def get_usage_dashboard(
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = _scope_query(),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        return {"dashboard": summarize_usage_dashboard(db, resolved_scope)}


@router.get("/creation-history")
async def get_creation_history(
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
    q: str = "",
    status: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = 100,
    include_demo: bool = Query(False),
) -> dict:
    with get_db() as db:
        items = list_creation_history(
            db,
            user,
            limit=limit,
            query=q,
            status=status,
            date_from=date_from,
            date_to=date_to,
            include_demo=include_demo,
        )
        create_audit_log(db, int(user["id"]), "view_creation_history", "proposal_histories", "", "success", "sanitized=true")
    return {"items": items}


@router.get("/creation-history.csv")
async def download_creation_history_csv(
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
    q: str = "",
    status: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = 500,
    include_demo: bool = Query(False),
) -> Response:
    with get_db() as db:
        items = list_creation_history(
            db,
            user,
            limit=limit,
            query=q,
            status=status,
            date_from=date_from,
            date_to=date_to,
            include_demo=include_demo,
        )
        create_audit_log(db, int(user["id"]), "download_creation_history_csv", "proposal_histories", "", "success", "sanitized=true")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "案件名",
            "データ種別",
            "生成日時",
            "生成者",
            "提案書生成時間(ms)",
            "PowerPoint生成時間(ms)",
            "Beautiful.ai生成時間(ms)",
            "PDF生成時間(ms)",
            "合計生成時間(ms)",
            "出力形式",
            "ステータス",
        ]
    )
    for item in items:
        writer.writerow(
            [
                _csv_safe(item.get("project_name", "")),
                "デモデータ" if int(item.get("is_demo") or 0) else "実データ",
                item.get("created_at", ""),
                _csv_safe(item.get("created_by_name") or item.get("created_by_email") or ""),
                int(item.get("proposal_generation_duration_ms") or 0),
                int(item.get("powerpoint_generation_duration_ms") or 0),
                int(item.get("beautiful_ai_generation_duration_ms") or 0),
                int(item.get("pdf_generation_duration_ms") or 0),
                int(item.get("total_generation_duration_ms") or 0),
                item.get("output_type", ""),
                item.get("status", ""),
            ]
        )
    return Response(
        content=f"\ufeff{output.getvalue()}",
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=proposal-generation-history.csv"},
    )


@router.get("/business-improvement-reports")
async def get_business_improvement_reports(
    include_demo: bool = Query(False),
    user: dict = Depends(require_roles("admin", "manager", "member")),
) -> dict:
    with get_db() as db:
        items = _list_business_improvement_reports(db, user, include_demo=include_demo)
        summary = _business_improvement_summary(items)
        create_audit_log(db, int(user["id"]), "view_business_improvement_reports", "business_improvement_reports", "", "success", "sanitized=true")
    return {"items": items, "summary": summary, "include_demo": include_demo}


@router.post("/business-improvement-reports")
async def create_business_improvement_report(
    payload: BusinessImprovementReportRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
) -> dict:
    with get_db() as db:
        report = _insert_business_improvement_report(db, user, payload.dict())
        create_audit_log(db, int(user["id"]), "create_business_improvement_report", "business_improvement_reports", str(report.get("id") or ""), "success", "sanitized=true")
    return {"report": report}


@router.post("/business-improvement-reports/demo-data")
async def create_business_improvement_demo_data(user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    demo_items = [
        {
            "project_name": "AI-OCR請求書処理",
            "before_minutes": 120,
            "after_minutes": 24,
            "ai_input_minutes": 8,
            "ai_wait_minutes": 24,
            "revision_minutes": 12,
            "review_minutes": 10,
            "quality_score": 4,
            "mistake_count": 1,
            "comment": "請求書確認と提案書たたき台作成の時間を大きく短縮。",
            "is_demo": True,
            "history": ("提案書生成", "markdown+pptx-data", 28600, 0, 0, 0),
        },
        {
            "project_name": "SaaS提案書作成",
            "before_minutes": 95,
            "after_minutes": 20,
            "ai_input_minutes": 8,
            "ai_wait_minutes": 20,
            "revision_minutes": 14,
            "review_minutes": 8,
            "quality_score": 5,
            "mistake_count": 0,
            "comment": "構成作成と見積整理が標準化され、初稿作成が早くなった。",
            "is_demo": True,
            "history": ("PowerPoint生成", "pptx", 0, 18400, 0, 0),
        },
        {
            "project_name": "Beautiful.ai資料化",
            "before_minutes": 150,
            "after_minutes": 32,
            "ai_input_minutes": 13,
            "ai_wait_minutes": 32,
            "revision_minutes": 18,
            "review_minutes": 15,
            "quality_score": 4,
            "mistake_count": 1,
            "comment": "デザイン調整の初期作業を削減し、確認時間を短縮。",
            "is_demo": True,
            "history": ("Beautiful.ai生成", "beautiful-ai", 0, 0, 42200, 0),
        },
        {
            "project_name": "見積PDF作成",
            "before_minutes": 60,
            "after_minutes": 10,
            "ai_input_minutes": 6,
            "ai_wait_minutes": 10,
            "revision_minutes": 8,
            "review_minutes": 6,
            "quality_score": 4,
            "mistake_count": 0,
            "comment": "提出用PDFまでの転記作業を減らし、ミス確認が楽になった。",
            "is_demo": True,
            "history": ("見積PDF生成", "estimate-pdf", 0, 0, 0, 12600),
        },
    ]
    reports: list[dict] = []
    history_created = 0
    with get_db() as db:
        for item in demo_items:
            report = _insert_business_improvement_report(db, user, item)
            reports.append(report)
            feature_name, output_type, proposal_ms, powerpoint_ms, beautiful_ms, pdf_ms = item["history"]
            create_history_log(
                db,
                int(user["id"]),
                None,
                None,
                feature_name,
                120,
                output_type,
                "success",
                "",
                project_name=item["project_name"],
                proposal_generation_duration_ms=proposal_ms,
                powerpoint_generation_duration_ms=powerpoint_ms,
                beautiful_ai_generation_duration_ms=beautiful_ms,
                pdf_generation_duration_ms=pdf_ms,
                is_demo=True,
            )
            history_created += 1
        summary = _business_improvement_summary(_list_business_improvement_reports(db, user, include_demo=True))
        create_audit_log(db, int(user["id"]), "create_business_improvement_demo_data", "business_improvement_reports", "", "success", "sanitized=true")
    return {"created": len(reports), "history_created": history_created, "items": reports, "summary": summary}


@router.get("/business-improvement-reports.csv")
async def download_business_improvement_reports_csv(
    include_demo: bool = Query(False),
    user: dict = Depends(require_roles("admin", "manager", "member")),
) -> Response:
    with get_db() as db:
        items = _list_business_improvement_reports(db, user, include_demo=include_demo)
        create_audit_log(db, int(user["id"]), "download_business_improvement_reports_csv", "business_improvement_reports", "", "success", "sanitized=true")

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["測定日", "案件名", "データ種別", "使用前時間", "AI入力時間", "AI処理待ち時間", "確認時間", "修正時間", "使用後合計時間", "短縮時間", "短縮率", "品質", "ミス件数", "コメント"])
    for item in items:
        writer.writerow(
            [
                item.get("created_at", ""),
                _csv_safe(item.get("project_name", "")),
                "デモデータ" if int(item.get("is_demo") or 0) else "実データ",
                item.get("before_minutes", 0),
                item.get("ai_input_minutes", 0),
                item.get("ai_wait_minutes", 0),
                item.get("review_minutes", 0),
                item.get("revision_minutes", 0),
                item.get("total_after_minutes", 0),
                item.get("saved_minutes", 0),
                item.get("reduction_rate", 0),
                item.get("quality_score", 0),
                item.get("mistake_count", 0),
                _csv_safe(item.get("comment", "")),
            ]
        )
    return Response(
        content=f"\ufeff{output.getvalue()}",
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=business-improvement-report.csv"},
    )


@router.get("/usage-dashboard.csv")
async def download_usage_dashboard_csv(
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = _scope_query(),
) -> Response:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        dashboard = summarize_usage_dashboard(db, resolved_scope)

    output = StringIO()
    writer = csv.writer(output)
    scope_info = dashboard.get("scope", {})

    writer.writerow(["AI営業秘書 利用状況ダッシュボード"])
    writer.writerow(["集計範囲", scope_info.get("scope", "workspace")])
    writer.writerow(["Organization", scope_info.get("organization_name", "")])
    writer.writerow(["Workspace", scope_info.get("workspace_name", "")])
    writer.writerow([])

    writer.writerow(["指標", "件数"])
    summary_labels = {
        "total_usage": "総利用回数",
        "today_usage": "今日の利用回数",
        "week_usage": "今週の利用回数",
        "proposal_generation": "提案書作成回数",
        "ppt_download": "PPTダウンロード回数",
        "error_count": "エラー発生回数",
        "feedback_count": "フィードバック件数",
    }
    for key, label in summary_labels.items():
        writer.writerow([label, dashboard["summary"].get(key, 0)])

    writer.writerow([])
    writer.writerow(["エラー分類", "件数"])
    error_labels = {
        "api_limit": "API上限",
        "backend_unreachable": "Backend未接続",
        "input_missing": "入力不足",
        "ppt_generation_failed": "PPT生成失敗",
        "auth_error": "認証エラー",
    }
    for key, label in error_labels.items():
        writer.writerow([label, dashboard["error_analysis"].get(key, 0)])

    writer.writerow([])
    writer.writerow(["機能別利用", "利用回数", "成功", "失敗"])
    for item in dashboard["features"]:
        writer.writerow([item["feature_name"], item["usage_count"], item["success_count"], item["failure_count"]])

    writer.writerow([])
    writer.writerow(["利用者別集計", "ロール", "利用回数", "最終利用日時", "成功", "失敗"])
    for item in dashboard["users"]:
        writer.writerow(
            [
                item["user_name"],
                item["user_role"],
                item["usage_count"],
                item["last_used_at"],
                item["success_count"],
                item["failure_count"],
            ]
        )

    writer.writerow([])
    writer.writerow(["フィードバック集計", "件数"])
    feedback_labels = {
        "usable": "使えそう",
        "needs_revision": "修正すれば使えそう",
        "hard_to_use": "使いにくい",
        "comments": "コメント件数",
    }
    for key, label in feedback_labels.items():
        writer.writerow([label, dashboard["feedback_summary"].get(key, 0)])

    file_scope = scope_info.get("scope", "workspace")
    return Response(
        content=f"\ufeff{output.getvalue()}",
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=ai-sales-secretary-usage-{file_scope}.csv"},
    )


@router.post("/trial-report")
async def create_trial_report(
    payload: TrialReportRequest,
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = _scope_query(),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        report = build_trial_report(db, payload.admin_comment, resolved_scope)
        create_audit_log(
            db,
            int(user["id"]),
            "generate",
            "trial_report",
            "",
            "success",
            f"sanitized=true;scope={resolved_scope.scope}",
        )
    return {"report": report}


@router.get("/operation-readiness")
async def get_operation_readiness(user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        readiness = build_operation_readiness_check(db)
        create_audit_log(db, int(user["id"]), "generate", "operation_readiness", "", "success", "sanitized=true")
    return {"readiness": readiness}


@router.get("/improvement-dashboard")
async def get_improvement_dashboard(
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = _scope_query(),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        dashboard = build_improvement_dashboard(db, resolved_scope)
        create_audit_log(
            db,
            int(user["id"]),
            "generate",
            "improvement_dashboard",
            "",
            "success",
            f"sanitized=true;scope={resolved_scope.scope}",
        )
    return {"dashboard": dashboard}


def _user_context(db, user: dict) -> tuple[int, int]:
    row = db.execute(
        "SELECT current_organization_id, current_workspace_id FROM users WHERE id = ?",
        (int(user["id"]),),
    ).fetchone()
    if not row:
        return 1, 1
    return int(row["current_organization_id"] or 1), int(row["current_workspace_id"] or 1)


def _get_business_improvement_report(db, report_id: int) -> dict:
    row = db.execute(
        """
        SELECT
            r.*,
            COALESCE(u.display_name, '') AS created_by_name,
            COALESCE(u.email, '') AS created_by_email
        FROM business_improvement_reports r
        LEFT JOIN users u ON u.id = r.user_id
        WHERE r.id = ?
        """,
        (report_id,),
    ).fetchone()
    return dict(row) if row else {}


def _csv_safe(value: object) -> object:
    if not isinstance(value, str):
        return value
    stripped = value.lstrip()
    if stripped.startswith(("=", "+", "-", "@", "\t", "\r", "\n")):
        return f"'{value}"
    return value


def _insert_business_improvement_report(db, user: dict, payload: dict[str, Any]) -> dict:
    organization_id, workspace_id = _user_context(db, user)
    project_id = payload.get("project_id")
    if project_id:
        project = db.execute(
            """
            SELECT id
            FROM projects
            WHERE id = ? AND organization_id = ? AND workspace_id = ?
            """,
            (int(project_id), organization_id, workspace_id),
        ).fetchone()
        if not project:
            raise HTTPException(status_code=400, detail="存在しない案件、または現在のWorkspaceで参照できない案件です。")

    before_minutes = float(payload.get("before_minutes") or 0)
    legacy_after_minutes = float(payload.get("after_minutes") or 0)
    ai_input_minutes = float(payload.get("ai_input_minutes") or 0)
    ai_wait_minutes = float(payload.get("ai_wait_minutes") if payload.get("ai_wait_minutes") is not None else legacy_after_minutes)
    has_split_after_minutes = ai_input_minutes > 0 or ai_wait_minutes > 0
    after_minutes = ai_wait_minutes if has_split_after_minutes else legacy_after_minutes
    revision_minutes = float(payload.get("revision_minutes") or 0)
    review_minutes = float(payload.get("review_minutes") or 0)
    quality_score = int(payload.get("quality_score") or 1)
    mistake_count = int(payload.get("mistake_count") or 0)
    total_after_minutes = ai_input_minutes + ai_wait_minutes + revision_minutes + review_minutes if has_split_after_minutes else after_minutes + revision_minutes + review_minutes
    if before_minutes <= 0:
        raise HTTPException(status_code=400, detail="使用前時間は0より大きい値を入力してください。")
    if total_after_minutes < 0 or total_after_minutes > 10080:
        raise HTTPException(status_code=400, detail="使用後合計時間が大きすぎます。入力値を確認してください。")
    if quality_score < 1 or quality_score > 5:
        raise HTTPException(status_code=400, detail="品質は1〜5で入力してください。")
    if mistake_count < 0:
        raise HTTPException(status_code=400, detail="ミス件数は0以上で入力してください。")
    saved_minutes = round(before_minutes - total_after_minutes, 1)
    reduction_rate = round((saved_minutes / before_minutes) * 100, 1)
    cursor = db.execute(
        """
        INSERT INTO business_improvement_reports
        (
            user_id,
            project_id,
            project_name,
            before_minutes,
            after_minutes,
            ai_input_minutes,
            ai_wait_minutes,
            revision_minutes,
            review_minutes,
            total_after_minutes,
            saved_minutes,
            reduction_rate,
            quality_score,
            mistake_count,
            comment,
            is_demo,
            organization_id,
            workspace_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(user["id"]),
            project_id,
            str(payload.get("project_name") or "")[:200],
            before_minutes,
            after_minutes,
            ai_input_minutes,
            ai_wait_minutes,
            revision_minutes,
            review_minutes,
            total_after_minutes,
            saved_minutes,
            reduction_rate,
            quality_score,
            mistake_count,
            str(payload.get("comment") or "")[:2000],
            1 if bool(payload.get("is_demo")) else 0,
            organization_id,
            workspace_id,
        ),
    )
    return _get_business_improvement_report(db, int(cursor.lastrowid))


def _list_business_improvement_reports(db, user: dict, *, include_demo: bool = False) -> list[dict]:
    organization_id, workspace_id = _user_context(db, user)
    role = str(user.get("role") or "")
    clauses = ["r.organization_id = ?", "r.workspace_id = ?"]
    params: list[object] = [organization_id, workspace_id]
    if not include_demo:
        clauses.append("COALESCE(r.is_demo, 0) = 0")
    if role not in {"admin", "manager"}:
        clauses.append("r.user_id = ?")
        params.append(int(user["id"]))
    rows = db.execute(
        f"""
        SELECT
            r.*,
            COALESCE(u.display_name, '') AS created_by_name,
            COALESCE(u.email, '') AS created_by_email
        FROM business_improvement_reports r
        LEFT JOIN users u ON u.id = r.user_id
        WHERE {" AND ".join(clauses)}
        ORDER BY r.created_at DESC, r.id DESC
        LIMIT 500
        """,
        tuple(params),
    ).fetchall()
    return [dict(row) for row in rows]


def _business_improvement_summary(items: list[dict]) -> dict:
    total_count = len(items)
    total_saved = round(sum(float(item.get("saved_minutes") or 0) for item in items), 1)
    total_before = sum(float(item.get("before_minutes") or 0) for item in items)
    total_after = sum(float(item.get("total_after_minutes") or 0) for item in items)
    total_mistakes = sum(int(item.get("mistake_count") or 0) for item in items)
    average_reduction_rate = round((total_saved / total_before) * 100, 1) if total_before > 0 else 0
    average_quality = round(sum(int(item.get("quality_score") or 0) for item in items) / total_count, 1) if total_count else 0
    return {
        "total_count": total_count,
        "total_before_minutes": round(total_before, 1),
        "total_after_minutes": round(total_after, 1),
        "total_saved_minutes": total_saved,
        "average_reduction_rate": average_reduction_rate,
        "average_quality": average_quality,
        "total_mistake_count": total_mistakes,
    }


@router.post("")
async def post_log(payload: UsageLogCreateRequest, user: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        create_history_log(
            db,
            int(user["id"]),
            None,
            None,
            payload.feature_name,
            payload.input_length,
            payload.output_type,
            payload.status,
            payload.error_type,
        )
    return {"ok": True}
