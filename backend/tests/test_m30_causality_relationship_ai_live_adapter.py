from __future__ import annotations

import json
from dataclasses import replace

import pytest

from app.config import settings
import app.services.presentation_master.integration.m30_causality_relationship_ai_live_adapter as live_adapter
from app.services.presentation_master.integration.m30_canonical_ai_acquisition import M30CanonicalAcquisitionRequest, M30CanonicalSourceRecord, build_m30_canonical_ai_proposals
from app.services.presentation_master.integration.m30_canonical_review_decisions import M30CanonicalReviewAction, M30CanonicalReviewDecision, reconstruct_m30_canonical_candidate
from app.services.presentation_master.integration.m30_causality_relationship_ai_live_adapter import M30CausalityRelationshipAILiveAdapterError, build_m30_causality_relationship_ai_input, propose_m30_causality_relationships_live
from app.services.presentation_master.integration.m30_causality_relationship_ai_proposals import M30CausalityRelationshipProposalRequest


SOURCES = (M30CanonicalSourceRecord("brief", "project_brief", "bounded context", "step1:brief"),)


def _node(role: str, revision: str):
    candidate = build_m30_canonical_ai_proposals(M30CanonicalAcquisitionRequest(role, 1, SOURCES, revision), json.dumps({"items":[{"semantic_role":role,"value":role}]}))[0]
    return reconstruct_m30_canonical_candidate(candidate, M30CanonicalReviewDecision(candidate.candidate_id, M30CanonicalReviewAction.CONFIRM), SOURCES)


def _request():
    return M30CausalityRelationshipProposalRequest((_node("root_cause", "v1"), _node("causal_state", "v2")), 1, "v1")


def test_input_is_bounded_and_excludes_unnecessary_context():
    raw = build_m30_causality_relationship_ai_input(_request())
    payload = json.loads(raw)
    assert payload["nodes"][0].keys() == {"node_id", "semantic_role", "value"}
    assert payload["requested_relationship_count"] == 1
    assert payload["proposal_revision"] == "v1"
    for forbidden in ("ProposalRequest", "presentation_topic", "PowerPoint", "deck_title", "Golden", "Renderer", "Native", "source_reference", "authority", "token", "credentials"):
        assert forbidden not in raw


def test_one_injected_call_delegates_to_frozen_builder_and_preserves_metadata():
    calls: list[str] = []
    request = _request()
    result = propose_m30_causality_relationships_live(request, SOURCES, transport=lambda value: calls.append(value) or json.dumps({"relationships":[{"from_id":request.current_nodes[0].candidate_id,"to_id":request.current_nodes[1].candidate_id}]}))
    assert len(calls) == 1
    assert result[0].relationship_type == "causality"
    assert result[0].authority.value == "AI_PROPOSED"
    assert result[0].review_state.value == "UNCONFIRMED"
    assert result[0].confirmation_authority is None and result[0].inferred is True


def test_invalid_direction_unknown_endpoint_duplicate_and_cycle_are_frozen_contract_errors():
    request = _request()
    cases = [
        {"relationships":[{"from_id":request.current_nodes[1].candidate_id,"to_id":request.current_nodes[0].candidate_id}]},
        {"relationships":[{"from_id":"unknown","to_id":request.current_nodes[1].candidate_id}]},
        {"relationships":[{"from_id":request.current_nodes[0].candidate_id,"to_id":request.current_nodes[1].candidate_id},{"from_id":request.current_nodes[0].candidate_id,"to_id":request.current_nodes[1].candidate_id}]},
    ]
    for payload in cases:
        with pytest.raises(M30CausalityRelationshipAILiveAdapterError) as error:
            propose_m30_causality_relationships_live(request, SOURCES, transport=lambda _: json.dumps(payload))
        assert error.value.category == "OFFLINE_CONTRACT_REJECTED"


def test_timeout_and_request_failure_are_bounded_without_retry():
    calls = 0

    def fail(_):
        nonlocal calls
        calls += 1
        raise RuntimeError("raw node value")

    with pytest.raises(M30CausalityRelationshipAILiveAdapterError) as error:
        propose_m30_causality_relationships_live(_request(), SOURCES, transport=fail)
    assert error.value.category == "AI_REQUEST_FAILED"
    assert "raw node" not in str(error.value)
    assert calls == 1
    with pytest.raises(M30CausalityRelationshipAILiveAdapterError) as timeout:
        propose_m30_causality_relationships_live(_request(), SOURCES, transport=lambda _: (_ for _ in ()).throw(TimeoutError()))
    assert timeout.value.category == "AI_TIMEOUT"


def test_invalid_response_is_bounded_and_not_logged():
    with pytest.raises(M30CausalityRelationshipAILiveAdapterError) as error:
        propose_m30_causality_relationships_live(_request(), SOURCES, transport=lambda _: "sensitive raw response")
    assert error.value.category == "OFFLINE_CONTRACT_REJECTED"
    assert "sensitive" not in str(error.value)


def test_missing_configuration_is_bounded(monkeypatch):
    monkeypatch.setattr(live_adapter, "settings", replace(settings, openai_api_key=""))
    with pytest.raises(M30CausalityRelationshipAILiveAdapterError) as error:
        propose_m30_causality_relationships_live(_request(), SOURCES)
    assert error.value.category == "CONFIGURATION_ERROR"
