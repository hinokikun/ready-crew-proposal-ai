from __future__ import annotations

from dataclasses import dataclass

from .spacing import COLUMN_GAP, SAFE_AREA


@dataclass(frozen=True)
class GridColumn:
    index: int
    x: float
    width: float


def columns(count: int, *, gutter: float = COLUMN_GAP) -> list[GridColumn]:
    count = max(1, min(count, 6))
    width = (SAFE_AREA["w"] - gutter * (count - 1)) / count
    return [GridColumn(index=i + 1, x=SAFE_AREA["x"] + i * (width + gutter), width=width) for i in range(count)]


def thirds() -> list[GridColumn]:
    return columns(3)


def quarters() -> list[GridColumn]:
    return columns(4)
