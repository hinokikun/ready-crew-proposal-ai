"""Static rules for Visual Plan Contract validation and future Visual Director."""

from __future__ import annotations

from .enums import (
    CalloutStrategy,
    ChartStrategy,
    DiagramStrategy,
    IconStrategy,
    ImageStrategy,
    LayoutStrategy,
    TableStrategy,
    VisualReadingOrder,
    VisualStrategy,
)


VISUAL_PATTERN_DEFAULTS: dict[str, dict[str, str]] = {
    "hero": {
        "visual_strategy": VisualStrategy.EXECUTIVE_FRAME.value,
        "layout_strategy": LayoutStrategy.HERO_FOCUS.value,
        "reading_order": VisualReadingOrder.CENTER_OUT.value,
        "diagram_strategy": DiagramStrategy.NONE.value,
        "image_strategy": ImageStrategy.ABSTRACT_PLACEHOLDER.value,
    },
    "summary_cards": {
        "visual_strategy": VisualStrategy.DECISION_SUMMARY.value,
        "layout_strategy": LayoutStrategy.CARD_GRID.value,
        "reading_order": VisualReadingOrder.SCAN_CARDS.value,
        "diagram_strategy": DiagramStrategy.CALLOUT.value,
    },
    "comparison": {
        "visual_strategy": VisualStrategy.COMPARISON.value,
        "layout_strategy": LayoutStrategy.SPLIT_COMPARISON.value,
        "reading_order": VisualReadingOrder.BEFORE_AFTER.value,
        "diagram_strategy": DiagramStrategy.COMPARISON_TABLE.value,
        "table_strategy": TableStrategy.SIMPLE_COMPARISON.value,
    },
    "kpi_cards": {
        "visual_strategy": VisualStrategy.EVIDENCE_FIRST.value,
        "layout_strategy": LayoutStrategy.METRIC_FOCUS.value,
        "reading_order": VisualReadingOrder.SCAN_CARDS.value,
        "chart_strategy": ChartStrategy.KPI_CARD.value,
    },
    "timeline": {
        "visual_strategy": VisualStrategy.ROADMAP_STORY.value,
        "layout_strategy": LayoutStrategy.ROADMAP_LANE.value,
        "reading_order": VisualReadingOrder.TIMELINE.value,
        "diagram_strategy": DiagramStrategy.TIMELINE.value,
    },
    "roadmap": {
        "visual_strategy": VisualStrategy.ROADMAP_STORY.value,
        "layout_strategy": LayoutStrategy.ROADMAP_LANE.value,
        "reading_order": VisualReadingOrder.TIMELINE.value,
        "diagram_strategy": DiagramStrategy.ROADMAP.value,
    },
    "process": {
        "visual_strategy": VisualStrategy.PROCESS_EXPLANATION.value,
        "layout_strategy": LayoutStrategy.PROCESS_LANE.value,
        "reading_order": VisualReadingOrder.LEFT_TO_RIGHT.value,
        "diagram_strategy": DiagramStrategy.PROCESS_FLOW.value,
    },
    "hierarchy": {
        "visual_strategy": VisualStrategy.PROCESS_EXPLANATION.value,
        "layout_strategy": LayoutStrategy.MATRIX_VIEW.value,
        "reading_order": VisualReadingOrder.HIERARCHY.value,
        "diagram_strategy": DiagramStrategy.HIERARCHY_TREE.value,
    },
    "checklist": {
        "visual_strategy": VisualStrategy.CLOSING_ACTION.value,
        "layout_strategy": LayoutStrategy.CHECKLIST_FLOW.value,
        "reading_order": VisualReadingOrder.TOP_TO_BOTTOM.value,
        "diagram_strategy": DiagramStrategy.CHECKLIST.value,
        "callout_strategy": CalloutStrategy.NEXT_ACTION.value,
        "icon_strategy": IconStrategy.ACTION.value,
    },
    "matrix": {
        "visual_strategy": VisualStrategy.EVIDENCE_FIRST.value,
        "layout_strategy": LayoutStrategy.MATRIX_VIEW.value,
        "reading_order": VisualReadingOrder.Z_PATTERN.value,
        "diagram_strategy": DiagramStrategy.MATRIX.value,
        "table_strategy": TableStrategy.DECISION_MATRIX.value,
    },
    "table": {
        "visual_strategy": VisualStrategy.EVIDENCE_FIRST.value,
        "layout_strategy": LayoutStrategy.TABLE_FIRST.value,
        "reading_order": VisualReadingOrder.LEFT_TO_RIGHT.value,
        "table_strategy": TableStrategy.EVIDENCE_TABLE.value,
    },
    "number_dominant": {
        "visual_strategy": VisualStrategy.INVESTMENT_CASE.value,
        "layout_strategy": LayoutStrategy.METRIC_FOCUS.value,
        "reading_order": VisualReadingOrder.CENTER_OUT.value,
        "chart_strategy": ChartStrategy.WATERFALL.value,
    },
    "image_dominant": {
        "visual_strategy": VisualStrategy.MESSAGE_FIRST.value,
        "layout_strategy": LayoutStrategy.IMAGE_SUPPORT.value,
        "reading_order": VisualReadingOrder.Z_PATTERN.value,
        "image_strategy": ImageStrategy.PLACEHOLDER_ONLY.value,
    },
    "text_dominant": {
        "visual_strategy": VisualStrategy.MESSAGE_FIRST.value,
        "layout_strategy": LayoutStrategy.TEXT_SUPPORT.value,
        "reading_order": VisualReadingOrder.TOP_TO_BOTTOM.value,
    },
    "callout": {
        "visual_strategy": VisualStrategy.MESSAGE_FIRST.value,
        "layout_strategy": LayoutStrategy.CALLOUT_FOCUS.value,
        "reading_order": VisualReadingOrder.TITLE_FIRST.value,
        "callout_strategy": CalloutStrategy.KEY_TAKEAWAY.value,
    },
}


