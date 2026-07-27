"""Typed enum definitions for Presentation Engine 2.0 slide blueprints."""

from enum import Enum


class _StrEnum(str, Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class SlideGoal(_StrEnum):
    COVER = "cover"
    AGENDA = "agenda"
    EXECUTIVE_SUMMARY = "executive_summary"
    PROBLEM_SHARING = "problem_sharing"
    CURRENT_STATE = "current_state"
    BACKGROUND = "background"
    MARKET_CONTEXT = "market_context"
    CUSTOMER_INSIGHT = "customer_insight"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    COMPARISON = "comparison"
    ROI_EXPLANATION = "roi_explanation"
    KPI_DEFINITION = "kpi_definition"
    PROPOSAL_OVERVIEW = "proposal_overview"
    SOLUTION_DETAIL = "solution_detail"
    ARCHITECTURE = "architecture"
    PROCESS = "process"
    ROADMAP = "roadmap"
    TIMELINE = "timeline"
    ESTIMATE = "estimate"
    PRICING = "pricing"
    RISK_HANDLING = "risk_handling"
    CASE_STUDY = "case_study"
    TEAM = "team"
    IMPLEMENTATION_PLAN = "implementation_plan"
    FAQ = "faq"
    NEXT_ACTION = "next_action"
    CLOSING = "closing"
    APPENDIX = "appendix"


class AudienceType(_StrEnum):
    CEO = "ceo"
    EXECUTIVE = "executive"
    DEPARTMENT_HEAD = "department_head"
    MANAGER = "manager"
    FIELD_LEADER = "field_leader"
    INFORMATION_SYSTEMS = "information_systems"
    FINANCE = "finance"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    PROCUREMENT = "procurement"
    GENERAL = "general"


class SlideType(_StrEnum):
    COVER = "cover"
    AGENDA = "agenda"
    EXECUTIVE_SUMMARY = "executive_summary"
    KEY_MESSAGE = "key_message"
    CUSTOMER_CONTEXT = "customer_context"
    PROBLEM_STATEMENT = "problem_statement"
    CURRENT_STATE = "current_state"
    ROOT_CAUSE = "root_cause"
    BEFORE_AFTER = "before_after"
    COMPETITIVE_LANDSCAPE = "competitive_landscape"
    COMPETITOR_COMPARISON = "competitor_comparison"
    DIFFERENTIATION = "differentiation"
    RECOMMENDED_STRATEGY = "recommended_strategy"
    PROPOSAL_OVERVIEW = "proposal_overview"
    SOLUTION_CONCEPT = "solution_concept"
    SOLUTION_ARCHITECTURE = "solution_architecture"
    AI_WORKFLOW = "ai_workflow"
    BUSINESS_PROCESS = "business_process"
    FEATURE_OVERVIEW = "feature_overview"
    BENEFIT_OVERVIEW = "benefit_overview"
    KPI_DEFINITION = "kpi_definition"
    ROI_ESTIMATE = "roi_estimate"
    ESTIMATE_OVERVIEW = "estimate_overview"
    TIMELINE = "timeline"
    ROADMAP = "roadmap"
    IMPLEMENTATION_PLAN = "implementation_plan"
    RISK_REGISTER = "risk_register"
    TEAM_STRUCTURE = "team_structure"
    CASE_STUDY = "case_study"
    FAQ = "faq"
    NEXT_ACTION = "next_action"
    CLOSING = "closing"
    APPENDIX = "appendix"


class VisualType(_StrEnum):
    HERO = "hero"
    TEXT_ONLY = "text_only"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    COMPARISON_TABLE = "comparison_table"
    KPI_DASHBOARD = "kpi_dashboard"
    TIMELINE = "timeline"
    ROADMAP = "roadmap"
    PROCESS_FLOW = "process_flow"
    ARCHITECTURE_MAP = "architecture_map"
    MATRIX_2X2 = "matrix_2x2"
    PYRAMID = "pyramid"
    FUNNEL = "funnel"
    TREE = "tree"
    SWIMLANE = "swimlane"
    RISK_MATRIX = "risk_matrix"
    HEATMAP = "heatmap"
    CHART = "chart"
    TABLE = "table"
    METRIC_CARDS = "metric_cards"
    IMAGE_PLACEHOLDER = "image_placeholder"
    QUOTE = "quote"
    CLOSING = "closing"


class DiagramType(_StrEnum):
    NONE = "none"
    LINEAR_TIMELINE = "linear_timeline"
    ROADMAP_LANES = "roadmap_lanes"
    PROCESS_FLOW = "process_flow"
    SWIMLANE_PROCESS = "swimlane_process"
    BEFORE_AFTER_FLOW = "before_after_flow"
    MATRIX_2X2 = "matrix_2x2"
    RISK_MATRIX = "risk_matrix"
    COMPARISON_TABLE = "comparison_table"
    FEATURE_MATRIX = "feature_matrix"
    KPI_DASHBOARD = "kpi_dashboard"
    METRIC_CARDS = "metric_cards"
    LAYERED_ARCHITECTURE = "layered_architecture"
    DATA_FLOW = "data_flow"
    SYSTEM_INTEGRATION_MAP = "system_integration_map"
    AI_PIPELINE = "ai_pipeline"
    HUMAN_IN_THE_LOOP = "human_in_the_loop"
    FEEDBACK_LOOP = "feedback_loop"
    MATURITY_MODEL = "maturity_model"
    STAKEHOLDER_MAP = "stakeholder_map"
    ROI_BRIDGE = "roi_bridge"
    COST_BREAKDOWN = "cost_breakdown"
    NEXT_ACTION_BOARD = "next_action_board"


class ThemeType(_StrEnum):
    CORPORATE = "corporate"
    CONSULTING = "consulting"
    EXECUTIVE = "executive"
    AGENCY = "agency"
    MODERN = "modern"
    MINIMAL = "minimal"
    STARTUP = "startup"
    INVESTOR = "investor"


class HierarchyLevel(_StrEnum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    SUPPORTING = "supporting"


class ContentPriority(_StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AlignmentType(_StrEnum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class LayoutDirection(_StrEnum):
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    TOP_TO_BOTTOM = "top_to_bottom"
    BOTTOM_TO_TOP = "bottom_to_top"
    RADIAL = "radial"
    GRID = "grid"


class DensityLevel(_StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmphasisLevel(_StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HERO = "hero"


class CTAType(_StrEnum):
    NONE = "none"
    APPROVE = "approve"
    DISCUSS = "discuss"
    DECIDE = "decide"
    CONTACT = "contact"
    NEXT_MEETING = "next_meeting"
    START_POC = "start_poc"


class AnimationHint(_StrEnum):
    NONE = "none"
    APPEAR_BY_SECTION = "appear_by_section"
    APPEAR_BY_STEP = "appear_by_step"
    HIGHLIGHT_MAIN_MESSAGE = "highlight_main_message"
    BUILD_TIMELINE = "build_timeline"
    BUILD_PROCESS = "build_process"
    FADE_SUPPORTING_EVIDENCE = "fade_supporting_evidence"


class EvidenceType(_StrEnum):
    USER_INPUT = "user_input"
    CUSTOMER_DOCUMENT = "customer_document"
    INTERVIEW = "interview"
    ANALYSIS = "analysis"
    BENCHMARK = "benchmark"
    ASSUMPTION = "assumption"
    MISSING = "missing"


class DataConfidence(_StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class OverflowStrategy(_StrEnum):
    FIT = "fit"
    COMPRESS = "compress"
    SPLIT = "split"
    DIAGRAMIZE = "diagramize"
    REQUIRE_REVIEW = "require_review"


class ValidationSeverity(_StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class BlueprintStatus(_StrEnum):
    DRAFT = "draft"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    READY_FOR_RENDER = "ready_for_render"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"
