from __future__ import annotations

import json
from dataclasses import replace

import pytest

from app.services.presentation_master.integration.m30_canonical_ai_acquisition import M30CanonicalAcquisitionRequest, M30CanonicalSourceRecord, build_m30_canonical_ai_proposals
from app.services.presentation_master.integration.m30_canonical_review_decisions import M30CanonicalReviewAction, M30CanonicalReviewDecision, reconstruct_m30_canonical_candidate
from app.services.presentation_master.integration.m30_causality_relationship_ai_proposals import M30CausalityRelationshipProposalRequest, build_m30_causality_relationship_proposals
from app.services.presentation_master.integration.m30_causality_relationship_review_decisions import (
    M30CausalityRelationshipReviewAction,
    M30CausalityRelationshipReviewDecision,
    M30CausalityRelationshipReviewError,
    M30ReviewedCausalityRelationship,
    reconstruct_m30_causality_relationship,
)
from app.services.presentation_master.integration.production_semantic_contract import SemanticAuthority, SemanticReviewState


SOURCES = (M30CanonicalSourceRecord("brief", "project_brief", "context", "step1:brief"),)


def _node(role: str, revision: str):
    candidate = build_m30_canonical_ai_proposals(M30CanonicalAcquisitionRequest(role, 1, SOURCES, revision), json.dumps({"items":[{"semantic_role":role,"value":role}]}))[0]
    return reconstruct_m30_canonical_candidate(candidate, M30CanonicalReviewDecision(candidate.candidate_id, M30CanonicalReviewAction.CONFIRM), SOURCES)


def _edge(source, target):
    request = M30CausalityRelationshipProposalRequest((source, target), 1)
    return build_m30_causality_relationship_proposals(request, json.dumps({"relationships":[{"from_id":source.candidate_id,"to_id":target.candidate_id}]}), SOURCES)[0]


def _decision(edge, action, from_id=None, to_id=None):
    return M30CausalityRelationshipReviewDecision(edge.relationship_id, action, from_id, to_id)


def test_confirm_reconstructs_user_review_without_rewriting_ai_provenance():
    root, state = _node("root_cause", "v1"), _node("causal_state", "v2")
    edge = _edge(root, state)
    result = reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CONFIRM), (root, state), SOURCES)
    assert result.relationship_id == edge.relationship_id
    assert result.original_relationship_id == edge.relationship_id
    assert (result.from_id, result.to_id, result.relationship_type) == (edge.from_id, edge.to_id, "causality")
    assert result.authority == SemanticAuthority.USER_EXPLICIT
    assert result.review_state == SemanticReviewState.CONFIRMED
    assert result.confirmation_authority == SemanticAuthority.USER_EXPLICIT
    assert result.inferred is True and result.provenance == edge.provenance


def test_corrected_endpoints_get_new_deterministic_id_and_preserve_lineage():
    root, state, visible = _node("root_cause", "v1"), _node("causal_state", "v2"), _node("visible_issue", "v3")
    edge = _edge(root, state)
    result = reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CORRECT, root.candidate_id, visible.candidate_id), (root, state, visible), SOURCES, review_revision="v1")
    assert result.relationship_id != edge.relationship_id
    assert result.original_relationship_id == edge.relationship_id
    assert (result.from_id, result.to_id) == (root.candidate_id, visible.candidate_id)
    assert result.relationship_type == "causality"
    assert result.authority == SemanticAuthority.USER_EXPLICIT
    assert result.review_state == SemanticReviewState.CORRECTED
    assert result.confirmation_authority == SemanticAuthority.USER_EXPLICIT
    assert result.inferred is True and result.provenance == edge.provenance
    assert result.relationship_id == reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CORRECT, root.candidate_id, visible.candidate_id), (root, state, visible), SOURCES, review_revision="v1").relationship_id


def test_reject_is_inadmissible_and_preserves_original_edge():
    root, state = _node("root_cause", "v1"), _node("causal_state", "v2")
    edge = _edge(root, state)
    result = reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.REJECT), (root, state), SOURCES)
    assert result.relationship_id == edge.relationship_id and result.original_relationship_id == edge.relationship_id
    assert result.review_state == SemanticReviewState.REJECTED
    assert result.authority == SemanticAuthority.AI_PROPOSED and result.confirmation_authority is None
    assert result.inferred is True


