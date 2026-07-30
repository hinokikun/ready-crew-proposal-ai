from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth import ensure_not_maintenance_mode, require_roles
from app.models import PowerPointData
from app.rate_limit.service import rate_limit_dependency
from app.services.proposal_validation_engine import run_golden_validation_suite, validate_proposal

router = APIRouter(prefix="/api/proposal-validation", tags=["proposal-validation"])


class ProposalValidationRequest(BaseModel):
    powerpoint_generation_data: PowerPointData
    proposal_context: dict[str, Any] = Field(default_factory=dict)


@router.post("/validate", dependencies=[Depends(rate_limit_dependency("generation"))])
async def post_proposal_validation(
    payload: ProposalValidationRequest,
    user: dict = Depends(require_roles("admin", "manager", "member")),
) -> dict[str, Any]:
    ensure_not_maintenance_mode()
    result = validate_proposal(payload.powerpoint_generation_data, payload.proposal_context)
    return {"validation": result.to_dict(), "user_id": int(user["id"])}


@router.get("/golden-suite")
async def get_proposal_validation_golden_suite(
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict[str, Any]:
    ensure_not_maintenance_mode()
    return {"golden_suite": run_golden_validation_suite(), "user_id": int(user["id"])}
