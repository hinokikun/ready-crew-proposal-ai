from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0


class InMemoryRateLimitBackend:
    """Small sliding-window backend that can be replaced by Redis later."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = {}
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.time()
        threshold = now - max(1, window_seconds)
        with self._lock:
            current = [timestamp for timestamp in self._hits.get(key, []) if timestamp > threshold]
            if len(current) >= max(1, limit):
                retry_after = max(1, int(current[0] + window_seconds - now) + 1)
                self._hits[key] = current
                return RateLimitResult(False, retry_after)
            current.append(now)
            self._hits[key] = current
        return RateLimitResult(True, 0)

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
