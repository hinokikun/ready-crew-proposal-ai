"""Models for Presentation Engine 2.0 Phase 2D Slide Intent Foundation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from ..deck_models import DeckBlueprint
from ..deck_planner.planner_models import ProposalContext
from ..evidence_planner.evidence_models import EvidencePlannerResult
from ..message_designer.designer_models import MessageDesignerOutput
from .intent_enums import (
    ChartCandidate,
    DiagramCandidate,
    InformationDensity,
    IntentConfidence,
    LayoutConstraint,
    ReadingOrder,
    SlideIntentType,
    SlideType,
    ValidationSeverity,
    VisualPattern,
)


SUPPORTED_SLIDE_INTENT_VERSION = "pe2_slide_intent_v1"
SUPPORTED_SLIDE_INTENT_OUTPUT_VERSION = "pe2_slide_intent_output_v1"


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


class InformationPriority(_BaseModel):
    primary_focus: str = Field(..., min_length=1, max_length=160)
    secondary_focus: list[str] = Field(default_factory=list, max_items=5)
    muted_content: list[str] = Field(default_factory=list, max_items=5)
    density: InformationDensity = InformationDensity.MEDIUM
    emphasis: str = Field(default="main_message", min_length=1, max_length=80)

    _normalize = validator("primary_focus", "emphasis", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_lists = validator("secondary_focus", "muted_content", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class IntentInputMetrics(_BaseModel):
    total_text_chars: int = Field(..., ge=0, le=2000)
    supporting_message_count: int = Field(..., ge=0, le=20)
    required_evidence_count: int = Field(..., ge=0, le=30)
    missing_evidence_count: int = Field(..., ge=0, le=30)
    numeric_claim_count: int = Field(..., ge=0, le=20)
    comparison_basis_present: bool = False
    time_sequence_present: bool = False
    hierarchy_basis_present: bool = False
    checklist_item_count: int = Field(default=0, ge=0, le=20)
    image_evidence_present: bool = False


class IntentWarning(_BaseModel):
    warning_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=260)
    suggestion: str = Field(..., min_length=1, max_length=260)
    severity: ValidationSeverity = ValidationSeverity.WARNING

    _normalize = validator("warning_id", "message", "suggestion", pre=True, allow_reuse=True)(_clean_optional_text)


class IntentValidationIssue(_BaseModel):
    code: str = Field(..., min_length=1, max_length=80)
    severity: ValidationSeverity
    field_path: str = Field(..., min_length=1, max_length=180)
    message: str = Field(..., min_length=1, max_length=280)
    suggestion: str = Field(..., min_length=1, max_length=280)
    blocking: bool = False
    related_slide_id: Optional[str] = Field(default=None, max_length=120)

    _normalize = validator(
        "code",
        "field_path",
        "message",
        "suggestion",
        "related_slide_id",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class IntentValidationResult(_BaseModel):
    valid: bool
    issues: list[IntentValidationIssue] = Field(default_factory=list, max_items=60)

    @property
    def errors(self) -> list[IntentValidationIssue]:
        return [item for item in self.issues if item.severity == ValidationSeverity.ERROR.value]

    @property
    def warnings(self) -> list[IntentValidationIssue]:
        return [item for item in self.issues if item.severity == ValidationSeverity.WARNING.value]


class IntentEvaluationDimension(_BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=0, le=10)
    max_score: int = 10
    reason: str = Field(..., min_length=1, max_length=280)
    issues: list[str] = Field(default_factory=list, max_items=10)
    recommendations: list[str] = Field(default_factory=list, max_items=10)


class IntentEvaluationResult(_BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    max_score: int = 100
    grade: str = Field(..., min_length=1, max_length=2)
    dimensions: list[IntentEvaluationDimension] = Field(default_factory=list, min_items=1, max_items=12)
    blocking_issue_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    note: str = Field(..., min_length=1, max_length=320)


class SlideIntentDesign(_BaseModel):
    slide_intent_version: str = Field(default=SUPPORTED_SLIDE_INTENT_VERSION, const=True)
    intent_id: str = Field(..., min_length=1, max_length=140)
    deck_id: str = Field(..., min_length=1, max_length=120)
    slide_blueprint_id: str = Field(..., min_length=1, max_length=120)
    source_message_design_id: str = Field(..., min_length=1, max_length=140)
    slide_order: int = Field(..., ge=0, le=200)
    slide_intent: SlideIntentType
    slide_type: SlideType
    information_priority: InformationPriority
    reading_order: ReadingOrder
    visual_pattern_candidate: VisualPattern
    diagram_candidate: DiagramCandidate = DiagramCandidate.NONE
    chart_candidate: ChartCandidate = ChartCandidate.NONE
    layout_constraint: list[LayoutConstraint] = Field(default_factory=list, max_items=12)
    rendering_hint: str = Field(..., min_length=1, max_length=280)
    intent_confidence: IntentConfidence = IntentConfidence.MEDIUM
    warnings: list[IntentWarning] = Field(default_factory=list, max_items=12)
    validation_result: Optional[IntentValidationResult] = None
    evaluation_result: Optional[IntentEvaluationResult] = None
    input_metrics: IntentInputMetrics
    source_evidence_ids: list[str] = Field(default_factory=list, max_items=24)
    input_fingerprint: str = Field(..., min_length=1, max_length=100)
    created_at: datetime
    schema_version: str = Field(default=SUPPORTED_SLIDE_INTENT_VERSION, const=True)
    generated_slide_blueprint: bool = False
    generated_diagram: bool = False
    generated_chart: bool = False
    generated_pptx: bool = False
    connected_to_runtime: bool = False

    _normalize = validator(
        "intent_id",
        "deck_id",
        "slide_blueprint_id",
        "source_message_design_id",
        "rendering_hint",
        "input_fingerprint",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_ids = validator("source_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class SlideIntentInput(_BaseModel):
    proposal_context: ProposalContext
    deck_blueprint: DeckBlueprint
    evidence_planner_output: EvidencePlannerResult
    message_designer_output: MessageDesignerOutput


class SlideIntentOutput(_BaseModel):
    slide_intent_output_version: str = Field(default=SUPPORTED_SLIDE_INTENT_OUTPUT_VERSION, const=True)
    created_at: datetime
    deck_id: str = Field(..., min_length=1, max_length=120)
    project_id: Optional[str] = Field(default=None, max_length=120)
    project_name: Optional[str] = Field(default=None, max_length=160)
    slide_intents: list[SlideIntentDesign] = Field(default_factory=list, min_items=1, max_items=80)
    validation_result: Optional[IntentValidationResult] = None
    evaluation_result: Optional[IntentEvaluationResult] = None
    warnings: list[IntentWarning] = Field(default_factory=list, max_items=60)
    generated_slide_blueprints: bool = False
    generated_diagrams: bool = False
    generated_charts: bool = False
    generated_pptx: bool = False
    connected_to_runtime: bool = False

    _normalize = validator("deck_id", "project_id", "project_name", pre=True, allow_reuse=True)(_clean_optional_text)
