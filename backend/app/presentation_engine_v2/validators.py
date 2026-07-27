"""Semantic validators for Presentation Engine 2.0 slide blueprints."""

from __future__ import annotations

from typing import Any, Iterable, List, Sequence

from pydantic import ValidationError as PydanticValidationError

from .contracts import (
    CUSTOMER_PLACEHOLDER_LABELS,
    GOAL_VISUAL_REQUIREMENTS,
    LIMITS,
    VISUAL_DIAGRAM_COMPATIBILITY,
)
from .enums import (
    BlueprintStatus,
    CTAType,
    DiagramType,
    SlideGoal,
    ValidationSeverity,
    VisualType,
)
from .errors import ErrorCode, SUPPORTED_BLUEPRINT_VERSION
from .models import SlideBlueprint, ValidationIssue, ValidationResult
from .normalizers import normalize_blueprint_dict


def _issue(
    code: str,
    severity: ValidationSeverity,
    field_path: str,
    message: str,
    suggestion: str,
    *,
    blocking: bool | None = None,
    source: str = "validator",
) -> ValidationIssue:
    is_blocking = severity == ValidationSeverity.ERROR if blocking is None else blocking
    safe_message = message if len(message) <= 260 else f"{message[:240]}..."
    safe_suggestion = suggestion if len(suggestion) <= 260 else f"{suggestion[:240]}..."
    return ValidationIssue(
        code=code,
        severity=severity,
        field_path=field_path,
        message=safe_message,
        suggestion=safe_suggestion,
        blocking=is_blocking,
        source=source,
    )


def _pydantic_issues(error: PydanticValidationError) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for item in error.errors():
        field_path = ".".join(str(part) for part in item.get("loc", ("payload",)))
        msg = str(item.get("msg", "Invalid field"))
        err_type = str(item.get("type", ""))
        code = ErrorCode.SCHEMA_REQUIRED
        if "enum" in err_type:
            code = ErrorCode.SCHEMA_ENUM
        elif "max_length" in err_type or "min_length" in err_type:
            code = ErrorCode.SCHEMA_LENGTH
        issues.append(
            _issue(
                code,
                ValidationSeverity.ERROR,
                field_path,
                msg,
                "Fix the field so it matches the Slide Blueprint schema.",
                source="schema",
            )
        )
    return issues


def _duplicate_values(values: Iterable[str]) -> list[str]:
    seen = set()
    duplicates = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return duplicates


def _contains_placeholder(text: str | None) -> bool:
    normalized = str(text or "").strip().lower()
    if not normalized:
        return False
    return normalized in CUSTOMER_PLACEHOLDER_LABELS


def _add_duplicate_id_issue(issues: list[ValidationIssue], field_path: str, ids: Sequence[str]) -> None:
    duplicates = _duplicate_values([item for item in ids if item])
    if duplicates:
        issues.append(
            _issue(
                ErrorCode.SCHEMA_DUPLICATE_ID,
                ValidationSeverity.ERROR,
                field_path,
                f"Duplicate IDs detected: {', '.join(duplicates)}",
                "Use stable unique IDs within the slide blueprint.",
            )
        )


