import json

import pytest

def _payload(role="visible_issue", count=1):
    return {
        "semantic_role": role,
        "requested_count": count,
        "source_records": [{
            "source_id": "step1",
            "source_field": "project_brief",
            "value": "案件の現状と課題",
            "source_reference": "Step1.project_brief",
        }],
    }


def _fake_proposal(request):
    from app.services.presentation_master.integration.m30_canonical_ai_acquisition import build_m30_canonical_ai_proposals

    return build_m30_canonical_ai_proposals(
        request,
        json.dumps({"items": [{"semantic_role": request.semantic_role, "value": "提案候補"}] * request.requested_count}, ensure_ascii=False),
    )


def test_route_returns_frozen_candidate_shape_for_admin(client, admin_headers, monkeypatch):
    import importlib
    api = importlib.import_module("app.services.presentation_master.integration.m30_canonical_node_proposal_api")
    monkeypatch.setattr(api, "propose_m30_canonical_live", _fake_proposal)
    response = client.post("/api/m30/canonical/proposals", headers=admin_headers, json=_payload())
    assert response.status_code == 200
    candidate = response.json()["candidates"][0]
    assert candidate["authority"] == "AI_PROPOSED"
    assert candidate["review_state"] == "UNCONFIRMED"
    assert candidate["confirmation_authority"] is None
    assert candidate["inferred"] is True
    assert candidate["acquisition_revision"] == "v1"
    assert candidate["candidate_id"].startswith("m30-canonical-ai:")
    assert candidate["source_identities"][0]["source_reference"] == "Step1.project_brief"


def test_route_requires_authentication(client):
    assert client.post("/api/m30/canonical/proposals", json=_payload()).status_code == 401


def test_route_accepts_member(client, admin_headers, monkeypatch):
    from app.db import get_db
    from app.repository_parts.users import create_user

    with get_db() as db:
        create_user(db, "m30-member@example.com", "member-password", "member")
    login = client.post("/api/auth/login", json={"email": "m30-member@example.com", "password": "member-password"})
    assert login.status_code == 200
    monkeypatch.setattr(
        __import__("importlib").import_module("app.services.presentation_master.integration.m30_canonical_node_proposal_api"),
        "propose_m30_canonical_live",
        _fake_proposal,
    )
    response = client.post(
        "/api/m30/canonical/proposals",
        headers={"Authorization": f"Bearer {login.json()['token']}"},
        json=_payload(),
    )
    assert response.status_code == 200


@pytest.mark.parametrize("role", ["visible_issue", "root_cause", "causal_state", "business_implication", "solution_direction"])
def test_supported_roles_use_frozen_builder(client, admin_headers, monkeypatch, role):
    import importlib
    api = importlib.import_module("app.services.presentation_master.integration.m30_canonical_node_proposal_api")
    monkeypatch.setattr(api, "propose_m30_canonical_live", _fake_proposal)
    response = client.post("/api/m30/canonical/proposals", headers=admin_headers, json=_payload(role))
    assert response.status_code == 200
    assert response.json()["candidates"][0]["semantic_role"] == role


@pytest.mark.parametrize("field", ["acquisition_revision", "candidate_id", "authority", "review_state", "confirmation_authority", "inferred", "source_fingerprint", "source_identities", "original_candidate_id", "presentation_topic", "relationships", "evidence_candidates"])
def test_trusted_or_out_of_scope_fields_are_rejected(client, admin_headers, field):
    payload = _payload()
    payload[field] = "forbidden"
    assert client.post("/api/m30/canonical/proposals", headers=admin_headers, json=payload).status_code == 422


def test_extra_source_field_is_rejected(client, admin_headers):
    payload = _payload()
    payload["source_records"][0]["authority"] = "USER_EXPLICIT"
    assert client.post("/api/m30/canonical/proposals", headers=admin_headers, json=payload).status_code == 422


@pytest.mark.parametrize("role", ["unsupported", "presentation_topic"])
def test_unsupported_role_is_bounded(client, admin_headers, monkeypatch, role):
    import importlib
    api = importlib.import_module("app.services.presentation_master.integration.m30_canonical_node_proposal_api")
    monkeypatch.setattr(api, "propose_m30_canonical_live", _fake_proposal)
    response = client.post("/api/m30/canonical/proposals", headers=admin_headers, json=_payload(role))
    assert response.status_code == 422
    assert response.json()["detail"]["error_type"] == "INVALID_CANONICAL_INPUT"


def test_adapter_error_is_bounded_without_raw_content(client, admin_headers, monkeypatch):
    import importlib
    api = importlib.import_module("app.services.presentation_master.integration.m30_canonical_node_proposal_api")
    from app.services.presentation_master.integration.m30_canonical_ai_live_adapter import M30CanonicalAILiveAdapterError

    def fail(_request):
        raise M30CanonicalAILiveAdapterError("AI_TIMEOUT", 504)

    monkeypatch.setattr(api, "propose_m30_canonical_live", fail)
    response = client.post("/api/m30/canonical/proposals", headers=admin_headers, json=_payload())
    assert response.status_code == 504
    assert response.json()["detail"] == {"error_type": "AI_TIMEOUT", "message": "M30 canonical proposal could not be generated."}
