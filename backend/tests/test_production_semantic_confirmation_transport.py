from __future__ import annotations

from dataclasses import replace

import pytest

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest
from app.services.presentation_master.integration import (
    AdapterStatus,
    ProductionSemanticCandidate,
    ProductionSemanticCandidateSet,
    SemanticAuthority,
    SemanticConfirmationTransportError,
    SemanticItemType,
    SemanticReviewState,
    apply_semantic_confirmation_state,
    build_adapter_input,
    prepare_pmv3,
)


def _candidate(candidate_id: str, semantic_type: SemanticItemType, value: str, *, authority=SemanticAuthority.AI_PROPOSED, review=SemanticReviewState.UNCONFIRMED):
    return ProductionSemanticCandidate(candidate_id, semantic_type, value, "analysis", "analysis.field", authority, 0.8, review, inferred=authority == SemanticAuthority.AI_PROPOSED)


def _base() -> ProductionSemanticCandidateSet:
    return ProductionSemanticCandidateSet((
        _candidate("condition", SemanticItemType.DECISION_CONDITION, "条件"),
        _candidate("action", SemanticItemType.EXECUTION_ACTION, "実行"),
    ))


def _request(**kwargs) -> PptxDownloadRequest:
    return PptxDownloadRequest(
        powerpoint_generation_data=PowerPointData(
            deck_title="Transport test", client_name="Customer",
            slides=[PowerPointSlide(slide_no=1, layout="title", title="Transport", bullets=[], speaker_notes="", visual_suggestion="")],
        ), **kwargs,
    )


def _state(candidate_id: str, semantic_type=SemanticItemType.DECISION_CONDITION.value, review_state=SemanticReviewState.CONFIRMED.value, value=None):
    item = {"id": candidate_id, "semantic_type": semantic_type, "review_state": review_state}
    if value is not None:
        item["value"] = value
    return item


def test_no_confirmation_preserves_unconfirmed_and_old_request_compatibility():
    base = _base()
    assert apply_semantic_confirmation_state(base, None) == base
    adapter_input = build_adapter_input(_request(), semantic_candidates=base)
    assert adapter_input.semantic_candidates == base


def test_confirmed_candidate_promotes_effective_authority_and_preserves_ai_origin():
    result = apply_semantic_confirmation_state(_base(), [_state("condition")])
    candidate = result.candidates[0]
    assert candidate.review_state == SemanticReviewState.CONFIRMED
    assert candidate.authority == SemanticAuthority.USER_EXPLICIT
    assert candidate.confirmation_authority == SemanticAuthority.USER_EXPLICIT
    assert candidate.source_type == "analysis"
    assert candidate.source_field == "analysis.field"
    assert candidate.id == "condition"
    assert result.admissible() == (candidate,)


def test_corrected_candidate_is_user_explicit_and_traceable():
    result = apply_semantic_confirmation_state(_base(), [_state("condition", review_state="CORRECTED", value="修正条件")])
    candidate = result.candidates[0]
    assert candidate.value == "修正条件"
    assert candidate.authority == SemanticAuthority.USER_EXPLICIT
    assert candidate.review_state == SemanticReviewState.CORRECTED
    assert candidate.original_candidate_id == "condition"
    assert candidate.confirmation_authority == SemanticAuthority.USER_EXPLICIT
    assert result.admissible() == (candidate,)


def test_rejected_candidate_is_not_admissible():
    result = apply_semantic_confirmation_state(_base(), [_state("condition", review_state="REJECTED")])
    assert result.candidates[0].review_state == SemanticReviewState.REJECTED
    assert result.admissible() == ()
    assert result.unresolved_critical() == ("action",)


def test_mixed_states_apply_only_to_matching_candidates():
    result = apply_semantic_confirmation_state(_base(), [
        _state("condition"),
        _state("action", semantic_type=SemanticItemType.EXECUTION_ACTION.value, review_state="CORRECTED", value="修正実行"),
    ])
    assert [item.review_state for item in result.candidates] == [SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED]
    assert [item.authority for item in result.candidates] == [SemanticAuthority.USER_EXPLICIT, SemanticAuthority.USER_EXPLICIT]


