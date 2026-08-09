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
    return issues


def has_repeated_composition(deck: DesignDeck) -> bool:
    values = [contract.composition_type for contract in deck.slide_contracts]
    return any(values[index] == values[index - 1] == values[index - 2] for index in range(2, len(values)))
