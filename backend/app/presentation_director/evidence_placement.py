"""Evidence placement rules."""

from __future__ import annotations

from .models import SlideDirectorDecision


def plan_evidence_distribution(slides: tuple[SlideDirectorDecision, ...]) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for slide in slides:
        source_types = tuple(slide.evidence_required)
        placement = "near_key_visual" if slide.priority_level in {"hero", "key"} else "speaker_notes_or_appendix"
        if slide.priority_level == "appendix":
            placement = "appendix"
        rows.append(
            {
                "slide_id": slide.slide_id,
                "slide_role": slide.slide_role,
                "required_evidence": source_types,
                "placement": placement,
                "rule": "仮説は事実化せず、重要数値の近くに根拠を置く",
            }
        )
    return tuple(rows)
