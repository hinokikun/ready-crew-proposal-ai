"""Fixtures for the Phase 2B Evidence Planner."""

from __future__ import annotations

import copy
from typing import Any

from ...deck_planner import plan_deck
from ...deck_planner.planner_fixtures import invalid_context_payloads, valid_context_payloads


def valid_evidence_planning_payloads() -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for context in valid_context_payloads():
        deck = plan_deck(context).deck_blueprint
        payloads.append(
            {
                "deck_blueprint": deck.dict(),
                "proposal_context": copy.deepcopy(context),
            }
        )
    return payloads


def invalid_evidence_planning_payloads() -> list[dict[str, Any]]:
    valid = valid_evidence_planning_payloads()
    base = valid[0]
    invalid: list[dict[str, Any]] = []

    missing_deck = copy.deepcopy(base)
    missing_deck.pop("deck_blueprint")
    invalid.append(missing_deck)

    missing_context = copy.deepcopy(base)
    missing_context.pop("proposal_context")
    invalid.append(missing_context)

    extra_key = copy.deepcopy(base)
    extra_key["unexpected"] = "not allowed"
    invalid.append(extra_key)

    empty_slide_plan = copy.deepcopy(base)
    empty_slide_plan["deck_blueprint"]["slide_plan"] = []
    invalid.append(empty_slide_plan)

    missing_sections = copy.deepcopy(base)
    missing_sections["deck_blueprint"]["sections"] = []
    invalid.append(missing_sections)

    broken_section_ref = copy.deepcopy(base)
    broken_section_ref["deck_blueprint"]["slide_plan"][0]["section_id"] = "missing-section"
    invalid.append(broken_section_ref)

    missing_slide_id = copy.deepcopy(base)
    missing_slide_id["deck_blueprint"]["slide_plan"][0]["slide_blueprint_id"] = None
    invalid.append(missing_slide_id)

    wrong_version = copy.deepcopy(base)
    wrong_version["deck_blueprint"]["deck_blueprint_version"] = "old"
    invalid.append(wrong_version)

    invalid_enum = copy.deepcopy(base)
    invalid_enum["deck_blueprint"]["slide_plan"][0]["slide_goal"] = "unknown"
    invalid.append(invalid_enum)

    invalid_context = copy.deepcopy(base)
    invalid_context["proposal_context"] = invalid_context_payloads()[0]
    invalid.append(invalid_context)

    long_context = copy.deepcopy(base)
    long_context["proposal_context"]["project_summary"] = "x" * 1300
    invalid.append(long_context)

    duplicate_slide_order = copy.deepcopy(base)
    duplicate_slide_order["deck_blueprint"]["slide_plan"][1]["slide_order"] = duplicate_slide_order["deck_blueprint"]["slide_plan"][0]["slide_order"]
    invalid.append(duplicate_slide_order)

    no_next_action = copy.deepcopy(base)
    no_next_action["deck_blueprint"]["sections"] = [
        item for item in no_next_action["deck_blueprint"]["sections"] if item["section_type"] != "next_action"
    ]
    invalid.append(no_next_action)

    no_refs = copy.deepcopy(base)
    no_refs["deck_blueprint"]["slide_blueprint_refs"] = []
    invalid.append(no_refs)

    not_dict = {"deck_blueprint": "not a deck", "proposal_context": base["proposal_context"]}
    invalid.append(not_dict)

    return invalid

