import time
import hashlib
from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

import app.services.presentation_engine_integration as engine_integration
import app.services.presentation_master.integration as shadow_integration
from app.services.presentation_engine_integration import PresentationEngineResult
from app.services.presentation_master.integration.shadow_integration import ShadowController
from app.services.presentation_master.integration import candidate_set_to_dict
from app.services.presentation_master.integration.shadow_candidate_binding import bind_shadow_candidates
from app.services.presentation_master.integration.shadow_process_isolation import ProcessShadowJob, ShadowProcessWorkload
from tests.test_offline_production_path_e2e_v2 import _m48_candidates, _request, _state


def _eligibility(**overrides):
    values = dict(summary=False, confirmation_state_present=True, prepared_status="READY", selected_master="M48", composition_status="VALID")
    values.update(overrides)
    return ShadowController.eligibility(**values)


def _wait(controller, timeout=8):
    deadline = time.time() + timeout
    result = ()
    while not result and time.time() < deadline:
        result = controller.drain_results()
        time.sleep(0.01)
    return result


def _stuck_worker():
    time.sleep(30)
    return {}


def _success_worker():
    return {"package_valid": True}


def _crash_worker():
    raise RuntimeError("bounded child failure")


def _process_job(request_id, binding, worker=None, payload=None):
    payload = payload or _request([])
    return ProcessShadowJob(request_id, "legacy", "READY", "M48", "VALID", ShadowProcessWorkload(payload, binding, worker))


def test_default_off_and_sampling_are_safe():
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="off", candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=False, sample_rate=1.0)
    assert controller.submit(_process_job("off", binding), eligibility=_eligibility()) is False
    controller.shutdown()
    assert ShadowController.is_sampled("same-id", .37) == ShadowController.is_sampled("same-id", .37)


def test_eligibility_filters_invalid_cases():
    for overrides in ({"summary": True}, {"confirmation_state_present": False}, {"prepared_status": "REVIEW_REQUIRED"}, {"prepared_status": "NOT_READY"}, {"composition_status": "INVALID"}):
        assert _eligibility(**overrides).eligible is False


def test_binding_preserves_ids_and_real_m48_runs_through_final_controller():
    candidates = _m48_candidates()
    payload = _request(_state(candidates))
    binding = bind_shadow_candidates(payload, request_id="real-m48", candidates=candidates, confirmation_state=payload.semantic_confirmation_state)
    assert binding is not None
    prepared = __import__("app.services.presentation_master.integration.engine_adapter", fromlist=["prepare_pmv3"]).prepare_pmv3(payload, semantic_candidates=binding.candidates)
    eligibility = _eligibility(prepared_status=prepared.status.value, selected_master=prepared.selected_master_id, composition_status=prepared.composition_readiness)
    controller = ShadowController(enabled=True, sample_rate=1.0, timeout_seconds=8, max_pending=0)
    assert controller.submit(ProcessShadowJob("real-m48", "legacy", prepared.status.value, "M48", "VALID", ShadowProcessWorkload(payload, binding)), eligibility=eligibility)
    result = _wait(controller)[-1]
    controller.shutdown()
    assert result["package_valid"] is True and result["slide_count"] > 0
    assert result["rasterization_ratio"] == 0 and result["clipping"] == result["overflow"] == result["off_canvas"] == result["collision"] == 0


def test_stuck_child_is_killed_capacity_reclaimed_and_next_task_runs():
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="stuck", candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=True, sample_rate=1.0, timeout_seconds=3, max_pending=0)
    assert controller.submit(_process_job("stuck", binding, _stuck_worker))
    result = _wait(controller, 5)[-1]
    assert result["failure_category"] == "SHADOW_TIMEOUT"
    assert controller.submit(_process_job("after-timeout", binding, _success_worker))
    assert _wait(controller, 5)[-1]["package_valid"] is True
    controller.shutdown()


def test_child_crash_isolated_and_next_task_runs():
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="crash", candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=True, sample_rate=1.0, timeout_seconds=3, max_pending=0)
    assert controller.submit(_process_job("crash", binding, _crash_worker))
    assert _wait(controller, 5)[-1]["failure_category"] == "RENDER_FAILED"
    assert controller.submit(_process_job("after-crash", binding, _success_worker))
    assert _wait(controller, 5)[-1]["package_valid"] is True
    controller.shutdown()


def test_capacity_and_shutdown_are_bounded():
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="capacity", candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=True, sample_rate=1.0, timeout_seconds=2, max_pending=0)
    assert controller.submit(_process_job("active", binding, _stuck_worker))
    assert controller.submit(_process_job("rejected", binding, _success_worker), eligibility=_eligibility()) is False
    controller.shutdown()
    assert controller.submit(_process_job("after-shutdown", binding, _success_worker), eligibility=_eligibility()) is False


