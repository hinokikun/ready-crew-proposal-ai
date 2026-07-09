from fastapi import APIRouter, Depends

from app.auth import require_roles
from app.db import get_db
from app.models import FeedbackCreateRequest
from app.repositories import create_feedback_entry, list_feedback_entries, summarize_feedback_entries

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


@router.post("")
async def post_feedback(payload: FeedbackCreateRequest, user: dict = Depends(require_roles("admin", "member", "viewer"))) -> dict:
    with get_db() as db:
        feedback = create_feedback_entry(
            db,
            int(user["id"]),
            str(user["role"]),
            payload.rating,
            payload.comment,
            payload.feature_name,
        )
        summary = summarize_feedback_entries(db)
    return {"feedback": feedback, "summary": summary}


@router.get("")
async def get_feedback(_: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        return {
            "feedback": list_feedback_entries(db, 200),
            "summary": summarize_feedback_entries(db),
        }
