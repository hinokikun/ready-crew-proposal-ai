from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.analytics.repositories import list_candidate_boundary_events
from app.analytics.services import add_release_note, get_dashboard, get_release_notes as get_release_notes_service, record_event, set_error_resolved
from app.auth import require_roles
from app.db import get_db
from app.models import AnalyticsEventRequest, AnalyticsErrorUpdateRequest, ReleaseNoteCreateRequest
from app.repositories import create_audit_log
from app.scope_policy import resolve_scope

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.post("/events")
async def post_analytics_event(payload: AnalyticsEventRequest, user: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        return record_event(
            db,
            user_id=int(user["id"]),
            session_key=payload.session_id,
            event_name=payload.event_name,
            feature_name=payload.feature_name,
            status=payload.status,
            duration_ms=payload.duration_ms,
            error_type=payload.error_type,
            metadata=payload.metadata,
        )


@router.get("/dashboard")
async def get_analytics_dashboard(
    user: dict = Depends(require_roles("admin", "manager")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    scope: str = Query("workspace", pattern="^(workspace|organization|system)$"),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        return {"dashboard": get_dashboard(db, limit, offset, resolved_scope)}


def _parse_utc_bound(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"{name} must be an ISO-8601 timestamp with timezone.") from exc
    if parsed.tzinfo is None:
        raise HTTPException(status_code=400, detail=f"{name} must include a timezone.")
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


@router.get("/candidate-boundary-events")
async def get_candidate_boundary_events(
    start: str = Query(..., min_length=1),
    end: str = Query(..., min_length=1),
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = Query("workspace", pattern="^(workspace|organization)$"),
    candidate_boundary_correlation_id: str | None = Query(None, max_length=64, pattern=r"^[A-Za-z0-9_-]+$"),
) -> dict:
    start_dt = _parse_utc_bound(start, "start")
    end_dt = _parse_utc_bound(end, "end")
    if start_dt >= end_dt:
        raise HTTPException(status_code=400, detail="start must be before end.")
    if end_dt - start_dt > timedelta(hours=24):
        raise HTTPException(status_code=400, detail="time window must not exceed 24 hours.")
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        return {
            "events": list_candidate_boundary_events(
                db,
                start_dt.strftime("%Y-%m-%d %H:%M:%S"),
                end_dt.strftime("%Y-%m-%d %H:%M:%S"),
                resolved_scope,
                candidate_boundary_correlation_id,
            )
        }


@router.patch("/errors/{error_id}")
async def patch_analytics_error(
    error_id: int,
    payload: AnalyticsErrorUpdateRequest,
    user: dict = Depends(require_roles("admin", "manager")),
    scope: str = Query("workspace", pattern="^(workspace|organization|system)$"),
) -> dict:
    with get_db() as db:
        resolved_scope = resolve_scope(db, user, scope)
        error = set_error_resolved(db, error_id, payload.resolved, resolved_scope)
        if not error:
            raise HTTPException(status_code=404, detail="Analytics error was not found.")
        create_audit_log(
            db,
            int(user["id"]),
            "setting_change",
            "analytics_error",
            str(error_id),
            "success",
            f"resolved={payload.resolved};scope={resolved_scope.scope}",
        )
        return {"error": error}


@router.get("/release-notes")
async def get_release_notes(_: dict = Depends(require_roles("admin")), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)) -> dict:
    with get_db() as db:
        return {"release_notes": get_release_notes_service(db, limit, offset)}


@router.post("/release-notes")
async def post_release_note(payload: ReleaseNoteCreateRequest, user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        note = add_release_note(
            db,
            user_id=int(user["id"]),
            version=payload.version,
            release_date=payload.release_date,
            title=payload.title,
            improvements=payload.improvements,
        )
        create_audit_log(db, int(user["id"]), "save", "release_note", str(note["id"]), "success", f"version={payload.version[:40]}")
        return {"release_note": note}
