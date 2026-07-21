from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from app.strategy_engine.models import StrategyBrief

from .enums import ActionOwner, ActionPriority, MeetingStage, ObjectionType, QuestionPriority, ReviewSeverity


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _clean_text(value: Optional[str]) -> str:
    return str(value or "").strip()


class SalesAssistantInput(BaseModel):
    schema_version: str = "sales_assistant_input_v1"
    strategy_brief: StrategyBrief
    project_title: str = ""
    project_summary: str = ""
    client_name: str = ""
    known_requirements: List[str] = Field(default_factory=list)
    known_constraints: List[str] = Field(default_factory=list)
    budget_information: str = ""
    schedule_information: str = ""
    meeting_stage: MeetingStage = MeetingStage.PREPARATION
    previous_interactions: List[str] = Field(default_factory=list)
    evidence_items: List[str] = Field(default_factory=list)

    @validator(
        "known_requirements",
        "known_constraints",
        "previous_interactions",
        "evidence_items",
        pre=True,
        always=True,
        allow_reuse=True,
    )
    def normalize_lists(cls, value):
        return _as_list(value)

    @validator(
        "project_title",
        "project_summary",
        "client_name",
        "budget_information",
        "schedule_information",
        pre=True,
        always=True,
        allow_reuse=True,
    )
    def normalize_texts(cls, value):
        return _clean_text(value)

    class Config:
        use_enum_values = True


class SalesAssistantSummary(BaseModel):
    project_title: str
    client_name: str
    category: str
    persona: str
    decision_maker: str
    strategy: str
    story: str
    sales_objective: str
    recommended_positioning: str
    primary_message: str
    main_message: str
    confidence: float
    human_review_required: bool
    human_review_reasons: List[str] = Field(default_factory=list)
    summary_notes: List[str] = Field(default_factory=list)


class MeetingPlan(BaseModel):
    meeting_stage: MeetingStage
    recommended_duration_minutes: int
    objective: str
    opening: str
    agenda: List[str] = Field(default_factory=list)
    desired_outcome: str
    next_step_goal: str
    success_criteria: List[str] = Field(default_factory=list)
    time_allocation_minutes: Dict[str, int] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class DiscoveryQuestion(BaseModel):
    id: str
    priority: QuestionPriority
    question: str
    purpose: str
    target_persona: str
    required: bool
    follow_up_questions: List[str] = Field(default_factory=list)
    linked_strategy_field: str

    class Config:
        use_enum_values = True


class TalkTrack(BaseModel):
    opening_talk: str
    problem_confirmation: str
    proposal_explanation: str
    value_explanation: str
    differentiation_talk: str
    budget_talk: str
    schedule_talk: str
    closing_talk: str
    opening_message: str
    story_beats: List[str] = Field(default_factory=list)
    transition_phrases: List[str] = Field(default_factory=list)
    closing_message: str


class ObjectionHandlingItem(BaseModel):
    objection_type: ObjectionType
    expected_objection: str
    likely_objection: str
    recommended_response: str
    supporting_evidence: List[str] = Field(default_factory=list)
    evidence_to_prepare: List[str] = Field(default_factory=list)
    prohibited_claims: List[str] = Field(default_factory=list)
    escalation_required: bool = False
    avoid_saying: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class DecisionMakerSupport(BaseModel):
    decision_maker: str
    likely_decision_criteria: List[str] = Field(default_factory=list)
    approval_barriers: List[str] = Field(default_factory=list)
    information_required_for_approval: List[str] = Field(default_factory=list)
    recommended_materials: List[str] = Field(default_factory=list)
    internal_explanation_points: List[str] = Field(default_factory=list)
    decision_points: List[str] = Field(default_factory=list)
    materials_to_prepare: List[str] = Field(default_factory=list)
    approval_risks: List[str] = Field(default_factory=list)


class EvidenceGuidance(BaseModel):
    usable_evidence: List[str] = Field(default_factory=list)
    conditional_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    claims_requiring_review: List[str] = Field(default_factory=list)
    available_evidence: List[str] = Field(default_factory=list)
    evidence_gaps: List[str] = Field(default_factory=list)
    safe_claims: List[str] = Field(default_factory=list)
    claims_requiring_confirmation: List[str] = Field(default_factory=list)


class NextAction(BaseModel):
    id: str
    priority: ActionPriority
    owner: ActionOwner
    action: str
    timing: str = "confirmation required"
    completion_condition: str
    due_hint: str = "confirmation required"
    reason: str

    class Config:
        use_enum_values = True


class FollowUp(BaseModel):
    email_subject: str
    email_body: str
    meeting_summary_template: str
    requested_client_actions: List[str] = Field(default_factory=list)
    internal_follow_up_actions: List[str] = Field(default_factory=list)
    subject: str
    attachments_to_include: List[str] = Field(default_factory=list)
    confirmation_items: List[str] = Field(default_factory=list)


class RiskAndGuardrails(BaseModel):
    review_severity: ReviewSeverity
    allowed_terms: List[str] = Field(default_factory=list)
    conditional_terms: List[str] = Field(default_factory=list)
    guardrails: List[str] = Field(default_factory=list)
    human_review_reasons: List[str] = Field(default_factory=list)
    prohibited_terms: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    compliance_notes: List[str] = Field(default_factory=list)
    removed_or_replaced_terms: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


class GenerationMetadata(BaseModel):
    schema_version: str = "sales_assistant_brief_v1"
    generator_version: str = "v49_offline_deterministic"
    strategy_brief_version: str
    source_strategy_schema_version: str
    source_strategy_confidence: float
    selected_rules: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    fallback_reasons: List[str] = Field(default_factory=list)
    deterministic: bool = True


class SalesAssistantBrief(BaseModel):
    summary: SalesAssistantSummary
    meeting_plan: MeetingPlan
    discovery_questions: List[DiscoveryQuestion] = Field(default_factory=list)
    talk_track: TalkTrack
    objection_handling: List[ObjectionHandlingItem] = Field(default_factory=list)
    decision_maker_support: DecisionMakerSupport
    evidence_guidance: EvidenceGuidance
    next_actions: List[NextAction] = Field(default_factory=list)
    follow_up: FollowUp
    risk_and_guardrails: RiskAndGuardrails
    generation_metadata: GenerationMetadata


class EvaluationItem(BaseModel):
    name: str
    passed: bool
    score: int
    notes: List[str] = Field(default_factory=list)


class SalesAssistantEvaluationReport(BaseModel):
    schema_version: str = "sales_assistant_evaluation_v1"
    overall_score: int
    passed: bool
    unsupported_claim_count: int
    items: List[EvaluationItem] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
