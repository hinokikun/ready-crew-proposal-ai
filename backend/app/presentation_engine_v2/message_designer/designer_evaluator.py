"""Offline evaluator for Phase 2C message designs."""

from __future__ import annotations

from .designer_enums import EvidenceAlignmentLevel, MessageValidationSeverity
from .designer_models import (
    MessageDesignerOutput,
    MessageEvaluationDimension,
    MessageEvaluationResult,
    SlideMessageDesign,
)
from .designer_validators import validate_message_designer_output, validate_slide_message_design


MESSAGE_EVALUATOR_NOTE = (
    "This score evaluates message design readiness only. It does not evaluate "
    "Slide Blueprints, diagrams, layouts, theme tokens, typography, PPTX rendering, "
    "Beautiful.ai output, or final sales outcome."
)


def _dimension(
    name: str,
    score: int,
    reason: str,
    issues: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> MessageEvaluationDimension:
    return MessageEvaluationDimension(
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


def _issue_codes(design: SlideMessageDesign, severity: str | None = None) -> list[str]:
    result = validate_slide_message_design(design)
    if severity is None:
        return [item.code for item in result.issues]
    return [item.code for item in result.issues if item.severity == severity]


def _score_contract(design: SlideMessageDesign) -> MessageEvaluationDimension:
    result = validate_slide_message_design(design)
    errors = [item.code for item in result.issues if item.severity == MessageValidationSeverity.ERROR.value]
    score = 10 if not errors else max(0, 10 - len(errors) * 3)
    return _dimension(
        "Contract Validity",
        score,
        "Message output must satisfy the Phase 2C schema and validation contract.",
        errors,
        [] if score == 10 else ["Fix blocking schema or validation errors before downstream use."],
    )


def _score_headline(design: SlideMessageDesign) -> MessageEvaluationDimension:
    issues = _issue_codes(design)
    score = 10
    if "PE2-MSG-HEADLINE-001" in issues:
        score = 2
    elif "PE2-MSG-HEADLINE-002" in issues:
        score = 5
    elif "PE2-MSG-HEADLINE-003" in issues:
        score = 7
    elif len(design.headline) > 48:
        score = 8
    return _dimension(
        "Headline Quality",
        score,
        "Headline should state a conclusion or decision implication within 60 characters.",
        [code for code in issues if code.startswith("PE2-MSG-HEADLINE")],
        [] if score >= 8 else ["Rewrite headline as a short claim, not a noun-only section label."],
    )


def _score_message_clarity(design: SlideMessageDesign) -> MessageEvaluationDimension:
    duplicate = design.headline.strip() in {design.main_message.strip(), design.key_takeaway.strip()}
    support_count = len(design.supporting_messages)
    score = 10
    if duplicate:
        score -= 2
    if len(design.main_message) > 105:
        score -= 1
    if support_count == 0:
        score -= 2
    return _dimension(
        "Message Clarity",
        score,
        "Main message, supporting points, and takeaway should each have distinct roles.",
        ["duplicated message fields"] if duplicate else [],
        [] if score >= 8 else ["Clarify the main message and add concise supporting points."],
    )


def _score_one_message(design: SlideMessageDesign) -> MessageEvaluationDimension:
    support_count = len(design.supporting_messages)
    score = 10 if support_count <= 3 else 6
    if len(design.unsupported_claims) > 2:
        score -= 2
    return _dimension(
        "One-slide-one-message",
        score,
        "A slide should retain one core message and no more than three support points.",
        [],
        [] if score >= 8 else ["Split or reduce claims before Slide Blueprint generation."],
    )


def _score_evidence_alignment(design: SlideMessageDesign) -> MessageEvaluationDimension:
    level = design.evidence_alignment_level
    score_by_level = {
        EvidenceAlignmentLevel.EVIDENCE_SUPPORTED.value: 10,
        EvidenceAlignmentLevel.PARTIALLY_SUPPORTED.value: 8,
        EvidenceAlignmentLevel.ASSUMPTION_REQUIRED.value: 7,
        EvidenceAlignmentLevel.NOT_APPLICABLE.value: 8,
        EvidenceAlignmentLevel.EVIDENCE_MISSING.value: 4,
    }
    score = score_by_level.get(level, 5)
    if design.unsupported_claims:
        score = max(3, score - 2)
    return _dimension(
        "Evidence Alignment",
        score,
        "Message strength should match available Evidence Planner requirements.",
        [claim.claim_id for claim in design.unsupported_claims],
        [] if score >= 8 else ["Collect or disclose missing evidence before using stronger claims."],
    )


def _score_numeric_integrity(design: SlideMessageDesign) -> MessageEvaluationDimension:
    unsupported = [claim.claim_id for claim in design.numeric_claims if not claim.basis_evidence_ids]
    score = 10 if not unsupported else 3
    if design.numeric_claims and any(not claim.is_trial_calculation for claim in design.numeric_claims):
        score -= 1
    return _dimension(
        "Numeric Integrity Readiness",
        score,
        "Numeric, ROI, ratio, currency, and period claims require traceable basis evidence.",
        unsupported,
        [] if score >= 8 else ["Attach basis evidence or remove the numeric claim."],
    )


def _score_narrative_consistency(design: SlideMessageDesign) -> MessageEvaluationDimension:
    score = 9
    if not design.narrative_function or not design.slide_goal:
        score = 6
    if design.slide_role == "closing" and "次" not in design.key_takeaway:
        score -= 1
    return _dimension(
        "Narrative Consistency",
        score,
        "Message should respect Deck Blueprint slide role, slide goal, and narrative function.",
        [],
        [] if score >= 8 else ["Align the message with the Deck Planner narrative role."],
    )


def _score_audience_fit(design: SlideMessageDesign) -> MessageEvaluationDimension:
    score = 9
    if design.audience_seniority == "executive" and len(design.supporting_messages) > 2:
        score -= 1
    if design.message_style == "technical" and design.audience_seniority == "executive":
        score -= 2
    return _dimension(
        "Audience Fit",
        score,
        "Style and detail level should match audience seniority and decision stage.",
        [],
        [] if score >= 8 else ["Reduce technical detail or shift to decision language."],
    )


def _score_decision_relevance(design: SlideMessageDesign) -> MessageEvaluationDimension:
    decision_words = ("判断", "合意", "確認", "決め", "次")
    text = f"{design.headline} {design.main_message} {design.key_takeaway}"
    score = 10 if any(word in text for word in decision_words) else 7
    return _dimension(
        "Decision Relevance",
        score,
        "Customer-facing proposal messages should help the next decision.",
        [],
        [] if score >= 8 else ["Make the decision implication or next action explicit."],
    )


def _score_readability(design: SlideMessageDesign) -> MessageEvaluationDimension:
    issues = _issue_codes(design)
    unsafe = [
        code
        for code in issues
        if code
        in {
            "PE2-MSG-PLACEHOLDER-001",
            "PE2-MSG-SAFETY-001",
            "PE2-MSG-QUALITY-001",
            "PE2-MSG-QUALITY-002",
        }
    ]
    score = 10 if not unsafe else max(4, 10 - len(unsafe) * 2)
    return _dimension(
        "Customer-facing Readability",
        score,
        "Messages should avoid placeholders, internal labels, and vague language.",
        unsafe,
        [] if score >= 8 else ["Remove placeholders/internal wording and make abstract claims concrete."],
    )


def _score_executive_readiness(design: SlideMessageDesign) -> MessageEvaluationDimension:
    score = 8
    if design.message_style in {"executive", "strategic", "financial", "consulting"}:
        score += 1
    if design.evidence_alignment_level == EvidenceAlignmentLevel.EVIDENCE_MISSING.value:
        score -= 2
    return _dimension(
        "Executive Readiness",
        score,
        "Executive-ready messages separate conclusion, evidence, risk, and next action.",
        [],
        [] if score >= 8 else ["Reduce unsupported certainty and add decision-ready evidence."],
    )


def _score_sales_persuasiveness(design: SlideMessageDesign) -> MessageEvaluationDimension:
    score = 8
    if design.supporting_messages:
        score += 1
    if design.warnings:
        score -= 1
    if design.evidence_usage:
        score += 1
    return _dimension(
        "Sales Persuasiveness",
        score,
        "Message should be useful for a sales conversation while remaining evidence-safe.",
        [warning.warning_id for warning in design.warnings[:4]],
        [] if score >= 8 else ["Confirm missing evidence, then strengthen support points."],
    )


def evaluate_slide_message_design(design: SlideMessageDesign) -> MessageEvaluationResult:
    dimensions = [
        _score_contract(design),
        _score_headline(design),
        _score_message_clarity(design),
        _score_one_message(design),
        _score_evidence_alignment(design),
        _score_numeric_integrity(design),
        _score_narrative_consistency(design),
        _score_audience_fit(design),
        _score_decision_relevance(design),
        _score_readability(design),
        _score_executive_readiness(design),
        _score_sales_persuasiveness(design),
    ]
    total = round(sum(item.score for item in dimensions) / (len(dimensions) * 10) * 100)
    result = validate_slide_message_design(design)
    return MessageEvaluationResult(
        total_score=total,
        grade=_grade(total),
        dimensions=dimensions,
        blocking_issue_count=len(result.errors),
        warning_count=len(result.warnings),
        note=MESSAGE_EVALUATOR_NOTE,
    )


def evaluate_message_designer_output(output: MessageDesignerOutput) -> MessageEvaluationResult:
    validation = validate_message_designer_output(output)
    if not output.slide_messages:
        dimensions = [_dimension("Contract Validity", 0, "No slide messages were generated.", ["empty output"])]
        return MessageEvaluationResult(
            total_score=0,
            grade="D",
            dimensions=dimensions,
            blocking_issue_count=1,
            warning_count=0,
            note=MESSAGE_EVALUATOR_NOTE,
        )

    dimension_names = [
        "Contract Validity",
        "Headline Quality",
        "Message Clarity",
        "One-slide-one-message",
        "Evidence Alignment",
        "Numeric Integrity Readiness",
        "Narrative Consistency",
        "Audience Fit",
        "Decision Relevance",
        "Customer-facing Readability",
        "Executive Readiness",
        "Sales Persuasiveness",
    ]
    per_slide = [item.evaluation_result or evaluate_slide_message_design(item) for item in output.slide_messages]
    aggregate_dimensions: list[MessageEvaluationDimension] = []
    for name in dimension_names:
        scores = [
            dimension.score
            for result in per_slide
            for dimension in result.dimensions
            if dimension.name == name
        ]
        average = round(sum(scores) / len(scores)) if scores else 0
        aggregate_dimensions.append(
            _dimension(
                name,
                average,
                f"Average {name.lower()} across {len(output.slide_messages)} slide messages.",
                [],
                [] if average >= 8 else [f"Review low-scoring slides for {name}."],
            )
        )
    total = round(sum(item.score for item in aggregate_dimensions) / (len(aggregate_dimensions) * 10) * 100)
    return MessageEvaluationResult(
        total_score=total,
        grade=_grade(total),
        dimensions=aggregate_dimensions,
        blocking_issue_count=len(validation.errors),
        warning_count=len(validation.warnings),
        note=MESSAGE_EVALUATOR_NOTE,
    )
