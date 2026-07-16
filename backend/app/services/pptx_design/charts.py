from __future__ import annotations


def clamp_ratio(value: float) -> float:
    return max(0.0, min(1.0, value))


def bar_segments(values: list[float]) -> list[float]:
    return [clamp_ratio(value) for value in values]