def _validate_common(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> None:
    if blueprint.blueprint_version != SUPPORTED_BLUEPRINT_VERSION:
        issues.append(
            _issue(
                ErrorCode.SCHEMA_REQUIRED,
                ValidationSeverity.ERROR,
                "blueprint_version",
                "Unsupported blueprint version.",
                f"Use {SUPPORTED_BLUEPRINT_VERSION}.",
            )
        )
    if not blueprint.headline.strip():
        issues.append(
            _issue(
                ErrorCode.MESSAGE_EMPTY,
                ValidationSeverity.ERROR,
                "headline",
                "Headline must not be empty.",
                "Add a customer-facing headline.",
            )
        )
    if _contains_placeholder(blueprint.headline):
        issues.append(
            _issue(
                ErrorCode.MESSAGE_PLACEHOLDER,
                ValidationSeverity.ERROR,
                "headline",
                "Headline contains an internal placeholder label.",
                "Replace it with a customer-facing Japanese headline.",
            )
        )
    if _contains_placeholder(blueprint.main_message):
        issues.append(
            _issue(
                ErrorCode.MESSAGE_PLACEHOLDER,
                ValidationSeverity.ERROR,
                "main_message",
                "Main message contains an internal placeholder label.",
                "Replace it with a meaningful proposal message.",
            )
        )
    for index, message in enumerate(blueprint.supporting_messages):
        if _contains_placeholder(message):
            issues.append(
                _issue(
                    ErrorCode.MESSAGE_PLACEHOLDER,
                    ValidationSeverity.ERROR,
                    f"supporting_messages[{index}]",
                    "Supporting message contains an internal placeholder label.",
                    "Use customer-facing text.",
                )
            )

    _add_duplicate_id_issue(issues, "content_blocks.block_id", [block.block_id for block in blueprint.content_blocks])
    _add_duplicate_id_issue(issues, "metrics.metric_id", [metric.metric_id for metric in blueprint.metrics])
    _add_duplicate_id_issue(
        issues,
        "comparison_items.item_id",
        [item.item_id for item in blueprint.comparison_items],
    )
    _add_duplicate_id_issue(issues, "timeline_items.item_id", [item.item_id for item in blueprint.timeline_items])
    _add_duplicate_id_issue(issues, "process_steps.step_id", [step.step_id for step in blueprint.process_steps])
    _add_duplicate_id_issue(
        issues,
        "supporting_evidence.evidence_id",
        [evidence.evidence_id for evidence in blueprint.supporting_evidence],
    )
    _add_duplicate_id_issue(
        issues,
        "source_references.source_id",
        [source.source_id for source in blueprint.source_references],
    )

    reading_duplicates = _duplicate_values(blueprint.reading_order)
    if reading_duplicates:
        issues.append(
            _issue(
                ErrorCode.SCHEMA_DUPLICATE_ID,
                ValidationSeverity.WARNING,
                "reading_order",
                f"Reading order has duplicate entries: {', '.join(reading_duplicates)}",
                "Keep each reading-order target unique.",
            )
        )


def _validate_visual(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> None:
    compatible = VISUAL_DIAGRAM_COMPATIBILITY.get(blueprint.visual_type, {DiagramType.NONE.value})
    if blueprint.diagram_type not in compatible:
        issues.append(
            _issue(
                ErrorCode.VISUAL_MISMATCH,
                ValidationSeverity.ERROR,
                "diagram_type",
                f"{blueprint.diagram_type} is not compatible with visual_type={blueprint.visual_type}.",
                "Choose a compatible diagram type or set diagram_type=none.",
            )
        )

    required = GOAL_VISUAL_REQUIREMENTS.get(blueprint.slide_goal)
    if required == "comparison_items" and len(blueprint.comparison_items) < 2:
        issues.append(
            _issue(
                ErrorCode.VISUAL_MISSING_DATA,
                ValidationSeverity.ERROR,
                "comparison_items",
                "Comparison slides require at least two comparison items.",
                "Add the compared options, states, or vendors.",
            )
        )
    if required == "timeline_items" and not blueprint.timeline_items:
        issues.append(
            _issue(
                ErrorCode.VISUAL_MISSING_DATA,
                ValidationSeverity.ERROR,
                "timeline_items",
                "Timeline or roadmap slides require timeline items.",
                "Add phases, periods, or milestones.",
            )
        )
    if required == "process_steps" and not blueprint.process_steps:
        issues.append(
            _issue(
                ErrorCode.VISUAL_MISSING_DATA,
                ValidationSeverity.ERROR,
                "process_steps",
                "Process slides require process steps.",
                "Add the steps and outputs.",
            )
        )
    if required == "metrics" and not blueprint.metrics:
        issues.append(
            _issue(
                ErrorCode.VISUAL_MISSING_DATA,
                ValidationSeverity.ERROR,
                "metrics",
                "Metric-oriented slides require at least one metric.",
                "Add a metric value or mark the value as pending review.",
            )
        )
    if blueprint.visual_type == VisualType.TABLE.value:
        if not blueprint.table_data or not blueprint.table_data.columns or not blueprint.table_data.rows:
            issues.append(
                _issue(
                    ErrorCode.VISUAL_MISSING_DATA,
                    ValidationSeverity.ERROR,
                    "table_data",
                    "Table visual type requires table columns and rows.",
                    "Add renderer-ready table data.",
                )
            )
    if blueprint.visual_type == VisualType.MATRIX_2X2.value or blueprint.diagram_type == DiagramType.MATRIX_2X2.value:
        if len(blueprint.diagram_definition.axes) < 2:
            issues.append(
                _issue(
                    ErrorCode.VISUAL_MISSING_DATA,
                    ValidationSeverity.ERROR,
                    "diagram_definition.axes",
                    "Matrix slides require at least two axis definitions.",
                    "Define x-axis and y-axis labels for the matrix.",
                )
            )
    if blueprint.visual_type == VisualType.CHART.value and not blueprint.chart_requirement.required:
        issues.append(
            _issue(
                ErrorCode.VISUAL_MISSING_DATA,
                ValidationSeverity.WARNING,
                "chart_requirement",
                "Chart visual type should include chart requirements.",
                "Define chart type and data source.",
            )
        )


def _validate_message_quality(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> None:
    if blueprint.headline.strip() == blueprint.main_message.strip():
        issues.append(
            _issue(
                ErrorCode.MESSAGE_OVERLAP,
                ValidationSeverity.WARNING,
                "main_message",
                "Headline and main message are identical.",
                "Use the headline as the conclusion and main_message as its support.",
            )
        )
    content_weight = len(blueprint.content_blocks) + len(blueprint.supporting_messages)
    if content_weight > 10:
        issues.append(
            _issue(
                ErrorCode.QUALITY_ONE_MESSAGE,
                ValidationSeverity.WARNING,
                "content_blocks",
                "The slide may contain too many message fragments.",
                "Compress, split, or diagramize the slide.",
            )
        )
    if blueprint.slide_goal == SlideGoal.NEXT_ACTION.value and blueprint.cta.cta_type == CTAType.NONE.value:
        issues.append(
            _issue(
                ErrorCode.QUALITY_CTA_MISSING,
                ValidationSeverity.ERROR,
                "cta",
                "Next action slides require a CTA.",
                "Set cta_type and cta_label.",
            )
        )


def _validate_rendering_safety(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> None:
    if blueprint.body_style.font_size_pt < 12:
        issues.append(
            _issue(
                ErrorCode.LAYOUT_OVERFLOW,
                ValidationSeverity.ERROR,
                "body_style.font_size_pt",
                "Body font size is too small for an editable proposal slide.",
                "Use 17 pt or higher for main-deck body text.",
            )
        )
    elif blueprint.body_style.font_size_pt < LIMITS["body_font_floor_pt"]:
        issues.append(
            _issue(
                ErrorCode.LAYOUT_OVERFLOW,
                ValidationSeverity.WARNING,
                "body_style.font_size_pt",
                "Body font size is below the recommended proposal floor.",
                "Use 17 pt or higher for main-deck body text.",
            )
        )
    if blueprint.title_style.font_size_pt < LIMITS["headline_font_floor_pt"]:
        issues.append(
            _issue(
                ErrorCode.LAYOUT_OVERFLOW,
                ValidationSeverity.WARNING,
                "title_style.font_size_pt",
                "Headline font size is below the recommended floor.",
                "Use 28 pt or higher for headline text.",
            )
        )
    if blueprint.safe_area.x + blueprint.safe_area.w > 1.0 or blueprint.safe_area.y + blueprint.safe_area.h > 1.0:
        issues.append(
            _issue(
                ErrorCode.LAYOUT_SAFE_AREA,
                ValidationSeverity.ERROR,
                "safe_area",
                "Safe area exceeds slide bounds.",
                "Keep x+w and y+h within 1.0.",
            )
        )
    if len(blueprint.content_blocks) > LIMITS["max_cards"] and blueprint.density == "high":
        issues.append(
            _issue(
                ErrorCode.LAYOUT_OVERFLOW,
                ValidationSeverity.WARNING,
                "content_blocks",
                "High-density card content may overflow.",
                "Split or reduce the number of cards.",
            )
        )
    if blueprint.table_data:
        if len(blueprint.table_data.columns) > LIMITS["table_columns"]:
            issues.append(
                _issue(
                    ErrorCode.LAYOUT_OVERFLOW,
                    ValidationSeverity.ERROR,
                    "table_data.columns",
                    "Table has too many columns for a main proposal slide.",
                    "Use at most five columns or move detail to appendix.",
                )
            )
        if len(blueprint.table_data.rows) > LIMITS["table_rows"]:
            issues.append(
                _issue(
                    ErrorCode.LAYOUT_OVERFLOW,
                    ValidationSeverity.WARNING,
                    "table_data.rows",
                    "Table may be too dense for a main proposal slide.",
                    "Reduce rows or split the content.",
                )
            )


def _validate_numeric_integrity(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> None:
    metric_oriented = blueprint.slide_goal in {
        SlideGoal.ROI_EXPLANATION.value,
        SlideGoal.KPI_DEFINITION.value,
        SlideGoal.ESTIMATE.value,
        SlideGoal.PRICING.value,
    }
    if metric_oriented and not blueprint.metrics:
        issues.append(
            _issue(
                ErrorCode.SAFETY_NUMERIC_EVIDENCE,
                ValidationSeverity.ERROR,
                "metrics",
                "Metric-oriented slide lacks numeric or status metric blocks.",
                "Add metrics with source or mark them as assumptions.",
            )
        )
    for index, metric in enumerate(blueprint.metrics):
        if not metric.evidence_id and metric.confidence in {"low", "unknown"}:
            issues.append(
                _issue(
                    ErrorCode.SAFETY_NUMERIC_EVIDENCE,
                    ValidationSeverity.WARNING,
                    f"metrics[{index}]",
                    "Metric has low confidence and no evidence reference.",
                    "Attach evidence or mark the value as pending confirmation.",
                )
            )


def validate_blueprint(payload: SlideBlueprint | dict[str, Any], *, normalize: bool = False) -> ValidationResult:
    """Validate schema and business quality rules for one slide blueprint."""

    issues: list[ValidationIssue] = []
    blueprint: SlideBlueprint | None = None
    try:
        data = payload
        if normalize and isinstance(payload, dict):
            data, _changed = normalize_blueprint_dict(payload)
        blueprint = payload if isinstance(payload, SlideBlueprint) else SlideBlueprint.parse_obj(data)
    except PydanticValidationError as error:
        issues.extend(_pydantic_issues(error))
        return ValidationResult(valid=False, status=BlueprintStatus.INVALID, issues=issues)

    _validate_common(blueprint, issues)
    _validate_visual(blueprint, issues)
    _validate_message_quality(blueprint, issues)
    _validate_rendering_safety(blueprint, issues)
    _validate_numeric_integrity(blueprint, issues)

    has_errors = any(issue.severity == ValidationSeverity.ERROR.value for issue in issues)
    has_warnings = any(issue.severity == ValidationSeverity.WARNING.value for issue in issues)
    status = BlueprintStatus.INVALID if has_errors else BlueprintStatus.NEEDS_REVIEW if has_warnings else BlueprintStatus.READY_FOR_RENDER
    return ValidationResult(valid=not has_errors, status=status, issues=issues)
