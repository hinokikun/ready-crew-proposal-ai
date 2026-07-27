"""Integration evaluator for Presentation Engine 2.0 Alpha Review."""

from __future__ import annotations

from statistics import mean

from ..deck_models import DeckBlueprint
from ..evidence_planner.evidence_models import EvidencePlannerResult
from ..message_designer.designer_models import MessageDesignerOutput
from .pipeline_models import (
    AlphaEvaluationDimension,
    AlphaEvaluationResult,
    AlphaIntegrationCase,
    AlphaValidationSeverity,
    CrossModuleValidationResult,
    Phase2DReadinessStatus,
)


ALPHA_EVALUATOR_NOTE = (
    "This score evaluates offline integration readiness from Proposal Context through Message Designer. "
    "It does not evaluate PPTX rendering, visual quality, real customer outcome, API behavior, DB behavior, "
    "or any Version81 runtime flow."
)


def _dimension(
    name: str,
    score: int,
    reason: str,
    issues: list[str] | None = None,
    recommendations: list[str] | None = None,
    *,
    blocking: bool = False,
) -> AlphaEvaluationDimension:
    return AlphaEvaluationDimension(
        name=name,
        score=max(0, min(10, score)),
        reason=reason,
        issues=issues or [],
        recommendations=recommendations or [],
        blocking=blocking,
    )


def _grade(score: int) -> str:
    if score >= 95:
        return "S"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _readiness(score: int, blocking_count: int, warning_count: int) -> Phase2DReadinessStatus:
    if blocking_count > 0:
        return Phase2DReadinessStatus.BLOCKED
    if score >= 85 and warning_count <= 8:
        return Phase2DReadinessStatus.READY
    if score >= 72:
        return Phase2DReadinessStatus.READY_WITH_LIMITATIONS
    return Phase2DReadinessStatus.NOT_READY


def _avg_score(*scores: int | None) -> int:
    values = [score for score in scores if score is not None]
    if not values:
        return 0
    return round(mean(values))


