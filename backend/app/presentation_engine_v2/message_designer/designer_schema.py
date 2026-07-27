"""JSON schema helpers for Phase 2C Message Designer."""

from __future__ import annotations

import json
from typing import Any

from ..deck_planner import plan_deck
from ..deck_planner.planner_fixtures import valid_context_payloads
from ..evidence_planner import plan_evidence
from .designer_models import MessageDesignerInput, MessageDesignerOutput, SlideMessageDesign
from .designer import design_messages


def slide_message_design_schema() -> dict[str, Any]:
    schema = SlideMessageDesign.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Slide Message Design"
    schema["x-phase"] = "2C"
    return schema


def message_designer_input_schema() -> dict[str, Any]:
    schema = MessageDesignerInput.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Message Designer Input"
    schema["x-phase"] = "2C"
    return schema


def message_designer_output_schema() -> dict[str, Any]:
    schema = MessageDesignerOutput.schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "Presentation Engine 2.0 Message Designer Output"
    schema["x-phase"] = "2C"
    return schema


def example_message_designer_output() -> dict[str, Any]:
    context = valid_context_payloads()[0]
    deck = plan_deck(context).deck_blueprint
    evidence = plan_evidence(deck, context)
    return design_messages(context, deck, evidence).dict()


def example_slide_message_design() -> dict[str, Any]:
    return example_message_designer_output()["slide_messages"][0]


def invalid_slide_message_examples() -> list[dict[str, Any]]:
    base = example_slide_message_design()
    examples: list[dict[str, Any]] = []

    empty_headline = dict(base)
    empty_headline["headline"] = ""
    examples.append(empty_headline)

    long_headline = dict(base)
    long_headline["headline"] = "x" * 80
    examples.append(long_headline)

    placeholder = dict(base)
    placeholder["main_message"] = "TBD"
    examples.append(placeholder)

    unsupported_numeric = dict(base)
    unsupported_numeric["numeric_claims"] = [
        {
            "claim_id": "num-invalid",
            "label": "ROI",
            "value": "120%",
            "basis_evidence_ids": [],
            "confidence": "high",
        }
    ]
    examples.append(unsupported_numeric)

    return examples


def schema_json() -> str:
    return json.dumps(
        {
            "slide_message_design": slide_message_design_schema(),
            "message_designer_input": message_designer_input_schema(),
            "message_designer_output": message_designer_output_schema(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str,
    )
