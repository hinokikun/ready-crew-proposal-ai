from __future__ import annotations

import json
from dataclasses import replace

import pytest

from app.services.presentation_master.integration.m30_canonical_ai_acquisition import (
    M30CanonicalAcquisitionRequest,
    M30CanonicalSourceRecord,
)
from app.services.presentation_master.integration.m30_canonical_ai_live_adapter import (
    M30CanonicalAILiveAdapterError,
    build_m30_canonical_ai_input,
    propose_m30_canonical_live,
)
import app.services.presentation_master.integration.m30_canonical_ai_live_adapter as live_adapter
from app.config import settings


def _request(role: str = "root_cause", count: int = 2):
    return M30CanonicalAcquisitionRequest(
        role,
        count,
        (M30CanonicalSourceRecord("brief", "project_brief", "bounded context", "step1:brief"),),
    )


def _response(role: str = "root_cause"):
    return json.dumps({"items": [{"semantic_role": role, "value": "first cause"}, {"semantic_role": role, "value": "second cause"}]})


def test_input_serializes_only_bounded_canonical_context():
    payload = json.loads(build_m30_canonical_ai_input(_request()))
    assert set(payload) == {"semantic_role", "requested_count", "acquisition_revision", "source_context"}
    assert payload["source_context"][0]["source_reference"] == "step1:brief"
    for forbidden in ("powerpoint_generation_data", "presentation_topic", "Golden", "renderer", "native", "credentials", "token"):
        assert forbidden not in build_m30_canonical_ai_input(_request())


def test_one_injected_call_reuses_frozen_builder_and_metadata():
    calls: list[str] = []
    result = propose_m30_canonical_live(_request(), transport=lambda value: calls.append(value) or _response())
    assert len(calls) == 1
    assert len(result) == 2
    assert {item.authority.value for item in result} == {"AI_PROPOSED"}
    assert {item.review_state.value for item in result} == {"UNCONFIRMED"}
    assert all(item.confirmation_authority is None and item.inferred for item in result)
    assert all(item.source_reference == "step1:brief" for item in result)


def test_each_supported_role_preserves_requested_count():
    for role, count in (("visible_issue", 1), ("root_cause", 2), ("causal_state", 2), ("business_implication", 2), ("solution_direction", 1)):
        values = [f"{role} {index}" for index in range(count)]
        request = M30CanonicalAcquisitionRequest(role, count, _request().source_records)
        raw = json.dumps({"items": [{"semantic_role": role, "value": value} for value in values]})
        assert len(propose_m30_canonical_live(request, transport=lambda _: raw)) == count


def test_transport_exception_and_timeout_are_bounded_without_retry():
    calls = 0

    def failed(_value):
        nonlocal calls
        calls += 1
        raise RuntimeError("sensitive source text")

    with pytest.raises(M30CanonicalAILiveAdapterError) as error:
        propose_m30_canonical_live(_request(), transport=failed)
    assert error.value.category == "AI_REQUEST_FAILED"
    assert "sensitive" not in str(error.value)
    assert calls == 1

    with pytest.raises(M30CanonicalAILiveAdapterError) as timeout_error:
        propose_m30_canonical_live(_request(), transport=lambda _: (_ for _ in ()).throw(TimeoutError()))
    assert timeout_error.value.category == "AI_TIMEOUT"


@pytest.mark.parametrize("raw,category", [("not-json", "OFFLINE_CONTRACT_REJECTED"), ('{"items": [{"semantic_role": "root_cause", "value": "same"}, {"semantic_role": "root_cause", "value": " SAME "}]}', "OFFLINE_CONTRACT_REJECTED")])
def test_invalid_output_delegates_to_frozen_contract(raw: str, category: str):
    with pytest.raises(M30CanonicalAILiveAdapterError) as error:
        propose_m30_canonical_live(_request(), transport=lambda _: raw)
    assert error.value.category == category
    assert raw not in str(error.value)


def test_missing_configuration_is_bounded(monkeypatch):
    monkeypatch.setattr(live_adapter, "settings", replace(settings, openai_api_key=""))
    with pytest.raises(M30CanonicalAILiveAdapterError) as error:
        propose_m30_canonical_live(_request())
    assert error.value.category == "CONFIGURATION_ERROR"
