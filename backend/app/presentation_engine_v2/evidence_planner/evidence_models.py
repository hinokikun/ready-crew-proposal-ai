"""Models for the Phase 2B offline Evidence Planner."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from ..deck_models import DeckBlueprint
from ..deck_planner.planner_models import ProposalContext
from ..enums import VisualType


SUPPORTED_EVIDENCE_PLANNER_VERSION = "pe2_evidence_planner_v1"


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


class EvidenceSourceType(_StrEnum):
    CUSTOMER_INTERVIEW = "customer_interview"
    INTERNAL_KPI = "internal_kpi"
    INDUSTRY_STATISTICS = "industry_statistics"
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    FINANCIAL_ESTIMATE = "financial_estimate"
    PROJECT_EXPERIENCE = "project_experience"
    USER_FEEDBACK = "user_feedback"
    IMPLEMENTATION_RESULT = "implementation_result"
    PUBLIC_INFORMATION = "public_information"
    CUSTOMER_DOCUMENT = "customer_document"
    ASSUMPTION_LOG = "assumption_log"


class EvidencePriority(_StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EvidenceConfidence(_StrEnum):
    VERIFIED = "verified"
    LIKELY = "likely"
    ESTIMATED = "estimated"
    MISSING = "missing"
    UNKNOWN = "unknown"


class MissingEvidenceSeverity(_StrEnum):
    BLOCKING = "blocking"
    WARNING = "warning"
    INFO = "info"


class VisualEvidenceRecommendation(_StrEnum):
    NONE = "none"
    METRIC_CARD = "metric_card"
    KPI_TABLE = "kpi_table"
    COMPARISON_TABLE = "comparison_table"
    TIMELINE = "timeline"
    ROADMAP = "roadmap"
    RISK_MATRIX = "risk_matrix"
    CASE_STUDY_CARD = "case_study_card"
    QUOTE = "quote"
    SCREENSHOT_PLACEHOLDER = "screenshot_placeholder"
    PROCESS_EVIDENCE = "process_evidence"


class EvidenceRequirement(_BaseModel):
    requirement_id: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=160)
    source_type: EvidenceSourceType
    priority: EvidencePriority = EvidencePriority.MEDIUM
    confidence: EvidenceConfidence = EvidenceConfidence.UNKNOWN
    numeric_required: bool = False
    customer_proof_required: bool = False
    case_study_required: bool = False
    traceability_required: bool = True
    rationale: str = Field(..., min_length=1, max_length=280)

    _normalize = validator("requirement_id", "label", "rationale", pre=True, allow_reuse=True)(_clean_optional_text)


class MissingEvidenceWarning(_BaseModel):
    warning_id: str = Field(..., min_length=1, max_length=100)
    severity: MissingEvidenceSeverity
    message: str = Field(..., min_length=1, max_length=260)
    suggested_action: str = Field(..., min_length=1, max_length=260)
    related_requirement_ids: list[str] = Field(default_factory=list, max_items=12)

    _normalize = validator("warning_id", "message", "suggested_action", pre=True, allow_reuse=True)(
        _clean_optional_text
    )
    _normalize_list = validator("related_requirement_ids", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class SlideEvidencePlan(_BaseModel):
    slide_blueprint_id: str = Field(..., min_length=1, max_length=100)
    slide_order: int = Field(..., ge=0, le=200)
    section_id: str = Field(..., min_length=1, max_length=100)
    section_type: str = Field(..., min_length=1, max_length=80)
    slide_role: str = Field(..., min_length=1, max_length=80)
    slide_goal: str = Field(..., min_length=1, max_length=80)
    required_evidence: list[EvidenceRequirement] = Field(default_factory=list, min_items=1, max_items=10)
    optional_evidence: list[EvidenceRequirement] = Field(default_factory=list, max_items=10)
    evidence_priority: EvidencePriority = EvidencePriority.MEDIUM
    evidence_confidence: EvidenceConfidence = EvidenceConfidence.UNKNOWN
    evidence_source_types: list[EvidenceSourceType] = Field(default_factory=list, min_items=1, max_items=10)
    numeric_evidence_required: bool = False
    customer_proof_required: bool = False
    case_study_required: bool = False
    visual_evidence_recommendation: VisualEvidenceRecommendation = VisualEvidenceRecommendation.NONE
    missing_evidence_warnings: list[MissingEvidenceWarning] = Field(default_factory=list, max_items=8)
    risk_if_missing: str = Field(..., min_length=1, max_length=280)
    generated_headline: bool = False
    generated_main_message: bool = False
    generated_body_text: bool = False
    generated_slide_blueprint: bool = False

    _normalize = validator(
        "slide_blueprint_id",
        "section_id",
        "section_type",
        "slide_role",
        "slide_goal",
        "risk_if_missing",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class EvidencePlannerWarning(_BaseModel):
    code: str = Field(..., min_length=1, max_length=80)
    message: str = Field(..., min_length=1, max_length=280)
    suggestion: Optional[str] = Field(default=None, max_length=280)

    _normalize = validator("code", "message", "suggestion", pre=True, allow_reuse=True)(_clean_optional_text)


class EvidenceEvaluationDimension(_BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=0, le=10)
    max_score: int = 10
    reason: str = Field(..., min_length=1, max_length=280)
    issues: list[str] = Field(default_factory=list, max_items=10)
    recommendations: list[str] = Field(default_factory=list, max_items=10)


class EvidenceEvaluationResult(_BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    max_score: int = 100
    grade: str = Field(..., min_length=1, max_length=2)
    dimensions: list[EvidenceEvaluationDimension] = Field(default_factory=list, min_items=1, max_items=12)
    blocking_warning_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    note: str = Field(..., min_length=1, max_length=300)


class EvidencePlanningInput(_BaseModel):
    deck_blueprint: DeckBlueprint
    proposal_context: ProposalContext


class EvidencePlannerResult(_BaseModel):
    evidence_planner_version: str = Field(default=SUPPORTED_EVIDENCE_PLANNER_VERSION, const=True)
    created_at: datetime
    deck_id: str = Field(..., min_length=1, max_length=120)
    deck_blueprint_version: str = Field(..., min_length=1, max_length=80)
    project_id: Optional[str] = Field(default=None, max_length=120)
    slide_evidence: list[SlideEvidencePlan] = Field(default_factory=list, min_items=1, max_items=80)
    evaluation_result: Optional[EvidenceEvaluationResult] = None
    warnings: list[EvidencePlannerWarning] = Field(default_factory=list, max_items=20)
    generated_headlines: bool = False
    generated_main_messages: bool = False
    generated_body_text: bool = False
    generated_slide_blueprints: bool = False
    connected_to_runtime: bool = False

    _normalize = validator("deck_id", "deck_blueprint_version", "project_id", pre=True, allow_reuse=True)(
        _clean_optional_text
    )

