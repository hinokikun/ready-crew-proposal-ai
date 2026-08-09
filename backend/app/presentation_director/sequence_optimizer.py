"""Sequence optimizer for the V10 one-deck gate."""

from __future__ import annotations

from .models import SlideDirectorDecision


def optimize_sequence(slides: list[SlideDirectorDecision]) -> tuple[SlideDirectorDecision, ...]:
    """Keep the planned order and assert basic deck-level rhythm.

    The one-deck gate intentionally avoids a new AI reviewer. This function
    centralizes sequence assumptions so tests and artifact scripts read the
    same order.
    """

    return tuple(sorted(slides, key=lambda item: item.slide_no))
