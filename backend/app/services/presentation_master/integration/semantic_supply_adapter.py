from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.models import PptxDownloadRequest
from app.services.presentation_master.upstream_adapter import DerivationLevel, SemanticEnvelope, SemanticGroup, SemanticItem, SemanticRelationship

from .production_semantic_contract import ProductionSemanticCandidateSet, SemanticAuthority, SemanticItemType


class SemanticAvailability(str, Enum):
    EXPLICIT_SOURCE = "EXPLICIT_SOURCE"
    SAFE_DERIVED = "SAFE_DERIVED"
    AI_INFERRED_WITH_LABEL = "AI_INFERRED_WITH_LABEL"
    EXISTING_SEMANTIC_OUTPUT = "EXISTING_SEMANTIC_OUTPUT"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_ADMISSIBLE = "NOT_ADMISSIBLE"


@dataclass(frozen=True)
class SemanticSupplyField:
    name: str
    classification: SemanticAvailability
    source_fields: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class ProductionSemanticSupply:
    fields: tuple[SemanticSupplyField, ...]

    def classification(self, name: str) -> SemanticAvailability:
        return next((field.classification for field in self.fields if field.name == name), SemanticAvailability.UNAVAILABLE)

    def unresolved(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields if field.classification in {SemanticAvailability.UNAVAILABLE, SemanticAvailability.NOT_ADMISSIBLE})


def build_semantic_envelope_from_confirmed_candidates(candidate_set: ProductionSemanticCandidateSet) -> SemanticEnvelope:
    """Build a source semantic envelope from confirmed candidates only."""
    candidates = candidate_set.admissible()
    if not candidates:
        raise ValueError("confirmed semantic candidates are required")
    grouped: dict[str, list[str]] = {"preparation": [], "decision": [], "approval": [], "execution": [], "escalation": [], "evidence": []}
    role_map = {
        SemanticItemType.PREPARATION_ANALYSIS: ("analysis outputs", "analysis", "preparation"),
        SemanticItemType.DECISION_CONDITION: ("decision conditions", "condition", "decision"),
        SemanticItemType.ACCOUNTABLE_OWNER: ("approval owner", "owner", "approval"),
        SemanticItemType.APPROVER: ("approver", "approver", "approval"),
        SemanticItemType.EXECUTION_ACTION: ("execution actions", "action", "execution"),
        SemanticItemType.DECISION_CONTEXT: ("decision_context", "context", "decision"),
        SemanticItemType.ESCALATION: ("escalation route", "escalation", "escalation"),
        SemanticItemType.EVIDENCE: ("evidence", "evidence", "evidence"),
    }
    items: list[SemanticItem] = []
    for candidate in candidates:
        if candidate.semantic_type not in role_map:
            continue
        role, content_type, group = role_map[candidate.semantic_type]
        provenance_state = "source_backed" if candidate.admissible_as_evidence else "supplied"
        evidence_state = "source_backed" if candidate.admissible_as_evidence else "unverified"
        items.append(SemanticItem(candidate.id, role, candidate.value, content_type, provenance_state, evidence_state, candidate.confidence, False, candidate.source_reference or candidate.source_field, DerivationLevel.DIRECT, f"confirmed Production semantic candidate from {candidate.source_field}"))
        grouped[group].append(candidate.id)
    relationships = tuple(SemanticRelationship(item.relationship_type, item.from_item, item.to_item, item.confidence, item.authority.value.lower(), DerivationLevel.DIRECT, f"confirmed Production semantic candidate {item.id}", False) for item in candidates if item.relationship_type and item.from_item and item.to_item)
    groups = tuple(SemanticGroup(group, group, tuple(ids), True if group != "evidence" else None, DerivationLevel.DIRECT, "confirmed Production semantic candidates") for group, ids in grouped.items() if ids)
    signals = {"process", "responsibility", "approval", "execution"}
    if relationships:
        signals.add("handoff")
    return SemanticEnvelope("production_semantic_contract_v2", "governed execution", "department_head", "operating model", frozenset(signals), tuple(items), groups, relationships, frozenset({"provided"}) if any(item.admissible_as_evidence for item in candidates) else frozenset({"missing"}), (), min(item.confidence for item in candidates), False, ())


def _has_text(payload: PptxDownloadRequest, names: tuple[str, ...]) -> bool:
    return any(bool(str(getattr(payload, name, "") or "").strip()) for name in names)


def inspect_production_semantic_supply(payload: PptxDownloadRequest, *, strategy_brief: Any | None = None) -> ProductionSemanticSupply:
    """Classify only semantics actually present at the Production boundary."""
    if not isinstance(payload, PptxDownloadRequest):
        raise TypeError("Production semantic supply requires PptxDownloadRequest")
    existing = bool(strategy_brief or payload.strategy_review_report)
    constraints = ("special_function_required", "cms_required", "contact_form_required", "seo_required", "content_creation_required")
    fields = (
        SemanticSupplyField("kpi_name", SemanticAvailability.EXISTING_SEMANTIC_OUTPUT if existing else SemanticAvailability.UNAVAILABLE, ("StrategyBrief.kpi_pack",) if existing else (), "KPI pack label is not an item-level KPI."),
        SemanticSupplyField("kpi_value", SemanticAvailability.UNAVAILABLE, note="No item-level numeric KPI value is present."),
        SemanticSupplyField("kpi_threshold", SemanticAvailability.UNAVAILABLE, note="No explicit decision threshold is present."),
        SemanticSupplyField("decision_criterion", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("decision_condition", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("ordered_stages", SemanticAvailability.EXISTING_SEMANTIC_OUTPUT if getattr(strategy_brief, "roadmap_type", "") else SemanticAvailability.UNAVAILABLE, ("StrategyBrief.roadmap_type",) if getattr(strategy_brief, "roadmap_type", "") else (), "Roadmap label is not an ordered stage list."),
        SemanticSupplyField("stage_outputs", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("exit_criteria", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("responsibilities", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("approver", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("escalation", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("evidence_items", SemanticAvailability.EXPLICIT_SOURCE if payload.case_studies.strip() else SemanticAvailability.UNAVAILABLE, ("case_studies",) if payload.case_studies.strip() else (), "Narrative evidence is explicit, but item binding is still required."),
        SemanticSupplyField("evidence_source_bindings", SemanticAvailability.UNAVAILABLE),
        SemanticSupplyField("provenance", SemanticAvailability.EXISTING_SEMANTIC_OUTPUT if existing else SemanticAvailability.EXPLICIT_SOURCE, ("strategy_review_report",) if existing else ("project_brief", "hearing_result")),
        SemanticSupplyField("constraints", SemanticAvailability.EXPLICIT_SOURCE if _has_text(payload, constraints) else SemanticAvailability.UNAVAILABLE, constraints if _has_text(payload, constraints) else ()),
        SemanticSupplyField("budget", SemanticAvailability.EXPLICIT_SOURCE if payload.budget_range.strip() else SemanticAvailability.UNAVAILABLE, ("budget_range",) if payload.budget_range.strip() else ()),
        SemanticSupplyField("timeline", SemanticAvailability.EXPLICIT_SOURCE if payload.desired_launch_timing.strip() else SemanticAvailability.UNAVAILABLE, ("desired_launch_timing",) if payload.desired_launch_timing.strip() else ()),
    )
    return ProductionSemanticSupply(fields)


__all__ = ["ProductionSemanticSupply", "SemanticAvailability", "SemanticSupplyField", "inspect_production_semantic_supply", "build_semantic_envelope_from_confirmed_candidates"]
