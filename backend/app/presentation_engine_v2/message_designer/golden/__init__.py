"""Golden Message Designer outputs for Phase 2C."""

from __future__ import annotations

from typing import Any

from ..designer import design_messages_from_payload
from ..fixtures import valid_message_designer_payloads


def golden_message_designer_outputs() -> list[dict[str, Any]]:
    return [design_messages_from_payload(payload).dict() for payload in valid_message_designer_payloads()[:20]]
