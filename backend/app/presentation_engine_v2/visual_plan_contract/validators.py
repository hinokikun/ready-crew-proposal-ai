"""Validators for Visual Plan Contract foundation."""

from __future__ import annotations

from .enums import (
    ChartStrategy,
    DiagramStrategy,
    LayoutStrategy,
    ValidationSeverity,
    VisualConfidence,
    VisualPlanStatus,
    VisualReadingOrder,
    VisualStrategy,
)
from .models import VisualPlanContract, VisualPlanItem, VisualValidationIssue, VisualValidationResult
from .rules import (
    CHARTS_REQUIRING_NUMERIC_EVIDENCE,
    DIAGRAM_CHART_CONFLICTS,
    PLACEHOLDER_TOKENS,
    expected_defaults_for_visual_pattern,
    reading_order_allowed,
)


def _issue(
    code: str,
    severity: ValidationSeverity,
    field_path: str,
    message: str,
    suggestion: str,
    *,
    slide_id: str | None = None,
    blocking: bool | None = None,
) -> VisualValidationIssue:
    return VisualValidationIssue(
        code=code,
        severity=severity,
        field_path=field_path,
        message=message,
        suggestion=suggestion,
        related_slide_id=slide_id,
        blocking=severity == ValidationSeverity.ERROR if blocking is None else blocking,
    )


def _has_placeholder_text(*values: str | None) -> bool:
    text = " ".join(str(value or "").lower() for value in values)
    return any(token in text for token in PLACEHOLDER_TOKENS)


def validate_visual_plan_item(item: VisualPlanItem) -> VisualValidationResult:
    issues: list[VisualValidationIssue] = []
    slide_id = item.slide_blueprint_id

    if not item.visual_strategy:
        issues.append(
            _issue(
                "PE2-VISUAL-STRATEGY-001",
                ValidationSeverity.ERROR,
                "visual_strategy",
                "Visual Strategy is not set.",
                "Set a supported Visual Strategy before Phase 3 implementation.",
                slide_id=slide_id,
            )
        )

    defaults = expected_defaults_for_visual_pattern(item.source_visual_pattern_candidate)
    if defaults:
        expected_visual_strategy = defaults.get("visual_strategy")
        if expected_visual_strategy == VisualStrategy.COMPARISON.value and item.visual_strategy != VisualStrategy.COMPARISON:
            issues.append(
                _issue(
                    "PE2-VISUAL-INTENT-001",
                    ValidationSeverity.ERROR,
                    "visual_strategy",
                    "Visual Strategy contradicts the comparison Slide Intent.",
                    "Use a comparison-oriented visual plan or change the upstream Slide Intent.",
                    slide_id=slide_id,
                )
            )
        expected_reading_order = defaults.get("reading_order")
        if expected_reading_order and item.reading_order != expected_reading_order:
            issues.append(
                _issue(
                    "PE2-VISUAL-INTENT-002",
                    ValidationSeverity.WARNING,
                    "reading_order",
                    "Reading order differs from the upstream visual pattern default.",
                    "Confirm the deviation is intentional before Visual Director implementation.",
                    slide_id=slide_id,
                    blocking=False,
                )
            )

    diagram = DiagramStrategy(item.diagram_strategy.strategy)
    chart = ChartStrategy(item.chart_strategy.strategy)
    if diagram != DiagramStrategy.NONE and chart != ChartStrategy.NONE:
        conflict = (diagram, chart) in DIAGRAM_CHART_CONFLICTS
        issues.append(
            _issue(
                "PE2-VISUAL-VISUAL-CONFLICT-001",
                ValidationSeverity.ERROR if conflict else ValidationSeverity.WARNING,
                "diagram_strategy",
                "Diagram and Chart strategies are both selected for one slide.",
                "Select one primary visual representation or explicitly downgrade one to a supporting component.",
                slide_id=slide_id,
                blocking=conflict,
            )
        )

    if chart in CHARTS_REQUIRING_NUMERIC_EVIDENCE and not item.chart_strategy.numeric_evidence_ids:
        issues.append(
            _issue(
                "PE2-VISUAL-EVIDENCE-001",
                ValidationSeverity.ERROR,
                "chart_strategy.numeric_evidence_ids",
                "Chart strategy requires numeric evidence, but no numeric evidence ids are linked.",
                "Use a non-chart visual or connect numeric evidence from Message Designer.",
                slide_id=slide_id,
            )
        )

    if chart in CHARTS_REQUIRING_NUMERIC_EVIDENCE and item.chart_strategy.blocked_by_missing_numeric_evidence:
        issues.append(
            _issue(
                "PE2-VISUAL-EVIDENCE-002",
                ValidationSeverity.ERROR,
                "chart_strategy.blocked_by_missing_numeric_evidence",
                "Chart strategy is selected while numeric evidence is marked missing.",
                "Keep the slide in evidence-gap mode until the numeric basis is confirmed.",
                slide_id=slide_id,
            )
        )

    if not item.visual_priority.primary_element:
        issues.append(
            _issue(
                "PE2-VISUAL-PRIORITY-001",
                ValidationSeverity.ERROR,
                "visual_priority.primary_element",
                "Primary visual priority is empty.",
                "Set the single most important element for this slide.",
                slide_id=slide_id,
            )
        )

    if item.visual_priority.primary_element in item.visual_priority.muted_elements:
        issues.append(
            _issue(
                "PE2-VISUAL-PRIORITY-002",
                ValidationSeverity.ERROR,
                "visual_priority",
                "The same element is marked as primary and muted.",
                "Keep a clear information hierarchy with one primary element.",
                slide_id=slide_id,
            )
        )

    layout = LayoutStrategy(item.layout_strategy)
    reading_order = VisualReadingOrder(item.reading_order)
    if not reading_order_allowed(layout, reading_order):
        issues.append(
            _issue(
                "PE2-VISUAL-READING-001",
                ValidationSeverity.ERROR,
                "reading_order",
                "Reading order contradicts the selected layout strategy.",
                "Use a reading order supported by the layout strategy.",
                slide_id=slide_id,
            )
        )

    if diagram != DiagramStrategy.NONE and item.diagram_strategy.blocked_by_missing_evidence:
        issues.append(
            _issue(
                "PE2-VISUAL-EVIDENCE-003",
                ValidationSeverity.ERROR,
                "diagram_strategy.blocked_by_missing_evidence",
                "Diagram strategy is selected while required evidence is missing.",
                "Keep this as a risk flag or choose a non-evidence visual.",
                slide_id=slide_id,
            )
        )

    for component in item.component_candidates:
        if not component.placeholder_allowed and _has_placeholder_text(
            component.purpose,
            component.renderer_hint,
            component.source_field,
        ):
            issues.append(
                _issue(
                    "PE2-VISUAL-PLACEHOLDER-001",
                    ValidationSeverity.ERROR,
                    "component_candidates",
                    "A non-placeholder component contains placeholder-like text.",
                    "Remove TODO, template tokens, or dummy wording before Phase 3 implementation.",
                    slide_id=slide_id,
                )
            )

    if _has_placeholder_text(item.rationale, item.visual_priority.rationale):
        issues.append(
            _issue(
                "PE2-VISUAL-PLACEHOLDER-002",
                ValidationSeverity.ERROR,
                "rationale",
                "Placeholder-like text was detected in Visual Plan rationale.",
                "Use a concrete design reason tied to Slide Intent and evidence.",
                slide_id=slide_id,
            )
        )

    if (
        item.generated_blueprint
        or item.generated_theme
        or item.generated_coordinates
        or item.generated_diagram
        or item.generated_chart
        or item.generated_pptx
        or item.connected_to_runtime
    ):
        issues.append(
            _issue(
                "PE2-VISUAL-BOUNDARY-001",
                ValidationSeverity.ERROR,
                "generation_boundary",
                "Visual Plan Contract crossed the Phase 3 preparation boundary.",
                "Do not generate blueprint, theme, coordinates, diagrams, charts, PPTX, or runtime connections here.",
                slide_id=slide_id,
            )
        )

    if item.confidence == VisualConfidence.HIGH and item.risk_flags:
        issues.append(
            _issue(
                "PE2-VISUAL-CONFIDENCE-001",
                ValidationSeverity.WARNING,
                "confidence",
                "Confidence is high even though risk flags are present.",
                "Lower confidence or resolve risk flags before using the plan downstream.",
                slide_id=slide_id,
                blocking=False,
            )
        )

    valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
    return VisualValidationResult(
        valid=valid,
        status=VisualPlanStatus.VALIDATED if valid else VisualPlanStatus.BLOCKED,
        issues=issues,
    )


