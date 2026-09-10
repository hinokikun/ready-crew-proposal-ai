from __future__ import annotations

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
    M30CanonicalReviewDecisionError,
    reconstruct_m30_canonical_candidate,
)
from app.services.presentation_master.integration.production_semantic_contract import (
    SemanticAuthority,
    SemanticReviewState,
)


def _sources():
    return (
        M30CanonicalSourceRecord("brief", "project_brief", "bounded context", "step1:brief"),
        M30CanonicalSourceRecord("hearing", "hearing_result", "bounded hearing", "step1:hearing"),
    )


def _candidate():
    request = M30CanonicalAcquisitionRequest("root_cause", 1, _sources())
    return build_m30_canonical_ai_proposals(request, '{"items":[{"semantic_role":"root_cause","value":"cause"}]}')[0]


def _decision(candidate, action, corrected_value=None):
    return M30CanonicalReviewDecision(candidate.candidate_id, action, corrected_value)


def test_confirm_reconstructs_trusted_metadata_and_preserves_provenance():
    original = _candidate()
    result = reconstruct_m30_canonical_candidate(original, _decision(original, M30CanonicalReviewAction.CONFIRM), _sources())
    assert result.candidate_id == original.candidate_id
    assert result.semantic_role == original.semantic_role
    assert result.value == original.value
    assert result.source_identities == original.source_identities
    assert result.source_fingerprint == original.source_fingerprint
    assert result.source_reference == original.source_reference
    assert result.source_references == original.source_references
    assert result.acquisition_revision == original.acquisition_revision
    assert result.inferred is True
    assert result.authority == SemanticAuthority.USER_EXPLICIT
    assert result.review_state == SemanticReviewState.CONFIRMED
    assert result.confirmation_authority == SemanticAuthority.USER_EXPLICIT
    assert original.review_state == SemanticReviewState.UNCONFIRMED


def test_correct_changes_only_value_and_review_metadata():
    original = _candidate()
    result = reconstruct_m30_canonical_candidate(original, _decision(original, M30CanonicalReviewAction.CORRECT, " corrected meaning "), _sources())
    assert result.value == "corrected meaning"
    assert result.semantic_role == original.semantic_role
    assert result.candidate_id == original.candidate_id
    assert result.source_identities == original.source_identities
    assert result.source_fingerprint == original.source_fingerprint
    assert result.inferred is True
    assert result.authority == SemanticAuthority.USER_EXPLICIT
    assert result.review_state == SemanticReviewState.CORRECTED
    assert result.confirmation_authority == SemanticAuthority.USER_EXPLICIT
    assert original.value == "cause"


def test_reject_is_auditable_and_inadmissible_without_replacement():
    original = _candidate()
    result = reconstruct_m30_canonical_candidate(original, _decision(original, M30CanonicalReviewAction.REJECT), _sources())
    assert result.review_state == SemanticReviewState.REJECTED
    assert result.authority == SemanticAuthority.AI_PROPOSED
    assert result.confirmation_authority is None
    assert result.candidate_id == original.candidate_id
    assert result.value == original.value
    assert result.source_fingerprint == original.source_fingerprint
    assert result.inferred is True
    assert result.review_state not in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}


@pytest.mark.parametrize("state", [SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED, SemanticReviewState.REJECTED])
def test_already_reviewed_candidate_is_rejected(state):
    original = replace(_candidate(), review_state=state, authority=SemanticAuthority.USER_EXPLICIT if state != SemanticReviewState.REJECTED else SemanticAuthority.AI_PROPOSED)
    with pytest.raises(M30CanonicalReviewDecisionError) as error:
        reconstruct_m30_canonical_candidate(original, _decision(original, M30CanonicalReviewAction.CONFIRM), _sources())
    assert error.value.category == "INVALID_ORIGINAL_CANDIDATE"


def test_candidate_id_mismatch_fails_closed():
    original = _candidate()
    with pytest.raises(M30CanonicalReviewDecisionError) as error:
        reconstruct_m30_canonical_candidate(original, M30CanonicalReviewDecision("other", M30CanonicalReviewAction.CONFIRM), _sources())
    assert error.value.category == "CANDIDATE_ID_MISMATCH"


@pytest.mark.parametrize("value", [None, "", "   "])
def test_correct_requires_non_empty_value(value):
    original = _candidate()
    with pytest.raises(M30CanonicalReviewDecisionError) as error:
        reconstruct_m30_canonical_candidate(original, _decision(original, M30CanonicalReviewAction.CORRECT, value), _sources())
    assert error.value.category == "INVALID_CORRECTION"


def test_confirm_and_reject_do_not_accept_correction_value():
    original = _candidate()
    for action in (M30CanonicalReviewAction.CONFIRM, M30CanonicalReviewAction.REJECT):
        with pytest.raises(M30CanonicalReviewDecisionError) as error:
            reconstruct_m30_canonical_candidate(original, _decision(original, action, "not allowed"), _sources())
        assert error.value.category == "INVALID_DECISION"


@pytest.mark.parametrize("source_factory", [
    lambda: (M30CanonicalSourceRecord("brief", "project_brief", "changed", "step1:brief"), M30CanonicalSourceRecord("hearing", "hearing_result", "bounded hearing", "step1:hearing")),
    lambda: (M30CanonicalSourceRecord("brief", "project_brief", "bounded context", "step1:changed"), M30CanonicalSourceRecord("hearing", "hearing_result", "bounded hearing", "step1:hearing")),
    lambda: (_sources()[0],),
    lambda: _sources() + (M30CanonicalSourceRecord("extra", "field", "value", "ref"),),
    lambda: tuple(reversed(_sources())),
])
def test_currentness_is_required_before_any_decision(source_factory):
    original = _candidate()
    with pytest.raises(M30CanonicalReviewDecisionError) as error:
        reconstruct_m30_canonical_candidate(original, _decision(original, M30CanonicalReviewAction.REJECT), source_factory())
    assert error.value.category == "STALE_SOURCE"


def test_duplicate_current_source_fails_closed():
    original = _candidate()
    with pytest.raises(M30CanonicalReviewDecisionError) as error:
        reconstruct_m30_canonical_candidate(original, _decision(original, M30CanonicalReviewAction.CONFIRM), _sources() + (_sources()[0],))
    assert error.value.category == "STALE_SOURCE"


def test_decision_model_has_no_trusted_metadata_fields():
    fields = set(M30CanonicalReviewDecision.__dataclass_fields__)
    assert fields == {"original_candidate_id", "action", "corrected_value"}


def test_missing_candidate_currentness_data_fails_closed():
    original = _candidate()
    malformed = replace(original, source_fingerprint="")
    with pytest.raises(M30CanonicalReviewDecisionError) as error:
        reconstruct_m30_canonical_candidate(malformed, _decision(malformed, M30CanonicalReviewAction.CONFIRM), _sources())
    assert error.value.category == "STALE_SOURCE"
