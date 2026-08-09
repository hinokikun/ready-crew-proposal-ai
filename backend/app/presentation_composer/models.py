"""Contracts for the Version 7.0 consulting presentation composer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CaseContext:
    case_id: str
    case_name: str
    client_name: str
    industry: str
    category: str
    project_summary: str
    pain_points: tuple[str, ...]
    expected_outcomes: tuple[str, ...]
    budget: str
    timeline: str
    decision_maker: str
    competitor: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PageSpec:
    slide_no: int
    component_id: str
    component_name: str
    visual_type: str
    layout_family: str
    action_title: str
    conclusion: str
    diagram_labels: tuple[str, ...]
    evidence: str
    next_action: str
    diagram_ratio: float
    text_ratio: float
    speaker_notes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PresentationPlan:
    case: CaseContext
    pages: tuple[PageSpec, ...]
    palette_id: str
    design_system_version: str
    provider: str = "consulting_design_system"

    @property
    def slide_count(self) -> int:
        return len(self.pages)

    @property
    def distinct_layout_count(self) -> int:
        return len({page.layout_family for page in self.pages})

    @property
    def average_diagram_ratio(self) -> float:
        if not self.pages:
            return 0.0
        return round(sum(page.diagram_ratio for page in self.pages) / len(self.pages), 3)

    @property
    def average_text_ratio(self) -> float:
        if not self.pages:
            return 0.0
        return round(sum(page.text_ratio for page in self.pages) / len(self.pages), 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_dict(),
            "provider": self.provider,
            "palette_id": self.palette_id,
            "design_system_version": self.design_system_version,
            "slide_count": self.slide_count,
            "distinct_layout_count": self.distinct_layout_count,
            "average_diagram_ratio": self.average_diagram_ratio,
            "average_text_ratio": self.average_text_ratio,
            "pages": [page.to_dict() for page in self.pages],
        }
