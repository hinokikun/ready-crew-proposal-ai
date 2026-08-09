"""Data contracts for Presentation Design AI."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


InfoDisposition = Literal["dedicated_slide", "merge", "customer_visible", "speaker_notes", "delete", "hypothesis"]
EvidenceStatus = Literal["sufficient", "partial", "hypothesis", "missing"]
CompositionType = Literal[
    "hero",
    "full_width_diagram",
    "split_content",
    "three_column",
    "four_stage",
    "central_hub",
    "left_visual_right_text",
    "right_visual_left_text",
    "dashboard",
    "timeline",
    "matrix",
    "comparison",
    "cycle",
    "hierarchy",
    "section_divider",
    "closing_decision",
]


@dataclass(frozen=True)
class InformationItem:
    item_id: str
    label: str
    summary: str
    disposition: InfoDisposition
    customer_visible: bool
    speaker_notes_only: bool
    evidence_status: EvidenceStatus
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InformationArchitecture:
    case_id: str
    items: tuple[InformationItem, ...]
    removed_items: tuple[str, ...]
    merged_items: tuple[str, ...]
    hypothesis_items: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["items"] = [item.to_dict() for item in self.items]
        return payload


@dataclass(frozen=True)
class DiagramDecision:
    selected_diagram: str
    rejected_candidates: tuple[str, ...]
    selection_reason: str
    required_evidence: tuple[str, ...]
    visual_risk: str
    fallback_diagram: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VisualHierarchy:
    priority_1: str
    priority_2: str
    priority_3: tuple[str, ...]
    priority_4: tuple[str, ...]
    reading_order: tuple[str, ...]
    focal_point: str
    secondary_point: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DesignSlideContract:
    slide_id: str
    section_id: str
    page_goal: str
    audience: str
    decision_stage: str
    action_title: str
    core_message: str
    supporting_evidence: tuple[str, ...]
    expected_emotion: str
    visual_metaphor: str
    diagram_type: str
    composition_type: CompositionType
    information_priority: tuple[str, ...]
    reading_order: tuple[str, ...]
    focal_point: str
    secondary_point: str
    takeaway: str
    speaker_note_summary: str
    expected_question: str
    previous_slide_connection: str
    next_slide_transition: str
    text_density_target: str
    diagram_ratio_target: float
    color_role: str
    component_ids: tuple[str, ...]
    source_basis: tuple[str, ...]
    confidence: float
    human_review_reason: str
    diagram_decision: DiagramDecision
    visual_hierarchy: VisualHierarchy

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["diagram_decision"] = self.diagram_decision.to_dict()
        payload["visual_hierarchy"] = self.visual_hierarchy.to_dict()
        return payload


@dataclass(frozen=True)
class DesignDeck:
    version: str
    design_version: str
    case_id: str
    case_name: str
    client_name: str
    feature_flag_enabled: bool
    information_architecture: InformationArchitecture
    slide_contracts: tuple[DesignSlideContract, ...]
    design_language: dict[str, Any]
    design_plan_fingerprint: str
    fallback_count: int = 0
    native_fallback_count: int = 0
    render_warnings: tuple[str, ...] = ()

    @property
    def slide_count(self) -> int:
        return len(self.slide_contracts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "design_version": self.design_version,
            "case_id": self.case_id,
            "case_name": self.case_name,
            "client_name": self.client_name,
            "feature_flag_enabled": self.feature_flag_enabled,
            "information_architecture": self.information_architecture.to_dict(),
            "slide_count": self.slide_count,
            "slide_contracts": [slide.to_dict() for slide in self.slide_contracts],
            "design_language": self.design_language,
            "design_plan_fingerprint": self.design_plan_fingerprint,
            "fallback_count": self.fallback_count,
            "native_fallback_count": self.native_fallback_count,
            "render_warnings": list(self.render_warnings),
        }


@dataclass(frozen=True)
class RefinementIssue:
    slide_id: str
    category: str
    severity: Literal["P0", "P1", "P2", "P3"]
    finding: str
    correction: str
    iteration: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RefinementReport:
    iterations: int
    issues: tuple[RefinementIssue, ...]
    final_status: str
    changes_applied: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "iterations": self.iterations,
            "issues": [issue.to_dict() for issue in self.issues],
            "final_status": self.final_status,
            "changes_applied": list(self.changes_applied),
        }
