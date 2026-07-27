"""Offline Message Designer for Presentation Engine 2.0 Phase 2C."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..deck_models import DeckBlueprint, SlidePlanItem
from ..deck_planner.planner_models import ProposalContext
from ..deck_validators import validate_deck_blueprint
from ..evidence_planner.evidence_models import EvidencePlannerResult, SlideEvidencePlan
from .designer_contracts import STYLE_PROFILES
from .designer_enums import MessageStatus
from .designer_evaluator import evaluate_message_designer_output, evaluate_slide_message_design
from .designer_models import (
    MessageDesignerInput,
    MessageDesignerOutput,
    MessageGenerationMetadata,
    SlideMessageDesign,
)
from .designer_normalizers import stable_fingerprint, stable_message_design_id
from .designer_rules import (
    constraints_for,
    evidence_alignment_summary_for,
    evidence_usage_for,
    headline_for,
    key_takeaway_for,
    main_message_for,
    message_rule_decision,
    missing_disclosures_for,
    numeric_claims_for,
    source_references_for,
    speaker_note_for,
    supporting_messages_for,
    unsupported_claims_for,
    unused_required_evidence_ids,
    warnings_for,
)
from .designer_validators import validate_message_designer_output, validate_slide_message_design


MESSAGE_DESIGNER_FIXED_CREATED_AT = datetime(2026, 7, 27, tzinfo=timezone.utc)


class MessageDesignerInputError(ValueError):
    """Raised when Message Designer receives invalid offline input."""


def _parse_input(
    context_input: ProposalContext | dict[str, Any],
    deck_input: DeckBlueprint | dict[str, Any],
    evidence_input: EvidencePlannerResult | dict[str, Any],
) -> MessageDesignerInput:
    try:
        context = context_input if isinstance(context_input, ProposalContext) else ProposalContext.parse_obj(context_input)
        deck = deck_input if isinstance(deck_input, DeckBlueprint) else DeckBlueprint.parse_obj(deck_input)
        evidence = (
            evidence_input
            if isinstance(evidence_input, EvidencePlannerResult)
            else EvidencePlannerResult.parse_obj(evidence_input)
        )
    except ValidationError as exc:
        raise MessageDesignerInputError("Message Designer input failed schema validation.") from exc

    deck_validation = validate_deck_blueprint(deck)
    if not deck_validation.valid:
        codes = ", ".join(issue.code for issue in deck_validation.issues[:6])
        raise MessageDesignerInputError(f"Deck Blueprint is not valid for message design: {codes}")
    if evidence.deck_id != deck.deck_id:
        raise MessageDesignerInputError("Evidence Planner output deck_id does not match Deck Blueprint.")
    deck_slide_ids = {item.slide_blueprint_id for item in deck.slide_plan}
    evidence_slide_ids = {item.slide_blueprint_id for item in evidence.slide_evidence}
    if not deck_slide_ids or None in deck_slide_ids:
        raise MessageDesignerInputError("Deck Blueprint slide_plan must contain slide_blueprint_id for every slide.")
    if deck_slide_ids != evidence_slide_ids:
        missing = sorted(str(item) for item in deck_slide_ids - evidence_slide_ids)
        extra = sorted(str(item) for item in evidence_slide_ids - deck_slide_ids)
        raise MessageDesignerInputError(
            f"Evidence Planner slide references do not match Deck Blueprint. missing={missing}; extra={extra}"
        )
    if evidence.generated_headlines or evidence.generated_main_messages or evidence.generated_body_text:
        raise MessageDesignerInputError("Evidence Planner output must remain evidence-only before message design.")
    return MessageDesignerInput(
        proposal_context=context,
        deck_blueprint=deck,
        evidence_planner_output=evidence,
    )


def _slide_plan_id(slide: SlidePlanItem) -> str:
    return f"slide-plan-{slide.slide_order:02d}"


def _input_fingerprint(context: ProposalContext, deck: DeckBlueprint, slide: SlidePlanItem, evidence: SlideEvidencePlan) -> str:
    return stable_fingerprint(
        {
            "context": context.dict(),
            "deck_id": deck.deck_id,
            "deck_version": deck.deck_blueprint_version,
            "slide": slide.dict(),
            "evidence": evidence.dict(),
        }
    )


class MessageDesigner:
    """Rule-based offline designer that emits message-only slide plans."""

    def design(
        self,
        context_input: ProposalContext | dict[str, Any],
        deck_input: DeckBlueprint | dict[str, Any],
        evidence_input: EvidencePlannerResult | dict[str, Any],
    ) -> MessageDesignerOutput:
        parsed = _parse_input(context_input, deck_input, evidence_input)
        context = parsed.proposal_context
        deck = parsed.deck_blueprint
        evidence_output = parsed.evidence_planner_output
        evidence_by_slide = {item.slide_blueprint_id: item for item in evidence_output.slide_evidence}
        slide_messages: list[SlideMessageDesign] = []

        for slide in sorted(deck.slide_plan, key=lambda item: item.slide_order):
            slide_evidence = evidence_by_slide[str(slide.slide_blueprint_id)]
            decision = message_rule_decision(deck, slide, slide_evidence)
            used_evidence_ids = [
                evidence_id
                for item in supporting_messages_for(slide_evidence)
                for evidence_id in item.evidence_ids
            ]
            fingerprint = _input_fingerprint(context, deck, slide, slide_evidence)
            style_profile = STYLE_PROFILES[decision.style.value]
            message = SlideMessageDesign(
                message_design_id=stable_message_design_id(deck.deck_id, str(slide.slide_blueprint_id), fingerprint),
                deck_id=deck.deck_id,
                slide_plan_id=_slide_plan_id(slide),
                slide_blueprint_id=str(slide.slide_blueprint_id),
                slide_order=slide.slide_order,
                status=MessageStatus.DRAFT,
                slide_role=str(slide.slide_role),
                slide_goal=str(slide.slide_goal),
                narrative_function=str(slide.narrative_function),
                audience=str(deck.primary_audience),
                audience_seniority=str(deck.audience_seniority),
                decision_stage=str(deck.decision_stage),
                message_style=decision.style,
                message_tone=decision.tone,
                headline=headline_for(deck, slide, context, slide_evidence),
                main_message=main_message_for(deck, slide, context, slide_evidence),
                supporting_messages=supporting_messages_for(slide_evidence),
                key_takeaway=key_takeaway_for(deck, slide, context, slide_evidence),
                speaker_note_summary=speaker_note_for(deck, slide, context, slide_evidence),
                evidence_alignment_level=decision.evidence_alignment,
                evidence_alignment_summary=evidence_alignment_summary_for(slide_evidence, decision.evidence_alignment),
                used_evidence_ids=used_evidence_ids,
                unused_required_evidence_ids=unused_required_evidence_ids(slide_evidence, used_evidence_ids),
                missing_evidence_disclosure=missing_disclosures_for(slide_evidence),
                unsupported_claims=unsupported_claims_for(slide_evidence),
                numeric_claims=numeric_claims_for(context, slide_evidence),
                evidence_usage=evidence_usage_for(slide_evidence),
                message_strength=decision.strength,
                message_confidence=decision.confidence,
                warnings=warnings_for(slide_evidence),
                source_references=source_references_for(slide_evidence),
                style_profile=style_profile,
                constraints=constraints_for(),
                generation_metadata=MessageGenerationMetadata(
                    source_contracts=[
                        "deck_blueprint_v1",
                        "proposal_context_v1",
                        "evidence_planner_result_v1",
                    ]
                ),
                input_fingerprint=fingerprint,
                created_at=MESSAGE_DESIGNER_FIXED_CREATED_AT,
            )
            message.validation_result = validate_slide_message_design(message)
            message.status = MessageStatus.NEEDS_REVIEW if message.validation_result.warnings else MessageStatus.VALIDATED
            message.evaluation_result = evaluate_slide_message_design(message)
            slide_messages.append(message)

        output = MessageDesignerOutput(
            created_at=MESSAGE_DESIGNER_FIXED_CREATED_AT,
            deck_id=deck.deck_id,
            slide_messages=slide_messages,
            generated_slide_blueprints=False,
            generated_visuals=False,
            generated_diagrams=False,
            generated_layouts=False,
            generated_pptx=False,
            connected_to_runtime=False,
        )
        validation = validate_message_designer_output(output)
        output.warnings = [
            warning
            for message in output.slide_messages
            for warning in message.warnings
        ][:40]
        output.evaluation_result = evaluate_message_designer_output(output)
        if validation.errors:
            raise MessageDesignerInputError(
                "Message Designer generated invalid output: "
                + ", ".join(issue.code for issue in validation.errors[:6])
            )
        return output


def design_messages(
    context_input: ProposalContext | dict[str, Any],
    deck_input: DeckBlueprint | dict[str, Any],
    evidence_input: EvidencePlannerResult | dict[str, Any],
) -> MessageDesignerOutput:
    return MessageDesigner().design(context_input, deck_input, evidence_input)


def design_messages_from_payload(payload: dict[str, Any]) -> MessageDesignerOutput:
    if not isinstance(payload, dict):
        raise MessageDesignerInputError("Message Designer payload must be a dictionary.")
    required = {"proposal_context", "deck_blueprint", "evidence_planner_output"}
    missing = sorted(required - set(payload))
    if missing:
        raise MessageDesignerInputError(f"Message Designer payload missing keys: {', '.join(missing)}")
    unexpected = set(payload) - required
    if unexpected:
        raise MessageDesignerInputError(f"Unexpected Message Designer payload keys: {', '.join(sorted(unexpected))}")
    return design_messages(
        payload["proposal_context"],
        payload["deck_blueprint"],
        payload["evidence_planner_output"],
    )
