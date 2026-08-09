"""Contracts for Version 10.0 Presentation Director AI.

The director operates at deck level: audience, meeting stage, page budget,
section rhythm, evidence placement, appendix movement, and speaker notes.
It does not add a new scoring gate or change backend API contracts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


AudienceType = Literal[
    "executive",
    "department_leader",
    "field_leader",
    "it_leader",
    "procurement",
    "mixed",
    "unknown",
]
DecisionStage = Literal[
    "first_meeting",
    "problem_hypothesis",
    "specific_proposal",
    "poc_proposal",
    "final_approval",
    "execution_plan",
]
PriorityLevel = Literal["hero", "key", "support", "reference", "appendix"]
EmphasisLevel = Literal["low", "medium", "high", "peak"]
InformationStatus = Literal["known", "hypothesis", "requires_confirmation", "unknown"]


@dataclass(frozen=True)
class PresentationDirectorInput:
    case_id: str
    case_name: str
    client_name: str
    industry: str
    company_size: str
    proposal_category: str
    decision_maker: str
    secondary_audience: str
    current_sales_stage: str
    meeting_purpose: str
    presentation_time_minutes: int
    expected_outcome: str
    customer_concerns: tuple[str, ...]
    customer_maturity: InformationStatus
    budget_status: InformationStatus
    evidence_availability: InformationStatus
    kpi_availability: InformationStatus
    roi_availability: InformationStatus
    competitive_situation: str
    implementation_complexity: InformationStatus
    risk_level: InformationStatus
    proposal_context: dict[str, Any] = field(default_factory=dict)
    sales_consultant_output: dict[str, Any] = field(default_factory=dict)
    version9_design_contract: dict[str, Any] = field(default_factory=dict)
    customer_ready_validation_output: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AudienceAnalysis:
    primary_audience: str
    primary_audience_type: AudienceType
    secondary_audience: str
    secondary_audience_type: AudienceType
    decision_needs: tuple[str, ...]
    information_to_weaken: tuple[str, ...]
    human_review_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DeckObjective:
    objective: str
    sub_objectives: tuple[str, ...]
    expected_decision: str
    must_not_try_to_do: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StoryStrategyDecision:
    selected_story_strategy: str
    narrative_arc: str
    rejected_story_strategies: tuple[str, ...]
    selection_reason: str
    audience_fit: str
    sales_stage_fit: str
    evidence_fit: str
    risk: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SectionPlanItem:
    section_id: str
    title: str
    purpose: str
    slide_ids: tuple[str, ...]
    include_section_divider: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PageBudget:
    recommended_page_count: int
    presentation_time_minutes: int
    talk_time_minutes: float
    discussion_time_minutes: float
    q_and_a_minutes: float
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SlideDirectorDecision:
    slide_id: str
    slide_no: int
    section_id: str
    slide_role: str
    slide_purpose: str
    audience_need: str
    decision_support_role: str
    priority_level: PriorityLevel
    emphasis_level: EmphasisLevel
    estimated_minutes: float
    must_include: tuple[str, ...]
    may_include: tuple[str, ...]
    must_not_include: tuple[str, ...]
    action_title_intent: str
    diagram_intent: str
    evidence_required: tuple[str, ...]
    emotion_target: str
    transition_from_previous: str
    transition_to_next: str
    speaker_note_goal: str
    removal_reason_if_optional: str = ""
    appendix_reason_if_moved: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PresentationDirectorPlan:
    version: str
    deck_objective: DeckObjective
    audience_analysis: AudienceAnalysis
    primary_audience: str
    secondary_audience: str
    decision_stage: DecisionStage
    meeting_type: str
    recommended_page_count: int
    presentation_time: int
    story_strategy: StoryStrategyDecision
    narrative_arc: str
    section_plan: tuple[SectionPlanItem, ...]
    slide_sequence: tuple[SlideDirectorDecision, ...]
    priority_slides: tuple[str, ...]
    supporting_slides: tuple[str, ...]
    optional_slides: tuple[str, ...]
    appendix_slides: tuple[str, ...]
    omitted_slides: tuple[dict[str, str], ...]
    emphasis_curve: tuple[dict[str, Any], ...]
    emotion_curve: tuple[dict[str, Any], ...]
    evidence_distribution: tuple[dict[str, Any], ...]
    decision_points: tuple[str, ...]
    questions_to_answer: tuple[str, ...]
    objections_to_resolve: tuple[str, ...]
    final_call_to_action: str
    speaker_notes_strategy: dict[str, Any]
    fallback_strategy: dict[str, Any]
    confidence: float
    human_review_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["deck_objective"] = self.deck_objective.to_dict()
        payload["audience_analysis"] = self.audience_analysis.to_dict()
        payload["story_strategy"] = self.story_strategy.to_dict()
        payload["section_plan"] = [item.to_dict() for item in self.section_plan]
        payload["slide_sequence"] = [item.to_dict() for item in self.slide_sequence]
        return payload
