"""Fixtures for Presentation Engine 2.0 Alpha Integration Review."""

from __future__ import annotations

import copy
from typing import Any

from ...deck_planner.planner_fixtures import valid_context_payloads
from ..pipeline_adapters import default_integration_cases


def valid_alpha_integration_cases() -> list[Any]:
    return copy.deepcopy(default_integration_cases())


def invalid_alpha_integration_cases() -> list[dict[str, Any]]:
    valid = [case.dict() for case in valid_alpha_integration_cases()]
    base = valid[0]
    invalid: list[dict[str, Any]] = []

    missing_context = copy.deepcopy(base)
    missing_context.pop("proposal_context")
    invalid.append(missing_context)

    empty_id = copy.deepcopy(base)
    empty_id["integration_case_id"] = ""
    invalid.append(empty_id)

    bad_version = copy.deepcopy(base)
    bad_version["schema_version"] = "old"
    invalid.append(bad_version)

    extra_key = copy.deepcopy(base)
    extra_key["unexpected"] = "not allowed"
    invalid.append(extra_key)

    bad_context_summary = copy.deepcopy(base)
    bad_context_summary["proposal_context"]["project_summary"] = ""
    invalid.append(bad_context_summary)

    bad_context_extra = copy.deepcopy(base)
    bad_context_extra["proposal_context"]["unexpected"] = "not allowed"
    invalid.append(bad_context_extra)

    bad_problems = copy.deepcopy(base)
    bad_problems["proposal_context"]["problems"] = ["problem"] * 20
    invalid.append(bad_problems)

    bad_outcomes = copy.deepcopy(base)
    bad_outcomes["proposal_context"]["expected_outcomes"] = ["outcome"] * 20
    invalid.append(bad_outcomes)

    long_name = copy.deepcopy(base)
    long_name["case_name"] = "x" * 200
    invalid.append(long_name)

    too_many_tags = copy.deepcopy(base)
    too_many_tags["review_tags"] = [f"tag-{index}" for index in range(30)]
    invalid.append(too_many_tags)

    too_many_available = copy.deepcopy(base)
    too_many_available["available_evidence"] = [f"evidence-{index}" for index in range(40)]
    invalid.append(too_many_available)

    bad_constraints = copy.deepcopy(base)
    bad_constraints["known_constraints"] = ["constraint"] * 30
    invalid.append(bad_constraints)

    bad_language = copy.deepcopy(base)
    bad_language["proposal_context"]["language"] = "j"
    invalid.append(bad_language)

    long_budget = copy.deepcopy(base)
    long_budget["proposal_context"]["budget_range"] = "x" * 200
    invalid.append(long_budget)

    not_context = copy.deepcopy(base)
    not_context["proposal_context"] = "not a context"
    invalid.append(not_context)

    return invalid


def valid_alpha_context_payloads() -> list[dict[str, Any]]:
    return copy.deepcopy(valid_context_payloads())
