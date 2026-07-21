"""Offline AI Sales Assistant contract and deterministic generator."""

from .evaluator import evaluate_sales_assistant_brief
from .generator import generate_sales_assistant_brief
from .models import SalesAssistantBrief, SalesAssistantInput

__all__ = [
    "SalesAssistantBrief",
    "SalesAssistantInput",
    "evaluate_sales_assistant_brief",
    "generate_sales_assistant_brief",
]
