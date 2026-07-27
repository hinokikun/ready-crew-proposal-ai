"""Deck-level contract constants and story arc rules."""

from .deck_enums import (
    AudienceSeniority,
    DeckLengthType,
    DeckValidationSeverity,
    SectionType,
    StoryArcType,
)


DECK_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"

DECK_PLACEHOLDER_LABELS = {
    "section 1",
    "slide 1",
    "action 1",
    "message 1",
    "insight 1",
    "proposal 1",
    "tbd",
    "lorem ipsum",
    "confirm",
    "view 1",
    "metric 1",
    "kpi design 1",
    "internal code",
    "json key",
}

STORY_ARC_SECTION_RULES = {
    StoryArcType.PROBLEM_SOLUTION.value: [
        SectionType.COVER.value,
        SectionType.EXECUTIVE_SUMMARY.value,
        SectionType.BACKGROUND.value,
        SectionType.PROBLEM.value,
        SectionType.INSIGHT.value,
        SectionType.SOLUTION.value,
        SectionType.KPI.value,
        SectionType.ROADMAP.value,
        SectionType.PRICING.value,
        SectionType.NEXT_ACTION.value,
    ],
    StoryArcType.CURRENT_FUTURE.value: [
        SectionType.COVER.value,
        SectionType.EXECUTIVE_SUMMARY.value,
        SectionType.CURRENT_STATE.value,
        SectionType.PROBLEM.value,
        SectionType.OPPORTUNITY.value,
        SectionType.SOLUTION.value,
        SectionType.KPI.value,
        SectionType.ROADMAP.value,
        SectionType.NEXT_ACTION.value,
    ],
    StoryArcType.WHY_WHAT_HOW.value: [
        SectionType.COVER.value,
        SectionType.EXECUTIVE_SUMMARY.value,
        SectionType.BACKGROUND.value,
        SectionType.INSIGHT.value,
        SectionType.SOLUTION.value,
        SectionType.APPROACH.value,
        SectionType.ROADMAP.value,
        SectionType.NEXT_ACTION.value,
    ],
    StoryArcType.INSIGHT_RECOMMENDATION.value: [
        SectionType.COVER.value,
        SectionType.EXECUTIVE_SUMMARY.value,
        SectionType.PROBLEM.value,
        SectionType.INSIGHT.value,
        SectionType.STRATEGY.value,
        SectionType.SOLUTION.value,
        SectionType.KPI.value,
        SectionType.ROADMAP.value,
        SectionType.PRICING.value,
        SectionType.NEXT_ACTION.value,
    ],
    StoryArcType.OPPORTUNITY_SOLUTION_IMPACT.value: [
        SectionType.COVER.value,
        SectionType.EXECUTIVE_SUMMARY.value,
        SectionType.PROBLEM.value,
        SectionType.OPPORTUNITY.value,
        SectionType.SOLUTION.value,
        SectionType.KPI.value,
        SectionType.ROADMAP.value,
        SectionType.PRICING.value,
        SectionType.NEXT_ACTION.value,
    ],
    StoryArcType.DIAGNOSIS_STRATEGY_EXECUTION.value: [
        SectionType.COVER.value,
        SectionType.EXECUTIVE_SUMMARY.value,
        SectionType.CURRENT_STATE.value,
        SectionType.PROBLEM.value,
        SectionType.STRATEGY.value,
        SectionType.SOLUTION.value,
        SectionType.KPI.value,
        SectionType.ROADMAP.value,
        SectionType.PRICING.value,
        SectionType.RISK.value,
        SectionType.NEXT_ACTION.value,
    ],
    StoryArcType.EXECUTIVE_DECISION.value: [
        SectionType.COVER.value,
        SectionType.EXECUTIVE_SUMMARY.value,
        SectionType.PROBLEM.value,
        SectionType.SOLUTION.value,
        SectionType.KPI.value,
        SectionType.ROADMAP.value,
        SectionType.PRICING.value,
        SectionType.RISK.value,
        SectionType.NEXT_ACTION.value,
    ],
}

REQUIRED_SECTION_TYPES = {
    SectionType.COVER.value,
    SectionType.NEXT_ACTION.value,
}

EXECUTIVE_REQUIRED_SECTIONS = {
    SectionType.COVER.value,
    SectionType.EXECUTIVE_SUMMARY.value,
    SectionType.NEXT_ACTION.value,
}

TERMINAL_SECTION_TYPES = {
    SectionType.NEXT_ACTION.value,
    SectionType.CLOSING.value,
    SectionType.APPENDIX.value,
}

APPENDIX_ALLOWED_AFTER = {
    SectionType.NEXT_ACTION.value,
    SectionType.CLOSING.value,
}

DECK_LENGTH_LIMITS = {
    DeckLengthType.SHORT.value: (5, 8),
    DeckLengthType.STANDARD.value: (8, 14),
    DeckLengthType.DETAILED.value: (12, 25),
    DeckLengthType.EXECUTIVE.value: (5, 10),
    DeckLengthType.APPENDIX_HEAVY.value: (12, 40),
}

AUDIENCE_RULES = {
    AudienceSeniority.EXECUTIVE.value: {
        "requires_executive_summary": True,
        "max_target_slide_count": 14,
        "detail_warning_threshold": 16,
    },
    AudienceSeniority.SENIOR_MANAGER.value: {
        "requires_executive_summary": True,
        "max_target_slide_count": 18,
        "detail_warning_threshold": 20,
    },
    AudienceSeniority.FIELD_LEADER.value: {
        "requires_executive_summary": False,
        "max_target_slide_count": 24,
        "detail_warning_threshold": 26,
    },
}

SEVERITY_ORDER = {
    DeckValidationSeverity.ERROR.value: 3,
    DeckValidationSeverity.WARNING.value: 2,
    DeckValidationSeverity.INFO.value: 1,
}

DECK_LIMITS = {
    "deck_title_chars": 120,
    "core_message_chars": 280,
    "sections": 18,
    "slide_plan_items": 40,
    "story_beats": 16,
    "max_same_slide_type_run": 3,
}
