"""Offline evaluator for Deck Planner results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..deck_enums import AudienceSeniority, DeckValidationSeverity, SectionType
from ..deck_models import DeckEvaluationDimension, DeckEvaluationResult
from ..deck_validators import validate_deck_blueprint

if TYPE_CHECKING:
    from .planner_models import DeckPlannerResult


PLANNER_EVALUATOR_NOTE = (
    "This score evaluates Deck Planner readiness only. It does not evaluate "
    "Slide Blueprint quality, rendered PPTX design, final copy, or sales outcome."
)


def _dimension(
    name: str,
    score: int,
    reason: str,
    issues: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> DeckEvaluationDimension:
    return DeckEvaluationDimension(
        name=name,
        score=max(0, min(10, score)),
        max_score=10,
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


def evaluate_planner_result(result: "DeckPlannerResult") -> DeckEvaluationResult:
    deck = result.deck_blueprint
    validation = validate_deck_blueprint(deck)
    issues = validation.issues
    errors = [issue for issue in issues if issue.severity == DeckValidationSeverity.ERROR.value]
    warnings = [issue for issue in issues if issue.severity == DeckValidationSeverity.WARNING.value]
    section_types = [section.section_type for section in deck.sections]
    slide_count = len(deck.slide_plan)
    recommendation_ids = {item.slide_blueprint_id for item in result.slide_recommendations}
    planned_ids = {item.slide_blueprint_id for item in deck.slide_plan if item.slide_blueprint_id}

    dimensions = [
        _dimension(
            "Story",
            10 if deck.story_arc and deck.story_beats and deck.narrative_summary else 6,
            "Story arc, beats, and narrative summary are present.",
            [],
            [] if deck.story_beats else ["Add story beats before slide-level planning."],
        ),
        _dimension(
            "Audience",
            10 if deck.primary_audience and deck.audience_profile else 6,
            "Audience seniority and profile are available for downstream planning.",
            [],
            [] if deck.audience_profile else ["Add audience_profile."],
        ),
        _dimension(
            "Decision Flow",
            10 if deck.decision_points and deck.cta_plan and SectionType.NEXT_ACTION.value in section_types else 5,
            "Decision question, CTA, and next action are connected.",
            [],
            [] if deck.decision_points else ["Add at least one decision point."],
        ),
        _dimension(
            "Section Quality",
            max(0, 10 - len(errors) * 3 - len(warnings)),
            "Deck sections satisfy schema and semantic validation.",
            [issue.code for issue in issues[:6]],
            ["Resolve blocking deck validation errors."] if errors else [],
        ),
        _dimension(
            "Slide Balance",
            10 if deck.minimum_slide_count <= slide_count <= deck.maximum_slide_count else 6,
            "Planned slide count fits the selected deck length.",
            [],
            [] if deck.minimum_slide_count <= slide_count <= deck.maximum_slide_count else ["Adjust deck length or sections."],
        ),
        _dimension(
            "Sales Readiness",
            8 + (1 if deck.objection_response else 0) + (1 if SectionType.PRICING.value in section_types or SectionType.ROI.value in section_types else 0),
            "The plan includes objection handling and value or pricing support.",
            [],
            [] if deck.objection_response else ["Add primary objection handling."],
        ),
        _dimension(
            "Executive Readiness",
            10
            if deck.audience_seniority != AudienceSeniority.EXECUTIVE.value
            or SectionType.EXECUTIVE_SUMMARY.value in section_types
            else 4,
            "Executive audiences receive summary-first framing.",
            [],
            [] if SectionType.EXECUTIVE_SUMMARY.value in section_types else ["Add executive summary for executive decks."],
        ),
        _dimension(
            "Customer-facing Cleanliness",
            10 if recommendation_ids == planned_ids and not result.generated_slide_blueprints else 6,
            "Planner recommendations align with slide plan and do not generate slide blueprints.",
            [],
            [] if recommendation_ids == planned_ids else ["Align recommendations with slide plan IDs."],
        ),
    ]
    total = round(sum(item.score for item in dimensions) / (len(dimensions) * 10) * 100)
    return DeckEvaluationResult(
        total_score=total,
        max_score=100,
        grade=_grade(total),
        dimensions=dimensions,
        blocking_issue_count=len(errors),
        warning_count=len(warnings),
        note=PLANNER_EVALUATOR_NOTE,
    )

