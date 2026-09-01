from __future__ import annotations

from dataclasses import dataclass
from collections import deque
import hashlib
from multiprocessing.connection import Connection
import multiprocessing as mp
from queue import Empty, Full, Queue
from threading import Event, Lock, Semaphore, Thread
from time import monotonic, perf_counter
from typing import Any
from typing import Callable

from app.models import PptxDownloadRequest

from .engine_adapter import prepare_pmv3, render_pmv3
from .shadow_candidate_binding import ShadowCandidateBinding


@dataclass(frozen=True)
class ShadowProcessWorkload:
    payload: PptxDownloadRequest
    binding: ShadowCandidateBinding
    injected_worker: Callable[[], dict[str, Any]] | None = None


@dataclass(frozen=True)
class ProcessShadowJob:
    request_id: str
    primary_engine: str
    semantic_readiness: str
    selected_master: str
    composition_status: str
    workload: ShadowProcessWorkload


def _worker_entry(connection: Connection, workload: ShadowProcessWorkload) -> None:
    """Spawn-safe child entry point; only bounded metadata crosses the pipe."""
    try:
        if workload.injected_worker is not None:
            connection.send(dict(workload.injected_worker()))
            return
        started = perf_counter()
        prepared = prepare_pmv3(workload.payload, semantic_candidates=workload.binding.candidates)
        if prepared.status.value not in {"READY", "READY_WITH_VALID_BINDINGS"}:
            connection.send({"failure_category": "NOT_ELIGIBLE"})
            return
        rendered = render_pmv3(prepared)
        connection.send({
            "slide_count": rendered.slide_count,
            "package_valid": rendered.validation_status == "PASS",
            "rasterization_ratio": rendered.rasterization_ratio,
            "clipping": rendered.clipping_count,
            "overflow": rendered.overflow_count,
            "off_canvas": rendered.off_canvas_count,
            "collision": 0,
            "elapsed_ms": round((perf_counter() - started) * 1000),
        })
        del rendered
    except Exception:
        try:
            connection.send({
                "failure_category": "RENDER_FAILED",
                "terminal_outcome": "CRASHED" if workload.injected_worker is not None else "FAILED",
            })
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        connection.close()


