"""Pure offline AI proposal contract for M30 causal relationships."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable

from .m30_canonical_ai_acquisition import (
    M30CanonicalAIProposalCandidate,
    M30CanonicalSourceRecord,
    validate_m30_canonical_candidate_current_sources,
)
from .m30_semantic_bridge import _ALLOWED_DIRECTIONS
from .production_semantic_contract import SemanticAuthority, SemanticReviewState


_SUPPORTED_ENDPOINT_ROLES = frozenset({"root_cause", "causal_state", "visible_issue", "business_implication"})
_RELATIONSHIP_TYPE = "causality"


class M30CausalityRelationshipProposalError(ValueError):
    """Bounded error category that never includes node or AI content."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)


@dataclass(frozen=True)
class M30CausalityRelationshipProposalRequest:
    """Backend-owned bounded specification for one proposal batch."""

    current_nodes: tuple[M30CanonicalAIProposalCandidate, ...]
    requested_count: int
    proposal_revision: str = "v1"

    def __post_init__(self) -> None:
        if not isinstance(self.current_nodes, tuple) or not self.current_nodes:
            raise M30CausalityRelationshipProposalError("INVALID_REQUEST")
        if not isinstance(self.requested_count, int) or self.requested_count <= 0:
            raise M30CausalityRelationshipProposalError("INVALID_COUNT")
        if not isinstance(self.proposal_revision, str) or not self.proposal_revision.strip():
            raise M30CausalityRelationshipProposalError("INVALID_REQUEST")


@dataclass(frozen=True)
class M30CausalityRelationshipAIProposal:
    relationship_id: str
    from_id: str
    to_id: str
    relationship_type: str
    authority: SemanticAuthority
    review_state: SemanticReviewState
    confirmation_authority: SemanticAuthority | None
    inferred: bool
    provenance: str


def parse_m30_causality_relationship_response(raw_response: str) -> tuple[tuple[str, str], ...]:
    """Parse exactly ``{"relationships":[{"from_id","to_id"}]}``."""

    if not isinstance(raw_response, str):
        raise M30CausalityRelationshipProposalError("INVALID_STRUCTURED_OUTPUT")
    try:
        payload: Any = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError) as exc:
        raise M30CausalityRelationshipProposalError("INVALID_STRUCTURED_OUTPUT") from exc
    if not isinstance(payload, dict) or set(payload) != {"relationships"} or not isinstance(payload["relationships"], list):
        raise M30CausalityRelationshipProposalError("INVALID_STRUCTURED_OUTPUT")
    edges: list[tuple[str, str]] = []
    for item in payload["relationships"]:
        if not isinstance(item, dict) or set(item) != {"from_id", "to_id"}:
            raise M30CausalityRelationshipProposalError("INVALID_STRUCTURED_OUTPUT")
        from_id, to_id = item["from_id"], item["to_id"]
        if not isinstance(from_id, str) or not from_id.strip() or not isinstance(to_id, str) or not to_id.strip():
            raise M30CausalityRelationshipProposalError("INVALID_ENDPOINT")
        edges.append((from_id, to_id))
    return tuple(edges)


def _node_is_admissible(node: M30CanonicalAIProposalCandidate) -> bool:
    return (
        node.semantic_role in _SUPPORTED_ENDPOINT_ROLES
        and node.review_state in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}
        and node.authority in {SemanticAuthority.USER_EXPLICIT, SemanticAuthority.SYSTEM_EXTRACTED, SemanticAuthority.EXTERNAL_VERIFIED}
        and node.confirmation_authority == SemanticAuthority.USER_EXPLICIT
        and node.inferred is True
    )