def evaluate_alpha_pipeline(
    *,
    case: AlphaIntegrationCase,
    deck: DeckBlueprint,
    evidence: EvidencePlannerResult,
    message: MessageDesignerOutput,
    cross_validation: CrossModuleValidationResult,
) -> AlphaEvaluationResult:
    blocking = [item for item in cross_validation.issues if item.blocking or item.severity == AlphaValidationSeverity.ERROR.value]
    warnings = [item for item in cross_validation.issues if item.severity == AlphaValidationSeverity.WARNING.value]
    deck_score = deck.evaluation_result.total_score if deck.evaluation_result else 0
    evidence_score = evidence.evaluation_result.total_score if evidence.evaluation_result else 0
    message_score = message.evaluation_result.total_score if message.evaluation_result else 0
    slide_count = len(deck.slide_plan)
    evidence_count = len(evidence.slide_evidence)
    message_count = len(message.slide_messages)
    missing_evidence = [
        warning
        for slide in evidence.slide_evidence
        for warning in slide.missing_evidence_warnings
    ]
    unsupported = [claim for slide in message.slide_messages for claim in slide.unsupported_claims]
    disclosure_count = sum(len(slide.missing_evidence_disclosure) for slide in message.slide_messages)
    sections = {section.section_type for section in deck.sections}
    styles = {slide.message_style for slide in message.slide_messages}

    dimensions = [
        _dimension(
            "Contract Integrity",
            10 if not blocking else max(2, 10 - len(blocking) * 2),
            "All module contracts should parse, validate, and keep version boundaries.",
            [item.code for item in blocking[:8]],
            [] if not blocking else ["Resolve blocking contract issues before Phase 2D."],
            blocking=bool(blocking),
        ),
        _dimension(
            "Proposal Context Coverage",
            10
            - (0 if case.proposal_context.problems else 2)
            - (0 if case.proposal_context.expected_outcomes else 2)
            - (0 if case.proposal_context.decision_maker else 1),
            "Proposal Context should contain business goal, problems, audience, and expected outcomes.",
            case.intentionally_missing_evidence[:6],
            ["Collect missing context before customer-facing rendering."] if case.intentionally_missing_evidence else [],
        ),
        _dimension(
            "Story Coherence",
            min(10, max(5, deck_score // 10)),
            "Deck story should move from context to problem, recommendation, value, risk, and next action.",
            [],
            [] if deck_score >= 80 else ["Review section order and story arc."],
        ),
        _dimension(
            "Deck Structure Quality",
            10 if slide_count == deck.target_slide_count and slide_count >= 6 else 7,
            "Deck structure should have stable slide order and enough sections for a sales proposal.",
            [],
            [] if slide_count >= 6 else ["Add missing decision-support sections."],
        ),
        _dimension(
            "Audience Fit",
            9 if deck.primary_audience != "general" or not case.audience else 7,
            "Deck and messages should reflect audience and seniority.",
            [],
            [] if deck.primary_audience != "general" else ["Review broad audience inference."],
        ),
        _dimension(
            "Decision Flow",
            10 if deck.cta_plan and deck.next_action and "next_action" in sections else 7,
            "Pipeline should end with a clear decision or next action.",
            [],
            [] if "next_action" in sections else ["Add or preserve a next action section."],
        ),
        _dimension(
            "Evidence Completeness",
            max(4, 10 - len(missing_evidence)),
            "Every planned slide should have required evidence, and gaps should be visible.",
            [warning.warning_id for warning in missing_evidence[:8]],
            [] if not missing_evidence else ["Collect missing evidence before Phase 2D rendering."],
        ),
        _dimension(
            "Evidence Traceability",
            10 if evidence_count == slide_count and all(slide.required_evidence for slide in evidence.slide_evidence) else 5,
            "Evidence requirements should map to every deck slide.",
            [],
            [] if evidence_count == slide_count else ["Regenerate evidence planner output from the deck."],
        ),
        _dimension(
            "Numeric Integrity",
            min(10, max(4, evidence_score // 10)),
            "Numeric, ROI, pricing, and time claims should be backed by evidence requirements.",
            [],
            [] if evidence_score >= 80 else ["Confirm baselines, budget, or financial assumptions."],
        ),
        _dimension(
            "Message Clarity",
            min(10, max(5, message_score // 10)),
            "Message output should have concise headlines, clear main messages, and limited support points.",
            [],
            [] if message_score >= 80 else ["Review low-scoring message slides."],
        ),
        _dimension(
            "Evidence and Message Alignment",
            10 if not unsupported and disclosure_count >= len([w for w in missing_evidence if w.severity == "blocking"]) else 6,
            "Message Designer should not hide missing evidence or introduce unsupported claims.",
            [claim.claim_id for claim in unsupported[:8]],
            [] if not unsupported else ["Remove unsupported claims or attach basis evidence."],
        ),
        _dimension(
            "Slide-to-slide Consistency",
            10 if slide_count == evidence_count == message_count else 4,
            "Slide IDs and order should remain consistent across modules.",
            [],
            [] if slide_count == evidence_count == message_count else ["Fix slide reference drift."],
            blocking=slide_count != evidence_count or slide_count != message_count,
        ),
        _dimension(
            "Sales Readiness",
            9 if "sales" in styles or "executive" in styles or deck.next_action else 7,
            "Output should be useful for a sales review conversation.",
            [],
            ["Strengthen next action and sales-facing explanation."] if not deck.next_action else [],
        ),
        _dimension(
            "Executive Readiness",
            9 if "executive_summary" in sections else 6,
            "Executive review requires a concise summary and decision path.",
            [],
            [] if "executive_summary" in sections else ["Add an executive summary section."],
        ),
        _dimension(
            "Customer-facing Cleanliness",
            10
            if not (
                message.generated_pptx
                or message.generated_slide_blueprints
                or message.generated_visuals
                or message.generated_layouts
                or message.connected_to_runtime
            )
            else 2,
            "Alpha output must remain offline, customer-safe, and free of renderer/runtime artifacts.",
            [],
            [] if not message.connected_to_runtime else ["Remove runtime connection artifacts."],
        ),
        _dimension(
            "Phase 2D Readiness",
            _avg_score(deck_score, evidence_score, message_score) // 10,
            "Phase 2D requires stable deck, evidence, and message contracts.",
            [item.code for item in warnings[:8]],
            [] if not warnings else ["Carry warnings into Phase 2D handoff and preserve disclosures."],
        ),
    ]

    raw_score = round(sum(item.score for item in dimensions) / (len(dimensions) * 10) * 100)
    if blocking:
        raw_score = min(raw_score, 69)
    readiness = _readiness(raw_score, len(blocking), len(warnings))
    return AlphaEvaluationResult(
        overall_score=raw_score,
        grade=_grade(raw_score),
        dimensions=dimensions,
        blocking_issue_count=len(blocking),
        warning_count=len(warnings),
        passed_stage_count=cross_validation.passed_stage_count,
        failed_stage_count=cross_validation.failed_stage_count,
        phase2d_readiness_status=readiness,
        note=ALPHA_EVALUATOR_NOTE,
    )
