from fastapi import APIRouter, Depends

from app.auth import require_roles
from app.db import get_db
from app.models import QualityGateBypassRequest, QualityGateCompleteRequest, QualityGateSaveRequest
from app.quality_gates import bypass_quality_gate, complete_quality_gate, get_quality_gate, save_quality_gate

router = APIRouter(prefix="/api/quality-gates", tags=["quality-gates"])


@router.get("/{project_id}")
async def get_gate(project_id: str, _: dict = Depends(require_roles("admin", "manager", "member", "viewer"))) -> dict:
    with get_db() as db:
        return {"gate": get_quality_gate(db, project_id)}


@router.post("/{project_id}")
async def post_gate(project_id: str, payload: QualityGateSaveRequest, user: dict = Depends(require_roles("admin", "member"))) -> dict:
    with get_db() as db:
        gate = save_quality_gate(db, project_id, int(user["id"]), payload.checklist_items)
    return {"ok": True, "gate": gate}


@router.patch("/{project_id}/complete")
async def patch_gate_complete(
    project_id: str,
    payload: QualityGateCompleteRequest,
    user: dict = Depends(require_roles("admin", "member")),
) -> dict:
    with get_db() as db:
        gate = complete_quality_gate(db, project_id, int(user["id"]), payload.checklist_items)
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
