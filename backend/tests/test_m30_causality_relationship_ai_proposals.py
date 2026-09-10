from __future__ import annotations

import json
from dataclasses import replace

import pytest

from app.services.presentation_master.integration.m30_canonical_ai_acquisition import (
    M30CanonicalAcquisitionRequest,
    M30CanonicalSourceRecord,
    build_m30_canonical_ai_proposals,
)
from app.services.presentation_master.integration.m30_canonical_review_decisions import (
    M30CanonicalReviewAction,
    M30CanonicalReviewDecision,
    reconstruct_m30_canonical_candidate,
)
from app.services.presentation_master.integration.m30_causality_relationship_ai_proposals import (
    M30CausalityRelationshipProposalError,
    M30CausalityRelationshipProposalRequest,
    build_m30_causality_relationship_proposals,
)
from app.services.presentation_master.integration.production_semantic_contract import SemanticAuthority, SemanticReviewState


SOURCES = (M30CanonicalSourceRecord("brief", "project_brief", "context", "step1:brief"),)


def _node(role: str, ordinal: int):
    request = M30CanonicalAcquisitionRequest(role, 1, SOURCES, f"v{ordinal}")
    candidate = build_m30_canonical_ai_proposals(request, json.dumps({"items": [{"semantic_role": role, "value": f"{role} {ordinal}"}]}))[0]
    return reconstruct_m30_canonical_candidate(candidate, M30CanonicalReviewDecision(candidate.candidate_id, M30CanonicalReviewAction.CONFIRM), SOURCES)


def _request(nodes, count=1, revision="v1"):
    return M30CausalityRelationshipProposalRequest(tuple(nodes), count, revision)


def test_confirmed_and_corrected_nodes_are_admitted_and_result_is_ai_unconfirmed():
    root = _node("root_cause", 1)
    state = _node("causal_state", 1)
    corrected = reconstruct_m30_canonical_candidate(
        build_m30_canonical_ai_proposals(M30CanonicalAcquisitionRequest("visible_issue", 1, SOURCES), '{"items":[{"semantic_role":"visible_issue","value":"issue"}]}')[0],
        M30CanonicalReviewDecision(build_m30_canonical_ai_proposals(M30CanonicalAcquisitionRequest("visible_issue", 1, SOURCES), '{"items":[{"semantic_role":"visible_issue","value":"issue"}]}')[0].candidate_id, M30CanonicalReviewAction.CORRECT, "corrected issue"),
        SOURCES,
    )
    result = build_m30_causality_relationship_proposals(_request((root, state, corrected)), '{"relationships":[{"from_id":"%s","to_id":"%s"}]}' % (root.candidate_id, state.candidate_id), SOURCES)
    assert result[0].relationship_type == "causality"
    assert result[0].authority == SemanticAuthority.AI_PROPOSED
    assert result[0].review_state == SemanticReviewState.UNCONFIRMED
    assert result[0].confirmation_authority is None and result[0].inferred is True
    assert result[0].provenance == "AI_INFERRED_FROM_REVIEWED_CANONICAL_NODES"


@pytest.mark.parametrize("state,authority", [(SemanticReviewState.UNCONFIRMED, SemanticAuthority.AI_PROPOSED), (SemanticReviewState.REJECTED, SemanticAuthority.AI_PROPOSED)])
def test_unreviewed_or_rejected_endpoint_is_rejected(state, authority):
    root = replace(_node("root_cause", 1), review_state=state, authority=authority, confirmation_authority=None)
    with pytest.raises(M30CausalityRelationshipProposalError) as error:
        build_m30_causality_relationship_proposals(_request((root, _node("causal_state", 1))), '{"relationships":[]}', SOURCES)
    assert error.value.category == "INADMISSIBLE_NODE"