def test_final_controller_breaker_blocks_after_three_failures():
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="breaker", candidates=_m48_candidates(), confirmation_state=[])
    clock = [0.0]
    controller = ShadowController(enabled=True, sample_rate=1.0, timeout_seconds=3, max_pending=0, clock=lambda: clock[0])
    for index in range(3):
        assert controller.submit(_process_job(f"failure-{index}", binding, _crash_worker))
        results = _wait(controller, 5)
        assert results and results[-1]["failure_category"] == "RENDER_FAILED"
    assert controller.submit(_process_job("breaker-open", binding, _success_worker), eligibility=_eligibility()) is False
    clock[0] += 601
    assert controller.submit(_process_job("breaker-closed", binding, _success_worker), eligibility=_eligibility()) is True
    assert _wait(controller, 5)[-1]["package_valid"] is True
    controller.shutdown()


def test_shadow_lifecycle_uses_opaque_correlation_and_no_raw_request_id():
    events = []
    request_id = "request-with-sensitive-looking-marker"
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id=request_id, candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=True, sample_rate=1.0, max_pending=0, event_logger=lambda event, **fields: events.append((event, fields)))
    assert controller.submit(_process_job(request_id, binding, _success_worker), eligibility=_eligibility())
    _wait(controller)
    controller.shutdown()
    expected = hashlib.sha256(request_id.encode()).hexdigest()[:16]
    assert all(fields.get("correlation_id") == expected for _, fields in events)
    assert all("request_id" not in fields for _, fields in events)


def test_sampled_out_has_no_child_lifecycle():
    events = []
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="sampled-out", candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=True, sample_rate=0.0, event_logger=lambda event, **fields: events.append(event))
    assert controller.submit(_process_job("sampled-out", binding, _success_worker), eligibility=_eligibility()) is False
    time.sleep(0.05)
    controller.shutdown()
    assert events == ["presentation_shadow_admission"]


def test_sampled_in_success_emits_ordered_single_terminal_lifecycle():
    events = []
    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="sampled-in", candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=True, sample_rate=1.0, max_pending=0, event_logger=lambda event, **fields: events.append((event, fields)))
    assert controller.submit(_process_job("sampled-in", binding, _success_worker), eligibility=_eligibility())
    assert _wait(controller)
    controller.shutdown()
    names = [event for event, _ in events]
    assert names == [
        "presentation_shadow_admission",
        "presentation_shadow_sampled_in",
        "presentation_shadow_child_started",
        "presentation_shadow_completed",
        "presentation_shadow_capacity_reclaimed",
    ]
    assert sum(name in {"presentation_shadow_completed", "presentation_shadow_failed", "presentation_shadow_timeout", "presentation_shadow_crash"} for name in names) == 1


def test_timeout_and_crash_emit_terminal_evidence_and_reclaim_capacity():
    for request_id, worker, terminal in (("timeout-observe", _stuck_worker, "presentation_shadow_timeout"), ("crash-observe", _crash_worker, "presentation_shadow_crash")):
        events = []
        payload = _request([])
        binding = bind_shadow_candidates(payload, request_id=request_id, candidates=_m48_candidates(), confirmation_state=[])
        controller = ShadowController(enabled=True, sample_rate=1.0, timeout_seconds=3, max_pending=0, event_logger=lambda event, **fields: events.append(event))
        assert controller.submit(_process_job(request_id, binding, worker), eligibility=_eligibility())
        assert _wait(controller, 4)
        controller.shutdown()
        assert terminal in events
        assert events[-1] == "presentation_shadow_capacity_reclaimed"


def test_logger_failure_does_not_affect_primary_or_retry_synchronously():
    def failing_logger(event, **fields):
        raise RuntimeError("must not escape")

    payload = _request([])
    binding = bind_shadow_candidates(payload, request_id="logger-failure", candidates=_m48_candidates(), confirmation_state=[])
    controller = ShadowController(enabled=True, sample_rate=1.0, max_pending=0, event_logger=failing_logger)
    assert controller.submit(_process_job("logger-failure", binding, _success_worker), eligibility=_eligibility())
    assert _wait(controller)[-1]["package_valid"] is True
    controller.shutdown()


def _integration_payload(state):
    candidates = _m48_candidates()
    payload = _request(state)
    payload.semantic_candidates = candidate_set_to_dict(candidates)
    return payload


