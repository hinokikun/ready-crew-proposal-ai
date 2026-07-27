"""Offline Alpha Integration Review for Presentation Engine 2.0.

This package runs Phase 2A Deck Planner, Phase 2B Evidence Planner, and Phase
2C Message Designer as an offline review pipeline only. It does not connect to
existing Proposal generation, PPTX rendering, APIs, DB, Frontend, OpenAI, or
Beautiful.ai.
"""

from .pipeline import (
    AlphaIntegrationPipeline,
    run_alpha_integration,
    run_alpha_integration_from_payload,
    run_alpha_integration_markdown,
)
from .pipeline_models import AlphaIntegrationCase, AlphaIntegrationOutput, AlphaCrossCaseSummary
from .pipeline_reporter import cross_case_markdown, human_review_markdown, improvement_backlog_markdown

__all__ = [
    "AlphaCrossCaseSummary",
    "AlphaIntegrationCase",
    "AlphaIntegrationOutput",
    "AlphaIntegrationPipeline",
    "cross_case_markdown",
    "human_review_markdown",
    "improvement_backlog_markdown",
    "run_alpha_integration",
    "run_alpha_integration_from_payload",
    "run_alpha_integration_markdown",
]
