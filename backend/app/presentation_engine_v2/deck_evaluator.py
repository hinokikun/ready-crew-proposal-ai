"""Offline evaluator for Deck Blueprints."""

from __future__ import annotations

from typing import Any, Dict

from .deck_enums import DeckValidationSeverity, SectionType
from .deck_models import DeckBlueprint, DeckEvaluationDimension, DeckEvaluationResult
from .deck_normalizers import normalize_deck_blueprint_dict
from .deck_validators import validate_deck_blueprint


DECK_EVALUATOR_NOTE = (
    "本評価はDeck Blueprint構造上の準備度を示すものであり、"
    "PowerPointの最終デザイン品質、営業成果、顧客の意思決定を保証するものではない。"
)


def _dimension(name: str, score: int, reason: str, issues: list[str] | None = None, recommendations: list[str] | None = None) -> DeckEvaluationDimension:
    return DeckEvaluationDimension(
        name=name,
        score=max(0, min(10, score)),
        reason=reason,
        issues=issues or [],
        recommendations=recommendations or [],
    )


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "D"


def _parse_deck(payload: DeckBlueprint | Dict[str, Any], normalize: bool) -> DeckBlueprint:
    if isinstance(payload, DeckBlueprint):
        return payload
    data, _changed = normalize_deck_blueprint_dict(payload) if normalize else (payload, [])
    return DeckBlueprint.parse_obj(data)


def evaluate_deck_blueprint(payload: DeckBlueprint | Dict[str, Any], *, normalize: bool = False) -> DeckEvaluationResult:
    validation = validate_deck_blueprint(payload, normalize=normalize)
    deck = _parse_deck(payload, normalize)
    section_types = [section.section_type for section in deck.sections]
    issue_codes = [issue.code for issue in validation.issues]
    errors = [issue for issue in validation.issues if issue.severity == DeckValidationSeverity.ERROR.value]
    warnings = [issue for issue in validation.issues if issue.severity == DeckValidationSeverity.WARNING.value]

    dimensions = [
        _dimension(
            "Contract Validity",
            max(0, 10 - len(errors) * 3 - len(warnings)),
            "Schema and deck-level semantic validation readiness.",
            issue_codes[:5],
            ["Resolve blocking validation issues."] if errors else [],
        ),
        _dimension(
            "Structural Completeness",
            10 if SectionType.COVER.value in section_types and SectionType.NEXT_ACTION.value in section_types else 5,
            "Deck has required opening and decision-oriented ending.",
            [],
            [] if SectionType.NEXT_ACTION.value in section_types else ["Add next_action section."],
        ),
        _dimension(
            "Narrative Coherence",
            9 if deck.story_beats and deck.narrative_summary else 6,
            "Story beats and narrative summary make deck flow reviewable.",
            [],
            [] if deck.story_beats else ["Add story beats."],
        ),
        _dimension(
            "Audience Fit",
            10 if not any(code.startswith("PE2-DECK-AUDIENCE") for code in issue_codes) else 6,
            "Audience seniority, executive summary, and detail level are aligned.",
        ),
        _dimension(
            "Decision Readiness",
            8 + min(2, len(deck.decision_points)),
            "Decision questions and approval requirements are represented.",
            [],
            [] if deck.decision_points else ["Add decision points."],
        ),
        _dimension(
            "Message Consistency",
            9 if deck.core_thesis and deck.value_proposition and deck.key_differentiator else 5,
            "Core thesis, value proposition, and differentiator are present.",
        ),
        _dimension(
            "Evidence Coverage",
            6 + min(4, len(deck.source_references) + len(deck.approval_requirements)),
            "Deck has source references or approval evidence requirements.",
        ),
        _dimension(
            "Section Balance",
            10 if deck.minimum_slide_count <= len(deck.slide_plan) <= deck.maximum_slide_count else 6,
            "Actual slide plan fits declared deck count bounds.",
        ),
        _dimension(
            "Transition Quality",
            6 + min(4, len(deck.transitions)),
            "Transition metadata can support coherent deck flow.",
            [],
            [] if deck.transitions else ["Add transition bridge metadata."],
        ),
        _dimension(
            "Sales Persuasiveness",
            8 + (1 if deck.objection_response else 0) + (1 if deck.cta_plan else 0),
            "Deck contains objection handling and next action design.",
        ),
        _dimension(
            "Customer-facing Cleanliness",
            10 if not any(code == "PE2-DECK-SAFETY-001" for code in issue_codes) else 4,
            "Internal placeholder labels are not exposed.",
        ),
        _dimension(
            "Slide Blueprint Readiness",
            10 if len(deck.slide_blueprint_refs) >= len(deck.slide_plan) else 4,
            "Each slide plan item has a Slide Blueprint reference.",
            [],
            [] if len(deck.slide_blueprint_refs) >= len(deck.slide_plan) else ["Add slide_blueprint_refs."],
        ),
    ]
    raw = sum(item.score for item in dimensions)
    total = round(raw / (len(dimensions) * 10) * 100)
    return DeckEvaluationResult(
        total_score=total,
        grade=_grade(total),
        dimensions=dimensions,
        blocking_issue_count=len(errors),
        warning_count=len(warnings),
        note=DECK_EVALUATOR_NOTE,
    )
