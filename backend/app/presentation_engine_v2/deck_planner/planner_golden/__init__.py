"""Golden Deck Planner outputs for Phase 2A."""

from __future__ import annotations

from typing import Any

from ..planner import plan_deck
from ..planner_fixtures import valid_context_payloads


def golden_planner_results() -> list[dict[str, Any]]:
    return [plan_deck(payload).dict() for payload in valid_context_payloads()[:20]]


def golden_deck_blueprints() -> list[dict[str, Any]]:
    return [result["deck_blueprint"] for result in golden_planner_results()]

