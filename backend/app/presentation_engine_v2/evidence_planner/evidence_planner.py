"""Offline Evidence Planner for Presentation Engine 2.0 Phase 2B."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..deck_models import DeckBlueprint, SlidePlanItem
from ..deck_planner.planner_models import ProposalContext
from ..deck_validators import validate_deck_blueprint
from .evidence_evaluator import evaluate_evidence_plan
from .evidence_models import (
    EvidencePlannerResult,
    EvidencePlannerWarning,
    EvidencePlanningInput,
    SlideEvidencePlan,
)
from .evidence_rules import (
    aggregate_confidence,
    missing_warnings,
    optional_requirements_for,
    primary_priority,
    requirements_for,
    risk_if_missing,
    visual_recommendation,
)


EVIDENCE_PLANNER_FIXED_CREATED_AT = datetime(2026, 7, 27, tzinfo=timezone.utc)


class EvidencePlannerInputError(ValueError):
    """Raised when the Evidence Planner receives an invalid offline input."""


def _parse_input(deck_input: DeckBlueprint | dict[str, Any], context_input: ProposalContext | dict[str, Any]) -> EvidencePlanningInput:
    try:
        deck = deck_input if isinstance(deck_input, DeckBlueprint) else DeckBlueprint.parse_obj(deck_input)
        context = context_input if isinstance(context_input, ProposalContext) else ProposalContext.parse_obj(context_input)
    except ValidationError as exc:
        raise EvidencePlannerInputError("Evidence Planner input failed schema validation.") from exc

    validation = validate_deck_blueprint(deck)
    if not validation.valid:
        codes = ", ".join(issue.code for issue in validation.issues[:6])
        raise EvidencePlannerInputError(f"Deck Blueprint is not valid for evidence planning: {codes}")
    return EvidencePlanningInput(deck_blueprint=deck, proposal_context=context)


def _section_type_for(deck: DeckBlueprint, slide: SlidePlanItem) -> str:
    section = next((item for item in deck.sections if item.section_id == slide.section_id), None)
    if section is None:
        raise EvidencePlannerInputError(f"Slide references missing section: {slide.section_id}")
    return str(section.section_type)


def _source_types(requirements: list[Any]) -> list[str]:
    ordered: list[str] = []
    for item in requirements:
        value = str(item.source_type)
        if value not in ordered:
            ordered.append(value)
    return ordered


def _warning_summary(result: EvidencePlannerResult) -> list[EvidencePlannerWarning]:
    blocking_count = sum(
        1
        for slide in result.slide_evidence
        for warning in slide.missing_evidence_warnings
        if warning.severity == "blocking"
    )
    warnings: list[EvidencePlannerWarning] = []
    if blocking_count:
        warnings.append(
            EvidencePlannerWarning(
                code="PE2-EVIDENCE-MISSING-BLOCKING",
                message=f"{blocking_count} blocking missing-evidence warnings were detected.",
                suggestion="Collect critical numeric or customer proof before slide content generation.",
            )
        )
    if not result.slide_evidence:
        warnings.append(
            EvidencePlannerWarning(
                code="PE2-EVIDENCE-NO-SLIDES",
                message="No slide evidence plan was created.",
                suggestion="Confirm Deck Blueprint slide_plan before evidence planning.",
            )
        )
    return warnings


class EvidencePlanner:
    """Rule-based offline planner that emits evidence requirements per slide."""

    def plan(
        self,
        deck_input: DeckBlueprint | dict[str, Any],
        context_input: ProposalContext | dict[str, Any],
    ) -> EvidencePlannerResult:
        parsed = _parse_input(deck_input, context_input)
        deck = parsed.deck_blueprint
        context = parsed.proposal_context
        slide_evidence: list[SlideEvidencePlan] = []

        for slide in sorted(deck.slide_plan, key=lambda item: item.slide_order):
            if not slide.slide_blueprint_id:
                raise EvidencePlannerInputError("Every slide must have slide_blueprint_id before evidence planning.")
            section_type = _section_type_for(deck, slide)
            required = requirements_for(section_type, slide, context)
            optional = optional_requirements_for(section_type, slide)
            warnings = missing_warnings(required, context)
            all_requirements = [*required, *optional]
            slide_evidence.append(
                SlideEvidencePlan(
                    slide_blueprint_id=slide.slide_blueprint_id,
                    slide_order=slide.slide_order,
                    section_id=slide.section_id,
                    section_type=section_type,
                    slide_role=str(slide.slide_role),
                    slide_goal=str(slide.slide_goal),
                    required_evidence=required,
                    optional_evidence=optional,
                    evidence_priority=primary_priority(required, slide),
                    evidence_confidence=aggregate_confidence(required),
                    evidence_source_types=_source_types(all_requirements),
                    numeric_evidence_required=any(item.numeric_required for item in required),
                    customer_proof_required=any(item.customer_proof_required for item in required),
                    case_study_required=any(item.case_study_required for item in all_requirements),
                    visual_evidence_recommendation=visual_recommendation(section_type, required),
                    missing_evidence_warnings=warnings,
                    risk_if_missing=risk_if_missing(section_type),
                    generated_headline=False,
                    generated_main_message=False,
                    generated_body_text=False,
                    generated_slide_blueprint=False,
                )
            )

        result = EvidencePlannerResult(
            created_at=EVIDENCE_PLANNER_FIXED_CREATED_AT,
            deck_id=deck.deck_id,
            deck_blueprint_version=deck.deck_blueprint_version,
            project_id=deck.project_id,
            slide_evidence=slide_evidence,
            warnings=[],
            generated_headlines=False,
            generated_main_messages=False,
            generated_body_text=False,
            generated_slide_blueprints=False,
            connected_to_runtime=False,
        )
        result.warnings = _warning_summary(result)
        result.evaluation_result = evaluate_evidence_plan(result)
        return result


def plan_evidence(
    deck_input: DeckBlueprint | dict[str, Any],
    context_input: ProposalContext | dict[str, Any],
) -> EvidencePlannerResult:
    return EvidencePlanner().plan(deck_input, context_input)


def plan_evidence_from_payload(payload: dict[str, Any]) -> EvidencePlannerResult:
    if not isinstance(payload, dict):
        raise EvidencePlannerInputError("Evidence planning payload must be a dictionary.")
    if "deck_blueprint" not in payload:
        raise EvidencePlannerInputError("Evidence planning payload requires deck_blueprint.")
    if "proposal_context" not in payload:
        raise EvidencePlannerInputError("Evidence planning payload requires proposal_context.")
    unexpected = set(payload) - {"deck_blueprint", "proposal_context"}
    if unexpected:
        raise EvidencePlannerInputError(f"Unexpected evidence planning payload keys: {', '.join(sorted(unexpected))}")
    return plan_evidence(payload["deck_blueprint"], payload["proposal_context"])

