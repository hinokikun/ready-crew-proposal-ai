"""Shared contract constants for Presentation Engine 2.0 Phase 1."""

from .enums import DiagramType, SlideGoal, VisualType
from .models import (
    MAX_COMPARISON_ITEMS,
    MAX_CONTENT_BLOCKS,
    MAX_HEADLINE_CHARS,
    MAX_MAIN_MESSAGE_CHARS,
    MAX_METRICS,
    MAX_PROCESS_STEPS,
    MAX_TABLE_COLUMNS,
    MAX_TABLE_ROWS,
    MAX_TIMELINE_ITEMS,
)


SUPPORTED_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"

CUSTOMER_PLACEHOLDER_LABELS = {
    "metric 1",
    "view 1",
    "confirm",
    "kpi design 1",
    "slide 1",
    "action 1",
    "comparison 1",
    "timeline 1",
    "tbd",
    "lorem ipsum",
    "placeholder",
    "sample text",
}

VISUAL_DIAGRAM_COMPATIBILITY = {
    VisualType.HERO.value: {DiagramType.NONE.value},
    VisualType.TEXT_ONLY.value: {DiagramType.NONE.value},
    VisualType.TWO_COLUMN.value: {DiagramType.NONE.value, DiagramType.BEFORE_AFTER_FLOW.value},
    VisualType.THREE_COLUMN.value: {DiagramType.NONE.value},
    VisualType.COMPARISON_TABLE.value: {DiagramType.COMPARISON_TABLE.value, DiagramType.FEATURE_MATRIX.value},
    VisualType.KPI_DASHBOARD.value: {DiagramType.KPI_DASHBOARD.value, DiagramType.METRIC_CARDS.value},
    VisualType.TIMELINE.value: {DiagramType.LINEAR_TIMELINE.value},
    VisualType.ROADMAP.value: {DiagramType.ROADMAP_LANES.value},
    VisualType.PROCESS_FLOW.value: {
        DiagramType.PROCESS_FLOW.value,
        DiagramType.SWIMLANE_PROCESS.value,
        DiagramType.AI_PIPELINE.value,
        DiagramType.HUMAN_IN_THE_LOOP.value,
    },
    VisualType.ARCHITECTURE_MAP.value: {
        DiagramType.LAYERED_ARCHITECTURE.value,
        DiagramType.SYSTEM_INTEGRATION_MAP.value,
        DiagramType.DATA_FLOW.value,
    },
    VisualType.MATRIX_2X2.value: {DiagramType.MATRIX_2X2.value},
    VisualType.PYRAMID.value: {DiagramType.ROI_BRIDGE.value},
    VisualType.FUNNEL.value: {DiagramType.NONE.value},
    VisualType.TREE.value: {DiagramType.MATURITY_MODEL.value, DiagramType.STAKEHOLDER_MAP.value},
    VisualType.SWIMLANE.value: {DiagramType.SWIMLANE_PROCESS.value},
    VisualType.RISK_MATRIX.value: {DiagramType.RISK_MATRIX.value},
    VisualType.HEATMAP.value: {DiagramType.NONE.value},
    VisualType.CHART.value: {DiagramType.NONE.value},
    VisualType.TABLE.value: {DiagramType.COMPARISON_TABLE.value, DiagramType.COST_BREAKDOWN.value},
    VisualType.METRIC_CARDS.value: {DiagramType.METRIC_CARDS.value},
    VisualType.IMAGE_PLACEHOLDER.value: {DiagramType.NONE.value},
    VisualType.QUOTE.value: {DiagramType.NONE.value},
    VisualType.CLOSING.value: {DiagramType.NONE.value, DiagramType.NEXT_ACTION_BOARD.value},
}

GOAL_VISUAL_REQUIREMENTS = {
    SlideGoal.COMPARISON.value: "comparison_items",
    SlideGoal.TIMELINE.value: "timeline_items",
    SlideGoal.ROADMAP.value: "timeline_items",
    SlideGoal.PROCESS.value: "process_steps",
    SlideGoal.KPI_DEFINITION.value: "metrics",
    SlideGoal.ROI_EXPLANATION.value: "metrics",
    SlideGoal.ESTIMATE.value: "metrics",
    SlideGoal.PRICING.value: "metrics",
    SlideGoal.NEXT_ACTION.value: "cta",
}

LIMITS = {
    "headline_chars": MAX_HEADLINE_CHARS,
    "main_message_chars": MAX_MAIN_MESSAGE_CHARS,
    "content_blocks": MAX_CONTENT_BLOCKS,
    "metrics": MAX_METRICS,
    "comparison_items": MAX_COMPARISON_ITEMS,
    "timeline_items": MAX_TIMELINE_ITEMS,
    "process_steps": MAX_PROCESS_STEPS,
    "table_columns": MAX_TABLE_COLUMNS,
    "table_rows": MAX_TABLE_ROWS,
    "body_font_floor_pt": 17,
    "headline_font_floor_pt": 28,
    "max_cards": 6,
    "max_reading_order_duplicates": 0,
}
