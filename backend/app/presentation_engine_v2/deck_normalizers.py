"""Safe normalizers for Presentation Engine 2.0 Deck Blueprints."""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any, Dict, Tuple

from pydantic import BaseModel, Field

from .deck_enums import (
    AudienceSeniority,
    DecisionStage,
    DecisionUrgency,
    DeckGoal,
    DeckLengthType,
    DeckStatus,
    DeckType,
    DeckValidationSeverity,
    EvidenceStrategy,
    NarrativeFunction,
    PersuasionStrategy,
    RiskLevel,
    SectionType,
    SlideRole,
    StoryArcType,
    TransitionType,
)
from .deck_errors import SUPPORTED_DECK_BLUEPRINT_VERSION
from .deck_models import DeckBlueprint
from .enums import AudienceType, SlideGoal, SlideType, ThemeType


ENUM_FIELDS = {
    "deck_goal": DeckGoal,
    "deck_type": DeckType,
    "audience_seniority": AudienceSeniority,
    "seniority": AudienceSeniority,
    "decision_stage": DecisionStage,
    "story_arc": StoryArcType,
    "section_type": SectionType,
    "slide_role": SlideRole,
    "narrative_function": NarrativeFunction,
    "transition_type": TransitionType,
    "transition_from_previous": TransitionType,
    "transition_to_next": TransitionType,
    "deck_length_type": DeckLengthType,
    "evidence_strategy": EvidenceStrategy,
    "evidence_requirement": EvidenceStrategy,
    "evidence_density": EvidenceStrategy,
    "persuasion_strategy": PersuasionStrategy,
    "risk_level": RiskLevel,
    "urgency": DecisionUrgency,
    "decision_urgency": DecisionUrgency,
    "status": DeckStatus,
    "severity": DeckValidationSeverity,
    "primary_audience": AudienceType,
    "recommended_theme": ThemeType,
    "slide_type": SlideType,
    "expected_slide_type": SlideType,
    "slide_goal": SlideGoal,
    "expected_slide_goal": SlideGoal,
}


class DeckNormalizationResult(BaseModel):
    original: Dict[str, Any]
    normalized: Dict[str, Any]
    changed_fields: list[str] = Field(default_factory=list)
    deck: DeckBlueprint


def _canonical_key(value: Any) -> str:
    text = str(value or "").strip()
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    text = text.lower().replace("/", "_").replace("-", "_")
    text = re.sub(r"[\s\u3000]+", "_", text)
    text = re.sub(r"[^a-z0-9_]+", "", text)
    return re.sub(r"_+", "_", text).strip("_")


def _normalize_text(value: Any) -> Any:
    if value is None or not isinstance(value, str):
        return value
    text = value.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or None


def _normalize_enum(field_name: str, value: Any) -> Any:
    enum_cls = ENUM_FIELDS.get(field_name)
    if enum_cls is None or value is None:
        return value
    canonical = _canonical_key(value)
    for item in enum_cls:
        if canonical == item.value or canonical == _canonical_key(item.name):
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
    source = "|".join(str(payload.get(key, "")) for key in ["project_id", "deck_title", "deck_type", "story_arc"])
    digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _walk(value: Any, field_name: str = "", path: str = "") -> Tuple[Any, list[str]]:
    changed: list[str] = []
    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            child, child_changed = _walk(item, str(key), child_path)
            if child is not None:
                result[str(key)] = child
            if child != item:
                changed.append(child_path)
            changed.extend(child_changed)
        return result, changed
    if isinstance(value, list):
        normalized = []
        for index, item in enumerate(value):
            child, child_changed = _walk(item, field_name, f"{path}[{index}]")
            if child is not None:
                normalized.append(child)
            changed.extend(child_changed)
        deduped = _dedupe_list(normalized)
        if deduped != normalized:
            changed.append(path)
        return deduped, changed
    normalized_value = _normalize_enum(field_name, _normalize_text(value))
    return normalized_value, changed


def normalize_deck_blueprint_dict(payload: Dict[str, Any]) -> tuple[Dict[str, Any], list[str]]:
    original = copy.deepcopy(payload)
    normalized, changed = _walk(original)
    if not isinstance(normalized, dict):
        normalized = {}

    if not normalized.get("deck_blueprint_version"):
        normalized["deck_blueprint_version"] = SUPPORTED_DECK_BLUEPRINT_VERSION
        changed.append("deck_blueprint_version")
    if not normalized.get("schema_version"):
        normalized["schema_version"] = SUPPORTED_DECK_BLUEPRINT_VERSION
        changed.append("schema_version")
    if not normalized.get("deck_id"):
        normalized["deck_id"] = _stable_id("deck", normalized)
        changed.append("deck_id")
    if not normalized.get("target_slide_count"):
        normalized["target_slide_count"] = len(normalized.get("slide_plan") or [])
        changed.append("target_slide_count")
    if "sections" in normalized:
        for index, section in enumerate(normalized["sections"]):
            if isinstance(section, dict) and "section_order" not in section:
                section["section_order"] = index
                changed.append(f"sections[{index}].section_order")
    if "slide_plan" in normalized:
        for index, slide in enumerate(normalized["slide_plan"]):
            if isinstance(slide, dict) and "slide_order" not in slide:
                slide["slide_order"] = index
                changed.append(f"slide_plan[{index}].slide_order")
    return normalized, sorted(set(changed))


def normalize_deck_blueprint_payload(payload: Dict[str, Any]) -> DeckNormalizationResult:
    normalized, changed = normalize_deck_blueprint_dict(payload)
    deck = DeckBlueprint.parse_obj(normalized)
    return DeckNormalizationResult(
        original=copy.deepcopy(payload),
        normalized=normalized,
        changed_fields=changed,
        deck=deck,
    )
