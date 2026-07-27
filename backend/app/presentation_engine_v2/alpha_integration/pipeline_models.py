"""Models for Presentation Engine 2.0 Alpha Integration Review."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from ..deck_models import DeckBlueprint, DeckEvaluationResult, DeckValidationResult
from ..deck_planner.planner_models import DeckPlannerResult, ProposalContext
from ..evidence_planner.evidence_models import EvidenceEvaluationResult, EvidencePlannerResult
from ..message_designer.designer_models import (
    MessageDesignerOutput,
    MessageEvaluationResult,
    MessageValidationResult,
)


SUPPORTED_ALPHA_INTEGRATION_CASE_VERSION = "pe2_alpha_integration_case_v1"
SUPPORTED_ALPHA_INTEGRATION_OUTPUT_VERSION = "pe2_alpha_integration_output_v1"


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


class _StrEnum(str, Enum):
    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class _BaseModel(BaseModel):
    class Config:
        use_enum_values = True
        extra = "forbid"
        allow_population_by_field_name = True


class AlphaValidationSeverity(_StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AlphaPipelineStage(_StrEnum):
    INPUT = "input"
    DECK_PLANNER = "deck_planner"
    DECK_VALIDATION = "deck_validation"
    EVIDENCE_PLANNER = "evidence_planner"
    EVIDENCE_VALIDATION = "evidence_validation"
    MESSAGE_DESIGNER = "message_designer"
    MESSAGE_VALIDATION = "message_validation"
    CROSS_MODULE_VALIDATION = "cross_module_validation"
    EVALUATION = "evaluation"
    REPORTING = "reporting"


class Phase2DReadinessStatus(_StrEnum):
    READY = "READY"
    READY_WITH_LIMITATIONS = "READY_WITH_LIMITATIONS"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"


class AlphaIssueCode:
    INPUT = "PE2-ALPHA-INPUT-001"
    DECK = "PE2-ALPHA-DECK-001"
    EVIDENCE = "PE2-ALPHA-EVIDENCE-001"
    MESSAGE = "PE2-ALPHA-MESSAGE-001"
    REFERENCE = "PE2-ALPHA-REFERENCE-001"
    STORY = "PE2-ALPHA-STORY-001"
    AUDIENCE = "PE2-ALPHA-AUDIENCE-001"
    DECISION = "PE2-ALPHA-DECISION-001"
    SAFETY = "PE2-ALPHA-SAFETY-001"
    READINESS = "PE2-ALPHA-READINESS-001"


class AlphaValidationIssue(_BaseModel):
    code: str = Field(..., min_length=1, max_length=64)
    severity: AlphaValidationSeverity
    stage: AlphaPipelineStage
    field_path: str = Field(..., min_length=1, max_length=220)
    case_id: str = Field(..., min_length=1, max_length=120)
    slide_id: Optional[str] = Field(default=None, max_length=160)
    evidence_id: Optional[str] = Field(default=None, max_length=160)
    message: str = Field(..., min_length=1, max_length=320)
    reason: str = Field(..., min_length=1, max_length=320)
    suggestion: str = Field(..., min_length=1, max_length=320)
    blocking: bool = False
    source_module: str = Field(..., min_length=1, max_length=120)

    _normalize = validator(
        "code",
        "field_path",
        "case_id",
        "slide_id",
        "evidence_id",
        "message",
        "reason",
        "suggestion",
        "source_module",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class CrossModuleValidationResult(_BaseModel):
    valid: bool
    issues: list[AlphaValidationIssue] = Field(default_factory=list, max_items=120)
    checked_stage_count: int = Field(default=4, ge=0)
    passed_stage_count: int = Field(default=0, ge=0)
    failed_stage_count: int = Field(default=0, ge=0)

    @property
    def errors(self) -> list[AlphaValidationIssue]:
        return [item for item in self.issues if item.severity == AlphaValidationSeverity.ERROR.value]

    @property
    def warnings(self) -> list[AlphaValidationIssue]:
        return [item for item in self.issues if item.severity == AlphaValidationSeverity.WARNING.value]


class AlphaEvaluationDimension(_BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    score: int = Field(..., ge=0, le=10)
    max_score: int = 10
    reason: str = Field(..., min_length=1, max_length=320)
    issues: list[str] = Field(default_factory=list, max_items=12)
    recommendations: list[str] = Field(default_factory=list, max_items=12)
    blocking: bool = False


class AlphaEvaluationResult(_BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    max_score: int = 100
    grade: str = Field(..., min_length=1, max_length=2)
    dimensions: list[AlphaEvaluationDimension] = Field(default_factory=list, min_items=1, max_items=20)
    blocking_issue_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    passed_stage_count: int = Field(default=0, ge=0)
    failed_stage_count: int = Field(default=0, ge=0)
    phase2d_readiness_status: Phase2DReadinessStatus
    note: str = Field(..., min_length=1, max_length=360)


class AlphaHumanReviewSummary(_BaseModel):
    case_id: str = Field(..., min_length=1, max_length=120)
    case_name: str = Field(..., min_length=1, max_length=160)
    proposal_context_summary: str = Field(..., min_length=1, max_length=600)
    audience: str = Field(..., min_length=1, max_length=120)
    decision_stage: str = Field(..., min_length=1, max_length=120)
    deck_goal: str = Field(..., min_length=1, max_length=120)
    story_arc: str = Field(..., min_length=1, max_length=120)
    section_summary: list[str] = Field(default_factory=list, max_items=40)
    slide_summary: list[str] = Field(default_factory=list, max_items=80)
    headline_summary: list[str] = Field(default_factory=list, max_items=80)
    required_evidence_summary: list[str] = Field(default_factory=list, max_items=120)
    missing_evidence_summary: list[str] = Field(default_factory=list, max_items=80)
    key_warnings: list[str] = Field(default_factory=list, max_items=40)
    blocking_issues: list[str] = Field(default_factory=list, max_items=40)
    good_points: list[str] = Field(default_factory=list, max_items=20)
    unnatural_points: list[str] = Field(default_factory=list, max_items=20)
    weak_sales_points: list[str] = Field(default_factory=list, max_items=20)
    improvement_candidates: list[str] = Field(default_factory=list, max_items=20)
    phase2d_readiness: Phase2DReadinessStatus


class AlphaIntegrationCase(_BaseModel):
    integration_case_id: str = Field(..., min_length=1, max_length=120)
    case_name: str = Field(..., min_length=1, max_length=160)
    proposal_context: ProposalContext
    expected_deck_characteristics: list[str] = Field(default_factory=list, max_items=20)
    expected_evidence_characteristics: list[str] = Field(default_factory=list, max_items=20)
    expected_message_characteristics: list[str] = Field(default_factory=list, max_items=20)
    review_tags: list[str] = Field(default_factory=list, max_items=20)
    industry: Optional[str] = Field(default=None, max_length=120)
    proposal_category: Optional[str] = Field(default=None, max_length=120)
    audience: Optional[str] = Field(default=None, max_length=120)
    decision_stage: Optional[str] = Field(default=None, max_length=120)
    deck_length_preference: Optional[str] = Field(default=None, max_length=80)
    known_constraints: list[str] = Field(default_factory=list, max_items=20)
    available_evidence: list[str] = Field(default_factory=list, max_items=30)
    intentionally_missing_evidence: list[str] = Field(default_factory=list, max_items=30)
    schema_version: str = Field(default=SUPPORTED_ALPHA_INTEGRATION_CASE_VERSION, const=True)

    _normalize = validator(
        "integration_case_id",
        "case_name",
        "industry",
        "proposal_category",
        "audience",
        "decision_stage",
        "deck_length_preference",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_lists = validator(
        "expected_deck_characteristics",
        "expected_evidence_characteristics",
        "expected_message_characteristics",
        "review_tags",
        "known_constraints",
        "available_evidence",
        "intentionally_missing_evidence",
        pre=True,
        always=True,
        allow_reuse=True,
    )(_clean_text_list)


class AlphaIntegrationOutput(_BaseModel):
    integration_output_version: str = Field(default=SUPPORTED_ALPHA_INTEGRATION_OUTPUT_VERSION, const=True)
    created_at: datetime
    integration_case_id: str = Field(..., min_length=1, max_length=120)
    case_name: str = Field(..., min_length=1, max_length=160)
    proposal_context_summary: str = Field(..., min_length=1, max_length=600)
    deck_planner_result: DeckPlannerResult
    deck_validation_result: DeckValidationResult
    evidence_planner_result: EvidencePlannerResult
    evidence_validation_result: CrossModuleValidationResult
    message_designer_result: MessageDesignerOutput
    message_validation_result: MessageValidationResult
    cross_module_validation_result: CrossModuleValidationResult
    pipeline_evaluation_result: AlphaEvaluationResult
    human_review_summary: AlphaHumanReviewSummary
    blocking_issues: list[AlphaValidationIssue] = Field(default_factory=list, max_items=80)
    warnings: list[AlphaValidationIssue] = Field(default_factory=list, max_items=120)
    improvement_candidates: list[str] = Field(default_factory=list, max_items=40)
    phase2d_readiness: Phase2DReadinessStatus
    input_fingerprint: str = Field(..., min_length=1, max_length=100)
    schema_version: str = Field(default=SUPPORTED_ALPHA_INTEGRATION_OUTPUT_VERSION, const=True)
    generated_pptx: bool = False
    connected_to_runtime: bool = False
    generated_slide_blueprints: bool = False
    used_external_ai: bool = False


class AlphaCrossCaseSummary(_BaseModel):
    case_count: int = Field(..., ge=0)
    average_overall_score: float = Field(..., ge=0.0, le=100.0)
    min_overall_score: int = Field(..., ge=0, le=100)
    max_overall_score: int = Field(..., ge=0, le=100)
    grade_distribution: dict[str, int] = Field(default_factory=dict)
    readiness_distribution: dict[str, int] = Field(default_factory=dict)
    most_frequent_warnings: list[str] = Field(default_factory=list, max_items=20)
    most_frequent_blocking_issues: list[str] = Field(default_factory=list, max_items=20)
    weakest_dimensions: list[str] = Field(default_factory=list, max_items=10)
    strongest_dimensions: list[str] = Field(default_factory=list, max_items=10)
    industry_tendency: dict[str, float] = Field(default_factory=dict)
    audience_tendency: dict[str, float] = Field(default_factory=dict)
    decision_stage_tendency: dict[str, float] = Field(default_factory=dict)
    note: str = Field(..., min_length=1, max_length=360)


class AlphaGoldenCase(_BaseModel):
    case: AlphaIntegrationCase
    output: AlphaIntegrationOutput


class AlphaPipelineInput(_BaseModel):
    case: AlphaIntegrationCase
