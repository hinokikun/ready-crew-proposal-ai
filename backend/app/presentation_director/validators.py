"""Validation rules for Presentation Director output."""

from __future__ import annotations

from .models import PresentationDirectorPlan


def validate_director_plan(plan: PresentationDirectorPlan) -> list[str]:
    errors: list[str] = []
    if not plan.deck_objective.objective:
        errors.append("deck_objective is required")
    if plan.recommended_page_count != len(plan.slide_sequence):
        errors.append("recommended_page_count must match slide_sequence length")
    if len(plan.priority_slides) < 3 or len(plan.priority_slides) > 5:
        errors.append("priority_slides must contain 3 to 5 slides")
    peak_streak = 0
    for slide in plan.slide_sequence:
        if slide.emphasis_level == "peak":
            peak_streak += 1
            if peak_streak > 1:
                errors.append("peak emphasis slides must not be consecutive")
                break
        else:
            peak_streak = 0
    if len(plan.slide_sequence) >= 13 and not plan.appendix_slides:
        errors.append("appendix_slides are required for detailed evidence separation")
    if not plan.speaker_notes_strategy:
        errors.append("speaker_notes_strategy is required")
    if "PoC" in plan.deck_objective.objective and not any("評価指標" in slide.action_title_intent for slide in plan.slide_sequence):
        errors.append("PoC deck must include evaluation metrics")
    if not any(slide.slide_role == "decision" for slide in plan.slide_sequence):
        errors.append("decision slide is required")
    return errors
