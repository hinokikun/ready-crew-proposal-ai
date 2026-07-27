"""Adapters for offline Alpha Integration input and reporting."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..deck_planner.planner_fixtures import valid_context_payloads
from ..deck_planner.planner_models import ProposalContext
from .pipeline_models import AlphaIntegrationCase


def stable_fingerprint(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def context_summary(context: ProposalContext) -> str:
    problems = " / ".join(context.problems[:3]) if context.problems else "Problems not confirmed"
    outcomes = " / ".join(context.expected_outcomes[:3]) if context.expected_outcomes else "Outcomes not confirmed"
    parts = [
        f"Project: {context.project_name or context.project_id or 'not specified'}",
        f"Industry: {context.industry or 'not specified'}",
        f"Category: {context.proposal_category or 'not specified'}",
        f"Purpose: {context.implementation_purpose or context.project_summary}",
        f"Problems: {problems}",
        f"Expected outcomes: {outcomes}",
        f"Decision maker: {context.decision_maker or 'not specified'}",
        f"Budget: {context.budget_range or 'not specified'}",
        f"Timeline: {context.timeline or 'not specified'}",
    ]
    return " / ".join(parts)[:600]


def integration_case_from_context(
    context_payload: dict[str, Any],
    *,
    index: int,
    tags: list[str] | None = None,
) -> AlphaIntegrationCase:
    context = ProposalContext.parse_obj(context_payload)
    case_id = f"alpha-{index + 1:02d}-{context.project_id or stable_fingerprint(context_payload)[:8]}"
    missing: list[str] = []
    if not context.budget_range:
        missing.append("budget_range")
    if not context.competitive_information:
        missing.append("competitive_information")
    if not context.expected_outcomes:
        missing.append("expected_outcomes")
    available = [
        item
        for item, present in {
            "project_summary": bool(context.project_summary),
            "industry": bool(context.industry),
            "proposal_category": bool(context.proposal_category),
            "problems": bool(context.problems),
            "expected_outcomes": bool(context.expected_outcomes),
            "budget_range": bool(context.budget_range),
            "competitive_information": bool(context.competitive_information),
            "timeline": bool(context.timeline),
        }.items()
        if present
    ]
    return AlphaIntegrationCase(
        integration_case_id=case_id,
        case_name=context.project_name or f"Alpha Integration Case {index + 1}",
        proposal_context=context,
        expected_deck_characteristics=[
            "Deck starts with cover and ends with next action or appendix.",
            "Story progresses from problem framing to recommendation and decision.",
            "Slide order remains stable across modules.",
        ],
        expected_evidence_characteristics=[
            "Every planned slide has required evidence.",
            "Numeric slides require numeric evidence.",
            "Missing evidence is explicit and traceable.",
        ],
        expected_message_characteristics=[
            "Headline is conclusion-first.",
            "Main message is evidence-aware.",
            "Missing evidence is disclosed rather than invented.",
        ],
        review_tags=tags or [],
        industry=context.industry,
        proposal_category=context.proposal_category,
        audience=context.persona or context.decision_maker,
        decision_stage="auto",
        deck_length_preference="auto",
        known_constraints=[
            "No customer PII.",
            "No PPTX rendering.",
            "No external AI call.",
        ],
        available_evidence=available,
        intentionally_missing_evidence=missing,
    )


def default_integration_cases(limit: int | None = None) -> list[AlphaIntegrationCase]:
    contexts = valid_context_payloads()
    if limit is not None:
        contexts = contexts[:limit]
    return [
        integration_case_from_context(context, index=index, tags=["default", "synthetic"])
        for index, context in enumerate(contexts)
    ]


def output_to_compact_dict(output: Any) -> dict[str, Any]:
    if hasattr(output, "dict"):
        return output.dict()
    return json.loads(json.dumps(output, ensure_ascii=False, default=str))
