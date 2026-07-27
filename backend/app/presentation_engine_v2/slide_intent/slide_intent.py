"""Offline Slide Intent Engine for Presentation Engine 2.0 Phase 2D."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..deck_models import DeckBlueprint
from ..deck_planner.planner_models import ProposalContext
from ..deck_validators import validate_deck_blueprint
from ..evidence_planner.evidence_models import EvidencePlannerResult
from ..message_designer.designer_models import MessageDesignerOutput
from ..message_designer.designer_validators import validate_message_designer_output
from .intent_evaluator import evaluate_slide_intent_design, evaluate_slide_intent_output
from .intent_models import SlideIntentDesign, SlideIntentInput, SlideIntentOutput
from .intent_normalizers import stable_fingerprint, stable_intent_id
from .intent_rules import decide_intent
from .intent_validators import validate_slide_intent_design, validate_slide_intent_output


SLIDE_INTENT_FIXED_CREATED_AT = datetime(2026, 7, 27, tzinfo=timezone.utc)


class SlideIntentInputError(ValueError):
    """Raised when Slide Intent receives invalid offline input."""


def _parse_input(
    context_input: ProposalContext | dict[str, Any],
    deck_input: DeckBlueprint | dict[str, Any],
    evidence_input: EvidencePlannerResult | dict[str, Any],
    message_input: MessageDesignerOutput | dict[str, Any],
) -> SlideIntentInput:
    try:
        context = context_input if isinstance(context_input, ProposalContext) else ProposalContext.parse_obj(context_input)
        deck = deck_input if isinstance(deck_input, DeckBlueprint) else DeckBlueprint.parse_obj(deck_input)
        evidence = (
            evidence_input
            if isinstance(evidence_input, EvidencePlannerResult)
            else EvidencePlannerResult.parse_obj(evidence_input)
        )
        message = (
            message_input
            if isinstance(message_input, MessageDesignerOutput)
            else MessageDesignerOutput.parse_obj(message_input)
        )
    except ValidationError as exc:
        raise SlideIntentInputError("Slide Intent input failed schema validation.") from exc

    deck_validation = validate_deck_blueprint(deck)
    if not deck_validation.valid:
        codes = ", ".join(issue.code for issue in deck_validation.issues[:6])
        raise SlideIntentInputError(f"Deck Blueprint is not valid for Slide Intent: {codes}")
    message_validation = validate_message_designer_output(message)
    if message_validation.errors:
        codes = ", ".join(issue.code for issue in message_validation.errors[:6])
        raise SlideIntentInputError(f"Message Designer output is not valid for Slide Intent: {codes}")
    if evidence.deck_id != deck.deck_id or message.deck_id != deck.deck_id:
        raise SlideIntentInputError("Deck, Evidence, and Message outputs must share the same deck_id.")
    deck_slide_ids = {item.slide_blueprint_id for item in deck.slide_plan}
    evidence_slide_ids = {item.slide_blueprint_id for item in evidence.slide_evidence}
    message_slide_ids = {item.slide_blueprint_id for item in message.slide_messages}
    if not deck_slide_ids or None in deck_slide_ids:
        raise SlideIntentInputError("Deck Blueprint slide_plan must contain slide_blueprint_id for every slide.")
    if not (deck_slide_ids == evidence_slide_ids == message_slide_ids):
        raise SlideIntentInputError("Slide references must match across Deck, Evidence, and Message outputs.")
    if (
        evidence.generated_slide_blueprints
        or message.generated_slide_blueprints
        or message.generated_visuals
        or message.generated_diagrams
        or message.generated_layouts
        or message.generated_pptx
        or message.connected_to_runtime
    ):
        raise SlideIntentInputError("Slide Intent input must remain offline and pre-rendering.")
    return SlideIntentInput(
        proposal_context=context,
        deck_blueprint=deck,
        evidence_planner_output=evidence,
        message_designer_output=message,
    )


def _fingerprint(context: ProposalContext, deck: DeckBlueprint, evidence: Any, message: Any) -> str:
    return stable_fingerprint(
        {
            "context": context.dict(),
            "deck_id": deck.deck_id,
            "slide_id": message.slide_blueprint_id,
            "evidence": evidence.dict(),
            "message": message.dict(),
        }
    )


class SlideIntentEngine:
    """Rule-based offline engine that emits intent-only slide plans."""

    def design(
        self,
        context_input: ProposalContext | dict[str, Any],
        deck_input: DeckBlueprint | dict[str, Any],
        evidence_input: EvidencePlannerResult | dict[str, Any],
        message_input: MessageDesignerOutput | dict[str, Any],
    ) -> SlideIntentOutput:
        parsed = _parse_input(context_input, deck_input, evidence_input, message_input)
        context = parsed.proposal_context
        deck = parsed.deck_blueprint
        evidence_output = parsed.evidence_planner_output
        message_output = parsed.message_designer_output
        evidence_by_slide = {item.slide_blueprint_id: item for item in evidence_output.slide_evidence}
        message_by_slide = {item.slide_blueprint_id: item for item in message_output.slide_messages}
        slide_intents: list[SlideIntentDesign] = []

        for slide in sorted(deck.slide_plan, key=lambda item: item.slide_order):
            slide_id = str(slide.slide_blueprint_id)
            evidence = evidence_by_slide[slide_id]
            message = message_by_slide[slide_id]
            decision = decide_intent(
                context=context,
                deck=deck,
                slide=slide,
                evidence=evidence,
                message=message,
            )
            fingerprint = _fingerprint(context, deck, evidence, message)
            design = SlideIntentDesign(
                intent_id=stable_intent_id(deck.deck_id, slide_id, fingerprint),
                deck_id=deck.deck_id,
                slide_blueprint_id=slide_id,
                source_message_design_id=message.message_design_id,
                slide_order=slide.slide_order,
                slide_intent=decision.slide_intent,
                slide_type=decision.slide_type,
                information_priority=decision.information_priority,
                reading_order=decision.reading_order,
                visual_pattern_candidate=decision.visual_pattern,
                diagram_candidate=decision.diagram_candidate,
                chart_candidate=decision.chart_candidate,
                layout_constraint=decision.layout_constraints,
                rendering_hint=decision.rendering_hint,
                intent_confidence=decision.confidence,
                warnings=decision.warnings,
                input_metrics=decision.metrics,
                source_evidence_ids=message.used_evidence_ids,
                input_fingerprint=fingerprint,
                created_at=SLIDE_INTENT_FIXED_CREATED_AT,
                generated_slide_blueprint=False,
                generated_diagram=False,
                generated_chart=False,
                generated_pptx=False,
                connected_to_runtime=False,
            )
            design.validation_result = validate_slide_intent_design(design)
            design.evaluation_result = evaluate_slide_intent_design(design)
            slide_intents.append(design)

        output = SlideIntentOutput(
            created_at=SLIDE_INTENT_FIXED_CREATED_AT,
            deck_id=deck.deck_id,
            project_id=deck.project_id,
            project_name=context.project_name,
            slide_intents=slide_intents,
            warnings=[warning for intent in slide_intents for warning in intent.warnings][:60],
            generated_slide_blueprints=False,
            generated_diagrams=False,
            generated_charts=False,
            generated_pptx=False,
            connected_to_runtime=False,
        )
        output.validation_result = validate_slide_intent_output(output)
        output.evaluation_result = evaluate_slide_intent_output(output)
        return output


def design_slide_intents(
    context_input: ProposalContext | dict[str, Any],
    deck_input: DeckBlueprint | dict[str, Any],
    evidence_input: EvidencePlannerResult | dict[str, Any],
    message_input: MessageDesignerOutput | dict[str, Any],
) -> SlideIntentOutput:
    return SlideIntentEngine().design(context_input, deck_input, evidence_input, message_input)


def design_slide_intents_from_payload(payload: dict[str, Any]) -> SlideIntentOutput:
    if not isinstance(payload, dict):
        raise SlideIntentInputError("Slide Intent payload must be a dictionary.")
    required = {"proposal_context", "deck_blueprint", "evidence_planner_output", "message_designer_output"}
    missing = sorted(required - set(payload))
    if missing:
        raise SlideIntentInputError(f"Slide Intent payload missing keys: {', '.join(missing)}")
    unexpected = set(payload) - required
    if unexpected:
        raise SlideIntentInputError(f"Unexpected Slide Intent payload keys: {', '.join(sorted(unexpected))}")
    return design_slide_intents(
        payload["proposal_context"],
        payload["deck_blueprint"],
        payload["evidence_planner_output"],
        payload["message_designer_output"],
    )
