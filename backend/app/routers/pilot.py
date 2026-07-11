from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, require_roles
from app.config import settings
from app.db import get_db
from app.models import (
    FeedbackToIssueRequest,
    PilotDataRetentionRequest,
    PilotEndRequest,
    PilotIssueCreateRequest,
    PilotIssueUpdateRequest,
    PilotMaintenanceModeRequest,
)
from app.repositories import (
    apply_pilot_data_retention,
    build_pilot_dashboard,
    build_pilot_end_report,
    create_audit_log,
    create_pilot_issue,
    create_pilot_issue_from_feedback,
    get_pilot_data_retention_preview,
    get_pilot_status,
    list_pilot_issues,
    mark_pilot_checklist_confirmed,
    set_runtime_maintenance_mode,
    update_pilot_issue,
)
from app.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/api/pilot", tags=["pilot"])


@router.get("/status")
async def get_status() -> dict:
    return {"pilot": get_pilot_status()}


@router.post("/checklist-confirmed")
async def confirm_checklist(user: dict = Depends(get_current_user)) -> dict:
    with get_db() as db:
        current = mark_pilot_checklist_confirmed(db, int(user["id"]))
        create_audit_log(db, int(user["id"]), "save", "pilot_checklist", str(user["id"]), "success", "sanitized=true")
    return {"user": current, "ok": True}


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        dashboard = build_pilot_dashboard(db)
        create_audit_log(db, int(user["id"]), "view", "pilot_dashboard", "", "success", "sanitized=true")
    return {"dashboard": dashboard}


@router.get("/issues")
async def get_issues(user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        issues = list_pilot_issues(db)
        create_audit_log(db, int(user["id"]), "view", "pilot_issues", "", "success", "sanitized=true")
    return {"issues": issues}


@router.post("/issues")
async def create_issue(
    payload: PilotIssueCreateRequest,
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    with get_db() as db:
        issue = create_pilot_issue(db, payload, int(user["id"]))
        create_audit_log(db, int(user["id"]), "save", "pilot_issue", issue["issue_id"], "success", f"severity={issue['severity']};status={issue['status']}")
    return {"issue": issue}


@router.patch("/issues/{issue_id}")
async def patch_issue(issue_id: str, payload: PilotIssueUpdateRequest, user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        issue = update_pilot_issue(db, issue_id, payload, int(user["id"]))
        if not issue:
            raise HTTPException(status_code=404, detail="Pilot Issueが見つかりません。")
    return {"issue": issue}


@router.post("/issues/from-feedback/{feedback_id}")
async def issue_from_feedback(feedback_id: int, payload: FeedbackToIssueRequest, user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        result = create_pilot_issue_from_feedback(db, feedback_id, payload, int(user["id"]))
        if not result:
            raise HTTPException(status_code=404, detail="フィードバックが見つかりません。")
    return result


@router.patch("/maintenance")
async def update_maintenance(
    payload: PilotMaintenanceModeRequest,
    user: dict = Depends(require_roles("admin")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    if settings.maintenance_mode and not payload.enabled:
        raise HTTPException(status_code=409, detail="環境変数MAINTENANCE_MODE=trueが優先されるため、画面から解除できません。")
    with get_db() as db:
        maintenance = set_runtime_maintenance_mode(db, payload.enabled, payload.reason, int(user["id"]))
    return {"maintenance": maintenance}


@router.get("/data-retention/preview")
async def data_retention_preview(user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        preview = get_pilot_data_retention_preview(db)
        create_audit_log(db, int(user["id"]), "view", "pilot_data_retention", "", "success", "sanitized=true")
    return {"preview": preview}


@router.post("/data-retention")
async def data_retention(payload: PilotDataRetentionRequest, user: dict = Depends(require_roles("admin"))) -> dict:
    try:
        with get_db() as db:
            result = apply_pilot_data_retention(db, payload.action, payload.confirm_text, int(user["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="確認文字列 PILOT を入力してください。") from exc
    return result


@router.post("/end")
async def end_pilot(payload: PilotEndRequest, user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        report = build_pilot_end_report(db, payload.admin_comment)
        db.execute(
            """
            UPDATE users
            SET pilot_completed = 1,
                pilot_enabled = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE pilot_enabled = 1 AND role != 'admin'
            """
        )
        create_audit_log(db, int(user["id"]), "settings_change", "pilot", "end", "success", "pilot_ended=true")
    return {"report": report}
