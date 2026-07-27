"""Enum definitions for Presentation Engine 2.0 Phase 2D Slide Intent."""

from enum import Enum


class _StrEnum(str, Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class SlideIntentType(_StrEnum):
    FRAME_DECISION = "frame_decision"
    SUMMARIZE = "summarize"
    ALIGN_CONTEXT = "align_context"
    EXPLAIN_PROBLEM = "explain_problem"
    SHARE_INSIGHT = "share_insight"
    COMPARE_OPTIONS = "compare_options"
    RECOMMEND_ACTION = "recommend_action"
    PROVE_VALUE = "prove_value"
    EXPLAIN_INVESTMENT = "explain_investment"
    SHOW_PLAN = "show_plan"
    EXPLAIN_PROCESS = "explain_process"
    SHOW_HIERARCHY = "show_hierarchy"
    REDUCE_RISK = "reduce_risk"
    CLOSE_NEXT_STEP = "close_next_step"


class SlideType(_StrEnum):
    COVER = "cover"
    AGENDA = "agenda"
    EXECUTIVE_SUMMARY = "executive_summary"
    PROBLEM = "problem"
    CURRENT_STATE = "current_state"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"
    PROPOSAL = "proposal"
    FEATURE = "feature"
    BENEFIT = "benefit"
    TIMELINE = "timeline"
    ROADMAP = "roadmap"
    ESTIMATE = "estimate"
    KPI = "kpi"
    CASE_STUDY = "case_study"
    RISK = "risk"
    FAQ = "faq"
    SUMMARY = "summary"
    NEXT_ACTION = "next_action"
    CLOSING = "closing"
    APPENDIX = "appendix"


class VisualPattern(_StrEnum):
    HERO = "hero"
    SUMMARY_CARDS = "summary_cards"
    CALLOUT = "callout"
    COMPARISON = "comparison"
    KPI_CARDS = "kpi_cards"
    TIMELINE = "timeline"
    ROADMAP = "roadmap"
    PROCESS = "process"
    HIERARCHY = "hierarchy"
    CHECKLIST = "checklist"
    IMAGE_DOMINANT = "image_dominant"
    TEXT_DOMINANT = "text_dominant"
    NUMBER_DOMINANT = "number_dominant"
    TABLE = "table"
    MATRIX = "matrix"


class ReadingOrder(_StrEnum):
    TITLE_FIRST = "title_first"
    TOP_TO_BOTTOM = "top_to_bottom"
    LEFT_TO_RIGHT = "left_to_right"
    CENTER_OUT = "center_out"
    Z_PATTERN = "z_pattern"
    BEFORE_AFTER = "before_after"
    TIMELINE = "timeline"
    HIERARCHY = "hierarchy"
    SCAN_CARDS = "scan_cards"


class InformationDensity(_StrEnum):
    INSUFFICIENT = "insufficient"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXCESSIVE = "excessive"


class DiagramCandidate(_StrEnum):
    NONE = "none"
    COMPARISON_TABLE = "comparison_table"
    TIMELINE = "timeline"
    ROADMAP = "roadmap"
    PROCESS_FLOW = "process_flow"
    HIERARCHY_TREE = "hierarchy_tree"
    BEFORE_AFTER_FLOW = "before_after_flow"
    KPI_CARDS = "kpi_cards"
    MATRIX = "matrix"
    CHECKLIST = "checklist"
    ARCHITECTURE_MAP = "architecture_map"
    CALLOUT = "callout"
    IMAGE_PLACEHOLDER = "image_placeholder"
    COST_BREAKDOWN = "cost_breakdown"


class ChartCandidate(_StrEnum):
    NONE = "none"
    BAR = "bar"
    LINE = "line"
    GAUGE = "gauge"
    WATERFALL = "waterfall"
    KPI_CARD = "kpi_card"


class LayoutConstraint(_StrEnum):
    KEEP_SINGLE_MESSAGE = "keep_single_message"
    NO_LAYOUT_GENERATED = "no_layout_generated"
    REQUIRE_NUMERIC_EVIDENCE = "require_numeric_evidence"
    SHOW_EVIDENCE_GAP = "show_evidence_gap"
    SPLIT_IF_DENSE = "split_if_dense"
    AVOID_FAKE_NUMBERS = "avoid_fake_numbers"
    IMAGE_PLACEHOLDER_ONLY = "image_placeholder_only"
    KEEP_CTA_VISIBLE = "keep_cta_visible"


class IntentConfidence(_StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BLOCKED = "blocked"


class ValidationSeverity(_StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
