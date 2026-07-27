"""Static contract metadata for Visual Plan Contract foundation."""

from __future__ import annotations


SUPPORTED_VISUAL_PLAN_CONTRACT_VERSION = "pe2_visual_plan_contract_v1"
VISUAL_PLAN_CONTRACT_NAME = "presentation_engine_v2.visual_plan_contract"
VISUAL_PLAN_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"

VISUAL_DIRECTOR_INPUT_CONTRACTS: tuple[str, ...] = (
    "proposal_context",
    "deck_blueprint",
    "evidence_planner_output",
    "message_designer_output",
    "slide_intent_output",
)

VISUAL_PLAN_REQUIRED_OUTPUT_KEYS: tuple[str, ...] = (
    "visual_plan",
    "visual_strategy",
    "layout_strategy",
    "emphasis_strategy",
    "visual_priority",
    "component_candidates",
    "diagram_strategy",
    "chart_strategy",
    "image_strategy",
    "table_strategy",
    "callout_strategy",
    "icon_strategy",
    "risk_flags",
    "confidence",
)

VISUAL_PLAN_BOUNDARY_FLAGS: tuple[str, ...] = (
    "generated_blueprint",
    "generated_theme",
    "generated_coordinates",
    "generated_diagram",
    "generated_chart",
    "generated_pptx",
    "connected_to_runtime",
)

VISUAL_PLAN_PROHIBITED_OUTPUT_FIELDS: tuple[str, ...] = (
    "x",
    "y",
    "width",
    "height",
    "font_size",
    "font_family",
    "color",
    "shape_id",
    "pptx_path",
    "image_url",
)
