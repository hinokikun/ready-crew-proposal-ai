from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_roles
from app.db import get_db
from app.models import ProposalReviewRecreateRequest, ProposalReviewRequest, ProposalReviewUpdateRequest
from app.reviews import (
    apply_review_feedback,
    get_review_by_project,
    list_review_revisions,
    list_reviews,
    request_review,
    request_review_again,
    update_review_status,
)

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.get("")
async def get_reviews(_: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"reviews": list_reviews(db, 100)}


@router.get("/{project_id}")
async def get_review(project_id: str, _: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        review = get_review_by_project(db, project_id)
    return {"review": review}


@router.post("/request")
async def post_review_request(payload: ProposalReviewRequest, user: dict = Depends(require_roles("admin", "member"))) -> dict:
    with get_db() as db:
        review = request_review(db, payload.project_id, payload.project_name, int(user["id"]))
    return {"ok": True, "review": review}


@router.patch("/{review_id}")
async def patch_review(review_id: int, payload: ProposalReviewUpdateRequest, user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        review = update_review_status(db, review_id, int(user["id"]), payload.status, payload.review_comment)
    if not review:
        raise HTTPException(status_code=404, detail="レビュー依頼が見つかりません。")
    return {"ok": True, "review": review}


@router.post("/{review_id}/apply-feedback")
async def post_apply_review_feedback(
    review_id: int,
    payload: ProposalReviewRecreateRequest,
    user: dict = Depends(require_roles("admin", "member")),
) -> dict:
    with get_db() as db:
        result = apply_review_feedback(db, review_id, int(user["id"]), payload.current_summary)
    if not result:
        raise HTTPException(status_code=404, detail="レビュー依頼が見つかりません。")
    return {"ok": True, **result}


@router.post("/{review_id}/rerequest")
async def post_rerequest_review(review_id: int, user: dict = Depends(require_roles("admin", "member"))) -> dict:
    with get_db() as db:
        review = request_review_again(db, review_id, int(user["id"]))
    if not review:
        raise HTTPException(status_code=404, detail="レビュー依頼が見つかりません。")
    return {"ok": True, "review": review}


@router.get("/{review_id}/revisions")
async def get_review_revisions(review_id: int, _: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        revisions = list_review_revisions(db, review_id)
    return {"revisions": revisions}
