"""Fixtures for Phase 2D Slide Intent Foundation."""

from __future__ import annotations

import copy
from typing import Any

from ...deck_planner import plan_deck
from ...deck_planner.planner_fixtures import valid_context_payloads
from ...evidence_planner import plan_evidence
from ...message_designer import design_messages


def _payload_from_context(context_payload: dict[str, Any]) -> dict[str, Any]:
    deck = plan_deck(context_payload).deck_blueprint
    evidence = plan_evidence(deck, context_payload)
    message = design_messages(context_payload, deck, evidence)
    return {
        "proposal_context": context_payload,
        "deck_blueprint": deck.dict(),
        "evidence_planner_output": evidence.dict(),
        "message_designer_output": message.dict(),
    }


def valid_slide_intent_payloads(limit: int | None = None) -> list[dict[str, Any]]:
    contexts = valid_context_payloads()
    if limit is not None:
        contexts = contexts[:limit]
    return [_payload_from_context(context) for context in contexts]


def invalid_slide_intent_payloads() -> list[dict[str, Any]]:
    valid = valid_slide_intent_payloads(limit=3)
    base = valid[0]
    invalid: list[dict[str, Any]] = []

    missing_context = copy.deepcopy(base)
    missing_context.pop("proposal_context")
    invalid.append(missing_context)

    missing_deck = copy.deepcopy(base)
    missing_deck.pop("deck_blueprint")
    invalid.append(missing_deck)

    missing_evidence = copy.deepcopy(base)
    missing_evidence.pop("evidence_planner_output")
    invalid.append(missing_evidence)

    missing_message = copy.deepcopy(base)
    missing_message.pop("message_designer_output")
    invalid.append(missing_message)

    extra_key = copy.deepcopy(base)
    extra_key["unexpected"] = "not allowed"
    invalid.append(extra_key)

    bad_deck_id_message = copy.deepcopy(base)
    bad_deck_id_message["message_designer_output"]["deck_id"] = "another-deck"
    invalid.append(bad_deck_id_message)

    bad_deck_id_evidence = copy.deepcopy(base)
    bad_deck_id_evidence["evidence_planner_output"]["deck_id"] = "another-deck"
    invalid.append(bad_deck_id_evidence)

    missing_slide_message = copy.deepcopy(base)
    missing_slide_message["message_designer_output"]["slide_messages"] = missing_slide_message["message_designer_output"][
        "slide_messages"
    ][1:]
    invalid.append(missing_slide_message)

    missing_slide_evidence = copy.deepcopy(base)
    missing_slide_evidence["evidence_planner_output"]["slide_evidence"] = missing_slide_evidence[
        "evidence_planner_output"
    ]["slide_evidence"][1:]
    invalid.append(missing_slide_evidence)

    generated_pptx = copy.deepcopy(base)
    generated_pptx["message_designer_output"]["generated_pptx"] = True
    invalid.append(generated_pptx)

    generated_diagrams = copy.deepcopy(base)
    generated_diagrams["message_designer_output"]["generated_diagrams"] = True
    invalid.append(generated_diagrams)

    connected_runtime = copy.deepcopy(base)
    connected_runtime["message_designer_output"]["connected_to_runtime"] = True
    invalid.append(connected_runtime)

    empty_deck_slides = copy.deepcopy(base)
    empty_deck_slides["deck_blueprint"]["slide_plan"] = []
    invalid.append(empty_deck_slides)

    bad_context = copy.deepcopy(base)
    bad_context["proposal_context"]["project_summary"] = ""
    invalid.append(bad_context)

    not_payload = {"proposal_context": "not a context"}
    invalid.append(not_payload)

    return invalid
