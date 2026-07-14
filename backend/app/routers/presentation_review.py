from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db
from app.presentation_review import (
    approve_revision,
    compare_revisions,
    create_presentation_review,
    create_revision_from_review,
    generate_beautiful_ai_revision,
    list_presentation_reviews,
    list_presentation_revisions,
    reject_revision,
)
from app.rate_limit.service import rate_limit_dependency
from app.services.beautiful_ai_service import BeautifulAiServiceError

router = APIRouter(prefix="/api/presentation-review", tags=["presentation-review"])


class PresentationReviewCreateRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=120)
    project_name: str = Field("", max_length=160)
    powerpoint_generation_data: dict[str, Any]
    beautiful_ai_presentation_id: str = Field("", max_length=240)


class PresentationRevisionCreateRequest(BaseModel):
    review_id: int
    beautiful_ai_presentation_id: str = Field("", max_length=240)
    selected_actions: list[dict[str, Any]] = Field(default_factory=list)


class PresentationRevisionDecisionRequest(BaseModel):
    comment: str = Field("", max_length=500)


class PresentationRevisionGenerateRequest(BaseModel):
    beautiful_ai_payload: dict[str, Any]


@router.post("/reviews", dependencies=[Depends(rate_limit_dependency("generation"))])
async def post_presentation_review(
    payload: PresentationReviewCreateRequest,
    user: dict = Depends(require_roles("admin", "member")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        review = create_presentation_review(
            db,
            user_id=int(user["id"]),
            project_id=payload.project_id,
            project_name=payload.project_name,
            powerpoint_data=payload.powerpoint_generation_data,
            beautiful_ai_presentation_id=payload.beautiful_ai_presentation_id,
        )
    return {"review": review}


@router.get("/projects/{project_id}")
async def get_project_presentation_reviews(
    project_id: str,
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
) -> dict:
    with get_db() as db:
        reviews = list_presentation_reviews(db, project_id=project_id, user_id=int(user["id"]))
        revisions = list_presentation_revisions(db, project_id=project_id, user_id=int(user["id"]))
    return {"reviews": reviews, "revisions": revisions}


@router.post("/revisions", dependencies=[Depends(rate_limit_dependency("generation"))])
async def post_presentation_revision(
    payload: PresentationRevisionCreateRequest,
    user: dict = Depends(require_roles("admin", "member")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        try:
            revision = create_revision_from_review(
                db,
                review_id=payload.review_id,
                user_id=int(user["id"]),
                selected_actions=payload.selected_actions or None,
                beautiful_ai_presentation_id=payload.beautiful_ai_presentation_id,
            )
        except ValueError as exc:
            if str(exc) == "max_revisions_reached":
                raise HTTPException(status_code=409, detail="Revisionの最大回数に到達しました。") from exc
            if str(exc) == "revision_already_approved":
                raise HTTPException(status_code=409, detail="承認済みRevisionのため追加作成できません。") from exc
            if str(exc) == "no_actions_selected":
                raise HTTPException(status_code=400, detail="採用する改善Actionを選択してください。") from exc
            raise
    if not revision:
        raise HTTPException(status_code=404, detail="Presentation Reviewが見つかりません。")
    return {"revision": revision}


@router.patch("/revisions/{revision_id}/approve")
async def patch_revision_approved(
    revision_id: int,
    payload: PresentationRevisionDecisionRequest | None = None,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        revision = approve_revision(db, revision_id=revision_id, user_id=int(user["id"]), comment=(payload.comment if payload else ""))
    if not revision:
        raise HTTPException(status_code=404, detail="Presentation Revisionが見つかりません。")
    return {"revision": revision}


@router.patch("/revisions/{revision_id}/reject")
async def patch_revision_rejected(
    revision_id: int,
    payload: PresentationRevisionDecisionRequest | None = None,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        revision = reject_revision(db, revision_id=revision_id, user_id=int(user["id"]), comment=(payload.comment if payload else ""))
    if not revision:
        raise HTTPException(status_code=404, detail="Presentation Revisionが見つかりません。")
    return {"revision": revision}


@router.post("/revisions/{revision_id}/generate-beautiful-ai", dependencies=[Depends(rate_limit_dependency("generation"))])
async def post_revision_beautiful_ai_generation(
    revision_id: int,
    payload: PresentationRevisionGenerateRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        try:
            revision = await generate_beautiful_ai_revision(
                db,
                revision_id=revision_id,
                user_id=int(user["id"]),
                base_request=payload.beautiful_ai_payload,
            )
        except ValueError as exc:
            if str(exc) == "revision_not_approved":
                raise HTTPException(status_code=409, detail="Beautiful.ai再生成にはmanager/admin承認済みRevisionが必要です。") from exc
            raise
        except BeautifulAiServiceError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={
                    "error_type": exc.error_type,
                    "message": exc.message,
                    "fallback_available": True,
                    "retry_after_seconds": exc.retry_after_seconds,
                },
            ) from exc
    if not revision:
        raise HTTPException(status_code=404, detail="Presentation Revisionが見つかりません。")
    return {"revision": revision}


@router.get("/projects/{project_id}/compare")
async def get_revision_compare(
    project_id: str,
    from_revision_id: int | None = Query(None),
    to_revision_id: int | None = Query(None),
    user: dict = Depends(require_roles("admin", "manager", "member", "viewer")),
) -> dict:
    with get_db() as db:
        return compare_revisions(
            db,
            project_id=project_id,
            user_id=int(user["id"]),
            from_revision_id=from_revision_id,
            to_revision_id=to_revision_id,
        )