class ProcessShadowController:
    """One dispatcher, bounded queue, and one killable process per active task."""

    def __init__(self, *, enabled: bool = False, sample_rate: float = 0.01, timeout_seconds: float = 8.0, max_pending: int = 4, clock=monotonic, event_logger: Callable[..., None] | None = None):
        self.enabled = enabled
        self.sample_rate = sample_rate
        self.timeout_seconds = timeout_seconds
        self._queue: Queue[ProcessShadowJob] = Queue(maxsize=max(1, max_pending))
        self._slots = Semaphore(1 + max(0, max_pending))
        self._results: Queue[dict[str, Any]] = Queue(maxsize=64)
        self._stop = Event()
        self._lock = Lock()
        self._clock = clock
        self._event_logger = event_logger or (lambda event, **fields: None)
        self._failures: deque[float] = deque()
        self._cooldown_until = 0.0
        self._active: mp.Process | None = None
        self._context = mp.get_context("spawn")
        self._dispatcher = Thread(target=self._dispatch, name="presentation-v3-shadow-dispatcher", daemon=True)
        self._dispatcher.start()

    @staticmethod
    def correlation_id(request_id: str) -> str:
        return hashlib.sha256(request_id.encode()).hexdigest()[:16]

    @staticmethod
    def is_sampled(request_id: str, rate: float = 0.01) -> bool:
        if not request_id or rate <= 0:
            return False
        bucket = int(hashlib.sha256(request_id.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        return bucket < min(rate, 1.0)

    @staticmethod
    def eligibility(*, summary: bool, confirmation_state_present: bool, prepared_status: str, selected_master: str, composition_status: str):
        from .shadow_integration import ShadowEligibility
        if summary or not confirmation_state_present:
            return ShadowEligibility(False, "NOT_ELIGIBLE")
        if prepared_status not in {"READY", "READY_WITH_VALID_BINDINGS"}:
            return ShadowEligibility(False, "SEMANTIC_REVIEW_REQUIRED" if prepared_status == "REVIEW_REQUIRED" else "NOT_ELIGIBLE")
        if selected_master != "M48":
            return ShadowEligibility(False, "SELECTION_NO_MATCH")
        if composition_status != "VALID":
            return ShadowEligibility(False, "COMPOSITION_INVALID")
        return ShadowEligibility(True, "")

    def submit(self, job: ProcessShadowJob, *, eligibility=None) -> bool:
        if self._stop.is_set() or not self.enabled or (eligibility is not None and not eligibility.eligible):
            return False
        correlation_id = self.correlation_id(job.request_id)
        sampled = self.is_sampled(job.request_id, self.sample_rate)
        self._emit_event(
            "presentation_shadow_admission",
            correlation_id=correlation_id,
            sampled=sampled,
            capacity_active=self._capacity_active(),
            capacity_pending=min(self._queue.qsize(), self._queue.maxsize),
        )
        if not sampled:
            return False
        if not self._slots.acquire(blocking=False):
            self._publish({"request_id": job.request_id, "failure_category": "SHADOW_CAPACITY_SKIPPED"})
            return False
        with self._lock:
            now = self._clock()
            while self._failures and now - self._failures[0] > 300:
                self._failures.popleft()
            if now < self._cooldown_until:
                self._slots.release()
                return False
        try:
            self._queue.put_nowait(job)
            self._emit_event("presentation_shadow_sampled_in", correlation_id=correlation_id, sampled=True)
            return True
        except Full:
            self._slots.release()
            self._publish({"request_id": job.request_id, "failure_category": "SHADOW_CAPACITY_SKIPPED"})
            return False

    def drain_results(self) -> tuple[dict[str, Any], ...]:
        result: list[dict[str, Any]] = []
        while True:
            try:
                result.append(self._results.get_nowait())
            except Empty:
                return tuple(result)

    def _dispatch(self) -> None:
        while not self._stop.is_set():
            try:
                job = self._queue.get(timeout=0.05)
            except Empty:
                continue
            self._run_one(job)

    def _run_one(self, job: ProcessShadowJob) -> None:
        correlation_id = self.correlation_id(job.request_id)
        parent, child = self._context.Pipe(duplex=False)
        process = self._context.Process(target=_worker_entry, args=(child, job.workload), name="presentation-v3-shadow-worker")
        with self._lock:
            self._active = process
        started = monotonic()
        try:
            process.start()
        except Exception:
            self._slots.release()
            self._record_failure()
            self._emit_event("presentation_shadow_failed", correlation_id=correlation_id, outcome="FAILED", error_class="PROCESS_START_FAILED")
            self._emit_capacity_reclaimed(correlation_id)
            parent.close()
            child.close()
            with self._lock:
                self._active = None
            return
        child.close()
        self._emit_event("presentation_shadow_child_started", correlation_id=correlation_id)
        process.join(timeout=max(0.0, self.timeout_seconds))
        # The child has exited or is about to be terminated; reclaim admission
        # before publishing the result so consumers can submit immediately.
        self._slots.release()
        if process.is_alive():
            self._terminate(process)
            self._record_failure()
            self._emit_event("presentation_shadow_timeout", correlation_id=correlation_id, outcome="TIMEOUT", timeout_boolean=True, error_class="SHADOW_TIMEOUT")
            self._publish({"request_id": job.request_id, "failure_category": "SHADOW_TIMEOUT", "elapsed_ms": round((monotonic() - started) * 1000)})
        else:
            try:
                result = parent.recv()
            except (EOFError, OSError):
                result = {"failure_category": "UNEXPECTED_ERROR"}
            if result.get("failure_category"):
                self._record_failure()
            result["request_id"] = job.request_id
            terminal = result.get("terminal_outcome")
            if terminal == "CRASHED":
                self._emit_event("presentation_shadow_crash", correlation_id=correlation_id, outcome="CRASHED", crash_boolean=True, error_class="CHILD_CRASH")
            elif result.get("failure_category"):
                self._emit_event("presentation_shadow_failed", correlation_id=correlation_id, outcome="FAILED", error_class=self._bounded_error_class(result.get("failure_category")))
            else:
                self._emit_event("presentation_shadow_completed", correlation_id=correlation_id, outcome="COMPLETED", elapsed_ms=result.get("elapsed_ms", 0))
            self._publish(result)
        self._emit_capacity_reclaimed(correlation_id)
        parent.close()
        with self._lock:
            self._active = None

    @staticmethod
    def _terminate(process: mp.Process) -> None:
        process.terminate()
        process.join(timeout=0.5)
        if process.is_alive() and hasattr(process, "kill"):
            process.kill()
            process.join(timeout=0.5)

    def _publish(self, result: dict[str, Any]) -> None:
        try:
            self._results.put_nowait(dict(result))
        except Full:
            pass

    def _emit_event(self, event: str, **fields: Any) -> None:
        try:
            self._event_logger(event, **fields)
        except Exception:
            pass

    def _emit_capacity_reclaimed(self, correlation_id: str) -> None:
        self._emit_event(
            "presentation_shadow_capacity_reclaimed",
            correlation_id=correlation_id,
            capacity_active=self._capacity_active(),
            capacity_pending=min(self._queue.qsize(), self._queue.maxsize),
        )

    def _capacity_active(self) -> int:
        with self._lock:
            return int(self._active is not None and self._active.is_alive())

    @staticmethod
    def _bounded_error_class(value: Any) -> str:
        candidate = str(value or "UNKNOWN")
        return candidate if candidate.isidentifier() and len(candidate) <= 40 else "SHADOW_FAILURE"

    def _record_failure(self) -> None:
        with self._lock:
            now = self._clock()
            while self._failures and now - self._failures[0] > 300:
                self._failures.popleft()
            self._failures.append(now)
            if len(self._failures) >= 3:
                self._cooldown_until = now + 600

    def shutdown(self) -> None:
        self._stop.set()
        with self._lock:
            process = self._active
        if process is not None and process.is_alive():
            self._terminate(process)
        while True:
            try:
                self._queue.get_nowait()
                self._slots.release()
            except Empty:
                break
        self._dispatcher.join(timeout=1.0)


__all__ = ["ShadowProcessWorkload", "ProcessShadowJob", "ProcessShadowController"]
