"""Deck Blueprint models for Presentation Engine 2.0 Phase 1.5."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .deck_enums import (
    AudienceSeniority,
    DecisionStage,
    DecisionUrgency,
    DeckGoal,
    DeckLengthType,
    DeckStatus,
    DeckType,
    DeckValidationSeverity,
    EvidenceStrategy,
    NarrativeFunction,
    PersuasionStrategy,
    RiskLevel,
    SectionType,
    SlideRole,
    StoryArcType,
    TransitionType,
)
from .deck_errors import SUPPORTED_DECK_BLUEPRINT_VERSION
from .enums import AudienceType, SlideGoal, SlideType, ThemeType
from .models import SlideBlueprint, SourceReference


MAX_DECK_TITLE_CHARS = 120
MAX_DECK_MESSAGE_CHARS = 280
MAX_SECTIONS = 18
MAX_SLIDE_PLAN_ITEMS = 40
MAX_STORY_BEATS = 16
MAX_TAKEAWAYS = 8
MAX_DECISION_POINTS = 8


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _clean_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


class _BaseModel(BaseModel):
    class Config:
        use_enum_values = True
        extra = "forbid"
        allow_population_by_field_name = True


class AudienceProfile(_BaseModel):
    primary_audience: AudienceType = AudienceType.GENERAL
    seniority: AudienceSeniority = AudienceSeniority.MIXED
    decision_stage: DecisionStage = DecisionStage.DISCOVERY
    known_priorities: list[str] = Field(default_factory=list, max_items=8)
    avoid_topics: list[str] = Field(default_factory=list, max_items=8)

    _normalize_lists = validator("known_priorities", "avoid_topics", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class ObjectionResponse(_BaseModel):
    objection_id: str = Field(..., min_length=1, max_length=80)
    objection: str = Field(..., min_length=1, max_length=160)
    response: str = Field(..., min_length=1, max_length=240)
    evidence_requirement: EvidenceStrategy = EvidenceStrategy.BALANCED
    related_slide_ids: list[str] = Field(default_factory=list, max_items=8)

    _normalize = validator("objection_id", "objection", "response", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("related_slide_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class CTAPlan(_BaseModel):
    cta_strategy: str = Field(..., min_length=1, max_length=160)
    next_action: str = Field(..., min_length=1, max_length=160)
    owner: Optional[str] = Field(default=None, max_length=80)
    due_timing: Optional[str] = Field(default=None, max_length=80)
    success_condition: Optional[str] = Field(default=None, max_length=160)

    _normalize = validator(
        "cta_strategy",
        "next_action",
        "owner",
        "due_timing",
        "success_condition",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class DeckSourceReference(_BaseModel):
    source_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    source_type: str = Field(default="user_input", max_length=60)
    confidence: str = Field(default="medium", max_length=20)

    _normalize = validator("source_id", "label", "source_type", "confidence", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class DeckThemeDirection(_BaseModel):
    recommended_theme: ThemeType = ThemeType.CONSULTING
    tone: str = Field(default="consulting", max_length=80)
    formality: str = Field(default="business", max_length=80)
    visual_density: str = Field(default="medium", max_length=40)
    evidence_density: EvidenceStrategy = EvidenceStrategy.BALANCED
    executive_summary_required: bool = True

    _normalize = validator("tone", "formality", "visual_density", pre=True, allow_reuse=True)(_clean_optional_text)


class DeckTransition(_BaseModel):
    transition_type: TransitionType = TransitionType.CONTINUE
    from_slide_id: Optional[str] = Field(default=None, max_length=100)
    to_slide_id: Optional[str] = Field(default=None, max_length=100)
    bridge_message: Optional[str] = Field(default=None, max_length=180)

    _normalize = validator("from_slide_id", "to_slide_id", "bridge_message", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class DeckConstraint(_BaseModel):
    constraint_id: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=120)
    detail: Optional[str] = Field(default=None, max_length=240)
    blocking: bool = False

    _normalize = validator("constraint_id", "label", "detail", pre=True, allow_reuse=True)(_clean_optional_text)


class DeckWarning(_BaseModel):
    warning_id: str = Field(..., min_length=1, max_length=80)
    message: str = Field(..., min_length=1, max_length=220)
    related_slide_ids: list[str] = Field(default_factory=list, max_items=8)

    _normalize = validator("warning_id", "message", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("related_slide_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class DeckValidationIssue(_BaseModel):
    code: str = Field(..., min_length=1, max_length=48)
    severity: DeckValidationSeverity
    field_path: str = Field(..., min_length=1, max_length=180)
    message: str = Field(..., min_length=1, max_length=280)
    suggestion: Optional[str] = Field(default=None, max_length=280)
    blocking: bool = False
    source: str = Field(default="deck_validator", max_length=80)
    related_slide_ids: list[str] = Field(default_factory=list, max_items=10)
    related_section_ids: list[str] = Field(default_factory=list, max_items=10)

    _normalize = validator("code", "field_path", "message", "suggestion", "source", pre=True, allow_reuse=True)(
        _clean_optional_text
    )
    _normalize_ids = validator(
        "related_slide_ids",
        "related_section_ids",
        pre=True,
        always=True,
        allow_reuse=True,
    )(_clean_text_list)


class DeckValidationResult(_BaseModel):
    valid: bool
    status: DeckStatus
    issues: list[DeckValidationIssue] = Field(default_factory=list)

    @property
    def errors(self) -> list[DeckValidationIssue]:
        return [issue for issue in self.issues if issue.severity == DeckValidationSeverity.ERROR.value]

    @property
    def warnings(self) -> list[DeckValidationIssue]:
        return [issue for issue in self.issues if issue.severity == DeckValidationSeverity.WARNING.value]


class DeckEvaluationDimension(_BaseModel):
    name: str
    score: int = Field(..., ge=0, le=10)
    max_score: int = 10
    issues: list[str] = Field(default_factory=list)
    reason: str
    recommendations: list[str] = Field(default_factory=list)


class DeckEvaluationResult(_BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    max_score: int = 100
    grade: str
    dimensions: list[DeckEvaluationDimension]
    blocking_issue_count: int
    warning_count: int
    note: str


class SlideBlueprintReference(_BaseModel):
    slide_blueprint_id: str = Field(..., min_length=1, max_length=100)
    slide_id: str = Field(..., min_length=1, max_length=100)
    slide_order: int = Field(..., ge=0, le=200)
    expected_slide_type: SlideType
    expected_slide_goal: SlideGoal
    section_id: str = Field(..., min_length=1, max_length=100)
    required: bool = True
    embedded_slide_blueprint: Optional[SlideBlueprint] = None

    _normalize = validator("slide_blueprint_id", "slide_id", "section_id", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class SlidePlanItem(_BaseModel):
    slide_order: int = Field(..., ge=0, le=200)
    slide_role: SlideRole
    slide_type: SlideType
    section_id: str = Field(..., min_length=1, max_length=100)
    slide_goal: SlideGoal
    narrative_function: NarrativeFunction
    working_title: str = Field(..., min_length=1, max_length=120)
    key_message: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    required: bool = True
    optional: bool = False
    decision_relevance: str = Field(default="medium", max_length=40)
    evidence_requirement: EvidenceStrategy = EvidenceStrategy.BALANCED
    transition_from_previous: TransitionType = TransitionType.CONTINUE
    transition_to_next: TransitionType = TransitionType.CONTINUE
    slide_blueprint_id: Optional[str] = Field(default=None, max_length=100)

    _normalize = validator(
        "section_id",
        "working_title",
        "key_message",
        "decision_relevance",
        "slide_blueprint_id",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class DeckSection(_BaseModel):
    section_id: str = Field(..., min_length=1, max_length=100)
    section_type: SectionType
    section_title: str = Field(..., min_length=1, max_length=120)
    section_goal: str = Field(..., min_length=1, max_length=220)
    section_order: int = Field(..., ge=0, le=80)
    required: bool = True
    minimum_slides: int = Field(default=1, ge=0, le=20)
    maximum_slides: int = Field(default=4, ge=1, le=20)
    slide_ids: list[str] = Field(default_factory=list, max_items=20)
    entry_message: Optional[str] = Field(default=None, max_length=180)
    exit_message: Optional[str] = Field(default=None, max_length=180)
    transition_type: TransitionType = TransitionType.CONTINUE
    decision_relevance: str = Field(default="medium", max_length=40)

    _normalize = validator(
        "section_id",
        "section_title",
        "section_goal",
        "entry_message",
        "exit_message",
        "decision_relevance",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_ids = validator("slide_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class StoryBeat(_BaseModel):
    beat_id: str = Field(..., min_length=1, max_length=80)
    narrative_function: NarrativeFunction
    message: str = Field(..., min_length=1, max_length=220)
    related_section_ids: list[str] = Field(default_factory=list, max_items=8)
    related_slide_ids: list[str] = Field(default_factory=list, max_items=8)

    _normalize = validator("beat_id", "message", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator(
        "related_section_ids",
        "related_slide_ids",
        pre=True,
        always=True,
        allow_reuse=True,
    )(_clean_text_list)


class DecisionPoint(_BaseModel):
    decision_id: str = Field(..., min_length=1, max_length=80)
    question: str = Field(..., min_length=1, max_length=180)
    required_evidence: list[str] = Field(default_factory=list, max_items=8)
    related_slide_ids: list[str] = Field(default_factory=list, max_items=8)
    urgency: DecisionUrgency = DecisionUrgency.NORMAL

    _normalize = validator("decision_id", "question", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_lists = validator("required_evidence", "related_slide_ids", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class ApprovalRequirement(_BaseModel):
    requirement_id: str = Field(..., min_length=1, max_length=80)
    approver: str = Field(..., min_length=1, max_length=120)
    approval_condition: str = Field(..., min_length=1, max_length=220)
    related_slide_ids: list[str] = Field(default_factory=list, max_items=8)

    _normalize = validator("requirement_id", "approver", "approval_condition", pre=True, allow_reuse=True)(
        _clean_optional_text
    )
    _normalize_ids = validator("related_slide_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class DeckBlueprint(_BaseModel):
    deck_blueprint_version: str = Field(default=SUPPORTED_DECK_BLUEPRINT_VERSION, const=True)
    deck_id: str = Field(..., min_length=1, max_length=120)
    project_id: Optional[str] = Field(default=None, max_length=120)
    deck_title: str = Field(..., min_length=1, max_length=MAX_DECK_TITLE_CHARS)
    deck_type: DeckType = DeckType.SALES_PROPOSAL
    status: DeckStatus = DeckStatus.DRAFT
    language: str = Field(default="ja", min_length=2, max_length=16)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    deck_goal: DeckGoal
    primary_audience: AudienceType = AudienceType.GENERAL
    audience_seniority: AudienceSeniority = AudienceSeniority.MIXED
    decision_stage: DecisionStage = DecisionStage.DISCOVERY
    decision_question: str = Field(..., min_length=1, max_length=200)
    desired_decision: str = Field(..., min_length=1, max_length=200)
    desired_reaction: str = Field(..., min_length=1, max_length=200)
    decision_urgency: DecisionUrgency = DecisionUrgency.NORMAL

    story_arc: StoryArcType = StoryArcType.PROBLEM_SOLUTION
    persuasion_strategy: PersuasionStrategy = PersuasionStrategy.ROI
    evidence_strategy: EvidenceStrategy = EvidenceStrategy.BALANCED
    core_thesis: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    value_proposition: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    key_differentiator: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    primary_objection: Optional[str] = Field(default=None, max_length=180)
    objection_response: Optional[ObjectionResponse] = None

    sections: list[DeckSection] = Field(default_factory=list, min_items=1, max_items=MAX_SECTIONS)
    slide_plan: list[SlidePlanItem] = Field(default_factory=list, min_items=1, max_items=MAX_SLIDE_PLAN_ITEMS)
    target_slide_count: int = Field(..., ge=1, le=80)
    minimum_slide_count: int = Field(default=5, ge=1, le=80)
    maximum_slide_count: int = Field(default=20, ge=1, le=80)
    deck_length_type: DeckLengthType = DeckLengthType.STANDARD
    appendix_allowed: bool = True
    optional_sections: list[SectionType] = Field(default_factory=list, max_items=12)
    required_sections: list[SectionType] = Field(default_factory=list, max_items=16)

    opening_message: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    problem_statement: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    insight_statement: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    recommendation_statement: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    impact_statement: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    closing_message: str = Field(..., min_length=1, max_length=MAX_DECK_MESSAGE_CHARS)
    narrative_summary: str = Field(..., min_length=1, max_length=400)
    story_beats: list[StoryBeat] = Field(default_factory=list, max_items=MAX_STORY_BEATS)
    key_takeaways: list[str] = Field(default_factory=list, max_items=MAX_TAKEAWAYS)

    decision_points: list[DecisionPoint] = Field(default_factory=list, max_items=MAX_DECISION_POINTS)
    approval_requirements: list[ApprovalRequirement] = Field(default_factory=list, max_items=8)
    cta_plan: CTAPlan
    next_action: str = Field(..., min_length=1, max_length=180)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    decision_dependencies: list[str] = Field(default_factory=list, max_items=8)

    theme_direction: DeckThemeDirection = Field(default_factory=DeckThemeDirection)

    slide_blueprint_refs: list[SlideBlueprintReference] = Field(default_factory=list, max_items=MAX_SLIDE_PLAN_ITEMS)

    generation_source: str = Field(default="offline_fixture", max_length=80)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    warnings: list[DeckWarning] = Field(default_factory=list, max_items=20)
    validation_result: Optional[DeckValidationResult] = None
    evaluation_result: Optional[DeckEvaluationResult] = None
    source_references: list[DeckSourceReference] = Field(default_factory=list, max_items=16)
    created_by: Optional[str] = Field(default=None, max_length=120)
    schema_version: str = Field(default=SUPPORTED_DECK_BLUEPRINT_VERSION, const=True)
    audience_profile: Optional[AudienceProfile] = None
    constraints: list[DeckConstraint] = Field(default_factory=list, max_items=12)
    transitions: list[DeckTransition] = Field(default_factory=list, max_items=MAX_SLIDE_PLAN_ITEMS)

    _normalize = validator(
        "deck_id",
        "project_id",
        "deck_title",
        "language",
        "decision_question",
        "desired_decision",
        "desired_reaction",
        "core_thesis",
        "value_proposition",
        "key_differentiator",
        "primary_objection",
        "opening_message",
        "problem_statement",
        "insight_statement",
        "recommendation_statement",
        "impact_statement",
        "closing_message",
        "narrative_summary",
        "next_action",
        "generation_source",
        "created_by",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_lists = validator(
        "key_takeaways",
        "decision_dependencies",
        pre=True,
        always=True,
        allow_reuse=True,
    )(_clean_text_list)