READING_ORDER_BY_LAYOUT: dict[LayoutStrategy, set[VisualReadingOrder]] = {
    LayoutStrategy.HERO_FOCUS: {VisualReadingOrder.CENTER_OUT, VisualReadingOrder.TITLE_FIRST},
    LayoutStrategy.SPLIT_COMPARISON: {VisualReadingOrder.BEFORE_AFTER, VisualReadingOrder.LEFT_TO_RIGHT},
    LayoutStrategy.CARD_GRID: {VisualReadingOrder.SCAN_CARDS, VisualReadingOrder.TOP_TO_BOTTOM},
    LayoutStrategy.PROCESS_LANE: {VisualReadingOrder.LEFT_TO_RIGHT, VisualReadingOrder.TOP_TO_BOTTOM},
    LayoutStrategy.ROADMAP_LANE: {VisualReadingOrder.TIMELINE},
    LayoutStrategy.METRIC_FOCUS: {VisualReadingOrder.CENTER_OUT, VisualReadingOrder.SCAN_CARDS},
    LayoutStrategy.MATRIX_VIEW: {VisualReadingOrder.Z_PATTERN, VisualReadingOrder.HIERARCHY},
    LayoutStrategy.TABLE_FIRST: {VisualReadingOrder.LEFT_TO_RIGHT, VisualReadingOrder.TOP_TO_BOTTOM},
    LayoutStrategy.CALLOUT_FOCUS: {VisualReadingOrder.TITLE_FIRST, VisualReadingOrder.CENTER_OUT},
    LayoutStrategy.IMAGE_SUPPORT: {VisualReadingOrder.Z_PATTERN, VisualReadingOrder.LEFT_TO_RIGHT},
    LayoutStrategy.TEXT_SUPPORT: {VisualReadingOrder.TOP_TO_BOTTOM, VisualReadingOrder.TITLE_FIRST},
    LayoutStrategy.CHECKLIST_FLOW: {VisualReadingOrder.TOP_TO_BOTTOM},
}


DIAGRAM_CHART_CONFLICTS: set[tuple[DiagramStrategy, ChartStrategy]] = {
    (DiagramStrategy.COMPARISON_TABLE, ChartStrategy.BAR),
    (DiagramStrategy.COMPARISON_TABLE, ChartStrategy.LINE),
    (DiagramStrategy.TIMELINE, ChartStrategy.LINE),
    (DiagramStrategy.ROADMAP, ChartStrategy.WATERFALL),
    (DiagramStrategy.PROCESS_FLOW, ChartStrategy.BAR),
    (DiagramStrategy.MATRIX, ChartStrategy.LINE),
}


CHARTS_REQUIRING_NUMERIC_EVIDENCE: set[ChartStrategy] = {
    ChartStrategy.BAR,
    ChartStrategy.LINE,
    ChartStrategy.GAUGE,
    ChartStrategy.WATERFALL,
    ChartStrategy.KPI_CARD,
}


PLACEHOLDER_TOKENS: tuple[str, ...] = ("todo", "{{", "}}", "tbd", "dummy", "placeholder")


def expected_defaults_for_visual_pattern(pattern: str | None) -> dict[str, str]:
    if not pattern:
        return {}
    return VISUAL_PATTERN_DEFAULTS.get(str(pattern), {})


def reading_order_allowed(layout: LayoutStrategy, reading_order: VisualReadingOrder) -> bool:
    return reading_order in READING_ORDER_BY_LAYOUT.get(layout, {reading_order})
