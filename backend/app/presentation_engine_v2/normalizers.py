"""Safe normalizers for slide blueprint payloads."""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any, Dict, Tuple

from pydantic import BaseModel, Field

from .enums import (
    AlignmentType,
    AnimationHint,
    AudienceType,
    BlueprintStatus,
    CTAType,
    ContentPriority,
    DataConfidence,
    DensityLevel,
    DiagramType,
    EmphasisLevel,
    EvidenceType,
    HierarchyLevel,
    LayoutDirection,
    OverflowStrategy,
    SlideGoal,
    SlideType,
    ThemeType,
    ValidationSeverity,
    VisualType,
)
from .errors import SUPPORTED_BLUEPRINT_VERSION
from .models import SlideBlueprint


ENUM_FIELDS = {
    "slide_type": SlideType,
    "status": BlueprintStatus,
    "slide_goal": SlideGoal,
    "audience": AudienceType,
    "visual_type": VisualType,
    "diagram_type": DiagramType,
    "layout_direction": LayoutDirection,
    "content_priority": ContentPriority,
    "emphasis": EmphasisLevel,
    "hierarchy_level": HierarchyLevel,
    "theme": ThemeType,
    "alignment": AlignmentType,
    "density": DensityLevel,
    "overflow_strategy": OverflowStrategy,
    "fallback_visual_type": VisualType,
    "animation_hint": AnimationHint,
    "cta_type": CTAType,
    "evidence_type": EvidenceType,
    "source_type": EvidenceType,
    "confidence": DataConfidence,
    "severity": ValidationSeverity,
}


COLOR_FIELDS = {
    "background",
    "text",
    "primary",
    "secondary",
    "accent",
    "muted",
    "success",
    "warning",
    "danger",
    "color",
}


class NormalizationResult(BaseModel):
    original: Dict[str, Any]
    normalized: Dict[str, Any]
    changed_fields: list[str] = Field(default_factory=list)
    blueprint: SlideBlueprint


def _canonical_key(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = text.replace("/", "_").replace("-", "_")
    text = re.sub(r"[\s\u3000]+", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "", text)
    return re.sub(r"_+", "_", text).strip("_")


def _normalize_text(value: Any) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    return text or None


def _normalize_color(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if re.fullmatch(r"[0-9a-fA-F]{6}", text):
        return f"#{text.upper()}"
    if re.fullmatch(r"#[0-9a-fA-F]{6}", text):
        return text.upper()
    return text


def _normalize_enum(field_name: str, value: Any) -> Any:
    enum_cls = ENUM_FIELDS.get(field_name)
    if enum_cls is None or value is None:
        return value
    if isinstance(value, enum_cls):
        return value.value
    canonical = _canonical_key(value)
    for item in enum_cls:
        if canonical == item.value:
            return item.value
        if canonical == _canonical_key(item.name):
            return item.value
    return value


def _dedupe_list(items: list[Any]) -> list[Any]:
    seen = set()
    result = []
    for item in items:
        key = repr(item)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _stable_id(prefix: str, payload: Dict[str, Any]) -> str:
    source = "|".join(
        str(payload.get(key, ""))
        for key in ["slide_index", "slide_type", "slide_goal", "headline", "main_message"]
    )
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _walk(value: Any, field_name: str = "", path: str = "") -> Tuple[Any, list[str]]:
    changed: list[str] = []
    if isinstance(value, dict):
        normalized: Dict[str, Any] = {}
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            child, child_changed = _walk(item, str(key), child_path)
            if child is not None:
                normalized[str(key)] = child
            if child != item:
                changed.append(child_path)
            changed.extend(child_changed)
        return normalized, changed
    if isinstance(value, list):
        normalized_items = []
        for index, item in enumerate(value):
            child, child_changed = _walk(item, field_name, f"{path}[{index}]")
            if child is not None:
                normalized_items.append(child)
            changed.extend(child_changed)
        deduped = _dedupe_list(normalized_items)
        if deduped != normalized_items:
            changed.append(path)
        return deduped, changed
    normalized_value = _normalize_text(value)
    if field_name in COLOR_FIELDS:
        normalized_value = _normalize_color(normalized_value)
    normalized_value = _normalize_enum(field_name, normalized_value)
    return normalized_value, changed


def normalize_blueprint_dict(payload: Dict[str, Any]) -> tuple[Dict[str, Any], list[str]]:
    """Normalize a raw blueprint payload without changing meaning."""

    original = copy.deepcopy(payload)
    normalized, changed = _walk(original)
    if not isinstance(normalized, dict):
        normalized = {}

    if not normalized.get("blueprint_version"):
        normalized["blueprint_version"] = SUPPORTED_BLUEPRINT_VERSION
        changed.append("blueprint_version")
    if not normalized.get("slide_index") and normalized.get("slide_index") != 0:
        normalized["slide_index"] = 0
        changed.append("slide_index")
    if not normalized.get("blueprint_id"):
        normalized["blueprint_id"] = _stable_id("bp", normalized)
        changed.append("blueprint_id")
    if not normalized.get("slide_id"):
        normalized["slide_id"] = _stable_id("slide", normalized)
        changed.append("slide_id")
    if "diagram_definition" not in normalized:
        normalized["diagram_definition"] = {"diagram_id": f"diagram-{normalized['slide_id']}", "diagram_type": "none"}
        changed.append("diagram_definition")
    if "primary_element" not in normalized and normalized.get("headline"):
        normalized["primary_element"] = "headline"
        changed.append("primary_element")
    return normalized, sorted(set(changed))


def normalize_blueprint_payload(payload: Dict[str, Any]) -> NormalizationResult:
    """Return normalized dict plus parsed SlideBlueprint."""

    normalized, changed = normalize_blueprint_dict(payload)
    blueprint = SlideBlueprint.parse_obj(normalized)
    return NormalizationResult(
        original=copy.deepcopy(payload),
        normalized=normalized,
        changed_fields=changed,
        blueprint=blueprint,
    )
