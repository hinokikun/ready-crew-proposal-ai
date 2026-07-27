"""JSON schema helpers for Phase 2D Slide Intent."""

from __future__ import annotations

import json
from typing import Any

from .intent_fixtures import valid_slide_intent_payloads
from .intent_models import SlideIntentInput, SlideIntentOutput, SlideIntentDesign
from .slide_intent import design_slide_intents_from_payload


def input_schema() -> dict[str, Any]:
    schema = SlideIntentInput.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Slide Intent Input"
    schema["x-phase"] = "phase2d"
    return schema


def output_schema() -> dict[str, Any]:
    schema = SlideIntentOutput.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Slide Intent Output"
    schema["x-phase"] = "phase2d"
    return schema


def slide_intent_schema() -> dict[str, Any]:
    schema = SlideIntentDesign.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Slide Intent"
    schema["x-phase"] = "phase2d"
    return schema


def example_output() -> dict[str, Any]:
    return design_slide_intents_from_payload(valid_slide_intent_payloads()[0]).dict()


def invalid_examples() -> list[dict[str, Any]]:
    base = valid_slide_intent_payloads()[0]
    missing_message = dict(base)
    missing_message.pop("message_designer_output")
    bad_extra = dict(base)
    bad_extra["unexpected"] = "not allowed"
    bad_deck_id = json.loads(json.dumps(base, ensure_ascii=False, default=str))
    bad_deck_id["message_designer_output"]["deck_id"] = "another-deck"
    return [missing_message, bad_extra, bad_deck_id]


def schema_json() -> str:
    return json.dumps(
        {
            "input": input_schema(),
            "output": output_schema(),
            "slide_intent": slide_intent_schema(),
            "example": example_output(),
            "invalid_examples": invalid_examples(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str,
    )
