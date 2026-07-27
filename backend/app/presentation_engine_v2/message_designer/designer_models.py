"""Models for the Phase 2C Message Designer."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from ..deck_models import DeckBlueprint
from ..deck_planner.planner_models import ProposalContext
from ..evidence_planner.evidence_models import EvidencePlannerResult
from .designer_enums import (
    DisclosureType,
    EvidenceAlignmentLevel,
    MessageConfidence,
    MessagePurpose,
    MessageRiskLevel,
    MessageStatus,
    MessageStrength,
    MessageStyle,
    MessageTone,
    MessageValidationSeverity,
)
from .designer_errors import SUPPORTED_MESSAGE_DESIGN_VERSION, SUPPORTED_MESSAGE_DESIGNER_OUTPUT_VERSION


MAX_HEADLINE_CHARS = 60
MAX_MAIN_MESSAGE_CHARS = 120
MAX_SUPPORTING_MESSAGES = 3
MAX_SUPPORTING_MESSAGE_CHARS = 80
MAX_KEY_TAKEAWAY_CHARS = 80
MAX_SPEAKER_NOTE_CHARS = 300


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    text = str(value or "").strip()
    return text or None


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


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


class SupportingMessage(_BaseModel):
    supporting_message_id: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=MAX_SUPPORTING_MESSAGE_CHARS)
    purpose: MessagePurpose = MessagePurpose.PROVE_VALUE
    evidence_ids: list[str] = Field(default_factory=list, max_items=8)

    _normalize = validator("supporting_message_id", "text", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class NumericClaim(_BaseModel):
    claim_id: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=80)
    value: str = Field(..., min_length=1, max_length=80)
    unit: Optional[str] = Field(default=None, max_length=40)
    is_trial_calculation: bool = False
    basis_evidence_ids: list[str] = Field(default_factory=list, min_items=1, max_items=8)
    confidence: MessageConfidence = MessageConfidence.MEDIUM

    _normalize = validator("claim_id", "label", "value", "unit", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("basis_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class UnsupportedClaim(_BaseModel):
    claim_id: str = Field(..., min_length=1, max_length=100)
    text: str = Field(..., min_length=1, max_length=160)
    reason: str = Field(..., min_length=1, max_length=220)
    recommended_action: str = Field(..., min_length=1, max_length=220)

    _normalize = validator("claim_id", "text", "reason", "recommended_action", pre=True, allow_reuse=True)(
        _clean_optional_text
    )


class EvidenceUsage(_BaseModel):
    evidence_id: str = Field(..., min_length=1, max_length=120)
    usage: str = Field(..., min_length=1, max_length=160)
    source_type: str = Field(default="unknown", max_length=80)
    confidence: MessageConfidence = MessageConfidence.MEDIUM

    _normalize = validator("evidence_id", "usage", "source_type", pre=True, allow_reuse=True)(_clean_optional_text)


class MissingEvidenceDisclosure(_BaseModel):
    disclosure_id: str = Field(..., min_length=1, max_length=100)
    disclosure_type: DisclosureType = DisclosureType.NEEDS_CONFIRMATION
    message: str = Field(..., min_length=1, max_length=220)
    related_evidence_ids: list[str] = Field(default_factory=list, max_items=12)
    blocking: bool = False

    _normalize = validator("disclosure_id", "message", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("related_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class MessageWarning(_BaseModel):
    warning_id: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1, max_length=220)
    risk_level: MessageRiskLevel = MessageRiskLevel.MEDIUM
    related_evidence_ids: list[str] = Field(default_factory=list, max_items=12)

    _normalize = validator("warning_id", "message", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("related_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class MessageValidationIssue(_BaseModel):
    code: str = Field(..., min_length=1, max_length=48)
    severity: MessageValidationSeverity
    field_path: str = Field(..., min_length=1, max_length=180)
    message: str = Field(..., min_length=1, max_length=280)
    suggestion: Optional[str] = Field(default=None, max_length=280)
    blocking: bool = False
    source: str = Field(default="message_validator", max_length=80)
    related_slide_id: Optional[str] = Field(default=None, max_length=120)
    related_evidence_ids: list[str] = Field(default_factory=list, max_items=12)

    _normalize = validator(
        "code",
        "field_path",
        "message",
        "suggestion",
        "source",
        "related_slide_id",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_ids = validator("related_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class MessageValidationResult(_BaseModel):
    valid: bool
    status: MessageStatus
    issues: list[MessageValidationIssue] = Field(default_factory=list, max_items=40)

    @property
    def errors(self) -> list[MessageValidationIssue]:
        return [item for item in self.issues if item.severity == MessageValidationSeverity.ERROR.value]

    @property
    def warnings(self) -> list[MessageValidationIssue]:
        return [item for item in self.issues if item.severity == MessageValidationSeverity.WARNING.value]


class MessageEvaluationDimension(_BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=0, le=10)
    max_score: int = 10
    reason: str = Field(..., min_length=1, max_length=280)
    issues: list[str] = Field(default_factory=list, max_items=10)
    recommendations: list[str] = Field(default_factory=list, max_items=10)


class MessageEvaluationResult(_BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    max_score: int = 100
    grade: str = Field(..., min_length=1, max_length=2)
    dimensions: list[MessageEvaluationDimension] = Field(default_factory=list, min_items=1, max_items=16)
    blocking_issue_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    note: str = Field(..., min_length=1, max_length=320)


class MessageSourceReference(_BaseModel):
    source_id: str = Field(..., min_length=1, max_length=100)
    source_type: str = Field(..., min_length=1, max_length=80)
    label: str = Field(..., min_length=1, max_length=160)
    related_evidence_ids: list[str] = Field(default_factory=list, max_items=12)

    _normalize = validator("source_id", "source_type", "label", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_ids = validator("related_evidence_ids", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class MessageStyleProfile(_BaseModel):
    style: MessageStyle
    tone: MessageTone
    headline_rule: str = Field(..., min_length=1, max_length=220)
    main_message_rule: str = Field(..., min_length=1, max_length=220)
    avoid: list[str] = Field(default_factory=list, max_items=10)

    _normalize = validator("headline_rule", "main_message_rule", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_list = validator("avoid", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class MessageConstraint(_BaseModel):
    constraint_id: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=160)
    detail: Optional[str] = Field(default=None, max_length=260)
    blocking: bool = False

    _normalize = validator("constraint_id", "label", "detail", pre=True, allow_reuse=True)(_clean_optional_text)


class MessageGenerationMetadata(_BaseModel):
    generator: str = Field(default="offline_message_designer_phase2c", max_length=100)
    deterministic: bool = True
    llm_used: bool = False
    runtime_connected: bool = False
    source_contracts: list[str] = Field(default_factory=list, max_items=8)

    _normalize = validator("generator", pre=True, allow_reuse=True)(_clean_optional_text)
    _normalize_list = validator("source_contracts", pre=True, always=True, allow_reuse=True)(_clean_text_list)


class SlideMessageDesign(_BaseModel):
    message_design_version: str = Field(default=SUPPORTED_MESSAGE_DESIGN_VERSION, const=True)
    message_design_id: str = Field(..., min_length=1, max_length=140)
    deck_id: str = Field(..., min_length=1, max_length=120)
    slide_plan_id: str = Field(..., min_length=1, max_length=120)
    slide_blueprint_id: str = Field(..., min_length=1, max_length=120)
    slide_order: int = Field(..., ge=0, le=200)
    status: MessageStatus = MessageStatus.DRAFT

    slide_role: str = Field(..., min_length=1, max_length=80)
    slide_goal: str = Field(..., min_length=1, max_length=80)
    narrative_function: str = Field(..., min_length=1, max_length=80)
    audience: str = Field(..., min_length=1, max_length=80)
    audience_seniority: str = Field(..., min_length=1, max_length=80)
    decision_stage: str = Field(..., min_length=1, max_length=80)
    message_style: MessageStyle = MessageStyle.NEUTRAL
    message_tone: MessageTone = MessageTone.CONCISE

    headline: str = Field(..., min_length=1, max_length=MAX_HEADLINE_CHARS)
    main_message: str = Field(..., min_length=1, max_length=MAX_MAIN_MESSAGE_CHARS)
    supporting_messages: list[SupportingMessage] = Field(
        default_factory=list,
        max_items=MAX_SUPPORTING_MESSAGES,
    )
    key_takeaway: str = Field(..., min_length=1, max_length=MAX_KEY_TAKEAWAY_CHARS)
    speaker_note_summary: str = Field(..., min_length=1, max_length=MAX_SPEAKER_NOTE_CHARS)

    evidence_alignment_level: EvidenceAlignmentLevel = EvidenceAlignmentLevel.NOT_APPLICABLE
    evidence_alignment_summary: str = Field(..., min_length=1, max_length=240)
    used_evidence_ids: list[str] = Field(default_factory=list, max_items=20)
    unused_required_evidence_ids: list[str] = Field(default_factory=list, max_items=20)
    missing_evidence_disclosure: list[MissingEvidenceDisclosure] = Field(default_factory=list, max_items=10)
    unsupported_claims: list[UnsupportedClaim] = Field(default_factory=list, max_items=10)
    numeric_claims: list[NumericClaim] = Field(default_factory=list, max_items=8)
    evidence_usage: list[EvidenceUsage] = Field(default_factory=list, max_items=20)

    message_strength: MessageStrength = MessageStrength.CLEAR
    message_confidence: MessageConfidence = MessageConfidence.MEDIUM
    warnings: list[MessageWarning] = Field(default_factory=list, max_items=12)
    validation_result: Optional[MessageValidationResult] = None
    evaluation_result: Optional[MessageEvaluationResult] = None

    source_references: list[MessageSourceReference] = Field(default_factory=list, max_items=16)
    style_profile: Optional[MessageStyleProfile] = None
    constraints: list[MessageConstraint] = Field(default_factory=list, max_items=12)
    generation_metadata: MessageGenerationMetadata = Field(default_factory=MessageGenerationMetadata)
    generation_source: str = Field(default="offline_message_designer_phase2c", max_length=100)
    input_fingerprint: str = Field(..., min_length=1, max_length=100)
    created_at: datetime
    schema_version: str = Field(default=SUPPORTED_MESSAGE_DESIGN_VERSION, const=True)

    _normalize = validator(
        "message_design_id",
        "deck_id",
        "slide_plan_id",
        "slide_blueprint_id",
        "slide_role",
        "slide_goal",
        "narrative_function",
        "audience",
        "audience_seniority",
        "decision_stage",
        "headline",
        "main_message",
        "key_takeaway",
        "speaker_note_summary",
        "evidence_alignment_summary",
        "generation_source",
        "input_fingerprint",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_ids = validator(
        "used_evidence_ids",
        "unused_required_evidence_ids",
        pre=True,
        always=True,
        allow_reuse=True,
    )(_clean_text_list)


class MessageDesignerInput(_BaseModel):
    proposal_context: ProposalContext
    deck_blueprint: DeckBlueprint
    evidence_planner_output: EvidencePlannerResult


class MessageDesignerOutput(_BaseModel):
    message_designer_output_version: str = Field(default=SUPPORTED_MESSAGE_DESIGNER_OUTPUT_VERSION, const=True)
    created_at: datetime
    deck_id: str = Field(..., min_length=1, max_length=120)
    slide_messages: list[SlideMessageDesign] = Field(default_factory=list, min_items=1, max_items=80)
    evaluation_result: Optional[MessageEvaluationResult] = None
    warnings: list[MessageWarning] = Field(default_factory=list, max_items=40)
    generated_slide_blueprints: bool = False
    generated_visuals: bool = False
    generated_diagrams: bool = False
    generated_layouts: bool = False
    generated_pptx: bool = False
    connected_to_runtime: bool = False

    _normalize = validator("deck_id", pre=True, allow_reuse=True)(_clean_optional_text)

