"""Models for the Phase 2A offline Deck Planner."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator

from ..deck_models import DeckBlueprint, DeckEvaluationResult
from ..enums import VisualType


MAX_CONTEXT_TEXT = 1200
MAX_CONTEXT_LIST_ITEMS = 12


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


class ProposalContext(_BaseModel):
    """Minimal business context accepted by the offline planner."""

    project_id: Optional[str] = Field(default=None, max_length=120)
    project_name: Optional[str] = Field(default=None, max_length=160)
    project_summary: str = Field(..., min_length=1, max_length=MAX_CONTEXT_TEXT)
    industry: Optional[str] = Field(default=None, max_length=120)
    proposal_category: Optional[str] = Field(default=None, max_length=120)
    competitive_information: Optional[str] = Field(default=None, max_length=MAX_CONTEXT_TEXT)
    budget_range: Optional[str] = Field(default=None, max_length=120)
    decision_maker: Optional[str] = Field(default=None, max_length=120)
    persona: Optional[str] = Field(default=None, max_length=120)
    implementation_purpose: Optional[str] = Field(default=None, max_length=MAX_CONTEXT_TEXT)
    problems: list[str] = Field(default_factory=list, max_items=MAX_CONTEXT_LIST_ITEMS)
    expected_outcomes: list[str] = Field(default_factory=list, max_items=MAX_CONTEXT_LIST_ITEMS)
    timeline: Optional[str] = Field(default=None, max_length=160)
    language: str = Field(default="ja", min_length=2, max_length=16)

    _normalize_text = validator(
        "project_id",
        "project_name",
        "project_summary",
        "industry",
        "proposal_category",
        "competitive_information",
        "budget_range",
        "decision_maker",
        "persona",
        "implementation_purpose",
        "timeline",
        "language",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)
    _normalize_lists = validator("problems", "expected_outcomes", pre=True, always=True, allow_reuse=True)(
        _clean_text_list
    )


class PlannerRuleDecision(_BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    selected_value: str = Field(..., min_length=1, max_length=180)
    reason: str = Field(..., min_length=1, max_length=320)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)

    _normalize = validator("rule_name", "selected_value", "reason", pre=True, allow_reuse=True)(_clean_optional_text)


class PlannedSlideRecommendation(_BaseModel):
    slide_blueprint_id: str = Field(..., min_length=1, max_length=100)
    slide_order: int = Field(..., ge=0, le=200)
    section_id: str = Field(..., min_length=1, max_length=100)
    slide_role: str = Field(..., min_length=1, max_length=80)
    slide_purpose: str = Field(..., min_length=1, max_length=220)
    recommended_visual: VisualType = VisualType.TEXT_ONLY
    recommended_evidence: str = Field(default="balanced", max_length=80)
    cta_candidate: bool = False

    _normalize = validator(
        "slide_blueprint_id",
        "section_id",
        "slide_role",
        "slide_purpose",
        "recommended_evidence",
        pre=True,
        allow_reuse=True,
    )(_clean_optional_text)


class DeckPlannerWarning(_BaseModel):
    code: str = Field(..., min_length=1, max_length=80)
    message: str = Field(..., min_length=1, max_length=300)
    suggestion: Optional[str] = Field(default=None, max_length=300)

    _normalize = validator("code", "message", "suggestion", pre=True, allow_reuse=True)(_clean_optional_text)


class DeckPlannerResult(_BaseModel):
    planner_version: str = Field(default="pe2_deck_planner_v1", const=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    context: ProposalContext
    deck_blueprint: DeckBlueprint
    decisions: list[PlannerRuleDecision] = Field(default_factory=list, max_items=32)
    slide_recommendations: list[PlannedSlideRecommendation] = Field(default_factory=list, max_items=80)
    evaluation_result: Optional[DeckEvaluationResult] = None
    warnings: list[DeckPlannerWarning] = Field(default_factory=list, max_items=20)
    generated_slide_blueprints: bool = False
    connected_to_runtime: bool = False

