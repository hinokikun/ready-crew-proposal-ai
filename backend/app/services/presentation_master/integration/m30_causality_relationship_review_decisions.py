"""Offline Human review reconstruction for M30 causal relationship proposals."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from enum import Enum
from typing import Iterable

from .m30_canonical_ai_acquisition import (
    M30CanonicalAIProposalCandidate,
    M30CanonicalSourceRecord,
    validate_m30_canonical_candidate_current_sources,
)
from .m30_causality_relationship_ai_proposals import (
    M30CausalityRelationshipAIProposal,
    _ALLOWED_DIRECTIONS,
    _SUPPORTED_ENDPOINT_ROLES,
    _has_cycle,
    _node_is_admissible,
)
from .production_semantic_contract import SemanticAuthority, SemanticReviewState


class M30CausalityRelationshipReviewError(ValueError):
    """Bounded error category that never contains node or decision content."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


class M30CausalityRelationshipReviewAction(str, Enum):
    CONFIRM = "CONFIRM"
    CORRECT = "CORRECT"
    REJECT = "REJECT"


@dataclass(frozen=True)
class M30CausalityRelationshipReviewDecision:
    """The only Human-controlled fields accepted by reconstruction."""

    original_relationship_id: str
    action: M30CausalityRelationshipReviewAction
    corrected_from_id: str | None = None
    corrected_to_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.original_relationship_id, str) or not self.original_relationship_id.strip():
            raise M30CausalityRelationshipReviewError("INVALID_DECISION")
        if not isinstance(self.action, M30CausalityRelationshipReviewAction):
            raise M30CausalityRelationshipReviewError("INVALID_DECISION")
        if self.corrected_from_id is not None and not isinstance(self.corrected_from_id, str):
            raise M30CausalityRelationshipReviewError("INVALID_CORRECTION")
        if self.corrected_to_id is not None and not isinstance(self.corrected_to_id, str):
            raise M30CausalityRelationshipReviewError("INVALID_CORRECTION")


@dataclass(frozen=True)
class M30ReviewedCausalityRelationship:
    """Auditable reviewed edge; corrected edges retain original lineage."""

    relationship_id: str
    original_relationship_id: str
    from_id: str
    to_id: str
    relationship_type: str
    authority: SemanticAuthority
    review_state: SemanticReviewState
    confirmation_authority: SemanticAuthority | None
    inferred: bool
    provenance: str


def _validate_current_nodes(
    current_nodes: tuple[M30CanonicalAIProposalCandidate, ...],
    current_sources: tuple[M30CanonicalSourceRecord, ...],
) -> dict[str, M30CanonicalAIProposalCandidate]:
    by_id: dict[str, M30CanonicalAIProposalCandidate] = {}
    for node in current_nodes:
        if not isinstance(node, M30CanonicalAIProposalCandidate) or node.candidate_id in by_id:
            raise M30CausalityRelationshipReviewError("INVALID_ENDPOINT")
        if not _node_is_admissible(node):
            raise M30CausalityRelationshipReviewError("INADMISSIBLE_ENDPOINT")
        if not validate_m30_canonical_candidate_current_sources(node, current_sources):
            raise M30CausalityRelationshipReviewError("STALE_ENDPOINT")
        by_id[node.candidate_id] = node
    return by_id


def _validate_reviewed_graph(
    relationships: tuple[M30ReviewedCausalityRelationship, ...],
    nodes: dict[str, M30CanonicalAIProposalCandidate],
) -> tuple[tuple[str, str], ...]:
    seen_ids: set[str] = set()
    seen_edges: set[tuple[str, str]] = set()
    edges: list[tuple[str, str]] = []
    for relationship in relationships:
        if (
            not isinstance(relationship, M30ReviewedCausalityRelationship)
            or relationship.relationship_id in seen_ids
            or relationship.relationship_type != "causality"
            or relationship.authority != SemanticAuthority.USER_EXPLICIT
            or relationship.review_state not in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}
            or relationship.confirmation_authority != SemanticAuthority.USER_EXPLICIT
            or relationship.inferred is not True
            or relationship.from_id not in nodes
            or relationship.to_id not in nodes
            or relationship.from_id == relationship.to_id
            or (nodes[relationship.from_id].semantic_role, nodes[relationship.to_id].semantic_role) not in _ALLOWED_DIRECTIONS
        ):
            raise M30CausalityRelationshipReviewError("PROVENANCE_ERROR")
        edge = (relationship.from_id, relationship.to_id)
        if edge in seen_edges:
            raise M30CausalityRelationshipReviewError("PROVENANCE_ERROR")
        seen_ids.add(relationship.relationship_id)
        seen_edges.add(edge)
        edges.append(edge)
    if _has_cycle(tuple(edges)):
        raise M30CausalityRelationshipReviewError("CYCLE_DETECTED")
    return tuple(edges)


def _validate_original_relationship(candidate: M30CausalityRelationshipAIProposal) -> None:
    if (
        not isinstance(candidate, M30CausalityRelationshipAIProposal)
        or candidate.relationship_type != "causality"
        or candidate.authority != SemanticAuthority.AI_PROPOSED
        or candidate.review_state != SemanticReviewState.UNCONFIRMED
        or candidate.confirmation_authority is not None
        or candidate.inferred is not True
        or not candidate.relationship_id.strip()
    ):
        raise M30CausalityRelationshipReviewError("INVALID_ORIGINAL_RELATIONSHIP")