def _validate_nodes(
    request: M30CausalityRelationshipProposalRequest,
    current_sources: tuple[M30CanonicalSourceRecord, ...],
) -> dict[str, M30CanonicalAIProposalCandidate]:
    if any(not isinstance(node, M30CanonicalAIProposalCandidate) for node in request.current_nodes):
        raise M30CausalityRelationshipProposalError("INVALID_NODE")
    by_id: dict[str, M30CanonicalAIProposalCandidate] = {}
    for node in request.current_nodes:
        if not node.candidate_id.strip() or node.candidate_id in by_id:
            raise M30CausalityRelationshipProposalError("INVALID_NODE")
        if not _node_is_admissible(node):
            raise M30CausalityRelationshipProposalError("INADMISSIBLE_NODE")
        if not validate_m30_canonical_candidate_current_sources(node, current_sources):
            raise M30CausalityRelationshipProposalError("STALE_NODE")
        by_id[node.candidate_id] = node
    possible = {
        (source.candidate_id, target.candidate_id)
        for source in request.current_nodes
        for target in request.current_nodes
        if source.candidate_id != target.candidate_id
        and (source.semantic_role, target.semantic_role) in _ALLOWED_DIRECTIONS
    }
    if request.requested_count > len(possible):
        raise M30CausalityRelationshipProposalError("INVALID_COUNT")
    return by_id


def _has_cycle(edges: tuple[tuple[str, str], ...]) -> bool:
    adjacency: dict[str, list[str]] = {}
    for source, target in edges:
        adjacency.setdefault(source, []).append(target)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in adjacency.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in adjacency)


def build_m30_causality_relationship_proposals(
    request: M30CausalityRelationshipProposalRequest,
    raw_response: str,
    current_sources: Iterable[M30CanonicalSourceRecord],
) -> tuple[M30CausalityRelationshipAIProposal, ...]:
    """Validate endpoint choices and build non-admissible AI proposals."""

    if not isinstance(request, M30CausalityRelationshipProposalRequest):
        raise M30CausalityRelationshipProposalError("INVALID_REQUEST")
    try:
        sources = tuple(current_sources)
    except TypeError as exc:
        raise M30CausalityRelationshipProposalError("INVALID_PROVENANCE") from exc
    by_id = _validate_nodes(request, sources)
    edges = parse_m30_causality_relationship_response(raw_response)
    if len(edges) != request.requested_count:
        raise M30CausalityRelationshipProposalError("INVALID_COUNT")
    seen: set[tuple[str, str]] = set()
    for from_id, to_id in edges:
        if from_id not in by_id or to_id not in by_id:
            raise M30CausalityRelationshipProposalError("INVALID_ENDPOINT")
        if from_id == to_id:
            raise M30CausalityRelationshipProposalError("INVALID_ENDPOINT")
        source, target = by_id[from_id], by_id[to_id]
        if (source.semantic_role, target.semantic_role) not in _ALLOWED_DIRECTIONS:
            raise M30CausalityRelationshipProposalError("INVALID_DIRECTION")
        if (from_id, to_id) in seen:
            raise M30CausalityRelationshipProposalError("DUPLICATE_EDGE")
        seen.add((from_id, to_id))
    if _has_cycle(edges):
        raise M30CausalityRelationshipProposalError("CYCLE_DETECTED")

    proposals: list[M30CausalityRelationshipAIProposal] = []
    for ordinal, (from_id, to_id) in enumerate(edges):
        identity = {
            "from_id": from_id,
            "to_id": to_id,
            "relationship_type": _RELATIONSHIP_TYPE,
            "proposal_revision": request.proposal_revision,
            "ordinal": ordinal,
        }
        encoded = json.dumps(identity, ensure_ascii=False, separators=(",", ":"), sort_keys=False).encode("utf-8")
        proposals.append(
            M30CausalityRelationshipAIProposal(
                relationship_id=f"m30-causality-ai:{hashlib.sha256(encoded).hexdigest()}",
                from_id=from_id,
                to_id=to_id,
                relationship_type=_RELATIONSHIP_TYPE,
                authority=SemanticAuthority.AI_PROPOSED,
                review_state=SemanticReviewState.UNCONFIRMED,
                confirmation_authority=None,
                inferred=True,
                provenance="AI_INFERRED_FROM_REVIEWED_CANONICAL_NODES",
            )
        )
    return tuple(proposals)


__all__ = [
    "M30CausalityRelationshipAIProposal",
    "M30CausalityRelationshipProposalError",
    "M30CausalityRelationshipProposalRequest",
    "build_m30_causality_relationship_proposals",
    "parse_m30_causality_relationship_response",
]
