"""Proposal Strategy Engine utilities.

The production PPTX path remains legacy by default. Strategy integration is available only through
the presentation engine feature flag and requires an approved human review report.
"""

from .evaluator import evaluate_strategy
from .models import PresentationContext, ProposalStrategyInput, ProposalStrategyWorkspace, SalesStrategyBrief, StrategyBrief
from .review import create_review_report, render_strategy_brief_markdown
from .adapter import adapt_review_report_to_presentation_context
from .sales_strategy import generate_sales_strategy_brief

__all__ = [
    "PresentationContext",
    "ProposalStrategyInput",
    "ProposalStrategyWorkspace",
    "SalesStrategyBrief",
    "StrategyBrief",
    "adapt_review_report_to_presentation_context",
    "create_review_report",
    "evaluate_strategy",
    "generate_sales_strategy_brief",
    "render_strategy_brief_markdown",
]
