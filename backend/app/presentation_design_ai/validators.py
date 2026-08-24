"""Validation helpers for Presentation Design AI."""

from __future__ import annotations

import re

from .contracts import REQUIRED_CONTRACT_FIELDS
from .models import DesignDeck


INTERNAL_LABEL_PATTERN = re.compile(r"(COMP-\d+|LAYOUT-\d+|TODO|placeholder|dummy)", re.IGNORECASE)


def validate_design_deck(deck: DesignDeck) -> list[str]:
    issues: list[str] = []
    if not deck.slide_contracts:
        issues.append("no_design_contracts")
    for contract in deck.slide_contracts:
        payload = contract.to_dict()
        missing = [field for field in REQUIRED_CONTRACT_FIELDS if not payload.get(field)]
        if missing:
            issues.append(f"{contract.slide_id}_missing_{','.join(missing)}")
        if len(contract.action_title) > 40:
            issues.append(f"{contract.slide_id}_action_title_too_long")
        if "..." in contract.action_title or "..." in contract.core_message:
            issues.append(f"{contract.slide_id}_ellipsis_used")
        visible = " ".join([contract.action_title, contract.core_message, contract.takeaway, *contract.supporting_evidence])
        if INTERNAL_LABEL_PATTERN.search(visible):
            issues.append(f"{contract.slide_id}_internal_label_leak")
        if contract.diagram_ratio_target < 0.60:
            issues.append(f"{contract.slide_id}_diagram_ratio_too_low")
        if contract.composition_type in {"dashboard", "three_column", "four_stage"} and "because" not in contract.composition_selection_reason:
            issues.append(f"{contract.slide_id}_panel_layout_missing_selection_reason")
        if contract.red_semantic == "single_emphasis_only" and contract.composition_type in {"dashboard", "timeline", "matrix"}:
            issues.append(f"{contract.slide_id}_red_semantic_too_generic_for_structured_layout")
        retention = contract.quality_retention
        if not retention.business_object or not retention.decision_role or not retention.must_preserve_semantic_relationship:
            issues.append(f"{contract.slide_id}_quality_retention_contract_incomplete")
        if _is_generic_diagram_escape(contract):
            issues.append(f"{contract.slide_id}_generic_diagram_escape")
    return issues


def has_repeated_composition(deck: DesignDeck) -> bool:
    values = [contract.composition_type for contract in deck.slide_contracts]
    return any(values[index] == values[index - 1] == values[index - 2] for index in range(2, len(values)))


def _is_generic_diagram_escape(contract) -> bool:
    specific_terms = (
        "flower",
        "target image",
        "decision record",
        "AI candidate",
        "human judgment",
        "judgment reason",
        "readiness",
        "threshold",
        "site",
        "conversion",
        "content",
        "candidate",
        "screening",
        "defect",
        "inspection",
        "quality",
    )
    generic_diagrams = {
        "process_flow",
        "step_flow",
        "timeline",
        "phased_roadmap",
        "kpi_dashboard",
        "progress_meter",
        "comparison_matrix",
        "current_future_table",
    }
    object_text = contract.quality_retention.business_object
    has_business_object = any(term.lower() in object_text.lower() for term in specific_terms)
    if has_business_object and contract.diagram_decision.selected_diagram in generic_diagrams:
        return True
    if contract.source_basis and contract.source_basis[0] == "roi" and contract.composition_type in {"timeline", "three_column", "four_stage"}:
        return True
    return False
