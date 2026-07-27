"""Fixtures for the Phase 2C Message Designer."""

from __future__ import annotations

import copy
from typing import Any

from ...deck_planner import plan_deck
from ...deck_planner.planner_fixtures import invalid_context_payloads, valid_context_payloads
from ...evidence_planner import plan_evidence


def valid_message_designer_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for context in valid_context_payloads():
        deck = plan_deck(context).deck_blueprint
        evidence = plan_evidence(deck, context)
        payloads.append(
            {
                "proposal_context": copy.deepcopy(context),
                "deck_blueprint": deck.dict(),
                "evidence_planner_output": evidence.dict(),
            }
        )
    return payloads


def invalid_message_designer_payloads() -> list[dict[str, Any]]:
    valid = valid_message_designer_payloads()
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

    extra_key = copy.deepcopy(base)
    extra_key["unexpected"] = "not allowed"
    invalid.append(extra_key)

    invalid_context = copy.deepcopy(base)
    invalid_context["proposal_context"] = invalid_context_payloads()[0]
    invalid.append(invalid_context)

    invalid_deck_version = copy.deepcopy(base)
    invalid_deck_version["deck_blueprint"]["deck_blueprint_version"] = "old"
    invalid.append(invalid_deck_version)

    empty_slide_plan = copy.deepcopy(base)
    empty_slide_plan["deck_blueprint"]["slide_plan"] = []
    invalid.append(empty_slide_plan)

    evidence_deck_mismatch = copy.deepcopy(base)
    evidence_deck_mismatch["evidence_planner_output"]["deck_id"] = "different-deck"
    invalid.append(evidence_deck_mismatch)

    missing_slide_evidence = copy.deepcopy(base)
    missing_slide_evidence["evidence_planner_output"]["slide_evidence"] = missing_slide_evidence[
        "evidence_planner_output"
    ]["slide_evidence"][1:]
    invalid.append(missing_slide_evidence)

    extra_slide_evidence = copy.deepcopy(base)
    extra_slide = copy.deepcopy(extra_slide_evidence["evidence_planner_output"]["slide_evidence"][0])
    extra_slide["slide_blueprint_id"] = "not-in-deck"
    extra_slide_evidence["evidence_planner_output"]["slide_evidence"].append(extra_slide)
    invalid.append(extra_slide_evidence)

    generated_headline_flag = copy.deepcopy(base)
    generated_headline_flag["evidence_planner_output"]["generated_headlines"] = True
    invalid.append(generated_headline_flag)

    generated_body_flag = copy.deepcopy(base)
    generated_body_flag["evidence_planner_output"]["generated_body_text"] = True
    invalid.append(generated_body_flag)

    invalid_evidence_version = copy.deepcopy(base)
    invalid_evidence_version["evidence_planner_output"]["evidence_planner_version"] = "old"
    invalid.append(invalid_evidence_version)

    invalid_evidence_enum = copy.deepcopy(base)
    invalid_evidence_enum["evidence_planner_output"]["slide_evidence"][0]["evidence_priority"] = "urgent"
    invalid.append(invalid_evidence_enum)

    no_slide_blueprint_id = copy.deepcopy(base)
    no_slide_blueprint_id["deck_blueprint"]["slide_plan"][0]["slide_blueprint_id"] = None
    invalid.append(no_slide_blueprint_id)

    return invalid
