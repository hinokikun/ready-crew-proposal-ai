"""Version 7.0 Presentation Composer."""

from .composer import compose_consulting_presentation
from .models import CaseContext, PageSpec, PresentationPlan
from .renderer import render_director_plan_to_pptx, render_plan_to_pptx

__all__ = [
    "CaseContext",
    "PageSpec",
    "PresentationPlan",
    "compose_consulting_presentation",
    "render_director_plan_to_pptx",
    "render_plan_to_pptx",
]
