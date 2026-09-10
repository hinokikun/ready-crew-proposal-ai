from __future__ import annotations

from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.services.presentation_master.integration.m30_presentation_content_proposal_api import (
    EvidenceCandidateTransportItem,
    M30PresentationContentProposalRequest,
    M30PresentationContentRequestError,
    build_m30_presentation_content_proposal_response,
)
from app.services.presentation_master.integration.presentation_content_ai_proposals import (
    ParsedPresentationContentAIProposal,
    build_presentation_content_candidate,
)
from app.services.presentation_master.integration.presentation_content_candidates import PresentationContentField
from app.services.presentation_master.integration.production_semantic_contract import (
    SemanticAuthority,
    SemanticReviewState,
)


def _item(item_id: str, role: str, value: str):
    return {
        "id": item_id,
        "value": value,
        "source_type": "user_text",
        "source_field": "hearing_result",
        "source_reference": f"hearing_result:{item_id}",
        "authority": "USER_EXPLICIT",
        "review_state": "CONFIRMED",
        "role": role,
        "confirmation_authority": "USER_EXPLICIT",
    }


def _payload() -> M30PresentationContentProposalRequest:
    objects = [_item("visible", "visible_issue", "共有方法がばらばら")]
    objects += [_item(f"root-{index}", "root_cause", f"原因 {index}") for index in range(4)]
    objects += [_item(f"state-{index}", "causal_state", f"状態 {index}") for index in range(5)]
    implications = [replace_model(_item(f"impact-{index}", "business_implication", f"影響 {index}")) for index in range(4)]
    solution = replace_model(_item("solution", "solution_direction", "運用を標準化する"))
    relationships = [
        {"id": f"edge-{index}", "from_item": f"root-{index}", "to_item": "visible", "relationship_type": "causality", "review_state": "CONFIRMED", "authority": "USER_EXPLICIT", "confirmation_authority": "USER_EXPLICIT", "provenance_state": "supplied", "source_reference": f"hearing_result:edge-{index}"}
        for index in range(4)
    ]
    evidence = EvidenceCandidateTransportItem(
        id="evidence-1", value="ヒアリングで確認済み", source_type="user_text", source_field="hearing_result",
        source_reference="hearing_result:evidence", authority="USER_EXPLICIT", confidence=1.0,
        review_state="CONFIRMED", inferred=False, admissible_as_evidence=True, confirmation_authority="USER_EXPLICIT",
    )
    return M30PresentationContentProposalRequest(
        problem_objects=objects, business_implications=implications, solution_direction=solution,
        business_relationships=relationships, evidence_candidates=[evidence],
    )


def replace_model(item: dict):
    item = dict(item)
    item.pop("role", None)
    return item


def _proposal(request):
    return build_presentation_content_candidate(
        request,
        ParsedPresentationContentAIProposal(tuple(PresentationContentField(role, f"wording:{role}") for role in request.requested_field_roles)),
    )


def test_valid_request_reuses_frozen_orchestration_and_returns_nine_unconfirmed_candidates():
    response = build_m30_presentation_content_proposal_response(_payload(), proposal_callable=_proposal)
    assert len(response.presentation_candidates) == 9
    assert response.content_acquisition_complete_for_human_review is True
    assert all(candidate.authority == SemanticAuthority.AI_PROPOSED.value for candidate in response.presentation_candidates)
    assert all(candidate.review_state == SemanticReviewState.UNCONFIRMED.value for candidate in response.presentation_candidates)
    assert all(candidate.confirmation_authority is None for candidate in response.presentation_candidates)
    assert {candidate.semantic_role for candidate in response.presentation_candidates} == {"visible_issue", "root_cause", "business_implication"}


def test_partial_failure_returns_only_successful_candidates_without_fallback():
    calls = 0

    def one_failure(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise ValueError("sensitive canonical wording")
        return _proposal(request)

    response = build_m30_presentation_content_proposal_response(_payload(), proposal_callable=one_failure)
    assert len(response.presentation_candidates) == 8
    assert response.content_acquisition_complete_for_human_review is False
    assert len(response.issues) == 1
    assert response.issues[0].safe_error_category == "proposal_failure"
    assert "sensitive" not in response.issues[0].safe_error_category


def test_all_failure_returns_empty_without_fallback_wording():
    response = build_m30_presentation_content_proposal_response(_payload(), proposal_callable=lambda request: (_ for _ in ()).throw(ValueError("raw content")))
    assert response.presentation_candidates == ()
    assert response.content_acquisition_complete_for_human_review is False
    assert len(response.issues) == 9


def test_invalid_canonical_input_fails_before_ai():
    calls = 0

    def should_not_run(request):
        nonlocal calls
        calls += 1
        return _proposal(request)

    invalid = _payload().copy(update={"problem_objects": _payload().problem_objects[:-1]})
    with pytest.raises(M30PresentationContentRequestError, match="M30_SEMANTIC_INCOMPLETE"):
        build_m30_presentation_content_proposal_response(invalid, proposal_callable=should_not_run)
    assert calls == 0


def test_request_rejects_endpoint_unrelated_fields():
    with pytest.raises(ValueError):
        M30PresentationContentProposalRequest.parse_obj({**_payload().dict(), "presentation_topic": "not accepted"})


def test_route_is_dedicated_and_requires_existing_product_auth(client: TestClient):
    schema = client.get("/openapi.json").json()
    assert "/api/presentation-content/proposals" in schema["paths"]
    assert "/api/analyze" in schema["paths"]
    response = client.post("/api/presentation-content/proposals", json={})
    assert response.status_code == 401