def reconstruct_m30_causality_relationship(
    original_relationship: M30CausalityRelationshipAIProposal,
    decision: M30CausalityRelationshipReviewDecision,
    current_nodes: Iterable[M30CanonicalAIProposalCandidate],
    current_sources: Iterable[M30CanonicalSourceRecord],
    current_reviewed_relationships: Iterable[M30ReviewedCausalityRelationship] = (),
    *,
    review_revision: str = "v1",
) -> M30ReviewedCausalityRelationship:
    """Apply one bounded Human decision after endpoint and graph validation."""

    if not isinstance(decision, M30CausalityRelationshipReviewDecision):
        raise M30CausalityRelationshipReviewError("INVALID_DECISION")
    if decision.original_relationship_id != getattr(original_relationship, "relationship_id", None):
        raise M30CausalityRelationshipReviewError("RELATIONSHIP_ID_MISMATCH")
    if not isinstance(review_revision, str) or not review_revision.strip():
        raise M30CausalityRelationshipReviewError("INVALID_DECISION")
    _validate_original_relationship(original_relationship)
    try:
        nodes = _validate_current_nodes(tuple(current_nodes), tuple(current_sources))
        existing = tuple(current_reviewed_relationships)
    except TypeError as exc:
        raise M30CausalityRelationshipReviewError("INVALID_ENDPOINT") from exc
    existing_edges = _validate_reviewed_graph(existing, nodes)

    original_from = original_relationship.from_id
    original_to = original_relationship.to_id
    if original_from not in nodes or original_to not in nodes:
        raise M30CausalityRelationshipReviewError("INVALID_ENDPOINT")
    if (nodes[original_from].semantic_role, nodes[original_to].semantic_role) not in _ALLOWED_DIRECTIONS:
        raise M30CausalityRelationshipReviewError("INVALID_DIRECTION")
    if (original_from, original_to) in existing_edges or _has_cycle((*existing_edges, (original_from, original_to))):
        raise M30CausalityRelationshipReviewError("CYCLE_DETECTED")

    if decision.action == M30CausalityRelationshipReviewAction.CONFIRM:
        if decision.corrected_from_id is not None or decision.corrected_to_id is not None:
            raise M30CausalityRelationshipReviewError("INVALID_DECISION")
        return _reviewed_result(original_relationship, original_relationship.relationship_id, original_from, original_to)

    if decision.action == M30CausalityRelationshipReviewAction.REJECT:
        if decision.corrected_from_id is not None or decision.corrected_to_id is not None:
            raise M30CausalityRelationshipReviewError("INVALID_DECISION")
        return M30ReviewedCausalityRelationship(
            original_relationship.relationship_id,
            original_relationship.relationship_id,
            original_from,
            original_to,
            "causality",
            SemanticAuthority.AI_PROPOSED,
            SemanticReviewState.REJECTED,
            None,
            True,
            original_relationship.provenance,
        )

    if (
        not isinstance(decision.corrected_from_id, str)
        or not decision.corrected_from_id.strip()
        or not isinstance(decision.corrected_to_id, str)
        or not decision.corrected_to_id.strip()
    ):
        raise M30CausalityRelationshipReviewError("INVALID_CORRECTION")
    from_id, to_id = decision.corrected_from_id, decision.corrected_to_id
    if from_id not in nodes or to_id not in nodes:
        raise M30CausalityRelationshipReviewError("INVALID_ENDPOINT")
    if from_id == to_id:
        raise M30CausalityRelationshipReviewError("SELF_EDGE")
    if (nodes[from_id].semantic_role, nodes[to_id].semantic_role) not in _ALLOWED_DIRECTIONS:
        raise M30CausalityRelationshipReviewError("INVALID_DIRECTION")
    if (from_id, to_id) in existing_edges or _has_cycle((*existing_edges, (from_id, to_id))):
        raise M30CausalityRelationshipReviewError("CYCLE_DETECTED")
    identity = {
        "original_relationship_id": original_relationship.relationship_id,
        "from_id": from_id,
        "to_id": to_id,
        "relationship_type": "causality",
        "review_revision": review_revision,
    }
    encoded = json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
    relationship_id = f"m30-causality-reviewed:{hashlib.sha256(encoded).hexdigest()}"
    return _reviewed_result(original_relationship, relationship_id, from_id, to_id, SemanticReviewState.CORRECTED)


def _reviewed_result(
    original: M30CausalityRelationshipAIProposal,
    relationship_id: str,
    from_id: str,
    to_id: str,
    state: SemanticReviewState = SemanticReviewState.CONFIRMED,
) -> M30ReviewedCausalityRelationship:
    return M30ReviewedCausalityRelationship(
        relationship_id,
        original.relationship_id,
        from_id,
        to_id,
        "causality",
        SemanticAuthority.USER_EXPLICIT,
        state,
        SemanticAuthority.USER_EXPLICIT,
        True,
        original.provenance,
    )


__all__ = [
    "M30CausalityRelationshipReviewAction",
    "M30CausalityRelationshipReviewDecision",
    "M30CausalityRelationshipReviewError",
    "M30ReviewedCausalityRelationship",
    "reconstruct_m30_causality_relationship",
]
