"""Validators for Phase 2D Slide Intent."""

from __future__ import annotations

from .intent_enums import (
    ChartCandidate,
    DiagramCandidate,
    InformationDensity,
    IntentConfidence,
    ValidationSeverity,
    VisualPattern,
)
from .intent_models import IntentValidationIssue, IntentValidationResult, SlideIntentDesign, SlideIntentOutput


def _issue(
    code: str,
    severity: ValidationSeverity,
    field_path: str,
    message: str,
    suggestion: str,
    *,
    slide_id: str | None = None,
    blocking: bool | None = None,
) -> IntentValidationIssue:
    return IntentValidationIssue(
        code=code,
        severity=severity,
        field_path=field_path,
        message=message,
        suggestion=suggestion,
        blocking=severity == ValidationSeverity.ERROR if blocking is None else blocking,
        related_slide_id=slide_id,
    )


def validate_slide_intent_design(intent: SlideIntentDesign) -> IntentValidationResult:
    issues: list[IntentValidationIssue] = []
    slide_id = intent.slide_blueprint_id
    if not intent.slide_type:
        issues.append(
            _issue(
                "PE2-INTENT-SLIDE-TYPE-001",
                ValidationSeverity.ERROR,
                "slide_type",
                "Slide type is not set.",
                "Set a supported slide type before Phase 3.",
                slide_id=slide_id,
            )
        )
    if not intent.slide_intent:
        issues.append(
            _issue(
                "PE2-INTENT-TYPE-001",
                ValidationSeverity.ERROR,
                "slide_intent",
                "Slide intent is not set.",
                "Set a supported intent before Phase 3.",
                slide_id=slide_id,
            )
        )
    if intent.diagram_candidate != DiagramCandidate.NONE and intent.chart_candidate != ChartCandidate.NONE:
        issues.append(
            _issue(
                "PE2-INTENT-VISUAL-001",
                ValidationSeverity.WARNING,
                "diagram_candidate",
                "Diagram and chart candidates are both set.",
                "Prefer one primary visual representation before Visual Director.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    if intent.chart_candidate != ChartCandidate.NONE and intent.input_metrics.missing_evidence_count:
        issues.append(
            _issue(
                "PE2-INTENT-CHART-001",
                ValidationSeverity.ERROR,
                "chart_candidate",
                "A chart candidate was selected while evidence is missing.",
                "Use a non-chart visual or collect numeric evidence first.",
                slide_id=slide_id,
            )
        )
    if intent.chart_candidate != ChartCandidate.NONE and intent.input_metrics.numeric_claim_count == 0:
        issues.append(
            _issue(
                "PE2-INTENT-CHART-002",
                ValidationSeverity.WARNING,
                "chart_candidate",
                "A chart candidate was selected without a numeric claim in Message Designer output.",
                "Confirm numeric evidence before rendering a chart.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    if intent.visual_pattern_candidate == VisualPattern.COMPARISON and not intent.input_metrics.comparison_basis_present:
        issues.append(
            _issue(
                "PE2-INTENT-COMPARISON-001",
                ValidationSeverity.ERROR,
                "visual_pattern_candidate",
                "Comparison intent has no comparison basis.",
                "Collect competitor, before/after, current/future, or option comparison evidence.",
                slide_id=slide_id,
            )
        )
    if intent.diagram_candidate in {DiagramCandidate.TIMELINE, DiagramCandidate.ROADMAP} and not intent.input_metrics.time_sequence_present:
        issues.append(
            _issue(
                "PE2-INTENT-TIME-001",
                ValidationSeverity.WARNING,
                "diagram_candidate",
                "Timeline or roadmap candidate has no clear time sequence.",
                "Confirm milestones or timing before Phase 3.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    if intent.diagram_candidate == DiagramCandidate.HIERARCHY_TREE and not intent.input_metrics.hierarchy_basis_present:
        issues.append(
            _issue(
                "PE2-INTENT-HIERARCHY-001",
                ValidationSeverity.WARNING,
                "diagram_candidate",
                "Hierarchy candidate has no clear layers.",
                "Confirm hierarchy, roles, or levels before visual design.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    if intent.visual_pattern_candidate == VisualPattern.CHECKLIST and intent.input_metrics.checklist_item_count < 1:
        issues.append(
            _issue(
                "PE2-INTENT-CHECKLIST-001",
                ValidationSeverity.WARNING,
                "visual_pattern_candidate",
                "Checklist visual may not have enough items.",
                "Add checklist items or use a callout visual.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    if intent.visual_pattern_candidate == VisualPattern.IMAGE_DOMINANT and not intent.input_metrics.image_evidence_present:
        issues.append(
            _issue(
                "PE2-INTENT-IMAGE-001",
                ValidationSeverity.WARNING,
                "visual_pattern_candidate",
                "Image-dominant visual has no image evidence candidate.",
                "Use a placeholder only; do not assume an external image.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    if intent.information_priority.density == InformationDensity.EXCESSIVE:
        issues.append(
            _issue(
                "PE2-INTENT-DENSITY-001",
                ValidationSeverity.WARNING,
                "information_priority.density",
                "Information volume is high for one slide.",
                "Compress, split, or diagramize content before rendering.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    if intent.information_priority.density == InformationDensity.INSUFFICIENT:
        issues.append(
            _issue(
                "PE2-INTENT-DENSITY-002",
                ValidationSeverity.WARNING,
                "information_priority.density",
                "Information volume may be too low for a useful slide.",
                "Confirm the main message and evidence requirements.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    unsafe_text = f"{intent.information_priority.primary_focus} {intent.rendering_hint}".lower()
    if any(token in unsafe_text for token in ("todo", "internal only", "{{", "}}")):
        issues.append(
            _issue(
                "PE2-INTENT-SAFETY-001",
                ValidationSeverity.ERROR,
                "rendering_hint",
                "Placeholder or internal label text was detected.",
                "Remove internal labels before customer-facing visual design.",
                slide_id=slide_id,
            )
        )
    if (
        intent.generated_slide_blueprint
        or intent.generated_diagram
        or intent.generated_chart
        or intent.generated_pptx
        or intent.connected_to_runtime
    ):
        issues.append(
            _issue(
                "PE2-INTENT-BOUNDARY-001",
                ValidationSeverity.ERROR,
                "generation_boundary",
                "Slide Intent crossed the Phase 2D offline boundary.",
                "Do not generate Slide Blueprints, diagrams, charts, PPTX, or runtime connections in Phase 2D.",
                slide_id=slide_id,
            )
        )
    if intent.intent_confidence == IntentConfidence.HIGH and intent.input_metrics.missing_evidence_count:
        issues.append(
            _issue(
                "PE2-INTENT-CONFIDENCE-001",
                ValidationSeverity.WARNING,
                "intent_confidence",
                "Intent confidence is high despite missing evidence.",
                "Lower confidence or collect evidence before Phase 3.",
                slide_id=slide_id,
                blocking=False,
            )
        )
    return IntentValidationResult(valid=not any(item.severity == ValidationSeverity.ERROR for item in issues), issues=issues)


def validate_slide_intent_output(output: SlideIntentOutput) -> IntentValidationResult:
    issues: list[IntentValidationIssue] = []
    seen: set[str] = set()
    for design in output.slide_intents:
        if design.slide_blueprint_id in seen:
            issues.append(
                _issue(
                    "PE2-INTENT-REFERENCE-001",
                    ValidationSeverity.ERROR,
                    "slide_intents.slide_blueprint_id",
                    "Duplicate slide intent reference detected.",
                    "Each slide must have exactly one Slide Intent.",
                    slide_id=design.slide_blueprint_id,
                )
            )
        seen.add(design.slide_blueprint_id)
        issues.extend(validate_slide_intent_design(design).issues)
    orders = [item.slide_order for item in output.slide_intents]
    if orders != sorted(orders):
        issues.append(
            _issue(
                "PE2-INTENT-ORDER-001",
                ValidationSeverity.ERROR,
                "slide_intents.slide_order",
                "Slide Intent order is not stable.",
                "Keep the same order as Deck Blueprint and Message Designer output.",
            )
        )
    if output.generated_slide_blueprints or output.generated_diagrams or output.generated_charts or output.generated_pptx:
        issues.append(
            _issue(
                "PE2-INTENT-BOUNDARY-002",
                ValidationSeverity.ERROR,
                "output_generation_boundary",
                "Slide Intent output includes generated downstream artifacts.",
                "Phase 2D must remain intent-only.",
            )
        )
    return IntentValidationResult(valid=not any(item.severity == ValidationSeverity.ERROR for item in issues), issues=issues)
