"""Enum definitions for the Visual Plan Contract."""

from enum import Enum


class _StrEnum(str, Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class VisualStrategy(_StrEnum):
    MESSAGE_FIRST = "message_first"
    EVIDENCE_FIRST = "evidence_first"
    COMPARISON = "comparison"
    PROCESS_EXPLANATION = "process_explanation"
    DECISION_SUMMARY = "decision_summary"
    RISK_REDUCTION = "risk_reduction"
    INVESTMENT_CASE = "investment_case"
    ROADMAP_STORY = "roadmap_story"
    EXECUTIVE_FRAME = "executive_frame"
    CLOSING_ACTION = "closing_action"


class LayoutStrategy(_StrEnum):
    HERO_FOCUS = "hero_focus"
    SPLIT_COMPARISON = "split_comparison"
    CARD_GRID = "card_grid"
    PROCESS_LANE = "process_lane"
    ROADMAP_LANE = "roadmap_lane"
    METRIC_FOCUS = "metric_focus"
    MATRIX_VIEW = "matrix_view"
    TABLE_FIRST = "table_first"
    CALLOUT_FOCUS = "callout_focus"
    IMAGE_SUPPORT = "image_support"
    TEXT_SUPPORT = "text_support"
    CHECKLIST_FLOW = "checklist_flow"


class EmphasisStrategy(_StrEnum):
    HEADLINE = "headline"
    MAIN_MESSAGE = "main_message"
    KEY_NUMBER = "key_number"
    CONTRAST = "contrast"
    RISK = "risk"
    NEXT_ACTION = "next_action"
    EVIDENCE_GAP = "evidence_gap"
    PROOF = "proof"


class VisualPriorityLevel(_StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUPPORTING = "supporting"
    MUTED = "muted"


class ComponentCandidateType(_StrEnum):
    HEADLINE_BLOCK = "headline_block"
    MAIN_MESSAGE_BLOCK = "main_message_block"
    SUPPORTING_CARD = "supporting_card"
    EVIDENCE_CALLOUT = "evidence_callout"
    COMPARISON_PANEL = "comparison_panel"
    METRIC_CARD = "metric_card"
    TIMELINE_ITEM = "timeline_item"
    ROADMAP_MILESTONE = "roadmap_milestone"
    PROCESS_STEP = "process_step"
    RISK_BADGE = "risk_badge"
    IMAGE_PLACEHOLDER = "image_placeholder"
    ICON_CLUSTER = "icon_cluster"
    TABLE_SHELL = "table_shell"
    CTA_BLOCK = "cta_block"


class DiagramStrategy(_StrEnum):
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
    COST_BREAKDOWN = "cost_breakdown"


class ChartStrategy(_StrEnum):
    NONE = "none"
    BAR = "bar"
    LINE = "line"
    GAUGE = "gauge"
    WATERFALL = "waterfall"
    KPI_CARD = "kpi_card"


class ImageStrategy(_StrEnum):
    NONE = "none"
    PLACEHOLDER_ONLY = "placeholder_only"
    CUSTOMER_ASSET_REQUIRED = "customer_asset_required"
    ABSTRACT_PLACEHOLDER = "abstract_placeholder"
    SCREENSHOT_PLACEHOLDER = "screenshot_placeholder"


class TableStrategy(_StrEnum):
    NONE = "none"
    SIMPLE_COMPARISON = "simple_comparison"
    ESTIMATE_SUMMARY = "estimate_summary"
    RISK_MATRIX = "risk_matrix"
    DECISION_MATRIX = "decision_matrix"
    EVIDENCE_TABLE = "evidence_table"


class CalloutStrategy(_StrEnum):
    NONE = "none"
    KEY_TAKEAWAY = "key_takeaway"
    EVIDENCE_GAP = "evidence_gap"
    RISK_WARNING = "risk_warning"
    NEXT_ACTION = "next_action"
    ASSUMPTION = "assumption"


class IconStrategy(_StrEnum):
    NONE = "none"
    FUNCTIONAL = "functional"
    STATUS = "status"
    INDUSTRY = "industry"
    EVIDENCE = "evidence"
    ACTION = "action"


class VisualReadingOrder(_StrEnum):
    TITLE_FIRST = "title_first"
    TOP_TO_BOTTOM = "top_to_bottom"
    LEFT_TO_RIGHT = "left_to_right"
    CENTER_OUT = "center_out"
    Z_PATTERN = "z_pattern"
    BEFORE_AFTER = "before_after"
    TIMELINE = "timeline"
    HIERARCHY = "hierarchy"
    SCAN_CARDS = "scan_cards"


class VisualConfidence(_StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BLOCKED = "blocked"


class VisualPlanStatus(_StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    BLOCKED = "blocked"


class ValidationSeverity(_StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
