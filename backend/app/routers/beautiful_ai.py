from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import ensure_not_maintenance_mode, require_roles
from app.beautiful_ai.schemas import (
    BeautifulAiConnectionTestResponse,
    BeautifulAiDiagnosticsResponse,
    BeautifulAiPresentationRequest,
    BeautifulAiSafeError,
    BeautifulAiStatusResponse,
    BeautifulAiStoredListResponse,
)
from app.db import get_db
from app.repositories import create_history_log, get_user_context_ids
from app.rate_limit.service import rate_limit_dependency
from app.services.beautiful_ai_service import (
    BeautifulAiServiceError,
    create_beautiful_ai_presentation,
    get_beautiful_ai_diagnostics,
    get_beautiful_ai_status,
    list_presentations_by_project,
    record_editor_opened,
    run_beautiful_ai_connection_test,
)

router = APIRouter(prefix="/api/beautiful-ai", tags=["beautiful-ai"])


def _beautiful_ai_input_length(payload: BeautifulAiPresentationRequest) -> int:
    slides = getattr(payload.powerpoint_generation_data, "slides", []) or []
    slide_text = "".join(f"{getattr(slide, 'title', '')}{getattr(slide, 'body', '')}" for slide in slides)
    return len(payload.project_brief or "") + len(payload.client_company_info or "") + len(slide_text)


@router.get("/status", response_model=BeautifulAiStatusResponse)
async def get_status(_: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> BeautifulAiStatusResponse:
    with get_db() as db:
        return get_beautiful_ai_status(db)


@router.post("/presentations", dependencies=[Depends(rate_limit_dependency("generation"))])
async def create_presentation(payload: BeautifulAiPresentationRequest, user: dict = Depends(require_roles("admin", "member"))) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        try:
            response = await create_beautiful_ai_presentation(db, request=payload, user_id=int(user["id"]))
            create_history_log(
                db,
                int(user["id"]),
                None,
                None,
                "Beautiful.ai",
                _beautiful_ai_input_length(payload),
                "beautiful-ai",
                "success",
            )
            return response.dict()
        except BeautifulAiServiceError as exc:
            create_history_log(
                db,
                int(user["id"]),
                None,
                None,
                "Beautiful.ai",
                _beautiful_ai_input_length(payload),
                "beautiful-ai",
                "failure",
                exc.error_type,
            )
            error = BeautifulAiSafeError(
                error_type=exc.error_type,
                message=exc.message,
                retry_after_seconds=exc.retry_after_seconds,
            )
            headers = {"Retry-After": str(exc.retry_after_seconds)} if exc.retry_after_seconds else None
            raise HTTPException(status_code=exc.status_code, detail=error.dict(), headers=headers) from exc


@router.get("/presentations/{project_id}", response_model=BeautifulAiStoredListResponse)
async def get_presentations(project_id: str, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        organization_id, workspace_id = get_user_context_ids(db, int(user["id"]))
        presentations = list_presentations_by_project(db, project_id, organization_id=organization_id, workspace_id=workspace_id)
    return {"presentations": presentations}


@router.post("/presentations/{presentation_id}/editor-opened")
async def post_editor_opened(presentation_id: str, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        record_editor_opened(db, presentation_id=presentation_id, user_id=int(user["id"]))
    return {"ok": True}


@router.get("/diagnostics", response_model=BeautifulAiDiagnosticsResponse)
async def get_diagnostics(user: dict = Depends(require_roles("admin", "manager"))) -> BeautifulAiDiagnosticsResponse:
    with get_db() as db:
        organization_id, workspace_id = get_user_context_ids(db, int(user["id"]))
        return get_beautiful_ai_diagnostics(db, organization_id=organization_id, workspace_id=workspace_id)


@router.post("/diagnostics/test", response_model=BeautifulAiConnectionTestResponse)
async def post_connection_test(user: dict = Depends(require_roles("admin", "manager"))) -> BeautifulAiConnectionTestResponse:
    with get_db() as db:
        return await run_beautiful_ai_connection_test(db, user_id=int(user["id"]))
