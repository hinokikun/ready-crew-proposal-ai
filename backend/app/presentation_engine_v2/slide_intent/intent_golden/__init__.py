"""Golden outputs for Phase 2D Slide Intent Foundation."""

from __future__ import annotations

from typing import Any

from ..intent_fixtures import valid_slide_intent_payloads
from ..slide_intent import design_slide_intents_from_payload


def golden_slide_intent_outputs() -> list[dict[str, Any]]:
    return [design_slide_intents_from_payload(payload).dict() for payload in valid_slide_intent_payloads(limit=20)]
