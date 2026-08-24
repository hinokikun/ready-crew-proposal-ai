from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VisualHierarchy:
    primary_message: str
    secondary_items: list[str]
    emphasis_terms: list[str]
    density_score: int


def build_visual_hierarchy(title: str, bullets: list[str]) -> VisualHierarchy:
    primary = title or (bullets[0] if bullets else "提案の要点")
    emphasis = [item for item in bullets if any(token in item for token in ("円", "%", "％", "KPI", "ROI", "リスク", "効果"))]
    return VisualHierarchy(primary_message=primary, secondary_items=bullets[:5], emphasis_terms=emphasis[:4], density_score=len("".join(bullets)))
