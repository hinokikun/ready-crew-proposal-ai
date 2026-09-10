"""Logical SlotReady requirements for the isolated Golden M30 contract."""

from __future__ import annotations

from dataclasses import dataclass

from .slot_ready_content import SlotReadyDerivationType


@dataclass(frozen=True)
class MasterSlotReadyRequirement:
    """Immutable logical content requirement; not a physical Golden shape."""

    master_id: str
    semantic_role: str
    cardinality: int
    required_fields: tuple[str, ...]
    allowed_derivation_types: tuple[SlotReadyDerivationType, ...]


M30_MASTER_ID = "M30"
M30_SLOT_READY_REQUIREMENTS: tuple[MasterSlotReadyRequirement, ...] = (
    MasterSlotReadyRequirement(
        M30_MASTER_ID,
        "visible_issue",
        1,
        ("title", "accent", "subtitle"),
        tuple(SlotReadyDerivationType),
    ),
    MasterSlotReadyRequirement(
        M30_MASTER_ID,
        "root_cause",
        4,
        ("title", "body"),
        tuple(SlotReadyDerivationType),
    ),
    MasterSlotReadyRequirement(
        M30_MASTER_ID,
        "causal_state",
        5,
        ("statement",),
        tuple(SlotReadyDerivationType),
    ),
    MasterSlotReadyRequirement(
        M30_MASTER_ID,
        "business_implication",
        4,
        ("title", "body"),
        tuple(SlotReadyDerivationType),
    ),
    MasterSlotReadyRequirement(
        M30_MASTER_ID,
        "solution_direction",
        1,
        ("statement",),
        tuple(SlotReadyDerivationType),
    ),
)


def get_m30_slot_ready_requirement(semantic_role: str) -> MasterSlotReadyRequirement | None:
    """Return the isolated M30 requirement for a logical semantic role."""

    return next(
        (requirement for requirement in M30_SLOT_READY_REQUIREMENTS if requirement.semantic_role == semantic_role),
        None,
    )


__all__ = [
    "M30_MASTER_ID",
    "M30_SLOT_READY_REQUIREMENTS",
    "MasterSlotReadyRequirement",
    "get_m30_slot_ready_requirement",
]
