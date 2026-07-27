"""Golden Alpha Integration outputs."""

from __future__ import annotations

from typing import Any

from ..fixtures import valid_alpha_integration_cases
from ..pipeline import run_alpha_integration


def golden_alpha_integration_outputs() -> list[dict[str, Any]]:
    return [run_alpha_integration(case).dict() for case in valid_alpha_integration_cases()[:10]]
