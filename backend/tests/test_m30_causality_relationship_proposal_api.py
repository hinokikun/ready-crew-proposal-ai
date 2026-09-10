import json
from dataclasses import replace

import pytest


def _reviewed_node_payload(role="root_cause", candidate_id="node-root"):
    from app.services.presentation_master.integration.m30_canonical_ai_acquisition import (
        M30CanonicalAcquisitionRequest,
        M30CanonicalSourceRecord,
        build_m30_canonical_ai_proposals,
    )
    from app.services.presentation_master.integration.production_semantic_contract import SemanticAuthority, SemanticReviewState

    source = M30CanonicalSourceRecord("step1", "project_brief", "現状の課題", "Step1.project_brief")
    request = M30CanonicalAcquisitionRequest(role, 1, (source,))
    candidate = build_m30_canonical_ai_proposals(request, json.dumps({"items": [{"semantic_role": role, "value": "課題の根本原因"}]}))[0]
    candidate = replace(
        candidate,
        candidate_id=candidate_id,
        authority=SemanticAuthority.USER_EXPLICIT,
        review_state=SemanticReviewState.CONFIRMED,
        confirmation_authority=SemanticAuthority.USER_EXPLICIT,
    )
    return {
        "candidate_id": candidate.candidate_id,
        "semantic_role": candidate.semantic_role,
        "value": candidate.value,
        "source_type": candidate.source_type,
        "source_field": candidate.source_field,
        "source_reference": candidate.source_reference,
        "source_references": list(candidate.source_references),
        "source_identities": [{"source_id": i.source_id, "source_field": i.source_field, "source_reference": i.source_reference} for i in candidate.source_identities],
        "source_fingerprint": candidate.source_fingerprint,
        "authority": candidate.authority.value,
        "review_state": candidate.review_state.value,
        "confirmation_authority": candidate.confirmation_authority.value,
        "inferred": candidate.inferred,
        "acquisition_revision": candidate.acquisition_revision,
        "original_candidate_id": candidate.original_candidate_id,
    }


def _source_payload():
    return {"source_id": "step1", "source_field": "project_brief", "value": "現状の課題", "source_reference": "Step1.project_brief"}


def _payload():
    return {"current_reviewed_nodes": [_reviewed_node_payload()], "current_sources": [_source_payload()], "requested_count": 1}


def _fake_live(request, sources):
    from app.services.presentation_master.integration.m30_causality_relationship_ai_proposals import build_m30_causality_relationship_proposals

    return build_m30_causality_relationship_proposals(request, json.dumps({"relationships": [{"from_id": "node-root", "to_id": "node-state"}]}), sources)


def test_route_is_registered_and_reconstructs_backend_owned_proposal(client, admin_headers, monkeypatch):
    import importlib

    api = importlib.import_module("app.services.presentation_master.integration.m30_causality_relationship_proposal_api")
    payload = _payload()
    payload["current_reviewed_nodes"].append(_reviewed_node_payload("causal_state", "node-state"))
    monkeypatch.setattr(api, "propose_m30_causality_relationships_live", _fake_live)
    response = client.post("/api/m30/causality/proposals", headers=admin_headers, json=payload)
    assert response.status_code == 200
    item = response.json()["relationships"][0]
    assert item["from_id"] == "node-root"
    assert item["to_id"] == "node-state"
    assert item["relationship_type"] == "causality"
    assert item["authority"] == "AI_PROPOSED"
    assert item["review_state"] == "UNCONFIRMED"
    assert item["confirmation_authority"] is None
    assert item["inferred"] is True


def test_route_requires_authentication(client):
    assert client.post("/api/m30/causality/proposals", json=_payload()).status_code == 401


def test_extra_top_level_and_trusted_relationship_fields_are_rejected(client, admin_headers):
    for field in ("proposal_revision", "relationship_id", "authority", "review_state", "provenance", "evidence", "presentation_topic", "renderer"):
        payload = _payload()
        payload[field] = "forbidden"
        assert client.post("/api/m30/causality/proposals", headers=admin_headers, json=payload).status_code == 422


def test_extra_node_and_source_fields_are_rejected(client, admin_headers):
    node_payload = _payload()
    node_payload["current_reviewed_nodes"][0]["relationship_id"] = "forbidden"
    assert client.post("/api/m30/causality/proposals", headers=admin_headers, json=node_payload).status_code == 422
    source_payload = _payload()
    source_payload["current_sources"][0]["authority"] = "forbidden"
    assert client.post("/api/m30/causality/proposals", headers=admin_headers, json=source_payload).status_code == 422


@pytest.mark.parametrize("field", ["current_sources", "requested_count"])
def test_required_request_fields_are_enforced(client, admin_headers, field):
    payload = _payload()
    del payload[field]
    assert client.post("/api/m30/causality/proposals", headers=admin_headers, json=payload).status_code == 422


@pytest.mark.parametrize("authority,review_state", [("AI_PROPOSED", "UNCONFIRMED"), ("USER_EXPLICIT", "REJECTED")])
def test_only_admissible_reviewed_nodes_are_accepted(client, admin_headers, monkeypatch, authority, review_state):
    import importlib

    api = importlib.import_module("app.services.presentation_master.integration.m30_causality_relationship_proposal_api")
    monkeypatch.setattr(api, "propose_m30_causality_relationships_live", _fake_live)
    payload = _payload()
    payload["current_reviewed_nodes"][0]["authority"] = authority
    payload["current_reviewed_nodes"][0]["review_state"] = review_state
    response = client.post("/api/m30/causality/proposals", headers=admin_headers, json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["error_type"] == "OFFLINE_CONTRACT_REJECTED"


def test_solution_direction_is_not_an_endpoint(client, admin_headers, monkeypatch):
    import importlib

    api = importlib.import_module("app.services.presentation_master.integration.m30_causality_relationship_proposal_api")
    monkeypatch.setattr(api, "propose_m30_causality_relationships_live", _fake_live)
    payload = _payload()
    payload["current_reviewed_nodes"][0] = _reviewed_node_payload("solution_direction", "node-root")
    response = client.post("/api/m30/causality/proposals", headers=admin_headers, json=payload)
    assert response.status_code == 422


def test_adapter_error_is_bounded_without_raw_content(client, admin_headers, monkeypatch):
    import importlib
    from app.services.presentation_master.integration.m30_causality_relationship_ai_live_adapter import M30CausalityRelationshipAILiveAdapterError

    api = importlib.import_module("app.services.presentation_master.integration.m30_causality_relationship_proposal_api")

    def fail(_request, _sources):
        raise M30CausalityRelationshipAILiveAdapterError("AI_TIMEOUT", 504)

    monkeypatch.setattr(api, "propose_m30_causality_relationships_live", fail)
    response = client.post("/api/m30/causality/proposals", headers=admin_headers, json=_payload())
    assert response.status_code == 504
    assert response.json()["detail"]["error_type"] == "AI_TIMEOUT"
    assert "現状の課題" not in response.text


def test_no_direct_openai_or_persistence_boundary_in_api_module():
    from pathlib import Path

    text = Path("backend/app/services/presentation_master/integration/m30_causality_relationship_proposal_api.py").read_text(encoding="utf-8")
    assert "OpenAI" not in text
    assert "get_db" not in text
    assert "m30_causality_relationship_review_decisions" not in text
    assert "m30_product_evidence_adapter" not in text
