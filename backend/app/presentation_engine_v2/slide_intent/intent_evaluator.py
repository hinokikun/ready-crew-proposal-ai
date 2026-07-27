"""Offline evaluator for Phase 2D Slide Intent."""

from __future__ import annotations

from .intent_enums import ChartCandidate, DiagramCandidate, InformationDensity, IntentConfidence, ValidationSeverity
from .intent_models import (
    IntentEvaluationDimension,
    IntentEvaluationResult,
    SlideIntentDesign,
    SlideIntentOutput,
)
from .intent_validators import validate_slide_intent_design, validate_slide_intent_output


INTENT_EVALUATOR_NOTE = (
    "This score evaluates Slide Intent readiness only. It does not evaluate Slide Blueprint generation, "
    "layout, diagram rendering, chart rendering, typography, theme, PPTX output, API behavior, or sales outcome."
)


def _dimension(
    name: str,
    score: int,
    reason: str,
    issues: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> IntentEvaluationDimension:
    return IntentEvaluationDimension(
        name=name,
        score=max(0, min(10, score)),
        reason=reason,
        issues=issues or [],
        recommendations=recommendations or [],
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


def _codes(design: SlideIntentDesign, severity: str | None = None) -> list[str]:
    result = validate_slide_intent_design(design)
    if severity is None:
        return [item.code for item in result.issues]
    return [item.code for item in result.issues if item.severity == severity]


def evaluate_slide_intent_design(design: SlideIntentDesign) -> IntentEvaluationResult:
    result = validate_slide_intent_design(design)
    errors = [item.code for item in result.issues if item.severity == ValidationSeverity.ERROR.value]
    warnings = [item.code for item in result.issues if item.severity == ValidationSeverity.WARNING.value]
    density = design.information_priority.density
    has_visual = design.visual_pattern_candidate != "text_dominant" or design.diagram_candidate != DiagramCandidate.NONE
    has_diagram_or_chart = design.diagram_candidate != DiagramCandidate.NONE or design.chart_candidate != ChartCandidate.NONE
    missing = design.input_metrics.missing_evidence_count

    dimensions = [
        _dimension(
            "Intent Clarity",
            10 if not errors and design.slide_intent else 5,
            "Slide Intent must say what the viewer should understand or decide.",
            errors[:6],
            [] if not errors else ["Resolve blocking Slide Intent validation errors."],
        ),
        _dimension(
            "Visual Readiness",
            10 if has_visual else 7,
            "Slide Intent should provide enough abstraction for Visual Director to choose a visual pattern.",
            [],
            [] if has_visual else ["Prefer a visual candidate other than text-dominant when possible."],
        ),
        _dimension(
            "Information Hierarchy",
            10 if density in {InformationDensity.LOW.value, InformationDensity.MEDIUM.value} else 7,
            "Primary focus, secondary points, and muted content should be clearly separated.",
            [str(density)] if density in {InformationDensity.INSUFFICIENT.value, InformationDensity.EXCESSIVE.value} else [],
            [] if density in {InformationDensity.LOW.value, InformationDensity.MEDIUM.value} else ["Compress, split, or confirm content volume."],
        ),
        _dimension(
            "Reading Flow",
            9 if design.reading_order else 5,
            "Reading order should describe how information should be scanned before rendering.",
        ),
        _dimension(
            "Evidence Compatibility",
            max(4, 10 - missing * 2),
            "Visual intent must respect evidence gaps and avoid hiding missing proof.",
            [warning.warning_id for warning in design.warnings[:5]],
            [] if not missing else ["Carry missing evidence warnings into downstream visual review."],
        ),
        _dimension(
            "Message Compatibility",
            10 if design.source_message_design_id and design.information_priority.primary_focus else 5,
            "Intent should be traceable to Message Designer output.",
        ),
        _dimension(
            "Diagram Suitability",
            10 if design.diagram_candidate != DiagramCandidate.NONE or design.visual_pattern_candidate in {"text_dominant", "table"} else 8,
            "Diagram candidate should be selected only when it clarifies the slide purpose.",
        ),
        _dimension(
            "Chart Suitability",
            10
            if design.chart_candidate == ChartCandidate.NONE or design.input_metrics.numeric_claim_count > 0
            else 6,
            "Chart candidate should require numeric evidence and avoid fake numbers.",
            ["chart_without_numeric_claim"] if design.chart_candidate != ChartCandidate.NONE and not design.input_metrics.numeric_claim_count else [],
            [] if design.chart_candidate == ChartCandidate.NONE or design.input_metrics.numeric_claim_count else ["Confirm numeric evidence before chart rendering."],
        ),
        _dimension(
            "Customer-facing Readiness",
            10 if not warnings and design.intent_confidence != IntentConfidence.LOW.value else 8 if not errors else 4,
            "Intent should be safe for customer-facing visual planning.",
            warnings[:6],
            [] if not warnings else ["Resolve warnings or keep them visible in Phase 3 review."],
        ),
    ]
    total = round(sum(item.score for item in dimensions) / (len(dimensions) * 10) * 100)
    return IntentEvaluationResult(
        total_score=total,
        grade=_grade(total),
        dimensions=dimensions,
        blocking_issue_count=len(errors),
        warning_count=len(result.warnings),
        note=INTENT_EVALUATOR_NOTE,
    )


def evaluate_slide_intent_output(output: SlideIntentOutput) -> IntentEvaluationResult:
    validation = validate_slide_intent_output(output)
    if not output.slide_intents:
        return IntentEvaluationResult(
            total_score=0,
            grade="F",
            dimensions=[_dimension("Intent Clarity", 0, "No slide intents were generated.", ["empty output"])],
            blocking_issue_count=1,
            warning_count=0,
            note=INTENT_EVALUATOR_NOTE,
        )
    dimension_names = [
        "Intent Clarity",
        "Visual Readiness",
        "Information Hierarchy",
        "Reading Flow",
        "Evidence Compatibility",
        "Message Compatibility",
        "Diagram Suitability",
        "Chart Suitability",
        "Customer-facing Readiness",
    ]
    per_slide = [item.evaluation_result or evaluate_slide_intent_design(item) for item in output.slide_intents]
    dimensions: list[IntentEvaluationDimension] = []
    for name in dimension_names:
        scores = [
            dimension.score
            for result in per_slide
            for dimension in result.dimensions
            if dimension.name == name
        ]
        average = round(sum(scores) / len(scores)) if scores else 0
        dimensions.append(
            _dimension(
                name,
                average,
                f"Average {name.lower()} across {len(output.slide_intents)} slide intents.",
                [],
                [] if average >= 8 else [f"Review slide intents with low {name}."],
            )
        )
    total = round(sum(item.score for item in dimensions) / (len(dimensions) * 10) * 100)
    return IntentEvaluationResult(
        total_score=total,
        grade=_grade(total),
        dimensions=dimensions,
        blocking_issue_count=len(validation.errors),
        warning_count=len(validation.warnings),
        note=INTENT_EVALUATOR_NOTE,
    )
