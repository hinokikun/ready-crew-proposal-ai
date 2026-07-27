"""Offline Evidence Planner for Presentation Engine 2.0 Phase 2B.

The Evidence Planner receives a Deck Blueprint and Proposal Context, then
creates slide-level evidence requirements only. It does not generate headlines,
main messages, body text, Slide Blueprints, diagrams, layouts, PowerPoint files,
API responses, database records, or runtime proposal output.
"""

from .evidence_evaluator import evaluate_evidence_plan
from .evidence_planner import EvidencePlanner, plan_evidence, plan_evidence_from_payload
from .evidence_models import EvidencePlannerResult, EvidencePlanningInput

__all__ = [
    "EvidencePlanner",
    "EvidencePlannerResult",
    "EvidencePlanningInput",
    "evaluate_evidence_plan",
    "plan_evidence",
    "plan_evidence_from_payload",
]
