"""JSON schema helpers for Phase 2B Evidence Planner."""

from __future__ import annotations

import json
from typing import Any

from ..deck_planner import plan_deck
from ..deck_planner.planner_fixtures import valid_context_payloads
from .evidence_models import EvidencePlannerResult, EvidencePlanningInput
from .evidence_planner import plan_evidence


def evidence_planning_input_schema() -> dict[str, Any]:
    schema = EvidencePlanningInput.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Evidence Planning Input"
    schema["x-phase"] = "2B"
    return schema


def evidence_planner_result_schema() -> dict[str, Any]:
    schema = EvidencePlannerResult.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Evidence Planner Result"
    schema["x-phase"] = "2B"
    return schema


def example_evidence_planner_result() -> dict[str, Any]:
    context = valid_context_payloads()[0]
    deck = plan_deck(context).deck_blueprint
    return plan_evidence(deck, context).dict()


def schema_json() -> str:
    return json.dumps(
        {
            "evidence_planning_input": evidence_planning_input_schema(),
            "evidence_planner_result": evidence_planner_result_schema(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str,
    )

