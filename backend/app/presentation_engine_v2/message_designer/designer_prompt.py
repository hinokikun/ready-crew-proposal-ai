"""Prompt contract documentation for the offline Phase 2C Message Designer."""

from __future__ import annotations

from typing import Any


def message_designer_prompt_contract() -> dict[str, Any]:
    """Return the intended LLM contract without invoking any model.

    Phase 2C is deterministic and offline. This prompt specification exists so
    later AI-backed phases can preserve the same boundary.
    """

    return {
        "phase": "2C",
        "llm_enabled": False,
        "temperature": 0,
        "system_prompt": (
            "You are Presentation Engine 2.0 Message Designer. Generate only "
            "headline, main_message, supporting_messages, key_takeaway, "
            "speaker_note_summary, evidence alignment, missing evidence "
            "disclosures, warnings, and validation metadata. Do not generate "
            "Slide Blueprints, diagrams, layouts, theme tokens, typography, "
            "charts, images, coordinates, PowerPoint, or customer-unsupported claims."
        ),
        "developer_prompt": (
            "Use Proposal Context, Deck Blueprint, and Evidence Planner output. "
            "Every numeric, ROI, ratio, currency, or period claim must be backed "
            "by explicit Evidence IDs. If evidence is missing, disclose it and "
            "avoid definitive claims. Keep headline <=60 chars, main_message <=120 "
            "chars, supporting_messages <=3 and <=80 chars each."
        ),
        "input_keys": ["proposal_context", "deck_blueprint", "evidence_planner_output"],
        "output_keys": [
            "headline",
            "main_message",
            "supporting_messages",
            "key_takeaway",
            "speaker_note_summary",
            "message_style",
            "message_confidence",
            "evidence_alignment_summary",
            "missing_evidence_disclosure",
            "warnings",
            "validation_result",
        ],
        "forbidden_output_keys": [
            "slide_blueprint",
            "diagram",
            "layout",
            "theme",
            "typography",
            "image",
            "chart",
            "shape",
            "coordinates",
            "pptx",
        ],
        "few_shot_summary": [
            {
                "case": "missing_numeric_evidence",
                "rule": "Return cautious wording and a missing evidence disclosure; do not invent ROI.",
            },
            {
                "case": "executive_summary",
                "rule": "Lead with decision implication and keep support points minimal.",
            },
            {
                "case": "pricing",
                "rule": "Separate estimate, assumption, and confirmation requirement.",
            },
        ],
        "failure_recovery": [
            "If schema validation fails, retry only the invalid fields.",
            "If evidence is missing, lower confidence and add disclosure.",
            "If output requests layout or diagram fields, drop those fields.",
            "If unsupported numeric claims appear, remove them or attach evidence IDs.",
        ],
    }
