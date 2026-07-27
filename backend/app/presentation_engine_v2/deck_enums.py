"""Deck-level enum definitions for Presentation Engine 2.0 Phase 1.5."""

from enum import Enum


class _StrEnum(str, Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class DeckGoal(_StrEnum):
    INFORM = "inform"
    DIAGNOSE = "diagnose"
    PERSUADE = "persuade"
    COMPARE = "compare"
    RECOMMEND = "recommend"
    APPROVE = "approve"
    SELL = "sell"
    ALIGN = "align"
    DECIDE = "decide"


class DeckType(_StrEnum):
    SALES_PROPOSAL = "sales_proposal"
    EXECUTIVE_PROPOSAL = "executive_proposal"
    CONSULTING_PROPOSAL = "consulting_proposal"
    WEB_PRODUCTION_PROPOSAL = "web_production_proposal"
    SAAS_INTRODUCTION = "saas_introduction"
    PROJECT_PLAN = "project_plan"
    RENEWAL_PROPOSAL = "renewal_proposal"
    COMPETITIVE_PITCH = "competitive_pitch"
    INVESTMENT_PITCH = "investment_pitch"
    INTERNAL_APPROVAL = "internal_approval"


class AudienceSeniority(_StrEnum):
    EXECUTIVE = "executive"
    SENIOR_MANAGER = "senior_manager"
    MANAGER = "manager"
    FIELD_LEADER = "field_leader"
    PRACTITIONER = "practitioner"
    MIXED = "mixed"


class DecisionStage(_StrEnum):
    AWARENESS = "awareness"
    DISCOVERY = "discovery"
    COMPARISON = "comparison"
    APPROVAL = "approval"
    PROCUREMENT = "procurement"
    RENEWAL = "renewal"
    INTERNAL_ALIGNMENT = "internal_alignment"


class StoryArcType(_StrEnum):
    PROBLEM_SOLUTION = "problem_solution"
    CURRENT_FUTURE = "current_future"
    WHY_WHAT_HOW = "why_what_how"
    INSIGHT_RECOMMENDATION = "insight_recommendation"
    OPPORTUNITY_SOLUTION_IMPACT = "opportunity_solution_impact"
    DIAGNOSIS_STRATEGY_EXECUTION = "diagnosis_strategy_execution"
    EXECUTIVE_DECISION = "executive_decision"
    CUSTOM = "custom"


class SectionType(_StrEnum):
    COVER = "cover"
    EXECUTIVE_SUMMARY = "executive_summary"
    BACKGROUND = "background"
    CURRENT_STATE = "current_state"
    PROBLEM = "problem"
    INSIGHT = "insight"
    OPPORTUNITY = "opportunity"
    MARKET = "market"
    COMPETITOR = "competitor"
    STRATEGY = "strategy"
    SOLUTION = "solution"
    SCOPE = "scope"
    DELIVERABLES = "deliverables"
    APPROACH = "approach"
    ROADMAP = "roadmap"
    TIMELINE = "timeline"
    TEAM = "team"
    CASE_STUDY = "case_study"
    KPI = "kpi"
    ROI = "roi"
    PRICING = "pricing"
    ESTIMATE = "estimate"
    RISK = "risk"
    FAQ = "faq"
    NEXT_ACTION = "next_action"
    CLOSING = "closing"
    APPENDIX = "appendix"


class SlideRole(_StrEnum):
    OPENING = "opening"
    SUMMARY = "summary"
    CONTEXT = "context"
    PROBLEM = "problem"
    INSIGHT = "insight"
    PROOF = "proof"
    RECOMMENDATION = "recommendation"
    PLAN = "plan"
    DECISION = "decision"
    SUPPORT = "support"
    CLOSING = "closing"
    APPENDIX = "appendix"


class NarrativeFunction(_StrEnum):
    HOOK = "hook"
    FRAME = "frame"
    DIAGNOSE = "diagnose"
    EXPLAIN = "explain"
    COMPARE = "compare"
    PROVE = "prove"
    RECOMMEND = "recommend"
    QUANTIFY = "quantify"
    DE_RISK = "de_risk"
    ASK = "ask"
    CLOSE = "close"


class TransitionType(_StrEnum):
    NONE = "none"
    CONTINUE = "continue"
    CONTRAST = "contrast"
    CAUSE_EFFECT = "cause_effect"
    PROBLEM_TO_SOLUTION = "problem_to_solution"
    VALUE_TO_PRICE = "value_to_price"
    RISK_TO_MITIGATION = "risk_to_mitigation"
    SUMMARY_TO_ACTION = "summary_to_action"


class DeckLengthType(_StrEnum):
    SHORT = "short"
    STANDARD = "standard"
    DETAILED = "detailed"
    EXECUTIVE = "executive"
    APPENDIX_HEAVY = "appendix_heavy"


class EvidenceStrategy(_StrEnum):
    LIGHT = "light"
    BALANCED = "balanced"
    DATA_DRIVEN = "data_driven"
    CASE_STUDY_DRIVEN = "case_study_driven"
    EXECUTIVE_SUMMARY = "executive_summary"


class PersuasionStrategy(_StrEnum):
    ROI = "roi"
    RISK_REDUCTION = "risk_reduction"
    QUALITY_IMPROVEMENT = "quality_improvement"
    SPEED = "speed"
    DIFFERENTIATION = "differentiation"
    DX = "dx"
    AI_ADOPTION = "ai_adoption"
    COST_REDUCTION = "cost_reduction"
    GROWTH = "growth"


class RiskLevel(_StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DecisionUrgency(_StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    IMMEDIATE = "immediate"


class DeckStatus(_StrEnum):
    DRAFT = "draft"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    READY_FOR_STORY_REVIEW = "ready_for_story_review"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"


class DeckValidationSeverity(_StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
