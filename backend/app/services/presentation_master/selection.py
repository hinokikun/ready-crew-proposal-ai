"""Renderer-neutral suitability and selection contract for M45-M54.

Selection is intentionally offline and semantic.  It does not route requests,
render content, or know anything about a slide renderer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .definitions import MASTER_REGISTRY, MasterDefinition


SELECTION_STATES = frozenset({"selected", "review_required", "no_match"})


@dataclass(frozen=True)
class MasterSelectionInput:
    """Small semantic projection of fields already produced upstream."""

    narrative_intent: str = ""
    information_pattern: str = ""
    relationship_types: frozenset[str] = frozenset()
    decision_context: str = ""
    evidence_states: frozenset[str] = frozenset()
    available_groups: frozenset[str] = frozenset()
    semantic_signals: frozenset[str] = frozenset()
    content_counts: Mapping[str, int] = field(default_factory=dict)
    confidence: float = 0.0
    human_review_required: bool = False
    missing_information: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if any(count < 0 for count in self.content_counts.values()):
            raise ValueError("content counts must be non-negative")

    @classmethod
    def from_strategy_brief(cls, brief: Any) -> "MasterSelectionInput":
        """Project actual StrategyBrief fields without importing its runtime model."""

        def text(name: str) -> str:
            return str(getattr(brief, name, "") or "").strip().lower()

        def values(name: str) -> tuple[str, ...]:
            value = getattr(brief, name, ()) or ()
            return tuple(str(item).strip().lower() for item in value if str(item).strip())

        evidence = getattr(brief, "evidence_summary", {}) or {}
        evidence_states = frozenset(str(value).strip().lower() for value in evidence.values())
        signals = {
            text("project_category"),
            text("primary_strategy"),
            text("story_type"),
            text("primary_pack"),
            text("kpi_pack"),
            text("roadmap_type"),
            *values("required_slide_types"),
            *values("optional_slide_types"),
        }
        signals.discard("")
        return cls(
            narrative_intent=text("story_type"),
            information_pattern=text("roadmap_type") or text("kpi_pack"),
            decision_context=text("decision_maker"),
            evidence_states=evidence_states,
            semantic_signals=frozenset(signals),
            confidence=float(getattr(brief, "confidence", 0.0) or 0.0),
            human_review_required=bool(getattr(brief, "human_review_required", False)),
            missing_information=values("missing_information"),
        )


@dataclass(frozen=True)
class SuitabilityMetadata:
    master_id: str
    positive_signals: frozenset[str]
    required_signals: frozenset[str]
    negative_signals: frozenset[str]
    decision_contexts: frozenset[str]
    evidence_required: bool = True


@dataclass(frozen=True)
class CandidateScore:
    master_id: str
    score: int
    eligible: bool
    dimension_scores: Mapping[str, int]
    selection_reason: str
    matched_signals: tuple[str, ...]
    missing_signals: tuple[str, ...]


@dataclass(frozen=True)
class MasterSelectionResult:
    state: str
    selected_master_id: str | None
    ranked_candidates: tuple[CandidateScore, ...]
    selection_reason: str
    matched_signals: tuple[str, ...]
    missing_signals: tuple[str, ...]
    confidence: float
    human_review_required: bool
    fallback_reason: str | None = None


def _metadata_for(definition: MasterDefinition) -> SuitabilityMetadata:
    common = {
        "M45": ({"executive", "summary", "thesis", "proof", "implication", "strategic_summary"}, {"thesis", "proof", "implication"}, {"metric", "journey", "escalation"}, {"ceo", "executive", "department_head"}),
        "M46": ({"observation", "record", "review", "verification", "evidence_ledger", "decision_value", "evidence_lifecycle"}, {"observation", "review"}, {"roadmap", "journey", "governance"}, {"manager", "quality_assurance", "executive"}),
        "M47": ({"kpi", "metric", "threshold", "action", "measurable", "evidence"}, {"metric", "threshold", "evidence"}, {"journey", "governance", "roadmap"}, {"executive", "department_head", "manager"}),
        "M48": ({"responsibility", "handoff", "approval", "execution", "process"}, {"responsibility", "approval", "execution"}, {"metric", "journey", "roadmap"}, {"department_head", "manager", "field_leader", "information_systems"}),
        "M49": ({"roadmap", "staged", "stage", "exit_criteria", "go_hold"}, {"roadmap", "exit_criteria", "go_hold"}, {"journey", "metric", "governance"}, {"executive", "department_head", "manager"}),
        "M50": ({"data", "data_value", "source", "business_value", "data_chain", "analysis"}, {"data", "business_value", "data_chain"}, {"journey", "governance", "roadmap"}, {"information_systems", "executive", "department_head"}),
        "M51": ({"barrier", "intervention", "behavior_change", "adoption", "outcome", "feedback"}, {"barrier", "intervention", "adoption"}, {"metric", "roadmap", "escalation"}, {"field_leader", "manager", "department_head"}),
        "M52": ({"investment", "capability", "verification", "outcome", "business_value", "go_hold"}, {"investment", "capability", "verification", "go_hold"}, {"journey", "data", "ordinary_process"}, {"ceo", "executive", "department_head"}),
        "M53": ({"journey", "friction", "intervention", "value", "touchpoint", "customer_experience"}, {"journey", "friction", "intervention"}, {"governance", "escalation", "metric"}, {"sales", "manager", "executive"}),
        "M54": ({"risk", "governance", "escalation", "responsibility", "decision_record", "control"}, {"governance", "escalation", "responsibility"}, {"ordinary_process", "journey", "kpi"}, {"quality_assurance", "information_systems", "executive", "department_head"}),
    }[definition.master_id]
    return SuitabilityMetadata(definition.master_id, frozenset(common[0]), frozenset(common[1]), frozenset(common[2]), frozenset(common[3]))


SUITABILITY_METADATA = {definition.master_id: _metadata_for(definition) for definition in MASTER_REGISTRY.all()}


def suitability_metadata(master_id: str) -> SuitabilityMetadata:
    return SUITABILITY_METADATA[master_id]


def _candidate(definition: MasterDefinition, selection: MasterSelectionInput) -> CandidateScore:
    metadata = suitability_metadata(definition.master_id)
    definition_groups = {group.group_id for group in definition.information_groups}
    definition_relationships = {relationship.relationship_type for relationship in definition.relationships}
    signals = set(selection.semantic_signals)
    matched = tuple(sorted(signals & metadata.positive_signals))
    missing = tuple(sorted(metadata.required_signals - signals))

    semantic = round(25 * len(signals & metadata.positive_signals) / max(1, len(metadata.positive_signals)))
    topology = 20 if not selection.relationship_types else round(20 * len(selection.relationship_types & definition_relationships) / max(1, len(selection.relationship_types | definition_relationships)))
    groups_present = len(selection.available_groups & definition_groups)
    groups = round(20 * groups_present / max(1, len(definition_groups))) if selection.available_groups else 10
    evidence_present = bool(selection.evidence_states - {"missing", ""})
    evidence = 15 if evidence_present else (-10 if metadata.evidence_required else 8)
    decision = 10 if selection.decision_context in metadata.decision_contexts else 0
    count_values = []
    for slot in definition.slots:
        if slot.slot_id in selection.content_counts:
            count = selection.content_counts[slot.slot_id]
            count_values.append(slot.cardinality.max_items is None or count <= slot.cardinality.max_items)
    cardinality = 5 if not count_values or all(count_values) else 0
    density = 5 if len(signals) <= 12 else 2
    dimensions = {"semantic": semantic, "topology": topology, "groups": groups, "evidence": evidence, "decision": decision, "cardinality": cardinality, "density": density}
    unsupported_topology = bool(selection.relationship_types) and not selection.relationship_types.intersection(definition_relationships)
    missing_groups = definition_groups - selection.available_groups if selection.available_groups else set()
    eligible = not missing and not unsupported_topology and not missing_groups and cardinality == 5
    if not eligible:
        reason = "candidate rejected by required semantic signal, group, topology, or cardinality boundary"
    elif not evidence_present:
        reason = "semantic fit exists, but required evidence is absent and human review is required"
    else:
        reason = f"semantic fit across {', '.join(key for key, value in dimensions.items() if value > 0)}"
    missing = tuple(sorted(set(missing) | {f"group:{group}" for group in missing_groups}))
    return CandidateScore(definition.master_id, max(0, sum(dimensions.values())), eligible, dimensions, reason, matched, missing)


def score_candidates(selection: MasterSelectionInput) -> tuple[CandidateScore, ...]:
    return tuple(sorted((_candidate(definition, selection) for definition in MASTER_REGISTRY.all()), key=lambda item: (-item.score, item.master_id)))


def select_master(selection: MasterSelectionInput) -> MasterSelectionResult:
    """Evaluate all candidates without routing or rendering."""

    ranked = score_candidates(selection)
    eligible = tuple(candidate for candidate in ranked if candidate.eligible)
    if not eligible:
        return MasterSelectionResult(
            "no_match", None, ranked, "No master satisfies the required semantic boundaries.", (), tuple(sorted(selection.missing_information)), 0.0, True, "no eligible candidate",
        )

    winner = eligible[0]
    runner_score = eligible[1].score if len(eligible) > 1 else 0
    margin = winner.score - runner_score
    matched = winner.matched_signals
    confidence = min(0.99, round(winner.score / 100, 2))
    if len(eligible) > 1 and margin < 12:
        return MasterSelectionResult("review_required", None, ranked, "Top candidates are too close for deterministic selection.", matched, winner.missing_signals, min(confidence, 0.6), True, "ambiguous semantic fit")
    if winner.score < 60:
        return MasterSelectionResult("no_match", None, ranked, "All candidates have weak semantic fit.", matched, winner.missing_signals, min(confidence, 0.4), True, "weak semantic fit")
    if not (selection.evidence_states - {"missing", ""}):
        return MasterSelectionResult("review_required", winner.master_id, ranked, "Candidate fit requires evidence confirmation before use.", matched, winner.missing_signals, min(confidence, 0.6), True, "required evidence missing")
    if selection.human_review_required:
        return MasterSelectionResult("review_required", winner.master_id, ranked, "Upstream input already requires human review.", matched, winner.missing_signals, min(confidence, 0.6), True, "upstream human review required")
    return MasterSelectionResult("selected", winner.master_id, ranked, winner.selection_reason, matched, winner.missing_signals, confidence, False)


__all__ = [
    "CandidateScore",
    "MasterSelectionInput",
    "MasterSelectionResult",
    "SELECTION_STATES",
    "SUITABILITY_METADATA",
    "SuitabilityMetadata",
    "score_candidates",
    "select_master",
    "suitability_metadata",
]