def test_confirmed_ai_candidates_clear_previous_semantic_supply_invalid_fallback():
    base = _base()
    state = [_state("condition"), _state("action", semantic_type=SemanticItemType.EXECUTION_ACTION.value)]
    prepared = prepare_pmv3(_request(semantic_confirmation_state=state), semantic_candidates=base)
    assert prepared.diagnostics.get("semantic_supply_invalid_reason") is None
    assert not (prepared.status == AdapterStatus.INVALID_INPUT and prepared.fallback_stage.value == "SEMANTIC_ADAPTER")


def test_unconfirmed_rejected_and_unresolved_ai_candidates_remain_inadmissible():
    base = _base()
    unconfirmed = apply_semantic_confirmation_state(base, [_state("condition", review_state="UNCONFIRMED")])
    rejected = apply_semantic_confirmation_state(base, [_state("condition", review_state="REJECTED")])
    assert unconfirmed.candidates[0].authority == SemanticAuthority.AI_PROPOSED
    assert rejected.candidates[0].authority == SemanticAuthority.AI_PROPOSED
    assert unconfirmed.admissible() == ()
    assert rejected.admissible() == ()
    assert "condition" in unconfirmed.unresolved_critical()
    assert rejected.unresolved_critical() == ("action",)


def test_mixed_confirmed_and_rejected_candidates_separate_review_from_supply():
    result = apply_semantic_confirmation_state(_base(), [
        _state("condition"),
        _state("action", semantic_type=SemanticItemType.EXECUTION_ACTION.value, review_state="REJECTED"),
    ])
    assert result.unresolved_critical() == ()
    assert len(result.admissible()) == 1


def test_unconfirmed_and_unresolved_candidates_remain_critical():
    result = ProductionSemanticCandidateSet(tuple(
        replace(item, review_state=SemanticReviewState.UNCONFIRMED if item.id == "condition" else SemanticReviewState.UNRESOLVED)
        for item in _base().candidates
    ))
    assert set(result.unresolved_critical()) == {"condition", "action"}


def test_all_rejected_candidates_remain_fail_closed_for_supply():
    rejected = ProductionSemanticCandidateSet(tuple(replace(item, review_state=SemanticReviewState.REJECTED) for item in _base().candidates))
    assert rejected.unresolved_critical() == ()
    assert rejected.admissible() == ()
    prepared = prepare_pmv3(_request(), semantic_candidates=rejected)
    assert prepared.status == AdapterStatus.INVALID_INPUT


def test_unresolved_transport_fails_closed_without_authority_promotion():
    with pytest.raises(SemanticConfirmationTransportError):
        apply_semantic_confirmation_state(_base(), [_state("condition", review_state="UNRESOLVED")])


@pytest.mark.parametrize("authority", [SemanticAuthority.SYSTEM_EXTRACTED, SemanticAuthority.EXTERNAL_VERIFIED])
def test_existing_admissible_authorities_remain_admissible(authority):
    candidate = _candidate("existing", SemanticItemType.DECISION_CONDITION, "条件", authority=authority, review=SemanticReviewState.CONFIRMED)
    result = apply_semantic_confirmation_state(ProductionSemanticCandidateSet((candidate,)), [_state("existing")])
    assert result.candidates[0].authority == authority
    assert result.admissible() == (result.candidates[0],)


@pytest.mark.parametrize("state", [
    [_state("missing")],
    [_state("condition"), _state("condition")],
    [_state("condition", semantic_type=SemanticItemType.APPROVER.value)],
    [_state("condition", review_state="CORRECTED", value="")],
])
def test_invalid_transport_fails_closed(state):
    with pytest.raises(SemanticConfirmationTransportError):
        apply_semantic_confirmation_state(_base(), state)


def test_invalid_transport_reaches_structured_adapter_fallback():
    payload = _request(semantic_confirmation_state=[_state("missing")])
    prepared = prepare_pmv3(payload, semantic_candidates=_base())
    assert prepared.status == AdapterStatus.INVALID_INPUT
    assert prepared.fallback_required is True


def test_transport_does_not_accept_frontend_authority_or_readiness_fields():
    result = apply_semantic_confirmation_state(_base(), [{
        **_state("condition"), "authority": "USER_EXPLICIT", "admissible_as_evidence": True, "ready": True,
    }])
    candidate = result.candidates[0]
    assert candidate.authority == SemanticAuthority.USER_EXPLICIT
    assert candidate.admissible_as_evidence is False
