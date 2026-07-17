"""Offline Proposal Strategy Engine.

This package is intentionally not wired into FastAPI, proposal generation,
PPTX generation, external presentation integrations, or database persistence. It is used by tests
and offline evaluation only until the production integration is approved.
"""

from .evaluator import evaluate_strategy
from .models import ProposalStrategyInput, StrategyBrief
from .review import create_review_report, render_strategy_brief_markdown

__all__ = [
    "ProposalStrategyInput",
    "StrategyBrief",
    "create_review_report",
    "evaluate_strategy",
    "render_strategy_brief_markdown",
]
