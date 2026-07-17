from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .enums import (
    BudgetType,
    EvidenceLevel,
    Persona,
    PresentationPack,
    ProjectCategory,
    ReviewDecision,
    StoryType,
    StrategyType,
)


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


class ProposalStrategyInput(BaseModel):
    project_title: str = ""
    project_summary: str = ""
    industry: str = ""
    business_goals: List[str] = Field(default_factory=list)
    current_problems: List[str] = Field(default_factory=list)
    proposed_solution: str = ""
    expected_deliverables: List[str] = Field(default_factory=list)
    integrations: List[str] = Field(default_factory=list)
    schedule: str = ""
    budget: str = ""
    budget_type: BudgetType = BudgetType.UNKNOWN
    expected_kpis: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    stakeholders: List[str] = Field(default_factory=list)
    audience_hint: Optional[Persona] = None
    evidence: Dict[str, EvidenceLevel] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    source_text: str = ""

    @validator(
        "business_goals",
        "current_problems",
        "expected_deliverables",
        "integrations",
        "expected_kpis",
        "risks",
        "stakeholders",
        "constraints",
        pre=True,
        always=True,
    )
    def normalize_list(cls, value):
        return _as_list(value)

    @validator(
        "project_title",
        "project_summary",
        "industry",
        "proposed_solution",
        "schedule",
        "budget",
        "source_text",
        pre=True,
        always=True,
    )
    def normalize_text(cls, value):
        return _clean_text(value)

    def combined_text(self) -> str:
        parts: List[str] = [
            self.project_title,
            self.project_summary,
            self.industry,
            self.proposed_solution,
            self.schedule,
            self.budget,
            self.source_text,
        ]
        for items in [
            self.business_goals,
            self.current_problems,
            self.expected_deliverables,
            self.integrations,
            self.expected_kpis,
            self.risks,
            self.stakeholders,
            self.constraints,
        ]:
            parts.extend(items)
        return " ".join(part for part in parts if part).lower()


class StrategyBrief(BaseModel):
    schema_version: str = "strategy_brief_v1"
    project_category: ProjectCategory
    secondary_category: Optional[ProjectCategory] = None
    primary_persona: Persona
    secondary_personas: List[Persona] = Field(default_factory=list)
    decision_maker: Persona
    primary_strategy: StrategyType
    secondary_strategies: List[StrategyType] = Field(default_factory=list)
    story_type: StoryType
    primary_pack: PresentationPack
    secondary_pack: Optional[PresentationPack] = None
    confidence: float
    selection_reasons: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    evidence_summary: Dict[str, EvidenceLevel] = Field(default_factory=dict)
    hero_theme: str
    main_message: str
    problem_theme: str
    before_after_type: str
    architecture_type: str
    roadmap_type: str
    kpi_pack: str
    estimate_pack: str
    priority_messages: List[str] = Field(default_factory=list)
    risk_messages: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    required_slide_types: List[str] = Field(default_factory=list)
    optional_slide_types: List[str] = Field(default_factory=list)
    allowed_terms: List[str] = Field(default_factory=list)
    conditional_terms: List[str] = Field(default_factory=list)
    prohibited_terms: List[str] = Field(default_factory=list)
    human_review_required: bool
    human_review_reasons: List[str] = Field(default_factory=list)

    @validator("confidence")
    def confidence_range(cls, value):
        return max(0.0, min(1.0, round(float(value), 2)))

    class Config:
        use_enum_values = True


class ReviewOverride(BaseModel):
    field: str
    value: object
    reason: str = ""

    @validator("field", "reason", pre=True, always=True)
    def normalize_override_text(cls, value):
        return _clean_text(value)


class HumanReviewResult(BaseModel):
    decision: ReviewDecision
    reviewer: str = ""
    comment: str = ""
    overrides: List[ReviewOverride] = Field(default_factory=list)
    reviewed_at: Optional[str] = None

    @validator("reviewer", "comment", "reviewed_at", pre=True, always=True)
    def normalize_review_text(cls, value):
        return _clean_text(value)

    class Config:
        use_enum_values = True


class HumanReviewReport(BaseModel):
    schema_version: str = "strategy_brief_review_v1"
    decision: ReviewDecision
    reviewer: str = ""
    comment: str = ""
    reviewed_at: Optional[str] = None
    status: str
    applied_overrides: List[ReviewOverride] = Field(default_factory=list)
    rejected_overrides: List[ReviewOverride] = Field(default_factory=list)
    review_required_before_presentation: bool = True
    original_brief: StrategyBrief
    reviewed_brief: StrategyBrief
    markdown_summary: str = ""

    class Config:
        use_enum_values = True


class PresentationContext(BaseModel):
    schema_version: str = "presentation_context_v1"
    source_strategy_schema_version: str
    review_status: str
    hero: Dict[str, str]
    main_message: str
    problem_theme: str
    architecture_type: str
    roadmap_type: str
    kpi_pack: str
    estimate_pack: str
    slide_order: List[str] = Field(default_factory=list)
    visual_theme: str
    presentation_pack: PresentationPack
    secondary_presentation_pack: Optional[PresentationPack] = None
    required_slides: List[str] = Field(default_factory=list)
    optional_slides: List[str] = Field(default_factory=list)
    priority_messages: List[str] = Field(default_factory=list)
    risk_messages: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    allowed_terms: List[str] = Field(default_factory=list)
    conditional_terms: List[str] = Field(default_factory=list)
    prohibited_terms: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True
