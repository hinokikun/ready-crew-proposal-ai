"""Side-effect-free Phase 1A transport validation for M30 problem structure.

This module intentionally does not create semantic candidates, select a master,
or connect the new fields to composition/rendering.  It only validates and
counts the additive transport contract while preserving supplied order and IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.models import (
    BusinessImplicationTransportItem,
    BusinessRelationshipTransportItem,
    ProblemObjectTransportItem,
    SemanticBusinessTransportItem,
    SolutionDirectionTransportItem,
)
from .production_semantic_contract import (
    ProductionSemanticCandidate,
    SemanticAuthority,
    SemanticItemType,
    SemanticReviewState,
)


class ProblemStructureTransportError(ValueError):
    """Raised when the additive problem-structure contract is malformed."""


@dataclass(frozen=True)
class ProblemStructureTransportResult:
    problem_objects: tuple[ProblemObjectTransportItem, ...]
    business_implications: tuple[BusinessImplicationTransportItem, ...]
    solution_direction: SolutionDirectionTransportItem | None
    business_relationships: tuple[BusinessRelationshipTransportItem, ...]

    @property
    def all_items(self) -> tuple[SemanticBusinessTransportItem, ...]:
        values: tuple[SemanticBusinessTransportItem, ...] = (
            *self.problem_objects,
            *self.business_implications,
        )
        if self.solution_direction is not None:
            values = (*values, self.solution_direction)
        return values

    @property
    def admitted_item_count(self) -> int:
        return sum(1 for item in self.all_items if is_admitted(item))


def is_admitted(item: SemanticBusinessTransportItem) -> bool:
    """Delegate to the authoritative Production candidate predicate exactly."""

    try:
        candidate = ProductionSemanticCandidate(
            id=item.id,
            semantic_type=SemanticItemType.EVIDENCE,
            value=item.value,
            source_type=item.source_type,
            source_field=item.source_field,
            authority=SemanticAuthority(item.authority),
            confidence=1.0,
            review_state=SemanticReviewState(item.review_state),
            inferred=item.inferred,
            source_reference=item.source_reference,
            confirmation_authority=(
                SemanticAuthority(item.confirmation_authority)
                if item.confirmation_authority
                else None
            ),
        )
    except (TypeError, ValueError):
        return False
    return candidate.admissible_for_supply


def validate_problem_structure_transport(
    problem_objects: Sequence[ProblemObjectTransportItem] = (),
    business_implications: Sequence[BusinessImplicationTransportItem] = (),
    solution_direction: SolutionDirectionTransportItem | None = None,
    business_relationships: Sequence[BusinessRelationshipTransportItem] = (),
) -> ProblemStructureTransportResult:
    """Validate supplied M30 transport without conversion, duplication, or promotion."""

    objects = tuple(problem_objects)
    implications = tuple(business_implications)
    relationships = tuple(business_relationships)
    all_items = (*objects, *implications, *((solution_direction,) if solution_direction else ()))
    item_ids = tuple(item.id for item in all_items)
    if len(set(item_ids)) != len(item_ids):
        raise ProblemStructureTransportError("problem-structure item ids must be unique")
    if len({relationship.id for relationship in relationships}) != len(relationships):
        raise ProblemStructureTransportError("business relationship ids must be unique")
    known_ids = set(item_ids)
    for relationship in relationships:
        if relationship.from_item == relationship.to_item:
            raise ProblemStructureTransportError("causality relationship endpoints must differ")
        if relationship.from_item not in known_ids or relationship.to_item not in known_ids:
            raise ProblemStructureTransportError("causality relationship endpoint is unknown")
    return ProblemStructureTransportResult(objects, implications, solution_direction, relationships)


__all__ = [
    "ProblemStructureTransportError",
    "ProblemStructureTransportResult",
    "is_admitted",
    "validate_problem_structure_transport",
]
