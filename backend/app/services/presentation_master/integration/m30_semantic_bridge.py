"""Isolated Phase 1B semantic bridge for the M30 problem structure.

The bridge evaluates explicit Phase 1A transport only.  It does not convert
M30 roles into Production semantic item types, select a master, or render.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Iterable, Sequence

from .problem_structure_transport import is_admitted
from .production_semantic_contract import ProductionSemanticCandidate, SemanticAuthority, SemanticItemType, SemanticReviewState
from app.models import (
    BusinessImplicationTransportItem,
    BusinessRelationshipTransportItem,
    ProblemObjectTransportItem,
    SolutionDirectionTransportItem,
)


_ALLOWED_DIRECTIONS = frozenset(
    {
        ("root_cause", "causal_state"),
        ("root_cause", "visible_issue"),
        ("causal_state", "causal_state"),
        ("causal_state", "visible_issue"),
        ("visible_issue", "business_implication"),
        ("causal_state", "business_implication"),
    }
)
_TRAILING_PUNCTUATION = re.compile(r"[。．.!！?？,:：;；]+$")


@dataclass(frozen=True)
class AdmittedSemanticNodeIdentity:
    """Stable identity and role copied from an already-admitted node."""

    id: str
    role: str


@dataclass(frozen=True)
class ValidatedCausalEdgeIdentity:
    """Identity of a causal edge already accepted by Phase 1B."""

    relationship_id: str
    from_item: str
    to_item: str
    relationship_type: str


@dataclass(frozen=True)
class M30SemanticEvaluation:
    """Auditable offline result; original transport records remain intact."""

    problem_objects: tuple[ProblemObjectTransportItem, ...]
    business_implications: tuple[BusinessImplicationTransportItem, ...]
    solution_direction: SolutionDirectionTransportItem | None
    business_relationships: tuple[BusinessRelationshipTransportItem, ...]
    admitted_visible_issue_count: int
    distinct_root_cause_count: int
    distinct_causal_state_count: int
    distinct_business_implication_count: int
    admitted_solution_direction_count: int
    valid_causality_count: int
    admissible_evidence_count: int
    m30_semantic_complete: bool
    incompleteness_reasons: tuple[str, ...]
    invalid_relationship_ids: tuple[str, ...] = ()
    admitted_node_identities: tuple[AdmittedSemanticNodeIdentity, ...] = ()
    distinct_admitted_node_identities: tuple[AdmittedSemanticNodeIdentity, ...] = ()
    admitted_solution_direction_id: str | None = None
    validated_causal_edges: tuple[ValidatedCausalEdgeIdentity, ...] = ()
    validated_graph_available: bool = False


def normalize_distinctness_value(value: str) -> str:
    """Apply only deterministic, meaning-preserving normalization."""

    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    normalized = re.sub(r"\s+", " ", normalized)
    return _TRAILING_PUNCTUATION.sub("", normalized).strip()


def _is_current(item: object) -> bool:
    """Provide a future invalidation extension without adding STALE now."""

    return str(getattr(item, "invalidation_state", "")).upper() != "STALE" and str(getattr(item, "review_state", "")).upper() != "STALE"


def _admitted(items: Iterable[object]) -> tuple[object, ...]:
    return tuple(item for item in items if _is_current(item) and is_admitted(item))


def _distinct_count(items: Iterable[object]) -> int:
    return len({normalize_distinctness_value(str(getattr(item, "value", ""))) for item in items})


def _role_of_endpoint(item_id: str, items: dict[str, object]) -> str | None:
    item = items.get(item_id)
    if isinstance(item, ProblemObjectTransportItem):
        return item.role
    if isinstance(item, BusinessImplicationTransportItem):
        return "business_implication"
    if isinstance(item, SolutionDirectionTransportItem):
        return "solution_direction"
    return None


def _node_identity(item: object) -> AdmittedSemanticNodeIdentity:
    if isinstance(item, ProblemObjectTransportItem):
        return AdmittedSemanticNodeIdentity(item.id, item.role)
    if isinstance(item, BusinessImplicationTransportItem):
        return AdmittedSemanticNodeIdentity(item.id, "business_implication")
    raise TypeError("unsupported admitted node type")


def _distinct_node_identities(
    identities: Sequence[AdmittedSemanticNodeIdentity],
    items_by_id: dict[str, object],
) -> tuple[AdmittedSemanticNodeIdentity, ...]:
    seen: set[tuple[str, str]] = set()
    distinct: list[AdmittedSemanticNodeIdentity] = []
    for identity in identities:
        item = items_by_id[identity.id]
        key = (identity.role, normalize_distinctness_value(str(getattr(item, "value", ""))))
        if key not in seen:
            seen.add(key)
            distinct.append(identity)
    return tuple(distinct)


def _relationship_authority_admitted(relationship: BusinessRelationshipTransportItem) -> bool:
    """Use the existing authority predicate only; this is not semantic remapping."""

    try:
        candidate = ProductionSemanticCandidate(
            id=relationship.id,
            # The existing predicate is authority/review based.  This temporary
            # adapter must not be used as an M30 semantic type conversion.
            semantic_type=SemanticItemType.EVIDENCE,
            value=f"relationship:{relationship.from_item}->{relationship.to_item}",
            source_type="relationship_transport",
            source_field="business_relationships",
            authority=SemanticAuthority(relationship.authority),
            confidence=1.0,
            review_state=SemanticReviewState(relationship.review_state),
            source_reference=relationship.source_reference,
            confirmation_authority=(
                SemanticAuthority(relationship.confirmation_authority)
                if relationship.confirmation_authority
                else None
            ),
        )
    except (TypeError, ValueError):
        return False
    return candidate.admissible_for_supply


def _valid_causality(
    relationships: Sequence[BusinessRelationshipTransportItem],
    items: dict[str, object],
    admitted_items: dict[str, object],
) -> tuple[BusinessRelationshipTransportItem, ...]:
    valid: list[BusinessRelationshipTransportItem] = []
    seen_edges: set[tuple[str, str, str]] = set()
    for relationship in relationships:
        source_role = _role_of_endpoint(relationship.from_item, admitted_items)
        target_role = _role_of_endpoint(relationship.to_item, admitted_items)
        edge = (relationship.from_item, relationship.to_item, relationship.relationship_type)
        if (
            relationship.relationship_type != "causality"
            or relationship.from_item == relationship.to_item
            or source_role is None
            or target_role is None
            or (source_role, target_role) not in _ALLOWED_DIRECTIONS
            or not relationship.source_reference.strip()
            or relationship.provenance_state != "supplied"
            or not _relationship_authority_admitted(relationship)
            or edge in seen_edges
        ):
            continue
        seen_edges.add(edge)
        valid.append(relationship)
    return tuple(valid)


def evaluate_m30_semantic_bridge(
    problem_objects: Sequence[ProblemObjectTransportItem] = (),
    business_implications: Sequence[BusinessImplicationTransportItem] = (),
    solution_direction: SolutionDirectionTransportItem | None = None,
    business_relationships: Sequence[BusinessRelationshipTransportItem] = (),
    *,
    evidence_candidates: Sequence[ProductionSemanticCandidate] = (),
) -> M30SemanticEvaluation:
    """Evaluate truthful M30 cardinality without activating M30 selection."""

    objects = tuple(problem_objects)
    implications = tuple(business_implications)
    relationships = tuple(business_relationships)
    all_items: tuple[object, ...] = (*objects, *implications, *((solution_direction,) if solution_direction else ()))
    item_ids = [str(getattr(item, "id", "")) for item in all_items]
    duplicate_item_ids = len(item_ids) != len(set(item_ids))
    by_id = {str(getattr(item, "id", "")): item for item in all_items}
    admitted_objects = _admitted(objects)
    admitted_implications = _admitted(implications)
    admitted_solution = _admitted((solution_direction,)) if solution_direction else ()
    admitted_nodes = (*admitted_objects, *admitted_implications)
    admitted_node_identities = tuple(_node_identity(item) for item in admitted_nodes)
    admitted_by_id = {identity.id: item for identity, item in zip(admitted_node_identities, admitted_nodes)}
    distinct_admitted_node_identities = _distinct_node_identities(admitted_node_identities, admitted_by_id)
    visible = tuple(item for item in admitted_objects if item.role == "visible_issue")
    roots = tuple(item for item in admitted_objects if item.role == "root_cause")
    states = tuple(item for item in admitted_objects if item.role == "causal_state")
    admitted_endpoint_items = {} if duplicate_item_ids else admitted_by_id
    valid_relationships = _valid_causality(relationships, by_id, admitted_endpoint_items)
    evidence = tuple(
        candidate
        for candidate in evidence_candidates
        if candidate.admissible_for_supply
        and candidate.admissible_as_evidence
        and bool(candidate.source_reference.strip())
        and _is_current(candidate)
    )
    reasons: list[str] = []
    counts = {
        "visible": _distinct_count(visible),
        "root": _distinct_count(roots),
        "state": _distinct_count(states),
        "implication": _distinct_count(admitted_implications),
        "solution": _distinct_count(admitted_solution),
    }
    thresholds = (
        ("visible", 1, "VISIBLE_ISSUE_INSUFFICIENT"),
        ("root", 4, "ROOT_CAUSE_INSUFFICIENT"),
        ("state", 5, "CAUSAL_STATE_INSUFFICIENT"),
        ("implication", 4, "BUSINESS_IMPLICATION_INSUFFICIENT"),
        ("solution", 1, "SOLUTION_DIRECTION_MISSING"),
    )
    for key, minimum, reason in thresholds:
        if counts[key] < minimum:
            reasons.append(reason)
    if len(valid_relationships) < 4:
        reasons.append("CAUSALITY_INSUFFICIENT")
    if not evidence:
        reasons.append("EVIDENCE_INSUFFICIENT")
    if duplicate_item_ids:
        reasons.append("DUPLICATE_ITEM_ID")
    invalid_relationship_ids = tuple(
        relationship.id
        for relationship in relationships
        if relationship not in valid_relationships
    )
    distinct_by_key = {
        (identity.role, normalize_distinctness_value(str(getattr(admitted_by_id[identity.id], "value", "")))): identity
        for identity in distinct_admitted_node_identities
    }
    representative_by_id = {
        identity.id: distinct_by_key[
            (identity.role, normalize_distinctness_value(str(getattr(admitted_by_id[identity.id], "value", ""))))
        ].id
        for identity in admitted_node_identities
        if identity.id in admitted_by_id
    }
    distinct_node_ids = {identity.id for identity in distinct_admitted_node_identities}
    validated_causal_edges = tuple(
        ValidatedCausalEdgeIdentity(
            relationship.id,
            representative_by_id[relationship.from_item],
            representative_by_id[relationship.to_item],
            relationship.relationship_type,
        )
        for relationship in valid_relationships
        if relationship.from_item in representative_by_id and relationship.to_item in representative_by_id
    )
    validated_graph_available = (
        not duplicate_item_ids
        and len(validated_causal_edges) == len(valid_relationships)
        and all(edge.from_item in distinct_node_ids and edge.to_item in distinct_node_ids for edge in validated_causal_edges)
    )
    return M30SemanticEvaluation(
        objects,
        implications,
        solution_direction,
        relationships,
        counts["visible"],
        counts["root"],
        counts["state"],
        counts["implication"],
        counts["solution"],
        len(valid_relationships),
        len(evidence),
        not reasons,
        tuple(dict.fromkeys(reasons)),
        invalid_relationship_ids,
        admitted_node_identities,
        distinct_admitted_node_identities,
        admitted_solution[0].id if admitted_solution else None,
        validated_causal_edges,
        validated_graph_available,
    )


__all__ = [
    "AdmittedSemanticNodeIdentity",
    "M30SemanticEvaluation",
    "ValidatedCausalEdgeIdentity",
    "evaluate_m30_semantic_bridge",
    "normalize_distinctness_value",
]
