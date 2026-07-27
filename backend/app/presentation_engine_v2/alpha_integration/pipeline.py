"""Offline Alpha Integration Pipeline for Presentation Engine 2.0."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..deck_planner import plan_deck
from ..evidence_planner import plan_evidence
from ..message_designer import design_messages
from ..message_designer.designer_validators import validate_message_designer_output
from .pipeline_adapters import context_summary, stable_fingerprint
from .pipeline_evaluator import evaluate_alpha_pipeline
from .pipeline_models import (
    AlphaHumanReviewSummary,
    AlphaIntegrationCase,
    AlphaIntegrationOutput,
    AlphaValidationIssue,
    CrossModuleValidationResult,
)
from .pipeline_reporter import human_review_markdown
from .pipeline_validators import validate_cross_module, validate_evidence_stage


ALPHA_PIPELINE_FIXED_CREATED_AT = datetime(2026, 7, 27, tzinfo=timezone.utc)


class AlphaPipelineInputError(ValueError):
    """Raised when Alpha Integration receives invalid input."""


def _parse_case(case_input: AlphaIntegrationCase | dict[str, Any]) -> AlphaIntegrationCase:
    try:
        return case_input if isinstance(case_input, AlphaIntegrationCase) else AlphaIntegrationCase.parse_obj(case_input)
    except ValidationError as exc:
        raise AlphaPipelineInputError("Alpha Integration case failed schema validation.") from exc


def _human_review(
    *,
    case: AlphaIntegrationCase,
    deck_result: Any,
    evidence_result: Any,
    message_result: Any,
    cross_validation: CrossModuleValidationResult,
    evaluation: Any,
) -> AlphaHumanReviewSummary:
    deck = deck_result.deck_blueprint
    section_summary = [
        f"{section.section_order + 1}. {section.section_title} ({section.section_type})"
        for section in sorted(deck.sections, key=lambda item: item.section_order)
    ]
    slide_summary = [
        f"{slide.slide_order + 1}. {slide.working_title} / role={slide.slide_role} / goal={slide.slide_goal}"
        for slide in sorted(deck.slide_plan, key=lambda item: item.slide_order)
    ]
    headline_summary = [
        f"{message.slide_order + 1}. {message.headline} - {message.main_message}"
        for message in sorted(message_result.slide_messages, key=lambda item: item.slide_order)
    ]
    evidence_summary = [
        f"{slide.slide_order + 1}. {req.label} ({req.source_type}, {req.priority}, confidence={req.confidence})"
        for slide in sorted(evidence_result.slide_evidence, key=lambda item: item.slide_order)
        for req in slide.required_evidence
    ]
    missing_summary = [
        f"{slide.slide_order + 1}. {warning.message} -> {warning.suggested_action}"
        for slide in sorted(evidence_result.slide_evidence, key=lambda item: item.slide_order)
        for warning in slide.missing_evidence_warnings
    ]
    warnings = [f"{issue.code}: {issue.message}" for issue in cross_validation.warnings[:20]]
    blocking = [f"{issue.code}: {issue.message}" for issue in cross_validation.errors[:20]]
    good_points = [
        "Deck, Evidence, and Message slide references are evaluated together.",
        "Missing evidence is carried into human-readable review.",
        "Pipeline remains offline and does not generate PPTX or Slide Blueprints.",
    ]
    unnatural = []
    if deck.primary_audience == "general" and case.audience:
        unnatural.append("Audience inference may be too broad for the provided persona.")
    weak = []
    if missing_summary:
        weak.append("Some slides still need evidence before customer-facing rendering.")
    improvements = [
        recommendation
        for dim in evaluation.dimensions
        for recommendation in dim.recommendations
    ][:20]
    return AlphaHumanReviewSummary(
        case_id=case.integration_case_id,
        case_name=case.case_name,
        proposal_context_summary=context_summary(case.proposal_context),
        audience=str(deck.primary_audience),
        decision_stage=str(deck.decision_stage),
        deck_goal=str(deck.deck_goal),
        story_arc=str(deck.story_arc),
        section_summary=section_summary,
        slide_summary=slide_summary,
        headline_summary=headline_summary,
        required_evidence_summary=evidence_summary,
        missing_evidence_summary=missing_summary,
        key_warnings=warnings,
        blocking_issues=blocking,
        good_points=good_points,
        unnatural_points=unnatural,
        weak_sales_points=weak,
        improvement_candidates=improvements,
        phase2d_readiness=evaluation.phase2d_readiness_status,
    )


class AlphaIntegrationPipeline:
    """Runs Phase 2A, 2B, and 2C offline for integration review."""

    def run(self, case_input: AlphaIntegrationCase | dict[str, Any]) -> AlphaIntegrationOutput:
        case = _parse_case(case_input)
        deck_result = plan_deck(case.proposal_context)
        deck = deck_result.deck_blueprint
        evidence_result = plan_evidence(deck, case.proposal_context)
        evidence_validation = validate_evidence_stage(
            case_id=case.integration_case_id,
            deck=deck,
            evidence=evidence_result,
        )
        message_result = design_messages(case.proposal_context, deck, evidence_result)
        message_validation = validate_message_designer_output(message_result)
        cross_validation = validate_cross_module(
            case_id=case.integration_case_id,
            context=case.proposal_context,
            deck=deck,
            evidence=evidence_result,
            message=message_result,
        )
        combined_issues: list[AlphaValidationIssue] = [
            *evidence_validation.issues,
            *cross_validation.issues,
        ]
        combined_validation = CrossModuleValidationResult(
            valid=not any(issue.blocking for issue in combined_issues),
            issues=combined_issues,
            checked_stage_count=max(evidence_validation.checked_stage_count, cross_validation.checked_stage_count),
            passed_stage_count=min(evidence_validation.passed_stage_count, cross_validation.passed_stage_count),
            failed_stage_count=max(evidence_validation.failed_stage_count, cross_validation.failed_stage_count),
        )
        evaluation = evaluate_alpha_pipeline(
            case=case,
            deck=deck,
            evidence=evidence_result,
            message=message_result,
            cross_validation=combined_validation,
        )
        human_review = _human_review(
            case=case,
            deck_result=deck_result,
            evidence_result=evidence_result,
            message_result=message_result,
            cross_validation=combined_validation,
            evaluation=evaluation,
        )
        blocking = [issue for issue in combined_issues if issue.blocking]
        warnings = [issue for issue in combined_issues if not issue.blocking]
        output = AlphaIntegrationOutput(
            created_at=ALPHA_PIPELINE_FIXED_CREATED_AT,
            integration_case_id=case.integration_case_id,
            case_name=case.case_name,
            proposal_context_summary=context_summary(case.proposal_context),
            deck_planner_result=deck_result,
            deck_validation_result=deck.validation_result,
            evidence_planner_result=evidence_result,
            evidence_validation_result=evidence_validation,
            message_designer_result=message_result,
            message_validation_result=message_validation,
            cross_module_validation_result=combined_validation,
            pipeline_evaluation_result=evaluation,
            human_review_summary=human_review,
            blocking_issues=blocking,
            warnings=warnings,
            improvement_candidates=human_review.improvement_candidates,
            phase2d_readiness=evaluation.phase2d_readiness_status,
            input_fingerprint=stable_fingerprint(case.dict()),
            generated_pptx=False,
            connected_to_runtime=False,
            generated_slide_blueprints=False,
            used_external_ai=False,
        )
        return output


def run_alpha_integration(case_input: AlphaIntegrationCase | dict[str, Any]) -> AlphaIntegrationOutput:
    return AlphaIntegrationPipeline().run(case_input)


def run_alpha_integration_from_payload(payload: dict[str, Any]) -> AlphaIntegrationOutput:
    if not isinstance(payload, dict):
        raise AlphaPipelineInputError("Alpha Integration payload must be a dictionary.")
    if "case" in payload:
        payload = payload["case"]
    return run_alpha_integration(payload)


def run_alpha_integration_markdown(case_input: AlphaIntegrationCase | dict[str, Any]) -> str:
    return human_review_markdown(run_alpha_integration(case_input))
