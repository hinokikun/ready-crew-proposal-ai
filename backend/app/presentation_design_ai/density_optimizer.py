"""Content density rules."""

from __future__ import annotations


def normalize_visible_text(text: str, limit: int) -> str:
    value = " ".join(str(text or "").replace("\n", " ").split())
    if len(value) <= limit:
        return value
    return value[:limit].rstrip("、。,. ")


def density_target_for_slide(composition_type: str) -> tuple[str, float]:
    if composition_type in {"hero", "section_divider", "closing_decision"}:
        return "60-110 visible characters", 0.72
    if composition_type in {"dashboard", "timeline", "matrix"}:
        return "80-140 visible characters", 0.70
    return "80-150 visible characters", 0.68


def visible_character_count(*parts: object) -> int:
    return sum(len(str(part or "")) for part in parts)
