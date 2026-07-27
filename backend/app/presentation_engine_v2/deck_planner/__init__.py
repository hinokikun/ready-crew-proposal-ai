"""Offline Deck Planner for Presentation Engine 2.0 Phase 2A.

The planner turns a proposal context into a Deck Blueprint only. It is not
connected to proposal generation, Slide Blueprint generation, PPTX rendering,
database persistence, API routes, or frontend flows.
"""

from .planner import DeckPlanner, plan_deck
from .planner_evaluator import evaluate_planner_result
from .planner_models import DeckPlannerResult, ProposalContext

__all__ = [
    "DeckPlanner",
    "DeckPlannerResult",
    "ProposalContext",
    "evaluate_planner_result",
    "plan_deck",
]
