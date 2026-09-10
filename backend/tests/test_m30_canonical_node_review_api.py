import json
import importlib

import pytest


def _review_payload(*, action="CONFIRM", corrected_value=None):
    acquisition = importlib.import_module("app.services.presentation_master.integration.m30_canonical_ai_acquisition")
    request = acquisition.M30CanonicalAcquisitionRequest(
        semantic_role="visible_issue",
        requested_count=1,
        source_records=(acquisition.M30CanonicalSourceRecord("step1", "project_brief", "現状課題", "Step1.project_brief"),),
        acquisition_revision="v1",
    )
    candidate = acquisition.build_m30_canonical_ai_proposals(
        request,
        json.dumps({"items": [{"semantic_role": "visible_issue", "value": "AI候補"}],}, ensure_ascii=False),
    )[0]
    return {
        "original_candidate": {
            "candidate_id": candidate.candidate_id,
            "semantic_role": candidate.semantic_role,
            "value": candidate.value,
            "source_type": candidate.source_type,
            "source_field": candidate.source_field,
            "source_reference": candidate.source_reference,
            "source_references": list(candidate.source_references),
            "source_identities": [{"source_id": item.source_id, "source_field": item.source_field, "source_reference": item.source_reference} for item in candidate.source_identities],
            "source_fingerprint": candidate.source_fingerprint,
            "authority": candidate.authority.value,
            "review_state": candidate.review_state.value,
            "confirmation_authority": None,
            "inferred": True,
            "acquisition_revision": candidate.acquisition_revision,
            "original_candidate_id": None,
        },
        "current_sources": [{"source_id": "step1", "source_field": "project_brief", "value": "現状課題", "source_reference": "Step1.project_brief"}],
        "decision": {"original_candidate_id": candidate.candidate_id, "action": action, "corrected_value": corrected_value},
    }


def test_confirm_reconstructs_trusted_metadata(client, admin_headers):
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=_review_payload())
    assert response.status_code == 200
    result = response.json()["candidate"]
    assert result["authority"] == "USER_EXPLICIT"
    assert result["review_state"] == "CONFIRMED"
    assert result["confirmation_authority"] == "USER_EXPLICIT"
    assert result["inferred"] is True


def test_member_and_unauthenticated_policy(client, admin_headers):
    assert client.post("/api/m30/canonical/reviews", json=_review_payload()).status_code == 401


def test_member_is_accepted(client, admin_headers):
    from app.db import get_db
    from app.repository_parts.users import create_user

    with get_db() as db:
        create_user(db, "m30-review-member@example.com", "member-password", "member")
    login = client.post("/api/auth/login", json={"email": "m30-review-member@example.com", "password": "member-password"})
    assert login.status_code == 200
    response = client.post(
        "/api/m30/canonical/reviews",
        headers={"Authorization": f"Bearer {login.json()['token']}"},
        json=_review_payload(),
    )
    assert response.status_code == 200


@pytest.mark.parametrize(("action", "corrected", "state"), [
    ("CORRECT", "Human correction", "CORRECTED"),
    ("REJECT", None, "REJECTED"),
])
def test_review_actions_follow_frozen_contract(client, admin_headers, action, corrected, state):
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=_review_payload(action=action, corrected_value=corrected))
    assert response.status_code == 200
    result = response.json()["candidate"]
    assert result["review_state"] == state
    if action == "CORRECT":
        assert result["value"] == corrected
        assert result["authority"] == "USER_EXPLICIT"
        assert result["inferred"] is True
    else:
        assert result["authority"] == "AI_PROPOSED"


@pytest.mark.parametrize("action", ["CONFIRM", "CORRECT", "REJECT"])
def test_decision_id_mismatch_is_bounded(client, admin_headers, action):
    payload = _review_payload(action=action, corrected_value="修正" if action == "CORRECT" else None)
    payload["decision"]["original_candidate_id"] = "wrong-id"
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["error_type"] == "CANDIDATE_ID_MISMATCH"


def test_changed_source_fails_closed(client, admin_headers):
    payload = _review_payload()
    payload["current_sources"][0]["value"] = "変更された情報"
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["error_type"] == "STALE_SOURCE"


@pytest.mark.parametrize("field", ["authority", "review_state", "inferred", "source_fingerprint", "candidate_id"])
def test_extra_trusted_fields_are_rejected(client, admin_headers, field):
    payload = _review_payload()
    payload["original_candidate"][field] = "forbidden"
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("action", ["CONFIRM", "REJECT"])
def test_corrected_value_for_non_correct_action_is_rejected(client, admin_headers, action):
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=_review_payload(action=action, corrected_value="不正な修正"))
    assert response.status_code == 422


def test_correction_requires_non_empty_value(client, admin_headers):
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=_review_payload(action="CORRECT", corrected_value="   "))
    assert response.status_code == 422


def test_original_confirmed_candidate_is_rejected(client, admin_headers):
    payload = _review_payload()
    payload["original_candidate"]["review_state"] = "CONFIRMED"
    response = client.post("/api/m30/canonical/reviews", headers=admin_headers, json=payload)
    assert response.status_code == 422
    assert response.json()["detail"]["error_type"] == "INVALID_ORIGINAL_CANDIDATE"
