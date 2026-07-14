from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import require_roles
from app.db import get_db
from app.knowledge.services import (
    add_knowledge_entry,
    add_template,
    build_best_practices,
    get_knowledge_entries,
    get_templates,
    recalculate_knowledge_quality,
    search_similar_knowledge,
    set_knowledge_evaluation,
    set_knowledge_status,
    set_template_active,
)
from app.models import (
    KnowledgeEntryCreateRequest,
    KnowledgeEvaluationRequest,
    KnowledgeSearchRequest,
    KnowledgeStatusUpdateRequest,
    ProposalTemplateCreateRequest,
    ProposalTemplateUpdateRequest,
)
from app.repositories import create_audit_log

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/entries")
async def list_entries(
    user: dict = Depends(require_roles("admin", "manager")),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    with get_db() as db:
        return {"entries": get_knowledge_entries(db, limit, offset, int(user["id"]))}


@router.post("/entries")
async def create_entry(payload: KnowledgeEntryCreateRequest, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        entry = add_knowledge_entry(db, payload.dict(), int(user["id"]))
        create_audit_log(
            db,
            int(user["id"]),
            "save",
            "proposal_knowledge",
            str(entry["id"]),
            "success",
            f"status={entry['approval_status']};score={entry['quality_score']};source={entry['source_type']}",
        )
        return {"entry": entry}


@router.patch("/entries/{entry_id}/evaluation")
async def update_entry_evaluation(
    entry_id: int,
    payload: KnowledgeEvaluationRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        entry = set_knowledge_evaluation(db, entry_id, payload.rating, payload.evaluation_status)
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry was not found.")
        create_audit_log(db, int(user["id"]), "setting_change", "proposal_knowledge", str(entry_id), "success", f"rating={payload.rating}")
        return {"entry": entry}


@router.patch("/entries/{entry_id}/status")
async def update_entry_status(
    entry_id: int,
    payload: KnowledgeStatusUpdateRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        try:
            entry = set_knowledge_status(db, entry_id, payload.approval_status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry was not found.")
        event_map = {
            "approved": "knowledge_approve",
            "rejected": "knowledge_reject",
            "archived": "knowledge_archive",
        }
        create_audit_log(
            db,
            int(user["id"]),
            event_map.get(payload.approval_status, "knowledge_status_change"),
            "proposal_knowledge",
            str(entry_id),
            "success",
            f"status={payload.approval_status}",
        )
        return {"entry": entry}


@router.post("/entries/{entry_id}/quality/recalculate")
async def recalculate_entry_quality(
    entry_id: int,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        entry = recalculate_knowledge_quality(db, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Knowledge entry was not found.")
        create_audit_log(
            db,
            int(user["id"]),
            "knowledge_quality_recalculate",
            "proposal_knowledge",
            str(entry_id),
            "success",
            f"score={entry['quality_score']};risk={entry['confidential_risk']}",
        )
        return {"entry": entry}


@router.post("/search")
async def search_entries(payload: KnowledgeSearchRequest, user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        return {"insights": search_similar_knowledge(db, payload.project_summary, payload.industry, payload.limit, int(user["id"]))}


@router.get("/best-practices")
async def best_practices(user: dict = Depends(require_roles("admin", "manager", "member"))) -> dict:
    with get_db() as db:
        return {"best_practices": build_best_practices(db, int(user["id"]))}


@router.get("/templates")
async def list_proposal_templates(
    user: dict = Depends(require_roles("admin", "member", "viewer")),
    category: str = Query("", max_length=40),
    include_inactive: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    with get_db() as db:
        return {"templates": get_templates(db, category, include_inactive, limit, offset, int(user["id"]))}


@router.post("/templates")
async def create_proposal_template(payload: ProposalTemplateCreateRequest, user: dict = Depends(require_roles("admin"))) -> dict:
    with get_db() as db:
        template = add_template(db, payload.dict(), int(user["id"]))
        create_audit_log(db, int(user["id"]), "template_change", "proposal_template", str(template["id"]), "success", f"category={template['category']}")
        return {"template": template}


@router.patch("/templates/{template_id}")
async def update_proposal_template(
    template_id: int,
    payload: ProposalTemplateUpdateRequest,
    user: dict = Depends(require_roles("admin")),
) -> dict:
    with get_db() as db:
        template = set_template_active(db, template_id, payload.is_active)
        if not template:
            raise HTTPException(status_code=404, detail="Proposal template was not found.")
        create_audit_log(db, int(user["id"]), "template_change", "proposal_template", str(template_id), "success", f"is_active={payload.is_active}")
        return {"template": template}
