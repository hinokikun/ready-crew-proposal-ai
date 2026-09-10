from dataclasses import FrozenInstanceError, replace

import pytest

from app.services.presentation_master.integration.m30_slot_ready_requirements import (
    M30_MASTER_ID,
    M30_SLOT_READY_REQUIREMENTS,
    MasterSlotReadyRequirement,
)


def test_m30_requirements_are_the_approved_logical_contract():
    assert [(item.semantic_role, item.cardinality, item.required_fields) for item in M30_SLOT_READY_REQUIREMENTS] == [
        ("visible_issue", 1, ("title", "accent", "subtitle")),
        ("root_cause", 4, ("title", "body")),
        ("causal_state", 5, ("statement",)),
        ("business_implication", 4, ("title", "body")),
        ("solution_direction", 1, ("statement",)),
    ]
    assert all(item.master_id == M30_MASTER_ID for item in M30_SLOT_READY_REQUIREMENTS)
    assert sum(item.cardinality for item in M30_SLOT_READY_REQUIREMENTS) == 15


def test_requirements_are_immutable_and_have_no_golden_identifiers():
    with pytest.raises(FrozenInstanceError):
        M30_SLOT_READY_REQUIREMENTS[0].cardinality = 2
    assert all("shape" not in field for item in M30_SLOT_READY_REQUIREMENTS for field in item.required_fields)
    assert all("golden" not in field.lower() for item in M30_SLOT_READY_REQUIREMENTS for field in item.required_fields)


def test_requirement_derivation_policy_accepts_existing_generic_types():
    assert all(set(item.allowed_derivation_types) == set(__import__(
        "app.services.presentation_master.integration.slot_ready_content",
        fromlist=["SlotReadyDerivationType"],
    ).SlotReadyDerivationType) for item in M30_SLOT_READY_REQUIREMENTS)
