from __future__ import annotations

from copy import deepcopy

import pytest

from app.services.presentation_master.integration import (
    AdapterStatus,
    CandidateStateBridgeError,
    ProductionShadowCandidateContext,
    build_candidate_state_bridge,
    candidate_set_to_dict,
    prepare_pmv3,
)
from tests.test_offline_production_path_e2e_v2 import _m48_candidates, _request, _state


def _payload(confirmed: bool = True):
    candidates = _m48_candidates()
    state = _state(candidates) if confirmed else _state(candidates, unconfirmed_id="approver")
    payload = _request(state)
    payload.semantic_candidates = candidate_set_to_dict(candidates)
    return payload, candidates, state


def test_authoritative_candidate_bridge_preserves_ids_and_reaches_m48():
    payload, candidates, _ = _payload()

    context = build_candidate_state_bridge(payload, request_id="bridge-m48")

    assert isinstance(context, ProductionShadowCandidateContext)
    assert tuple(item.id for item in context.candidates.candidates) == tuple(item.id for item in candidates.candidates)
    assert tuple(item.id for item in context.binding.candidates.candidates) == tuple(item.id for item in candidates.candidates)
    prepared = prepare_pmv3(payload, semantic_candidates=context.binding.candidates)
    assert prepared.status in {AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS}
    assert prepared.selected_master_id == "M48"
    assert prepared.composition_readiness == "VALID"


def test_corrected_state_preserves_stable_id_and_user_authority():
    payload, candidates, state = _payload()
    corrected = next(item for item in state if item["id"] == "action")
    corrected["review_state"] = "CORRECTED"
    corrected["value"] = "ユーザー確認済みの実行計画"
    payload.semantic_confirmation_state = state
    context = build_candidate_state_bridge(payload, request_id="bridge-corrected")

    action = next(item for item in context.binding.candidates.candidates if item.id == "action")
    assert action.id == next(item for item in candidates.candidates if item.id == "action").id
    assert action.authority.value == "USER_EXPLICIT"
    assert action.value == "ユーザー確認済みの実行計画"
    assert action.original_candidate_id == "action"


def test_rejected_and_unconfirmed_states_fail_closed_for_future_shadow():
    for keyword in ("rejected", "unconfirmed"):
        candidates = _m48_candidates()
        state = _state(candidates, reject_id="approver" if keyword == "rejected" else None, unconfirmed_id="approver" if keyword == "unconfirmed" else None)
        payload = _request(state)
        payload.semantic_candidates = candidate_set_to_dict(candidates)
        context = build_candidate_state_bridge(payload, request_id=f"bridge-{keyword}")
        assert context is not None
        assert context.binding.candidates.unresolved_critical()


def test_missing_and_malformed_candidate_transport_is_primary_safe():
    payload, _, _ = _payload()
    payload.semantic_candidates = None
    assert build_candidate_state_bridge(payload, request_id="bridge-missing") is None
    assert prepare_pmv3(payload).status == AdapterStatus.NOT_READY

    malformed, _, _ = _payload()
    malformed.semantic_candidates = {"candidates": [{"id": "duplicate"}]}
    with pytest.raises(CandidateStateBridgeError):
        build_candidate_state_bridge(malformed, request_id="bridge-malformed")
    assert prepare_pmv3(malformed).status == AdapterStatus.NOT_READY


def test_duplicate_candidate_ids_fail_closed():
    payload, _, _ = _payload()
    raw = deepcopy(payload.semantic_candidates)
    raw["candidates"].append(deepcopy(raw["candidates"][0]))
    payload.semantic_candidates = raw
    with pytest.raises(CandidateStateBridgeError):
        build_candidate_state_bridge(payload, request_id="bridge-duplicate")
