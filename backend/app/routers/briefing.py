from fastapi import APIRouter, Depends

from app.auth import require_roles
from app.daily_briefing import build_daily_briefing, record_briefing_event
from app.db import get_db
from app.models import DailyBriefingEventRequest

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("/today")
async def get_today_briefing(user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        briefing = build_daily_briefing(db, int(user["id"]))
    return {"briefing": briefing}


@router.post("/events")
async def post_briefing_event(payload: DailyBriefingEventRequest, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return record_briefing_event(
            db,
            user_id=int(user["id"]),
            session_key=payload.session_id,
            event_type=payload.event_type,
            project_id=payload.project_id,
            item_key=payload.item_key,
        )
