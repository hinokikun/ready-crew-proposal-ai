"""JSON schema helpers for the Phase 2A Deck Planner."""

from __future__ import annotations

import json
from typing import Any

from .planner import plan_deck
from .planner_fixtures import valid_context_payloads
from .planner_models import DeckPlannerResult, ProposalContext


def proposal_context_schema() -> dict[str, Any]:
    schema = ProposalContext.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Proposal Context"
    schema["x-phase"] = "2A"
    return schema


def deck_planner_result_schema() -> dict[str, Any]:
    schema = DeckPlannerResult.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Deck Planner Result"
    schema["x-phase"] = "2A"
    return schema


def example_planner_result() -> dict[str, Any]:
    return plan_deck(valid_context_payloads()[0]).dict()


def schema_json() -> str:
    return json.dumps(
        {
            "proposal_context": proposal_context_schema(),
            "deck_planner_result": deck_planner_result_schema(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )

