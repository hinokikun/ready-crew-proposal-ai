from __future__ import annotations

import json

import pytest

from app.services.presentation_master.integration.m30_canonical_ai_acquisition import (
    M30CanonicalAcquisitionError,
    M30CanonicalAcquisitionRequest,
    M30CanonicalSourceRecord,
    M30CanonicalSourceIdentity,
    build_m30_canonical_ai_proposals,
    compute_m30_canonical_source_fingerprint,
    parse_m30_canonical_ai_response,
    validate_m30_canonical_candidate_current_sources,
)
from app.services.presentation_master.integration.production_semantic_contract import (
    SemanticAuthority,
    SemanticReviewState,
)


def _request(role: str = "root_cause", count: int = 2, revision: str = "v1"):
    return M30CanonicalAcquisitionRequest(
        role,
        count,
        (M30CanonicalSourceRecord("brief", "project_brief", "bounded business context", "step1:brief"),),
        revision,
    )


def _response(role: str, values: list[str]) -> str:
    return json.dumps({"items": [{"semantic_role": role, "value": value} for value in values]}, ensure_ascii=False)


def test_bounded_request_and_all_roles_are_supported():
    for role, count in (("visible_issue", 1), ("root_cause", 4), ("causal_state", 5), ("business_implication", 4), ("solution_direction", 1)):
        request = _request(role, count)
        values = [f"{role} business meaning {index}" for index in range(count)]
        assert len(build_m30_canonical_ai_proposals(request, _response(role, values))) == count


def test_request_does_not_accept_arbitrary_payload_or_forbidden_input_fields():
    with pytest.raises(TypeError):
        M30CanonicalAcquisitionRequest(**{"semantic_role": "root_cause", "requested_count": 1, "source_records": (), "powerpoint_data": {}})


def test_missing_count_and_bounds_fail_closed():
    with pytest.raises(M30CanonicalAcquisitionError) as error:
        _request("root_cause", 5)
    assert error.value.category == "INVALID_COUNT"
    with pytest.raises(M30CanonicalAcquisitionError):
        _request("root_cause", 0)


def test_ai_initial_state_is_never_admitted():
    candidate = build_m30_canonical_ai_proposals(_request(), _response("root_cause", ["one", "two"]))[0]
    assert candidate.authority == SemanticAuthority.AI_PROPOSED
    assert candidate.review_state == SemanticReviewState.UNCONFIRMED
    assert candidate.confirmation_authority is None
    assert candidate.inferred is True


def test_identity_is_deterministic_and_revision_scoped_but_not_wording_scoped():
    first = build_m30_canonical_ai_proposals(_request(), _response("root_cause", ["one", "two"]))
    second = build_m30_canonical_ai_proposals(_request(), _response("root_cause", ["changed", "words"]))
    other_revision = build_m30_canonical_ai_proposals(_request(revision="v2"), _response("root_cause", ["one", "two"]))
    assert [item.candidate_id for item in first] == [item.candidate_id for item in second]
    assert [item.candidate_id for item in first] != [item.candidate_id for item in other_revision]
    assert all("uuid" not in item.candidate_id.lower() for item in first)


@pytest.mark.parametrize("raw", ["not json", '{"items":[{"semantic_role":"root_cause","value":"x","extra":true}]}'])
def test_structured_output_is_strict_and_no_markdown_fallback(raw: str):
    with pytest.raises(M30CanonicalAcquisitionError) as error:
        parse_m30_canonical_ai_response(raw, _request("root_cause", 1))
    assert error.value.category == "INVALID_STRUCTURED_OUTPUT"


def test_unknown_role_wrong_count_empty_and_duplicate_values_fail():
    with pytest.raises(M30CanonicalAcquisitionError):
        parse_m30_canonical_ai_response(_response("unknown", ["x"]), _request("root_cause", 1))
    with pytest.raises(M30CanonicalAcquisitionError):
        parse_m30_canonical_ai_response(_response("root_cause", ["x"]), _request("root_cause", 2))
    with pytest.raises(M30CanonicalAcquisitionError):
        parse_m30_canonical_ai_response(_response("root_cause", [" ", "x"]), _request("root_cause", 2))
    with pytest.raises(M30CanonicalAcquisitionError) as error:
        parse_m30_canonical_ai_response(_response("root_cause", ["same", " SAME "]), _request("root_cause", 2))
    assert error.value.category == "DUPLICATE_VALUE"


def test_source_provenance_is_preserved_and_evidence_is_not_generated():
    request = M30CanonicalAcquisitionRequest(
        "business_implication",
        1,
        (
            M30CanonicalSourceRecord("brief", "project_brief", "business context", "step1:brief"),
            M30CanonicalSourceRecord("hearing", "hearing_result", "hearing context", "step1:hearing"),
        ),
    )
    candidate = build_m30_canonical_ai_proposals(request, _response("business_implication", ["distinct impact"]))[0]
    assert candidate.source_references == ("step1:brief", "step1:hearing")
    assert candidate.source_reference == "step1:brief|step1:hearing"
    assert candidate.inferred is True
    assert candidate.semantic_role != "evidence"


def test_source_identity_and_fingerprint_are_ordered_and_raw_value_is_not_stored():
    request = M30CanonicalAcquisitionRequest(
        "root_cause", 1,
        (M30CanonicalSourceRecord("brief", "project_brief", "business context", "step1:brief"),),
    )
    candidate = build_m30_canonical_ai_proposals(request, _response("root_cause", ["cause"]))[0]
    assert candidate.source_identities == (M30CanonicalSourceIdentity("brief", "project_brief", "step1:brief"),)
    assert not hasattr(candidate, "source_value")
    assert "business context" not in repr(candidate.source_identities)
    assert len(candidate.source_fingerprint) == 64
    assert candidate.source_fingerprint == compute_m30_canonical_source_fingerprint(request.source_records)


def test_fingerprint_normalizes_whitespace_nfkc_but_preserves_case_and_punctuation():
    first = (M30CanonicalSourceRecord("A", "field", "ref", "  ABC   ．  "),)
    equivalent = (M30CanonicalSourceRecord("A", "field", "ref", "ABC ."),)
    assert compute_m30_canonical_source_fingerprint(first) == compute_m30_canonical_source_fingerprint(equivalent)
    assert compute_m30_canonical_source_fingerprint((M30CanonicalSourceRecord("A", "field", "ref", "abc ."),)) != compute_m30_canonical_source_fingerprint(equivalent)
    assert compute_m30_canonical_source_fingerprint((M30CanonicalSourceRecord("A", "field", "ref", "ABC"),)) != compute_m30_canonical_source_fingerprint((M30CanonicalSourceRecord("A", "field", "ref", "ABC."),))


def test_candidate_id_is_stable_when_only_source_value_changes():
    first_request = _request()
    changed_request = M30CanonicalAcquisitionRequest(
        "root_cause", 2,
        (M30CanonicalSourceRecord("brief", "project_brief", "changed context", "step1:brief"),),
    )
    first = build_m30_canonical_ai_proposals(first_request, _response("root_cause", ["one", "two"]))
    changed = build_m30_canonical_ai_proposals(changed_request, _response("root_cause", ["one", "two"]))
    assert [item.candidate_id for item in first] == [item.candidate_id for item in changed]
    assert first[0].source_fingerprint != changed[0].source_fingerprint


def test_currentness_accepts_unchanged_single_and_multi_source():
    request = M30CanonicalAcquisitionRequest(
        "business_implication", 1,
        (M30CanonicalSourceRecord("brief", "project_brief", "one", "step1:brief"), M30CanonicalSourceRecord("hearing", "hearing_result", "two", "step1:hearing")),
    )
    candidate = build_m30_canonical_ai_proposals(request, _response("business_implication", ["impact"]))[0]
    assert validate_m30_canonical_candidate_current_sources(candidate, request.source_records) is True


@pytest.mark.parametrize("mutation", [
    lambda records: (M30CanonicalSourceRecord("brief", "project_brief", "changed", "step1:brief"),),
    lambda records: (M30CanonicalSourceRecord("brief", "project_brief", "business context", "step1:other"),),
    lambda records: (),
    lambda records: records + (M30CanonicalSourceRecord("extra", "field", "value", "ref"),),
    lambda records: tuple(reversed(records)),
])
def test_currentness_fails_closed_for_changed_missing_extra_or_reordered_sources(mutation):
    request = M30CanonicalAcquisitionRequest(
        "root_cause", 1,
        (M30CanonicalSourceRecord("brief", "project_brief", "business context", "step1:brief"), M30CanonicalSourceRecord("hearing", "hearing_result", "hearing context", "step1:hearing")),
    )
    candidate = build_m30_canonical_ai_proposals(request, _response("root_cause", ["cause"]))[0]
    assert validate_m30_canonical_candidate_current_sources(candidate, mutation(request.source_records)) is False


def test_currentness_rejects_duplicate_and_missing_currentness_data():
    request = _request()
    candidate = build_m30_canonical_ai_proposals(request, _response("root_cause", ["one", "two"]))[0]
    duplicate = (request.source_records[0], request.source_records[0])
    assert validate_m30_canonical_candidate_current_sources(candidate, duplicate) is False
    assert validate_m30_canonical_candidate_current_sources(object(), request.source_records) is False
    assert validate_m30_canonical_candidate_current_sources(candidate, None) is False


def test_causal_state_rejects_physical_slide_language_without_nlp_heuristics():
    with pytest.raises(M30CanonicalAcquisitionError) as error:
        parse_m30_canonical_ai_response(_response("causal_state", ["center state"]), _request("causal_state", 1))
    assert error.value.category == "INVALID_STRUCTURED_OUTPUT"
