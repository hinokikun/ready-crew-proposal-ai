"""Slide transition plan."""

from __future__ import annotations

from .models import SlideDirectorDecision


def plan_transitions(slides: tuple[SlideDirectorDecision, ...]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for slide in slides:
        rows.append(
            {
                "slide_id": slide.slide_id,
                "slide_no": slide.slide_no,
                "previous_slide_connection": slide.transition_from_previous,
                "next_slide_transition": slide.transition_to_next,
                "transition_sentence": f"{slide.transition_from_previous}。{slide.transition_to_next}。",
            }
        )
    return tuple(rows)
