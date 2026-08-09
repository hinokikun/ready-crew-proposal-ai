"""Version 10.0 Presentation Director AI."""

from .contracts import build_director_input
from .director import build_directed_presentation_plan, direct_case, direct_presentation
from .models import (
    AudienceAnalysis,
    DeckObjective,
    PageBudget,
    PresentationDirectorInput,
    PresentationDirectorPlan,
    SectionPlanItem,
    SlideDirectorDecision,
    StoryStrategyDecision,
)
from .validators import validate_director_plan

__all__ = [
    "AudienceAnalysis",
    "DeckObjective",
    "PageBudget",
    "PresentationDirectorInput",
    "PresentationDirectorPlan",
    "SectionPlanItem",
    "SlideDirectorDecision",
    "StoryStrategyDecision",
    "build_directed_presentation_plan",
    "build_director_input",
    "direct_case",
    "direct_presentation",
    "validate_director_plan",
]
