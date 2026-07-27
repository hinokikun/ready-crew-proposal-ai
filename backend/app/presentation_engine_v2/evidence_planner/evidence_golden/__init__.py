"""Golden Evidence Planner outputs for Phase 2B."""

from __future__ import annotations

from typing import Any

from ..evidence_fixtures import valid_evidence_planning_payloads
from ..evidence_planner import plan_evidence_from_payload


def golden_evidence_planner_results() -> list[dict[str, Any]]:
    return [plan_evidence_from_payload(payload).dict() for payload in valid_evidence_planning_payloads()[:20]]

