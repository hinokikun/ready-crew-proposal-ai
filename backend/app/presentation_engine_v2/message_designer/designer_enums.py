"""Enum definitions for the Phase 2C Message Designer."""

from enum import Enum


class _StrEnum(str, Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class MessageStyle(_StrEnum):
    EXECUTIVE = "executive"
    CONSULTING = "consulting"
    SALES = "sales"
    MARKETING = "marketing"
    TECHNICAL = "technical"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    STRATEGIC = "strategic"
    NEUTRAL = "neutral"


class MessageTone(_StrEnum):
    FORMAL = "formal"
    CONFIDENT = "confident"
    ANALYTICAL = "analytical"
    PERSUASIVE = "persuasive"
    CONCISE = "concise"
    SUPPORTIVE = "supportive"
    URGENT = "urgent"
    CAUTIOUS = "cautious"


class MessageStrength(_StrEnum):
    STRONG = "strong"
    CLEAR = "clear"
    MODERATE = "moderate"
    WEAK = "weak"
    BLOCKED = "blocked"


class MessagePurpose(_StrEnum):
    FRAME_DECISION = "frame_decision"
    ALIGN_CONTEXT = "align_context"
    EXPLAIN_PROBLEM = "explain_problem"
    SHARE_INSIGHT = "share_insight"
    RECOMMEND_ACTION = "recommend_action"
    PROVE_VALUE = "prove_value"
    COMPARE_OPTIONS = "compare_options"
    EXPLAIN_INVESTMENT = "explain_investment"
    REDUCE_RISK = "reduce_risk"
    CLOSE_NEXT_STEP = "close_next_step"


class MessageConfidence(_StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BLOCKED = "blocked"


class EvidenceAlignmentLevel(_StrEnum):
    EVIDENCE_SUPPORTED = "evidence_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    ASSUMPTION_REQUIRED = "assumption_required"
    EVIDENCE_MISSING = "evidence_missing"
    NOT_APPLICABLE = "not_applicable"


class MessageRiskLevel(_StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKING = "blocking"


class DisclosureType(_StrEnum):
    NONE = "none"
    ASSUMPTION = "assumption"
    TRIAL_CALCULATION = "trial_calculation"
    CURRENT_HYPOTHESIS = "current_hypothesis"
    NEEDS_CONFIRMATION = "needs_confirmation"
    PUBLIC_INFORMATION_SCOPE = "public_information_scope"
    CONFIRM_AFTER_CONDITIONS = "confirm_after_conditions"


class MessageValidationSeverity(_StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class MessageStatus(_StrEnum):
    DRAFT = "draft"
    NORMALIZED = "normalized"
    VALIDATED = "validated"
    NEEDS_REVIEW = "needs_review"
    INVALID = "invalid"

