from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import ensure_not_maintenance_mode, require_roles
from app.beautiful_ai.schemas import (
    BeautifulAiPresentationRequest,
    BeautifulAiSafeError,
    BeautifulAiStatusResponse,
    BeautifulAiStoredListResponse,
)
from app.db import get_db
from app.rate_limit.service import rate_limit_dependency
from app.services.beautiful_ai_service import (
    BeautifulAiServiceError,
    create_beautiful_ai_presentation,
    get_beautiful_ai_status,
    list_presentations_by_project,
    record_editor_opened,
)

router = APIRouter(prefix="/api/beautiful-ai", tags=["beautiful-ai"])


@router.get("/status", response_model=BeautifulAiStatusResponse)
async def get_status(_: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> BeautifulAiStatusResponse:
    return get_beautiful_ai_status()


@router.post("/presentations", dependencies=[Depends(rate_limit_dependency("generation"))])
async def create_presentation(payload: BeautifulAiPresentationRequest, user: dict = Depends(require_roles("admin", "member"))) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        try:
            response = await create_beautiful_ai_presentation(db, request=payload, user_id=int(user["id"]))
            return response.dict()
        except BeautifulAiServiceError as exc:
            error = BeautifulAiSafeError(
                error_type=exc.error_type,
                message=exc.message,
                retry_after_seconds=exc.retry_after_seconds,
            )
            headers = {"Retry-After": str(exc.retry_after_seconds)} if exc.retry_after_seconds else None
            raise HTTPException(status_code=exc.status_code, detail=error.dict(), headers=headers) from exc


@router.get("/presentations/{project_id}", response_model=BeautifulAiStoredListResponse)
async def get_presentations(project_id: str, _: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        presentations = list_presentations_by_project(db, project_id)
    return {"presentations": presentations}


@router.post("/presentations/{presentation_id}/editor-opened")
async def post_editor_opened(presentation_id: str, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        record_editor_opened(db, presentation_id=presentation_id, user_id=int(user["id"]))
    return {"ok": True}