def test_exact_frozen_allowed_directions_are_accepted_and_reverse_is_rejected():
    pairs = [("root_cause", "causal_state"), ("root_cause", "visible_issue"), ("causal_state", "causal_state"), ("causal_state", "visible_issue"), ("visible_issue", "business_implication"), ("causal_state", "business_implication")]
    for source_role, target_role in pairs:
        source, target = _node(source_role, 1), _node(target_role, 2)
        result = build_m30_causality_relationship_proposals(_request((source, target)), json.dumps({"relationships":[{"from_id":source.candidate_id,"to_id":target.candidate_id}]}), SOURCES)
        assert len(result) == 1
    source, target = _node("causal_state", 3), _node("root_cause", 4)
    with pytest.raises(M30CausalityRelationshipProposalError) as error:
        build_m30_causality_relationship_proposals(_request((source, target)), json.dumps({"relationships":[{"from_id":source.candidate_id,"to_id":target.candidate_id}]}), SOURCES)
    assert error.value.category == "INVALID_DIRECTION"


def test_solution_direction_self_edge_and_duplicate_nodes_fail():
    solution = _node("solution_direction", 1)
    with pytest.raises(M30CausalityRelationshipProposalError):
        build_m30_causality_relationship_proposals(_request((solution, _node("root_cause", 1))), '{"relationships":[]}', SOURCES)
    root = _node("root_cause", 1)
    with pytest.raises(M30CausalityRelationshipProposalError) as error:
        build_m30_causality_relationship_proposals(_request((root,)), json.dumps({"relationships":[{"from_id":root.candidate_id,"to_id":root.candidate_id}]}), SOURCES)
    assert error.value.category == "INVALID_COUNT"


def test_strict_output_unknown_endpoint_duplicate_wrong_count_and_markdown_fail():
    root, state = _node("root_cause", 1), _node("causal_state", 1)
    request = _request((root, state))
    cases = ["```json {} ```", '{"relationships":[{"from_id":"x","to_id":"y"}]}', json.dumps({"relationships":[{"from_id":root.candidate_id,"to_id":state.candidate_id},{"from_id":root.candidate_id,"to_id":state.candidate_id}]}), '{"relationships":[]}']
    for raw in cases:
        with pytest.raises(M30CausalityRelationshipProposalError):
            build_m30_causality_relationship_proposals(request, raw, SOURCES)


def test_identity_is_deterministic_revision_scoped_and_not_prose_derived():
    root, state = _node("root_cause", 1), _node("causal_state", 1)
    raw = json.dumps({"relationships":[{"from_id":root.candidate_id,"to_id":state.candidate_id} ]})
    first = build_m30_causality_relationship_proposals(_request((root, state)), raw, SOURCES)[0]
    second = build_m30_causality_relationship_proposals(_request((root, state)), raw, SOURCES)[0]
    other = build_m30_causality_relationship_proposals(_request((root, state), revision="v2"), raw, SOURCES)[0]
    assert first.relationship_id == second.relationship_id
    assert first.relationship_id != other.relationship_id
    assert "uuid" not in first.relationship_id.lower()


def test_count_is_bounded_no_padding_and_cycle_fails_closed():
    root, state = _node("root_cause", 1), _node("causal_state", 1)
    with pytest.raises(M30CausalityRelationshipProposalError) as error:
        build_m30_causality_relationship_proposals(_request((root, state), count=2), '{"relationships":[]}', SOURCES)
    assert error.value.category == "INVALID_COUNT"
    a, b = _node("causal_state", 2), _node("causal_state", 3)
    raw = json.dumps({"relationships":[{"from_id":a.candidate_id,"to_id":b.candidate_id},{"from_id":b.candidate_id,"to_id":a.candidate_id}]})
    with pytest.raises(M30CausalityRelationshipProposalError) as error:
        build_m30_causality_relationship_proposals(_request((a, b), count=2), raw, SOURCES)
    assert error.value.category == "CYCLE_DETECTED"


def test_stale_endpoint_fails_closed_before_relationship_build():
    root, state = _node("root_cause", 1), _node("causal_state", 1)
    changed = (M30CanonicalSourceRecord("brief", "project_brief", "changed", "step1:brief"),)
    with pytest.raises(M30CausalityRelationshipProposalError) as error:
        build_m30_causality_relationship_proposals(_request((root, state)), json.dumps({"relationships":[{"from_id":root.candidate_id,"to_id":state.candidate_id}]}), changed)
    assert error.value.category == "STALE_NODE"