def validate_visual_plan_contract(contract: VisualPlanContract) -> VisualValidationResult:
    issues: list[VisualValidationIssue] = []
    seen: set[str] = set()

    for item in contract.visual_plan:
        if item.slide_blueprint_id in seen:
            issues.append(
                _issue(
                    "PE2-VISUAL-REFERENCE-001",
                    ValidationSeverity.ERROR,
                    "visual_plan.slide_blueprint_id",
                    "Duplicate Visual Plan slide reference detected.",
                    "Each slide must have exactly one Visual Plan item.",
                    slide_id=item.slide_blueprint_id,
                )
            )
        seen.add(item.slide_blueprint_id)
        if item.deck_id != contract.deck_id:
            issues.append(
                _issue(
                    "PE2-VISUAL-REFERENCE-002",
                    ValidationSeverity.ERROR,
                    "visual_plan.deck_id",
                    "Visual Plan item deck_id differs from the contract deck_id.",
                    "Keep all Visual Plan items attached to the same Deck Blueprint.",
                    slide_id=item.slide_blueprint_id,
                )
            )
        issues.extend(validate_visual_plan_item(item).issues)

    orders = [item.slide_order for item in contract.visual_plan]
    if orders != sorted(orders):
        issues.append(
            _issue(
                "PE2-VISUAL-ORDER-001",
                ValidationSeverity.ERROR,
                "visual_plan.slide_order",
                "Visual Plan item order is not stable.",
                "Keep Visual Plan order aligned with Slide Intent order.",
            )
        )

    if (
        contract.generated_blueprint
        or contract.generated_theme
        or contract.generated_coordinates
        or contract.generated_diagram
        or contract.generated_chart
        or contract.generated_pptx
        or contract.connected_to_runtime
    ):
        issues.append(
            _issue(
                "PE2-VISUAL-BOUNDARY-002",
                ValidationSeverity.ERROR,
                "contract_generation_boundary",
                "Visual Plan Contract includes downstream generated artifacts.",
                "Phase 3 preparation must remain contract-only.",
            )
        )

    valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
    return VisualValidationResult(
        valid=valid,
        status=VisualPlanStatus.VALIDATED if valid else VisualPlanStatus.BLOCKED,
        issues=issues,
    )
