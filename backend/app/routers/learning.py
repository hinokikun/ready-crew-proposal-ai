from fastapi import APIRouter, Depends, HTTPException

from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db
from app.learning.services import adopt_learning_improvement, get_learning_dashboard, run_learning_analysis
from app.models import LearningImprovementStatusRequest
from app.rate_limit import rate_limit_dependency

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("/dashboard")
async def get_dashboard(user: dict = Depends(require_roles("admin", "manager"))) -> dict:
    with get_db() as db:
        return {"dashboard": get_learning_dashboard(db, int(user["id"]))}


@router.post("/run")
async def run_learning(
    user: dict = Depends(require_roles("admin", "manager")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> dict:
    ensure_not_maintenance_mode()
    with get_db() as db:
        return {"dashboard": run_learning_analysis(db, user_id=int(user["id"]))}


@router.patch("/improvements/{improvement_id}/status")
async def update_improvement_status(
    improvement_id: int,
    payload: LearningImprovementStatusRequest,
    user: dict = Depends(require_roles("admin", "manager")),
) -> dict:
    with get_db() as db:
        improvement = adopt_learning_improvement(db, improvement_id=improvement_id, status=payload.status, user_id=int(user["id"]))
    if not improvement:
        raise HTTPException(status_code=404, detail="Improvement not found.")
    return {"improvement": improvement}
