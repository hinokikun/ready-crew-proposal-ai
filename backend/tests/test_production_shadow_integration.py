import time
import hashlib
from io import BytesIO
from zipfile import ZipFile

from app.services.presentation_master.integration.shadow_integration import ShadowController
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
