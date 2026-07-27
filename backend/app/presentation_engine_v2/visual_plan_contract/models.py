"""Pydantic models for the Visual Plan Contract.

This module defines contracts only. It does not implement Visual Director,
Blueprint Composer, Renderer, theme generation, coordinates, or PPTX output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from ..deck_models import DeckBlueprint
from ..deck_planner.planner_models import ProposalContext
from ..evidence_planner.evidence_models import EvidencePlannerResult
from ..message_designer.designer_models import MessageDesignerOutput
from ..slide_intent.intent_models import SlideIntentOutput
from .contracts import SUPPORTED_VISUAL_PLAN_CONTRACT_VERSION
from .enums import (
    CalloutStrategy,
    ChartStrategy,
    ComponentCandidateType,
    DiagramStrategy,
    EmphasisStrategy,
    IconStrategy,
    ImageStrategy,
    LayoutStrategy,
    TableStrategy,
    ValidationSeverity,
    VisualConfidence,
    VisualPlanStatus,
    VisualPriorityLevel,
    VisualReadingOrder,
    VisualStrategy,
)


MAX_REASON_CHARS = 320


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


class VisualPriorityPlan(_BaseModel):
    primary_element: str = Field(..., min_length=1, max_length=120)
    secondary_elements: list[str] = Field(default_factory=list, max_items=6)
    muted_elements: list[str] = Field(default_factory=list, max_items=6)
    priority_level: VisualPriorityLevel = VisualPriorityLevel.PRIMARY
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)

    _normalize = validator("primary_element", "rationale", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_lists = validator("secondary_elements", "muted_elements", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class ComponentCandidate(_BaseModel):
    component_id: str = Field(..., min_length=1, max_length=120)
    component_type: ComponentCandidateType
    priority_level: VisualPriorityLevel = VisualPriorityLevel.SUPPORTING
    source_field: str = Field(..., min_length=1, max_length=120)
    purpose: str = Field(..., min_length=1, max_length=220)
    evidence_ids: list[str] = Field(default_factory=list, max_items=12)
    placeholder_allowed: bool = False
    renderer_hint: str = Field(..., min_length=1, max_length=260)

    _normalize = validator("component_id", "source_field", "purpose", "renderer_hint", pre=True, allow_reuse=True)(
        _clean_optional_text
    )
    _normalize_ids = validator("evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class DiagramStrategyPlan(_BaseModel):
    strategy: DiagramStrategy = DiagramStrategy.NONE
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)
    required_evidence_ids: list[str] = Field(default_factory=list, max_items=12)
    blocked_by_missing_evidence: bool = False

    _normalize = validator("rationale", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("required_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class ChartStrategyPlan(_BaseModel):
    strategy: ChartStrategy = ChartStrategy.NONE
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)
    numeric_evidence_ids: list[str] = Field(default_factory=list, max_items=12)
    blocked_by_missing_numeric_evidence: bool = False

    _normalize = validator("rationale", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("numeric_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class ImageStrategyPlan(_BaseModel):
    strategy: ImageStrategy = ImageStrategy.NONE
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)
    asset_requirement: Optional[str] = Field(default=None, max_length=180)
    external_asset_allowed: bool = False

    _normalize = validator("rationale", "asset_requirement", pre=True, allow_reuse=True)(_clean_optional_text)


class TableStrategyPlan(_BaseModel):
    strategy: TableStrategy = TableStrategy.NONE
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)
    required_columns: list[str] = Field(default_factory=list, max_items=8)
    max_rows_hint: int = Field(default=5, ge=0, le=12)

    _normalize = validator("rationale", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_columns = validator("required_columns", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class CalloutStrategyPlan(_BaseModel):
    strategy: CalloutStrategy = CalloutStrategy.NONE
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)
    callout_source: Optional[str] = Field(default=None, max_length=160)

    _normalize = validator("rationale", "callout_source", pre=True, allow_reuse=True)(_clean_optional_text)


class IconStrategyPlan(_BaseModel):
    strategy: IconStrategy = IconStrategy.NONE
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)
    icon_concepts: list[str] = Field(default_factory=list, max_items=8)

    _normalize = validator("rationale", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_concepts = validator("icon_concepts", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class VisualRiskFlag(_BaseModel):
    code: str = Field(..., min_length=1, max_length=80)
    severity: ValidationSeverity = ValidationSeverity.WARNING
    message: str = Field(..., min_length=1, max_length=280)
    suggestion: str = Field(..., min_length=1, max_length=280)
    related_slide_id: Optional[str] = Field(default=None, max_length=120)
    blocking: bool = False

    _normalize = validator(
        "code",
        "message",
        "suggestion",
        "related_slide_id",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class VisualValidationIssue(_BaseModel):
    code: str = Field(..., min_length=1, max_length=80)
    severity: ValidationSeverity
    field_path: str = Field(..., min_length=1, max_length=180)
    message: str = Field(..., min_length=1, max_length=280)
    suggestion: str = Field(..., min_length=1, max_length=280)
    related_slide_id: Optional[str] = Field(default=None, max_length=120)
    blocking: bool = False

    _normalize = validator(
        "code",
        "field_path",
        "message",
        "suggestion",
        "related_slide_id",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class VisualValidationResult(_BaseModel):
    valid: bool
    status: VisualPlanStatus
    issues: list[VisualValidationIssue] = Field(default_factory=list, max_items=80)

    @property
    def errors(self) -> list[VisualValidationIssue]:
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR.value]

    @property
    def warnings(self) -> list[VisualValidationIssue]:
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING.value]


class VisualPlanItem(_BaseModel):
    visual_plan_version: str = Field(default=SUPPORTED_VISUAL_PLAN_CONTRACT_VERSION, const=True)
    visual_plan_id: str = Field(..., min_length=1, max_length=140)
    deck_id: str = Field(..., min_length=1, max_length=120)
    slide_blueprint_id: str = Field(..., min_length=1, max_length=120)
    source_intent_id: str = Field(..., min_length=1, max_length=140)
    slide_order: int = Field(..., ge=0, le=200)

    visual_strategy: VisualStrategy
    layout_strategy: LayoutStrategy
    emphasis_strategy: EmphasisStrategy
    visual_priority: VisualPriorityPlan
    reading_order: VisualReadingOrder
    component_candidates: list[ComponentCandidate] = Field(default_factory=list, min_items=1, max_items=16)

    diagram_strategy: DiagramStrategyPlan
    chart_strategy: ChartStrategyPlan
    image_strategy: ImageStrategyPlan
    table_strategy: TableStrategyPlan
    callout_strategy: CalloutStrategyPlan
    icon_strategy: IconStrategyPlan

    risk_flags: list[VisualRiskFlag] = Field(default_factory=list, max_items=16)
    confidence: VisualConfidence = VisualConfidence.MEDIUM
    rationale: str = Field(..., min_length=1, max_length=MAX_REASON_CHARS)

    source_visual_pattern_candidate: Optional[str] = Field(default=None, max_length=80)
    source_diagram_candidate: Optional[str] = Field(default=None, max_length=80)
    source_chart_candidate: Optional[str] = Field(default=None, max_length=80)
    source_reading_order: Optional[str] = Field(default=None, max_length=80)
    source_evidence_ids: list[str] = Field(default_factory=list, max_items=24)
    numeric_evidence_ids: list[str] = Field(default_factory=list, max_items=16)
    input_fingerprint: str = Field(..., min_length=1, max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    schema_version: str = Field(default=SUPPORTED_VISUAL_PLAN_CONTRACT_VERSION, const=True)

    generated_blueprint: bool = False
    generated_theme: bool = False
    generated_coordinates: bool = False
    generated_diagram: bool = False
    generated_chart: bool = False
    generated_pptx: bool = False
    connected_to_runtime: bool = False

    _normalize = validator(
        "visual_plan_id",
        "deck_id",
        "slide_blueprint_id",
        "source_intent_id",
        "rationale",
        "source_visual_pattern_candidate",
        "source_diagram_candidate",
        "source_chart_candidate",
        "source_reading_order",
        "input_fingerprint",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_ids = validator("source_evidence_ids", "numeric_evidence_ids", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class VisualDirectorInput(_BaseModel):
    proposal_context: ProposalContext
    deck_blueprint: DeckBlueprint
    evidence_planner_output: EvidencePlannerResult
    message_designer_output: MessageDesignerOutput
    slide_intent_output: SlideIntentOutput


class VisualPlanContract(_BaseModel):
    visual_plan_contract_version: str = Field(default=SUPPORTED_VISUAL_PLAN_CONTRACT_VERSION, const=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deck_id: str = Field(..., min_length=1, max_length=120)
    project_id: Optional[str] = Field(default=None, max_length=120)
    project_name: Optional[str] = Field(default=None, max_length=160)

    visual_plan: list[VisualPlanItem] = Field(default_factory=list, min_items=1, max_items=80)
    visual_strategy: VisualStrategy
    layout_strategy: LayoutStrategy
    emphasis_strategy: EmphasisStrategy
    visual_priority: VisualPriorityPlan
    component_candidates: list[ComponentCandidate] = Field(default_factory=list, min_items=1, max_items=24)
    diagram_strategy: DiagramStrategyPlan
    chart_strategy: ChartStrategyPlan
    image_strategy: ImageStrategyPlan
    table_strategy: TableStrategyPlan
    callout_strategy: CalloutStrategyPlan
    icon_strategy: IconStrategyPlan

    risk_flags: list[VisualRiskFlag] = Field(default_factory=list, max_items=60)
    confidence: VisualConfidence = VisualConfidence.MEDIUM
    validation_result: Optional[VisualValidationResult] = None
    source_contracts: list[str] = Field(default_factory=list, max_items=12)

    generated_blueprint: bool = False
    generated_theme: bool = False
    generated_coordinates: bool = False
    generated_diagram: bool = False
    generated_chart: bool = False
    generated_pptx: bool = False
    connected_to_runtime: bool = False

    _normalize = validator("deck_id", "project_id", "project_name", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_contracts = validator("source_contracts", pre=True, always=True, allow_reuse=True)(_clean_text_list)
