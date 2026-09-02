from __future__ import annotations

import hashlib

import pytest

from app.config import settings
from app.services import presentation_engine_integration as engine
from app.services.presentation_master.integration import candidate_set_to_dict
from tests.test_offline_production_path_e2e_v2 import _m48_candidates, _request, _state


@pytest.fixture(autouse=True)
def _shadow_flag_false_after_test():
    previous = settings.presentation_master_v3_renderer_mvp_shadow_enabled
    yield
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", previous)


def _eligible_payload():
    candidates = _m48_candidates()
    payload = _request(_state(candidates))
    payload.semantic_candidates = candidate_set_to_dict(candidates)
    return payload


class _FakeController:
    submissions: list[object] = []

    @staticmethod
    def eligibility(**kwargs):
        from app.services.presentation_master.integration import ShadowEligibility

        return ShadowEligibility(kwargs["prepared_status"] in {"READY", "READY_WITH_VALID_BINDINGS"} and kwargs["selected_master"] == "M48" and kwargs["composition_status"] == "VALID")

    def __init__(self, *, enabled: bool):
        assert enabled is True

    def submit(self, job, *, eligibility):
        assert eligibility.eligible is True
        self.submissions.append(job)
        return True


def test_default_off_returns_primary_without_shadow_admission(monkeypatch):
    primary = engine.PresentationEngineResult(b"primary", "legacy", quality_report={"validated": True})
    monkeypatch.setattr(engine, "_build_primary_pptx_bytes_for_engine", lambda *args, **kwargs: primary)
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", False)
    monkeypatch.setattr(engine, "_PRODUCTION_SHADOW_CONTROLLER", None)

    result = engine.build_pptx_bytes_for_engine(_eligible_payload(), request_id="off")

    assert result is primary
    assert result.pptx_bytes == b"primary"
    assert engine._PRODUCTION_SHADOW_CONTROLLER is None


def test_eligible_hook_submits_once_and_returns_before_shadow_completion(monkeypatch):
    primary = engine.PresentationEngineResult(b"primary", "legacy", quality_report={"validated": True})
    fake = _FakeController(enabled=True)
    fake.submissions.clear()
    monkeypatch.setattr(engine, "_build_primary_pptx_bytes_for_engine", lambda *args, **kwargs: primary)
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", True)
    monkeypatch.setattr(engine, "_PRODUCTION_SHADOW_CONTROLLER", fake)
    fake.submissions.clear()
    payload = _eligible_payload()

    result = engine.build_pptx_bytes_for_engine(payload, request_id="eligible")

    assert result is primary
    assert result.pptx_bytes == b"primary"
    assert len(fake.submissions) == 1
    assert fake.submissions[0].workload.binding.candidates.candidates


def test_hook_entry_emits_one_bounded_downstream_correlation_id(monkeypatch):
    primary = engine.PresentationEngineResult(b"primary", "legacy", quality_report={"validated": True})
    fake = _FakeController(enabled=True)
    fake.submissions.clear()
    events: list[tuple[str, dict[str, object]]] = []
    monkeypatch.setattr(engine, "_build_primary_pptx_bytes_for_engine", lambda *args, **kwargs: primary)
    monkeypatch.setattr(engine, "_log_shadow_metadata", lambda event, **fields: events.append((event, fields)))
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", True)
    monkeypatch.setattr(engine, "_PRODUCTION_SHADOW_CONTROLLER", fake)

    engine.build_pptx_bytes_for_engine(_eligible_payload(), request_id="correlated")

    hook_events = [
        (event, fields)
        for event, fields in events
        if event.startswith("presentation_shadow_hook_entered")
    ]
    correlation_id = hashlib.sha256(b"correlated").hexdigest()[:16]
    assert hook_events == [(f"presentation_shadow_hook_entered correlation_id={correlation_id}", {"correlation_id": correlation_id})]


def test_ineligible_and_logger_failure_are_primary_safe(monkeypatch):
    primary = engine.PresentationEngineResult(b"primary", "legacy", quality_report={"validated": True})
    fake = _FakeController(enabled=True)
    fake.submissions.clear()
    monkeypatch.setattr(engine, "_build_primary_pptx_bytes_for_engine", lambda *args, **kwargs: primary)
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", True)
    monkeypatch.setattr(engine, "_PRODUCTION_SHADOW_CONTROLLER", fake)

    payload = _eligible_payload()
    payload.summary = True
    assert engine.build_pptx_bytes_for_engine(payload, request_id="summary") is primary
    assert fake.submissions == []

    payload.summary = False
    monkeypatch.setattr(engine, "_log_shadow_metadata", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("logger")))
    assert engine.build_pptx_bytes_for_engine(payload, request_id="logger-failure") is primary
    assert len(fake.submissions) == 1
