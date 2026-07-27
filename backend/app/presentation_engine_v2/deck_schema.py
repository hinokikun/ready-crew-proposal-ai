"""JSON Schema and example helpers for Deck Blueprint contracts."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .deck_contracts import DECK_SCHEMA_DRAFT
from .deck_models import DeckBlueprint


def deck_blueprint_schema() -> Dict[str, Any]:
    schema = DeckBlueprint.schema(ref_template="#/definitions/{model}")
    schema["$schema"] = DECK_SCHEMA_DRAFT
    schema["$id"] = "https://proposalpilot.local/schemas/presentation-engine-v2/deck-blueprint.schema.json"
    schema["title"] = "Presentation Engine 2.0 Deck Blueprint"
    schema["description"] = "Offline contract for one proposal deck blueprint."
    schema["additionalProperties"] = False
    schema["x-model"] = "DeckBlueprint"
    return schema


def schema_json(indent: int = 2) -> str:
    return json.dumps(deck_blueprint_schema(), ensure_ascii=False, indent=indent)


def deck_slide_reference_contract() -> Dict[str, Any]:
    return {
        "$schema": DECK_SCHEMA_DRAFT,
        "$id": "https://proposalpilot.local/schemas/presentation-engine-v2/deck-slide-reference-contract.json",
        "title": "Deck to Slide Blueprint Reference Contract",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "slide_blueprint_id",
            "slide_id",
            "slide_order",
            "expected_slide_type",
            "expected_slide_goal",
            "section_id",
            "required",
        ],
        "properties": {
            "slide_blueprint_id": {"type": "string", "minLength": 1, "maxLength": 100},
            "slide_id": {"type": "string", "minLength": 1, "maxLength": 100},
            "slide_order": {"type": "integer", "minimum": 0, "maximum": 200},
            "expected_slide_type": {"type": "string"},
            "expected_slide_goal": {"type": "string"},
            "section_id": {"type": "string", "minLength": 1, "maxLength": 100},
            "required": {"type": "boolean"},
            "embedded_slide_blueprint": {
                "description": "Optional Phase 1 Slide Blueprint. Prefer references for Phase 1.5 fixtures.",
                "type": ["object", "null"],
            },
        },
    }


def example_deck_payload() -> Dict[str, Any]:
    from .deck_fixtures import valid_deck_payloads

    return valid_deck_payloads()[0]


def invalid_deck_payloads() -> List[Dict[str, Any]]:
    from .deck_fixtures import invalid_deck_payloads as _invalid

    return _invalid()