@pytest.mark.parametrize("state", [SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED, SemanticReviewState.REJECTED])
def test_already_reviewed_original_is_rejected(state):
    root, state_node = _node("root_cause", "v1"), _node("causal_state", "v2")
    edge = _edge(root, state_node)
    reviewed = replace(edge, review_state=state, authority=SemanticAuthority.USER_EXPLICIT if state != SemanticReviewState.REJECTED else SemanticAuthority.AI_PROPOSED, confirmation_authority=SemanticAuthority.USER_EXPLICIT if state != SemanticReviewState.REJECTED else None)
    with pytest.raises(M30CausalityRelationshipReviewError) as error:
        reconstruct_m30_causality_relationship(reviewed, _decision(reviewed, M30CausalityRelationshipReviewAction.CONFIRM), (root, state_node), SOURCES)
    assert error.value.category == "INVALID_ORIGINAL_RELATIONSHIP"


def test_invalid_decision_fields_and_id_fail_closed():
    root, state = _node("root_cause", "v1"), _node("causal_state", "v2")
    edge = _edge(root, state)
    with pytest.raises(M30CausalityRelationshipReviewError) as error:
        reconstruct_m30_causality_relationship(edge, M30CausalityRelationshipReviewDecision("other", M30CausalityRelationshipReviewAction.CONFIRM), (root, state), SOURCES)
    assert error.value.category == "RELATIONSHIP_ID_MISMATCH"
    for action in (M30CausalityRelationshipReviewAction.CONFIRM, M30CausalityRelationshipReviewAction.REJECT):
        with pytest.raises(M30CausalityRelationshipReviewError):
            reconstruct_m30_causality_relationship(edge, _decision(edge, action, root.candidate_id, state.candidate_id), (root, state), SOURCES)


def test_correct_requires_two_valid_current_admissible_endpoints():
    root, state, visible = _node("root_cause", "v1"), _node("causal_state", "v2"), _node("visible_issue", "v3")
    edge = _edge(root, state)
    invalids = [(None, visible.candidate_id), (root.candidate_id, None), ("unknown", visible.candidate_id), (root.candidate_id, root.candidate_id)]
    for from_id, to_id in invalids:
        with pytest.raises(M30CausalityRelationshipReviewError):
            reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CORRECT, from_id, to_id), (root, state, visible), SOURCES)
    solution = _node("solution_direction", "v4")
    with pytest.raises(M30CausalityRelationshipReviewError) as error:
        reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CORRECT, solution.candidate_id, visible.candidate_id), (root, state, visible, solution), SOURCES)
    assert error.value.category == "INADMISSIBLE_ENDPOINT"


def test_correct_invalid_direction_and_stale_endpoint_fail_closed():
    root, state = _node("root_cause", "v1"), _node("causal_state", "v2")
    edge = _edge(root, state)
    reverse = _node("root_cause", "v3")
    with pytest.raises(M30CausalityRelationshipReviewError) as error:
        reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CORRECT, state.candidate_id, reverse.candidate_id), (root, state, reverse), SOURCES)
    assert error.value.category == "INVALID_DIRECTION"
    changed = (M30CanonicalSourceRecord("brief", "project_brief", "changed", "step1:brief"),)
    with pytest.raises(M30CausalityRelationshipReviewError) as error:
        reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CONFIRM), (root, state), changed)
    assert error.value.category == "STALE_ENDPOINT"


def test_current_graph_cycle_and_duplicate_edge_fail_closed_without_repair():
    root, state, visible = _node("root_cause", "v1"), _node("causal_state", "v2"), _node("visible_issue", "v3")
    edge = _edge(root, state)
    existing = M30ReviewedCausalityRelationship("existing", "existing", state.candidate_id, visible.candidate_id, "causality", SemanticAuthority.USER_EXPLICIT, SemanticReviewState.CONFIRMED, SemanticAuthority.USER_EXPLICIT, True, "reviewed")
    result = reconstruct_m30_causality_relationship(edge, _decision(edge, M30CausalityRelationshipReviewAction.CONFIRM), (root, state, visible), SOURCES, (existing,))
    assert result.review_state == SemanticReviewState.CONFIRMED
    cycle_a, cycle_b = _node("causal_state", "v4"), _node("causal_state", "v5")
    cycle_edge = _edge(cycle_a, cycle_b)
    cycle = M30ReviewedCausalityRelationship("cycle", "cycle", cycle_b.candidate_id, cycle_a.candidate_id, "causality", SemanticAuthority.USER_EXPLICIT, SemanticReviewState.CONFIRMED, SemanticAuthority.USER_EXPLICIT, True, "reviewed")
    with pytest.raises(M30CausalityRelationshipReviewError) as error:
        reconstruct_m30_causality_relationship(cycle_edge, _decision(cycle_edge, M30CausalityRelationshipReviewAction.CONFIRM), (cycle_a, cycle_b), SOURCES, (cycle,))
    assert error.value.category == "CYCLE_DETECTED"
