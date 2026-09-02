import logging
from time import perf_counter

from fastapi import APIRouter, Depends, Request

from app.auth import require_roles
from app.db import get_db
from app.models import QualityGateBypassRequest, QualityGateCompleteRequest, QualityGateSaveRequest
from app.observability import log_structured
from app.quality_gates import bypass_quality_gate, complete_quality_gate, get_quality_gate, save_quality_gate

router = APIRouter(prefix="/api/quality-gates", tags=["quality-gates"])
logger = logging.getLogger(__name__)


@router.get("/{project_id}")
async def get_gate(project_id: str, user: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return {"gate": get_quality_gate(db, project_id, int(user["id"]))}


@router.post("/{project_id}")
async def post_gate(project_id: str, payload: QualityGateSaveRequest, user: dict = Depends(require_roles("admin", "member"))) -> dict:
    with get_db() as db:
        gate = save_quality_gate(db, project_id, int(user["id"]), payload.checklist_items)
    return {"ok": True, "gate": gate}


@router.patch("/{project_id}/complete")
async def patch_gate_complete(
    project_id: str,
    payload: QualityGateCompleteRequest,
    request: Request,
    user: dict = Depends(require_roles("admin", "member")),
) -> dict:
    started_at = perf_counter()
    request_id = getattr(request.state, "request_id", "")
    log_structured(
        logger,
        "info",
        "quality_gate_complete_stage",
        stage="quality_gate_complete_start",
        elapsed_ms=0,
        request_id=request_id,
    )
    with get_db() as db:
        gate = complete_quality_gate(db, project_id, int(user["id"]), payload.checklist_items)
        log_structured(
            logger,
            "info",
            "quality_gate_complete_stage",
            stage="complete_quality_gate_returned",
            elapsed_ms=max(0, round((perf_counter() - started_at) * 1000)),
            request_id=request_id,
        )
    log_structured(
        logger,
        "info",
        "quality_gate_complete_stage",
        stage="quality_gate_complete_end",
        elapsed_ms=max(0, round((perf_counter() - started_at) * 1000)),
        request_id=request_id,
    )
    return {"ok": True, "gate": gate}


@router.patch("/{project_id}/bypass")
async def patch_gate_bypass(
    project_id: str,
    payload: QualityGateBypassRequest,
    user: dict = Depends(require_roles("admin")),
) -> dict:
    with get_db() as db:
        gate = bypass_quality_gate(db, project_id, int(user["id"]), payload.bypass_reason)
    return {"ok": True, "gate": gate}
