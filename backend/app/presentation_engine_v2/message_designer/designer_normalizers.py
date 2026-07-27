"""Safe normalizers for Phase 2C message contracts."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from pydantic import ValidationError

from .designer_models import MessageDesignerOutput, SlideMessageDesign


def collapse_whitespace(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_enum_label(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def stable_fingerprint(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def stable_message_design_id(deck_id: str, slide_blueprint_id: str, fingerprint: str) -> str:
    return f"msg-{deck_id}-{slide_blueprint_id}-{fingerprint[:8]}"


def _dedupe_list(values: list[Any]) -> list[Any]:
    output: list[Any] = []
    seen = set()
    for item in values:
        key = json.dumps(item, ensure_ascii=False, sort_keys=True, default=str)
        if key in seen:
            continue
        output.append(item)
        seen.add(key)
    return output


def normalize_slide_message_design_dict(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    data = json.loads(json.dumps(payload, ensure_ascii=False, default=str))
    changed: list[str] = []
    for field in [
        "headline",
        "main_message",
        "key_takeaway",
        "speaker_note_summary",
        "evidence_alignment_summary",
    ]:
        if field in data:
            normalized = collapse_whitespace(data[field])
            if normalized != data[field]:
                data[field] = normalized
                changed.append(field)
    for field in ["message_style", "message_tone", "message_strength", "message_confidence", "status"]:
        if field in data:
            normalized = normalize_enum_label(data[field])
            if normalized != data[field]:
                data[field] = normalized
                changed.append(field)
    for field in ["used_evidence_ids", "unused_required_evidence_ids"]:
        if isinstance(data.get(field), list):
            before = list(data[field])
            data[field] = [collapse_whitespace(item) for item in data[field] if collapse_whitespace(item)]
            data[field] = _dedupe_list(data[field])
            if data[field] != before:
                changed.append(field)
    if isinstance(data.get("supporting_messages"), list):
        before = list(data["supporting_messages"])
        for item in data["supporting_messages"]:
            if isinstance(item, dict) and "text" in item:
                item["text"] = collapse_whitespace(item["text"])
        data["supporting_messages"] = _dedupe_list(data["supporting_messages"])
        if data["supporting_messages"] != before:
            changed.append("supporting_messages")
    if not data.get("input_fingerprint"):
        data["input_fingerprint"] = stable_fingerprint(data)
        changed.append("input_fingerprint")
    if not data.get("message_design_id") and data.get("deck_id") and data.get("slide_blueprint_id"):
        data["message_design_id"] = stable_message_design_id(data["deck_id"], data["slide_blueprint_id"], data["input_fingerprint"])
        changed.append("message_design_id")
    return data, changed


def normalize_slide_message_design(payload: dict[str, Any]) -> tuple[SlideMessageDesign, list[str]]:
    data, changed = normalize_slide_message_design_dict(payload)
    try:
        return SlideMessageDesign.parse_obj(data), changed
    except ValidationError:
        raise


def normalize_message_designer_output_dict(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    data = json.loads(json.dumps(payload, ensure_ascii=False, default=str))
    changed: list[str] = []
    if isinstance(data.get("slide_messages"), list):
        normalized_items = []
        for item in data["slide_messages"]:
            normalized, item_changed = normalize_slide_message_design_dict(item)
            normalized_items.append(normalized)
            changed.extend([f"slide_messages.{field}" for field in item_changed])
        data["slide_messages"] = normalized_items
    return data, changed


def normalize_message_designer_output(payload: dict[str, Any]) -> tuple[MessageDesignerOutput, list[str]]:
    data, changed = normalize_message_designer_output_dict(payload)
    return MessageDesignerOutput.parse_obj(data), changed