def _patch_integration_seam(monkeypatch, *, prepared_status="READY", selected_master="M48", composition="VALID"):
    events = []

    class FakeController:
        def __init__(self, **kwargs):
            self.event_logger = kwargs["event_logger"]

        @staticmethod
        def eligibility(**kwargs):
            return ShadowController.eligibility(**kwargs)

        def submit(self, job, *, eligibility):
            return True

    fake_context = SimpleNamespace(binding=SimpleNamespace(candidates=[]))
    fake_prepared = SimpleNamespace(
        status=SimpleNamespace(value=prepared_status),
        selected_master_id=selected_master,
        composition_readiness=composition,
        semantic_readiness=prepared_status,
    )
    monkeypatch.setattr(shadow_integration, "ShadowController", FakeController)
    monkeypatch.setattr(shadow_integration, "ShadowJob", lambda **kwargs: kwargs)
    monkeypatch.setattr(shadow_integration, "ShadowProcessWorkload", lambda **kwargs: kwargs)
    monkeypatch.setattr(shadow_integration, "build_candidate_state_bridge", lambda *args, **kwargs: fake_context)
    monkeypatch.setattr(shadow_integration, "prepare_pmv3", lambda *args, **kwargs: fake_prepared)
    monkeypatch.setattr(engine_integration.logger, "info", lambda event, extra=None: events.append((event, extra or {})))
    monkeypatch.setattr(engine_integration, "_PRODUCTION_SHADOW_CONTROLLER", None)
    monkeypatch.setattr(engine_integration, "settings", SimpleNamespace(presentation_master_v3_renderer_mvp_shadow_enabled=True))
    return events


def test_eligibility_observability_emits_one_eligible_decision_and_preserves_admission(monkeypatch):
    events = _patch_integration_seam(monkeypatch)
    payload = _integration_payload(_state(_m48_candidates()))
    primary = PresentationEngineResult(b"PK-primary", "legacy")

    result = engine_integration._submit_production_shadow_after_primary(primary, payload, request_id="eligible", project_id=None)

    assert result is primary
    decisions = [(event, extra) for event, extra in events if event.startswith("presentation_shadow_eligibility_decision")]
    assert len(decisions) == 1
    event, extra = decisions[0]
    assert event == f"presentation_shadow_eligibility_decision decision=ELIGIBLE reason=ELIGIBLE correlation_id={hashlib.sha256(b'eligible').hexdigest()[:16]}"
    assert extra == {"decision": "ELIGIBLE", "reason": "ELIGIBLE", "correlation_id": hashlib.sha256(b"eligible").hexdigest()[:16]}


def test_eligibility_observability_classifies_missing_state_without_admission(monkeypatch):
    events = _patch_integration_seam(monkeypatch)
    payload = _integration_payload([])
    payload.semantic_candidates = None
    primary = PresentationEngineResult(b"PK-primary", "legacy")

    engine_integration._submit_production_shadow_after_primary(primary, payload, request_id="missing", project_id=None)

    decisions = [(event, extra) for event, extra in events if event.startswith("presentation_shadow_eligibility_decision")]
    expected_correlation = hashlib.sha256(b"missing").hexdigest()[:16]
    assert decisions == [
        (
            f"presentation_shadow_eligibility_decision decision=INELIGIBLE reason=MISSING_CANDIDATE_STATE correlation_id={expected_correlation}",
            {"decision": "INELIGIBLE", "reason": "MISSING_CANDIDATE_STATE", "correlation_id": expected_correlation},
        )
    ]
    assert all(not event.startswith("presentation_shadow_admission") for event, _ in events)


@pytest.mark.parametrize(
    ("prepared_status", "selected_master", "composition", "reason"),
    [("REVIEW_REQUIRED", "M48", "VALID", "READINESS_NOT_ELIGIBLE"),
     ("READY", "M47", "VALID", "MASTER_NOT_M48"),
     ("READY", "M48", "INVALID", "COMPOSITION_INVALID")],
)
def test_eligibility_observability_uses_bounded_rejection_reasons(monkeypatch, prepared_status, selected_master, composition, reason):
    events = _patch_integration_seam(monkeypatch, prepared_status=prepared_status, selected_master=selected_master, composition=composition)
    payload = _integration_payload(_state(_m48_candidates()))
    primary = PresentationEngineResult(b"PK-primary", "legacy")

    engine_integration._submit_production_shadow_after_primary(primary, payload, request_id="rejected", project_id=None)

    decisions = [(event, extra) for event, extra in events if event.startswith("presentation_shadow_eligibility_decision")]
    assert len(decisions) == 1
    assert decisions[0][1]["decision"] == "INELIGIBLE"
    assert decisions[0][1]["reason"] == reason
    assert f"decision=INELIGIBLE reason={reason}" in decisions[0][0]


def test_eligibility_message_omits_unavailable_correlation_and_sensitive_content(monkeypatch):
    events = _patch_integration_seam(monkeypatch)
    payload = _integration_payload([])
    payload.semantic_candidates = None
    primary = PresentationEngineResult(b"PK-primary", "legacy")

    engine_integration._submit_production_shadow_after_primary(primary, payload, request_id=None, project_id="secret-project")

    decisions = [event for event, _ in events if event.startswith("presentation_shadow_eligibility_decision")]
    assert decisions == ["presentation_shadow_eligibility_decision decision=INELIGIBLE reason=MISSING_REQUEST_ID"]
    assert "correlation_id=" not in decisions[0]
    assert "secret-project" not in decisions[0]
