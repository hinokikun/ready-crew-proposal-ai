import json
from dataclasses import replace

import pytest


ORIGINAL_ID = "m30-causality-ai:original"


def _node(role, candidate_id):
    from app.services.presentation_master.integration.m30_canonical_ai_acquisition import (
        M30CanonicalAcquisitionRequest,
        M30CanonicalSourceRecord,
        build_m30_canonical_ai_proposals,
    )
    from app.services.presentation_master.integration.production_semantic_contract import SemanticAuthority, SemanticReviewState

    source = M30CanonicalSourceRecord("step1", "project_brief", "現状の課題", "Step1.project_brief")
    candidate = build_m30_canonical_ai_proposals(
        M30CanonicalAcquisitionRequest(role, 1, (source,)),
        json.dumps({"items": [{"semantic_role": role, "value": "確認済みノード"}]}, ensure_ascii=False),
    )[0]
    candidate = replace(candidate, candidate_id=candidate_id, authority=SemanticAuthority.USER_EXPLICIT, review_state=SemanticReviewState.CONFIRMED, confirmation_authority=SemanticAuthority.USER_EXPLICIT)
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


def _original(from_id="node-root", to_id="node-state", **overrides):
    value = {
        "relationship_id": ORIGINAL_ID,
        "from_id": from_id,
        "to_id": to_id,
        "relationship_type": "causality",
        "authority": "AI_PROPOSED",
        "review_state": "UNCONFIRMED",
        "confirmation_authority": None,
        "inferred": True,
        "provenance": "AI_INFERRED_FROM_REVIEWED_CANONICAL_NODES",
    }
    value.update(overrides)
    return value


def _payload(action="CONFIRM", **decision_overrides):
    decision = {"original_relationship_id": ORIGINAL_ID, "action": action, "corrected_from_id": None, "corrected_to_id": None}
    decision.update(decision_overrides)
    return {
        "original_relationship": _original(),
        "current_reviewed_nodes": [_node("root_cause", "node-root"), _node("causal_state", "node-state")],
        "current_reviewed_relationships": [],
        "current_sources": [{"source_id": "step1", "source_field": "project_brief", "value": "現状の課題", "source_reference": "Step1.project_brief"}],
        "decision": decision,
    }


def test_confirm_uses_frozen_contract_and_preserves_identity(client, admin_headers):
    response = client.post("/api/m30/causality/reviews", headers=admin_headers, json=_payload())
    assert response.status_code == 200
    result = response.json()["relationship"]
    assert result["relationship_id"] == ORIGINAL_ID
    assert result["original_relationship_id"] == ORIGINAL_ID
    assert result["from_id"] == "node-root"
    assert result["to_id"] == "node-state"
    assert result["authority"] == "USER_EXPLICIT"
    assert result["review_state"] == "CONFIRMED"
    assert result["confirmation_authority"] == "USER_EXPLICIT"
    assert result["inferred"] is True


def test_correct_generates_lineaged_deterministic_review(client, admin_headers):
    payload = _payload("CORRECT", corrected_from_id="node-root", corrected_to_id="node-state")
    response = client.post("/api/m30/causality/reviews", headers=admin_headers, json=payload)
    assert response.status_code == 200
    result = response.json()["relationship"]
    assert result["relationship_id"].startswith("m30-causality-reviewed:")
    assert result["relationship_id"] != ORIGINAL_ID
    assert result["original_relationship_id"] == ORIGINAL_ID
    assert result["review_state"] == "CORRECTED"
    assert result["authority"] == "USER_EXPLICIT"


def test_reject_preserves_original_identity_and_is_not_admitted(client, admin_headers):
    response = client.post("/api/m30/causality/reviews", headers=admin_headers, json=_payload("REJECT"))
    assert response.status_code == 200
    result = response.json()["relationship"]
    assert result["relationship_id"] == ORIGINAL_ID
    assert result["review_state"] == "REJECTED"
    assert result["authority"] == "AI_PROPOSED"
    assert result["confirmation_authority"] is None


def test_route_requires_authentication(client):
    assert client.post("/api/m30/causality/reviews", json=_payload()).status_code == 401


@pytest.mark.parametrize("field", ["review_revision", "proposal_revision", "relationship_id", "authority", "review_state", "provenance"])
def test_trusted_fields_are_rejected(client, admin_headers, field):
    payload = _payload()
    payload[field] = "forbidden"
    assert client.post("/api/m30/causality/reviews", headers=admin_headers, json=payload).status_code == 422


def test_nested_extra_fields_are_rejected(client, admin_headers):
    for section in ("original_relationship", "current_reviewed_nodes", "current_sources", "decision"):
        payload = _payload()
        target = payload[section][0] if isinstance(payload[section], list) else payload[section]
        target["unexpected"] = "forbidden"
        assert client.post("/api/m30/causality/reviews", headers=admin_headers, json=payload).status_code == 422


@pytest.mark.parametrize("field", ["current_sources", "current_reviewed_nodes", "decision"])
def test_required_sections_are_enforced(client, admin_headers, field):
    payload = _payload()
    del payload[field]
    assert client.post("/api/m30/causality/reviews", headers=admin_headers, json=payload).status_code == 422


@pytest.mark.parametrize("overrides", [{"authority": "USER_EXPLICIT"}, {"review_state": "CONFIRMED"}, {"inferred": False}, {"relationship_type": "not-causality"}])
def test_original_ai_state_is_fail_closed(client, admin_headers, overrides):
    payload = _payload()
    payload["original_relationship"].update(overrides)
    response = client.post("/api/m30/causality/reviews", headers=admin_headers, json=payload)
    assert response.status_code == 422
    assert "現状の課題" not in response.text


def test_changed_source_fails_closed(client, admin_headers):
    payload = _payload()
    payload["current_sources"][0]["value"] = "変更された課題"
    response = client.post("/api/m30/causality/reviews", headers=admin_headers, json=payload)
    assert response.status_code == 422
    assert "変更された課題" not in response.text


def test_correct_and_reject_forbid_corrected_endpoints(client, admin_headers):
    for action in ("CONFIRM", "REJECT"):
        response = client.post("/api/m30/causality/reviews", headers=admin_headers, json=_payload(action, corrected_from_id="node-root", corrected_to_id="node-state"))
        assert response.status_code == 422


def test_no_ai_or_persistence_boundary_in_api_module():
    from pathlib import Path

    text = Path("backend/app/services/presentation_master/integration/m30_causality_relationship_review_api.py").read_text(encoding="utf-8")
    assert "OpenAI" not in text
    assert "m30_causality_relationship_ai_live_adapter" not in text
    assert "m30_causality_relationship_proposal_api" not in text
    assert "get_db" not in text
