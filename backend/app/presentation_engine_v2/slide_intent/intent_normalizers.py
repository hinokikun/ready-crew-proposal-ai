"""Normalizers for Phase 2D Slide Intent."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable_fingerprint(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def stable_intent_id(deck_id: str, slide_id: str, fingerprint: str) -> str:
    return f"intent-{deck_id}-{slide_id}-{fingerprint[:10]}".replace(" ", "-")[:140]
