"""Conservative StrategyBrief -> semantic envelope adapter.

The adapter normalizes fields that already exist upstream and records every
derivation.  It does not select a master or create master-specific content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .composition import SemanticContentItem
from .selection import MasterSelectionInput


class DerivationLevel(str, Enum):
    DIRECT = "DIRECT"
    NORMALIZED = "NORMALIZED"
    DERIVED = "DERIVED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class SemanticItem:
    item_id: str
    semantic_role: str
    content: str
    content_type: str
    provenance_state: str
    evidence_state: str
    confidence: float
    review_required: bool
    source_field: str
    derivation_level: DerivationLevel
    derivation_basis: str


@dataclass(frozen=True)
class SemanticGroup:
    group_id: str
    semantic_purpose: str
    member_item_ids: tuple[str, ...]
    required: bool | None
    derivation_level: DerivationLevel
    derivation_basis: str


@dataclass(frozen=True)
class SemanticRelationship:
    relationship_type: str
    from_ref: str
    to_ref: str
    confidence: float
    provenance_state: str
    derivation_level: DerivationLevel
    derivation_basis: str
    human_review_required: bool


@dataclass(frozen=True)
class SemanticGap:
    gap_id: str
    description: str
    affected_semantics: tuple[str, ...]
    review_required: bool = True


@dataclass(frozen=True)
class SemanticEnvelope:
    source_schema_version: str
    narrative_intent: str
    decision_context: str
    information_pattern: str
    semantic_signals: frozenset[str]
    items: tuple[SemanticItem, ...]
    groups: tuple[SemanticGroup, ...]
    relationships: tuple[SemanticRelationship, ...]
    evidence_profile: frozenset[str]
    unresolved_gaps: tuple[SemanticGap, ...]
    confidence: float
    human_review_required: bool
    human_review_reasons: tuple[str, ...]

    def to_selection_input(self) -> MasterSelectionInput:
        return MasterSelectionInput(
            narrative_intent=self.narrative_intent,
            information_pattern=self.information_pattern,
            relationship_types=frozenset(item.relationship_type for item in self.relationships),
            decision_context=self.decision_context,
            evidence_states=self.evidence_profile,
            available_groups=frozenset(group.group_id for group in self.groups),
            semantic_signals=self.semantic_signals,
            content_counts={group.group_id: len(group.member_item_ids) for group in self.groups},
            confidence=self.confidence,
            human_review_required=self.human_review_required,
            missing_information=tuple(gap.gap_id for gap in self.unresolved_gaps),
        )


@dataclass(frozen=True)
class MasterCoverage:
    master_id: str
    status: str
    missing_semantics: tuple[str, ...]
    matched_semantics: tuple[str, ...]


ACTUAL_STRATEGY_BRIEF_FIELDS = (
    "schema_version",
    "project_category",
    "secondary_category",
    "primary_persona",
    "secondary_personas",
    "decision_maker",
    "primary_strategy",
    "secondary_strategies",
    "story_type",
    "primary_pack",
    "secondary_pack",
    "confidence",
    "selection_reasons",
    "assumptions",
    "missing_information",
    "evidence_summary",
    "hero_theme",
    "main_message",
    "problem_theme",
    "before_after_type",
    "architecture_type",
    "roadmap_type",
    "kpi_pack",
    "estimate_pack",
    "priority_messages",
    "risk_messages",
    "next_actions",
    "required_slide_types",
    "optional_slide_types",
    "allowed_terms",
    "conditional_terms",
    "prohibited_terms",
    "human_review_required",
    "human_review_reasons",
    "sales_strategy_brief",
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _value(value: Any) -> str:
    return _text(getattr(value, "value", value)).lower()


def _list_values(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(_text(item) for item in value if _text(item))


def _item(
    item_id: str,
    role: str,
    content: str,
    content_type: str,
    source_field: str,
    *,
    provenance: str = "generated_inferred",
    evidence: str = "unverified",
    confidence: float,
    level: DerivationLevel,
    basis: str,
    review: bool = False,
) -> SemanticItem:
    return SemanticItem(item_id, role, content, content_type, provenance, evidence, confidence, review, source_field, level, basis)


def _append_group(groups: dict[str, list[str]], group_id: str, item_id: str) -> None:
    groups.setdefault(group_id, []).append(item_id)


def adapt_strategy_brief(brief: Any) -> SemanticEnvelope:
    """Adapt an actual StrategyBrief-shaped object without master selection."""

    confidence = max(0.0, min(1.0, float(getattr(brief, "confidence", 0.0) or 0.0)))
    items: list[SemanticItem] = []
    group_members: dict[str, list[str]] = {}
    gaps: list[SemanticGap] = []
    signals: set[str] = set()

    direct_text_fields = (
        ("main_message", "main_message", "claim", "narrative"),
        ("problem_theme", "problem", "problem", "problems"),
        ("hero_theme", "theme", "theme", "narrative"),
    )
    for field_name, role, content_type, group_id in direct_text_fields:
        content = _text(getattr(brief, field_name, ""))
        if content:
            item_id = f"brief:{field_name}"
            items.append(_item(item_id, role, content, content_type, f"StrategyBrief.{field_name}", confidence=confidence, level=DerivationLevel.DIRECT, basis=f"explicit StrategyBrief.{field_name}"))
            _append_group(group_members, group_id, item_id)

    list_fields = (
        ("priority_messages", "priority_message", "message", "messages"),
        ("risk_messages", "risk", "risk", "risks"),
        ("next_actions", "action", "action", "actions"),
        ("required_slide_types", "required_presentation_element", "requirement", "presentation_requirements"),
    )
    for field_name, role, content_type, group_id in list_fields:
        for index, content in enumerate(_list_values(getattr(brief, field_name, ()) )):
            item_id = f"brief:{field_name}:{index}"
            items.append(_item(item_id, role, content, content_type, f"StrategyBrief.{field_name}[{index}]", confidence=confidence, level=DerivationLevel.DIRECT, basis=f"explicit ordered StrategyBrief.{field_name}"))
            _append_group(group_members, group_id, item_id)

    evidence_summary = getattr(brief, "evidence_summary", {}) or {}
    evidence_profile: set[str] = set()
    for key, level in sorted(evidence_summary.items()):
        evidence_state = _value(level) or "missing"
        evidence_profile.add(evidence_state)
        item_id = f"brief:evidence_summary:{key}"
        items.append(_item(item_id, "evidence_summary", key, "evidence", f"StrategyBrief.evidence_summary[{key!r}]", provenance="supplied", evidence=evidence_state, confidence=confidence, level=DerivationLevel.DIRECT, basis="explicit evidence summary; item-level source binding unavailable", review=True))
        _append_group(group_members, "evidence", item_id)
    if evidence_summary:
        gaps.append(SemanticGap("evidence_item_binding_missing", "Evidence summary exists but does not identify item-level source records.", ("evidence", "source_binding")))

    category = _value(getattr(brief, "project_category", ""))
    strategy = _value(getattr(brief, "primary_strategy", ""))
    story = _value(getattr(brief, "story_type", ""))
    decision_context = _value(getattr(brief, "decision_maker", ""))
    pack = _value(getattr(brief, "primary_pack", ""))
    for value in (category, strategy, story, pack):
        if value:
            signals.add(value)
    signal_aliases = {
        "roi": "investment",
        "customer_experience": "journey",
        "risk_reduction": "risk",
        "governance": "governance",
        "quality_improvement": "verification",
        "operational_improvement": "process",
        "digital_transformation": "transformation",
    }
    for value in (strategy, story):
        if value in signal_aliases:
            signals.add(signal_aliases[value])
    kpi_evidence = _value(evidence_summary.get("kpi", ""))
    if kpi_evidence in {"provided", "confirmed"}:
        signals.add("kpi")
        gaps.append(SemanticGap("kpi_values_missing", "KPI pack label exists, but item-level KPI values and thresholds are absent.", ("metric", "threshold")))
    roadmap = _text(getattr(brief, "roadmap_type", "" )).lower()
    if roadmap:
        signals.add("roadmap")
        if "stage" in roadmap or "phase" in roadmap:
            signals.add("staged")
            gaps.append(SemanticGap("stage_items_missing", "Roadmap type is present, but ordered stage items are absent.", ("stages", "sequence")))
    if not decision_context or decision_context == "unknown":
        gaps.append(SemanticGap("decision_context_unclear", "Decision maker is unknown or absent.", ("decision_context",)))
    if confidence < 0.6:
        gaps.append(SemanticGap("low_confidence", "Upstream confidence is below the conservative selection threshold.", ("selection",)))

    relationships: list[SemanticRelationship] = []
    action_ids = tuple(group_members.get("actions", ()))
    for source, target in zip(action_ids, action_ids[1:]):
        relationships.append(SemanticRelationship("sequence", source, target, confidence, "generated_inferred", DerivationLevel.DERIVED, "explicit order in StrategyBrief.next_actions", confidence < 0.75))

    groups = tuple(
        SemanticGroup(group_id, group_id.replace("_", " "), tuple(member_ids), None, DerivationLevel.DERIVED, "members share an explicit StrategyBrief field")
        for group_id, member_ids in sorted(group_members.items())
    )
    review_reasons = tuple(_list_values(getattr(brief, "human_review_reasons", ())))
    unresolved = tuple(gaps)
    return SemanticEnvelope(
        _text(getattr(brief, "schema_version", "")) or "unknown",
        story or _text(getattr(brief, "hero_theme", "")),
        decision_context,
        _text(getattr(brief, "roadmap_type", "")) or _text(getattr(brief, "kpi_pack", "")),
        frozenset(signals),
        tuple(items),
        groups,
        tuple(relationships),
        frozenset(evidence_profile or {"missing"}),
        unresolved,
        confidence,
        bool(getattr(brief, "human_review_required", False)) or bool(unresolved),
        review_reasons + tuple(gap.gap_id for gap in unresolved),
    )


def composition_items_for_master(envelope: SemanticEnvelope, master_id: str) -> tuple[SemanticContentItem, ...]:
    """Expose only explicit semantic matches; never invent a master-specific role."""

    from .definitions import MASTER_REGISTRY

    definition = MASTER_REGISTRY.get(master_id)
    item_groups = {
        item_id: group.group_id
        for group in envelope.groups
        for item_id in group.member_item_ids
    }
    result: list[SemanticContentItem] = []
    for item in envelope.items:
        for slot in definition.slots:
            if item_groups.get(item.item_id) != slot.parent_group:
                continue
            if item.semantic_role != slot.semantic_role or item.content_type != slot.content_type:
                continue
            result.append(SemanticContentItem(item.item_id, item.semantic_role, item.content_type, slot.parent_group, item.content, item.provenance_state, item.source_field, item.evidence_state))
            break
    return tuple(result)


def assess_master_coverage(envelope: SemanticEnvelope, master_id: str) -> MasterCoverage:
    """Report honest upstream coverage without selecting or inventing content."""

    from .definitions import MASTER_REGISTRY
    from .selection import suitability_metadata

    definition = MASTER_REGISTRY.get(master_id)
    metadata = suitability_metadata(master_id)
    matched = sorted(envelope.semantic_signals & metadata.required_signals)
    required_groups = {group.group_id for group in definition.information_groups if group.required}
    present_groups = {group.group_id for group in envelope.groups}
    missing = sorted((metadata.required_signals - envelope.semantic_signals) | {f"group:{group}" for group in required_groups - present_groups})
    affected_gaps = any(set(gap.affected_semantics) & (set(metadata.required_signals) | required_groups) for gap in envelope.unresolved_gaps)
    if not missing and not affected_gaps:
        status = "SUPPORTED"
    elif matched or present_groups & required_groups:
        status = "PARTIALLY_SUPPORTED"
    else:
        status = "NOT_SUPPORTED"
    return MasterCoverage(master_id, status, tuple(missing), tuple(matched))


__all__ = [
    "ACTUAL_STRATEGY_BRIEF_FIELDS",
    "DerivationLevel",
    "SemanticEnvelope",
    "SemanticGap",
    "SemanticGroup",
    "SemanticItem",
    "SemanticRelationship",
    "MasterCoverage",
    "assess_master_coverage",
    "adapt_strategy_brief",
    "composition_items_for_master",
]
