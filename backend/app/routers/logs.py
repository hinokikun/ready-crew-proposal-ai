import csv
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.auth import require_roles
from app.db import get_db
from app.models import TrialReportRequest, UsageLogCreateRequest
from app.repositories import (
    build_operation_readiness_check,
    build_improvement_dashboard,
    build_trial_report,
    create_audit_log,
    create_history_log,
    list_audit_logs,
    list_usage_logs,
    summarize_usage_dashboard,
)

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def get_logs(_: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        return {"logs": list_usage_logs(db, 100)}


@router.get("/audit")
async def get_audit_logs(_: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        return {"logs": list_audit_logs(db, 200)}


@router.get("/usage-dashboard")
async def get_usage_dashboard(_: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        return {"dashboard": summarize_usage_dashboard(db)}


@router.get("/usage-dashboard.csv")
async def download_usage_dashboard_csv(_: dict = Depends(require_roles("admin"))) -> Response:
    with get_db() as db:
        dashboard = summarize_usage_dashboard(db)

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["AI営業秘書 利用状況ダッシュボード"])
    writer.writerow([])
    writer.writerow(["集計", "件数"])
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
    writer.writerow(["エラー分析", "件数"])
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
    writer.writerow(["機能別利用集計", "利用回数", "成功", "失敗"])
    for item in dashboard["features"]:
        writer.writerow([item["feature_name"], item["usage_count"], item["success_count"], item["failure_count"]])

    writer.writerow([])
    writer.writerow(["利用者別集計", "ロール", "利用回数", "最終利用日時", "成功", "失敗"])
    for item in dashboard["users"]:
        writer.writerow([item["user_name"], item["user_role"], item["usage_count"], item["last_used_at"], item["success_count"], item["failure_count"]])

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

    return Response(
        content=f"\ufeff{output.getvalue()}",
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=ai-sales-secretary-usage-dashboard.csv"},
    )


@router.post("/trial-report")
async def create_trial_report(payload: TrialReportRequest, user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        report = build_trial_report(db, payload.admin_comment)
        create_audit_log(db, int(user["id"]), "generate", "trial_report", "", "success", "sanitized=true")
    return {"report": report}


@router.get("/operation-readiness")
async def get_operation_readiness(user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        readiness = build_operation_readiness_check(db)
        create_audit_log(db, int(user["id"]), "generate", "operation_readiness", "", "success", "sanitized=true")
    return {"readiness": readiness}


@router.get("/improvement-dashboard")
async def get_improvement_dashboard(user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        dashboard = build_improvement_dashboard(db)
        create_audit_log(db, int(user["id"]), "generate", "improvement_dashboard", "", "success", "sanitized=true")
    return {"dashboard": dashboard}


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
