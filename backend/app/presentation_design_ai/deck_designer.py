"""Deck-level Presentation Design AI orchestration."""

from __future__ import annotations

import hashlib
import json

from app.presentation_composer import CaseContext

from .contracts import DESIGN_VERSION, is_presentation_design_ai_enabled
from .design_language import build_design_language
from .information_architecture import build_information_architecture
from .models import CompositionType, DesignDeck
from .narrative_planner import select_story_items
from .slide_designer import design_slide_contract
from .validators import validate_design_deck


def design_presentation_deck(case: CaseContext, *, force_enabled: bool = False) -> DesignDeck:
    enabled = force_enabled or is_presentation_design_ai_enabled()
    architecture = build_information_architecture(case)
    story_items = select_story_items(architecture.items)
    previous_compositions: list[CompositionType] = []
    contracts = []
    for index, item in enumerate(story_items):
        contract = design_slide_contract(case, item, index, len(story_items), story_items, tuple(previous_compositions))
        contracts.append(contract)
        previous_compositions.append(contract.composition_type)

    deck = DesignDeck(
        version="9.0",
        design_version=DESIGN_VERSION,
        case_id=case.case_id,
        case_name=case.case_name,
        client_name=case.client_name,
        feature_flag_enabled=enabled,
        information_architecture=architecture,
        slide_contracts=tuple(contracts),
        design_language=build_design_language(case.category),
        design_plan_fingerprint=_fingerprint(case.case_id, [contract.to_dict() for contract in contracts]),
        fallback_count=0 if enabled else 1,
        native_fallback_count=0,
        render_warnings=tuple(validate_design_deck_contracts(contracts)),
    )
    issues = validate_design_deck(deck)
    if issues:
        deck = DesignDeck(
            version=deck.version,
            design_version=deck.design_version,
            case_id=deck.case_id,
            case_name=deck.case_name,
            client_name=deck.client_name,
            feature_flag_enabled=deck.feature_flag_enabled,
            information_architecture=deck.information_architecture,
            slide_contracts=deck.slide_contracts,
            design_language=deck.design_language,
            design_plan_fingerprint=deck.design_plan_fingerprint,
            fallback_count=deck.fallback_count,
            native_fallback_count=deck.native_fallback_count,
            render_warnings=tuple(sorted(set(deck.render_warnings + tuple(issues)))),
        )
    return deck


def validate_design_deck_contracts(contracts) -> list[str]:
    warnings: list[str] = []
    if len(contracts) < 10:
        warnings.append("deck_may_be_too_short_for_customer_proposal")
    compositions = [contract.composition_type for contract in contracts]
    for index in range(2, len(compositions)):
        if compositions[index] == compositions[index - 1] == compositions[index - 2]:
            warnings.append(f"three_repeated_compositions_at_slide_{index + 1}")
    return warnings


def _fingerprint(case_id: str, contracts: list[dict]) -> str:
    source = json.dumps({"case_id": case_id, "contracts": contracts}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
