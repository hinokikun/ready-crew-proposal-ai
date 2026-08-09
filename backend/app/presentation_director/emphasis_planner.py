"""Emphasis and emotion curves."""

from __future__ import annotations

from .models import SlideDirectorDecision


def build_emphasis_curve(slides: tuple[SlideDirectorDecision, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "slide_id": slide.slide_id,
            "slide_no": slide.slide_no,
            "slide_role": slide.slide_role,
            "emphasis_level": slide.emphasis_level,
            "reason": "Priority slide" if slide.priority_level in {"hero", "key"} else "Supports the surrounding decision flow",
        }
        for slide in slides
    )


def build_emotion_curve(slides: tuple[SlideDirectorDecision, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "slide_id": slide.slide_id,
            "slide_no": slide.slide_no,
            "emotion_target": slide.emotion_target,
            "transition": slide.transition_to_next,
        }
        for slide in slides
    )
