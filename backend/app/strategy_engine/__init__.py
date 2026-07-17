"""Offline Proposal Strategy Engine.

This package is intentionally not wired into FastAPI, proposal generation,
PPTX generation, external presentation integrations, or database persistence. It is used by tests
and offline evaluation only until the production integration is approved.
"""

from .evaluator import evaluate_strategy
from .models import ProposalStrategyInput, StrategyBrief

__all__ = ["ProposalStrategyInput", "StrategyBrief", "evaluate_strategy"]
