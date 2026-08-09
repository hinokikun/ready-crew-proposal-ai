"""Feature flag and contract constants for Presentation Design AI."""

from __future__ import annotations

import os


FEATURE_FLAG_NAME = "PRESENTATION_DESIGN_AI_V9_ENABLED"
DEFAULT_FEATURE_FLAG_VALUE = False
DESIGN_VERSION = "presentation_design_ai_v9"


def is_presentation_design_ai_enabled() -> bool:
    value = os.getenv(FEATURE_FLAG_NAME, "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


REQUIRED_CONTRACT_FIELDS = (
    "slide_id",
    "section_id",
    "page_goal",
    "audience",
    "decision_stage",
    "action_title",
    "core_message",
    "supporting_evidence",
    "expected_emotion",
    "visual_metaphor",
    "diagram_type",
    "composition_type",
    "information_priority",
    "reading_order",
    "focal_point",
    "secondary_point",
    "takeaway",
    "speaker_note_summary",
    "expected_question",
    "previous_slide_connection",
    "next_slide_transition",
    "text_density_target",
    "diagram_ratio_target",
    "color_role",
    "component_ids",
    "source_basis",
    "confidence",
    "human_review_reason",
)
