"""Offline evaluator for Presentation Engine 2.0 slide blueprints."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from .enums import CTAType, SlideGoal, ValidationSeverity
from .models import SlideBlueprint, ValidationIssue
from .validators import validate_blueprint


EVALUATOR_NOTE = (
    "Blueprint構造上の準備度であり、PowerPointの最終的な視覚品質を保証しません。"
)


class EvaluationItem(BaseModel):
    name: str
    score: int = Field(..., ge=0, le=10)
    max_score: int = 10
    issues: list[str] = Field(default_factory=list)
    reason: str
    recommendations: list[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    total_score: int = Field(..., ge=0, le=100)
    max_score: int = 100
    grade: str
    items: list[EvaluationItem]
    blocking_issue_count: int
    warning_count: int
    note: str = EVALUATOR_NOTE


def _score_contract(issues: list[ValidationIssue]) -> EvaluationItem:
    errors = [issue for issue in issues if issue.severity == ValidationSeverity.ERROR.value]
    warnings = [issue for issue in issues if issue.severity == ValidationSeverity.WARNING.value]
    score = max(0, 10 - len(errors) * 4 - len(warnings))
    return EvaluationItem(
        name="Contract Validity",
        score=score,
        issues=[issue.code for issue in errors[:5]],
        reason="Schema and semantic validation readiness.",
        recommendations=["Resolve validation errors before renderer handoff."] if errors else [],
    )


def _score_message(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> EvaluationItem:
    score = 10
    problems = []
    if len(blueprint.headline) > 70:
        score -= 2
        problems.append("headline_long")
    if len(blueprint.main_message) > 200:
        score -= 1
        problems.append("main_message_dense")
    if any(issue.code.startswith("PE2-MESSAGE") for issue in issues):
        score -= 4
        problems.append("message_validation_issue")
    return EvaluationItem(
        name="Message Clarity",
        score=max(0, score),
        issues=problems,
        reason="Headline and main message should be customer-facing and concise.",
        recommendations=["Shorten headline or remove placeholder wording."] if problems else [],
    )


def _score_intent(blueprint: SlideBlueprint) -> EvaluationItem:
    headline = blueprint.headline.lower()
    goal = blueprint.slide_goal
    score = 8
    if goal in {SlideGoal.NEXT_ACTION.value, SlideGoal.CLOSING.value} and blueprint.cta.cta_type != CTAType.NONE.value:
        score = 10
    elif goal in {SlideGoal.COMPARISON.value, SlideGoal.PROBLEM_SHARING.value} and blueprint.main_message:
        score = 9
    if str(goal).replace("_", " ") in headline:
        score = min(10, score + 1)
    return EvaluationItem(
        name="Intent Alignment",
        score=score,
        reason="Slide goal, headline, and desired reaction are aligned enough for Phase 1.",
        recommendations=[],
    )


def _score_visual(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> EvaluationItem:
    visual_issues = [issue for issue in issues if issue.code.startswith("PE2-VISUAL")]
    score = max(0, 10 - len(visual_issues) * 4)
    if blueprint.visual_rationale:
        score = min(10, score + 1)
    return EvaluationItem(
        name="Visual Suitability",
        score=score,
        issues=[issue.code for issue in visual_issues],
        reason="Visual type should match diagram type and required slide data.",
        recommendations=["Add required data for the selected visual type."] if visual_issues else [],
    )


def _score_content(blueprint: SlideBlueprint) -> EvaluationItem:
    blocks = len(blueprint.content_blocks)
    evidence = len(blueprint.supporting_evidence)
    score = 6 + min(2, blocks) + min(2, evidence)
    if blocks == 0:
        score -= 2
    return EvaluationItem(
        name="Content Completeness",
        score=max(0, min(10, score)),
        reason="Blueprint has enough content blocks and evidence for offline readiness.",
        recommendations=["Add content blocks or evidence references."] if blocks == 0 else [],
    )


def _score_hierarchy(blueprint: SlideBlueprint) -> EvaluationItem:
    score = 5
    if blueprint.primary_element:
        score += 2
    if blueprint.reading_order:
        score += 2
    if blueprint.secondary_elements:
        score += 1
    return EvaluationItem(
        name="Hierarchy Readiness",
        score=min(10, score),
        reason="Primary element and reading order are defined for renderer handoff.",
        recommendations=[] if blueprint.reading_order else ["Add reading_order for deterministic rendering."],
    )


def _score_rendering(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> EvaluationItem:
    layout_issues = [issue for issue in issues if issue.code.startswith("PE2-LAYOUT")]
    score = max(0, 10 - len(layout_issues) * 2)
    if blueprint.rendering_metadata.editable_shapes_required:
        score = min(10, score + 1)
    return EvaluationItem(
        name="Rendering Safety",
        score=score,
        issues=[issue.code for issue in layout_issues],
        reason="Renderer can inspect layout, typography, safe area, and metadata.",
        recommendations=["Resolve layout warnings before visual rendering."] if layout_issues else [],
    )


def _score_cleanliness(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> EvaluationItem:
    placeholder_issues = [issue for issue in issues if issue.code == "PE2-MESSAGE-002"]
    score = max(0, 10 - len(placeholder_issues) * 5)
    return EvaluationItem(
        name="Customer-facing Cleanliness",
        score=score,
        issues=[issue.field_path for issue in placeholder_issues],
        reason="Internal placeholder labels must not appear in customer-facing output.",
        recommendations=["Replace internal labels with natural proposal language."] if placeholder_issues else [],
    )


def _score_numeric(blueprint: SlideBlueprint, issues: list[ValidationIssue]) -> EvaluationItem:
    numeric_issues = [issue for issue in issues if issue.code.startswith("PE2-SAFETY")]
    score = max(0, 10 - len(numeric_issues) * 3)
    if blueprint.metrics:
        score = min(10, score + 1)
    return EvaluationItem(
        name="Numeric Integrity Readiness",
        score=score,
        issues=[issue.code for issue in numeric_issues],
        reason="Metric values must be explicit, sourced, or clearly marked as pending.",
        recommendations=["Attach evidence or mark low-confidence values."] if numeric_issues else [],
    )


def _score_cta(blueprint: SlideBlueprint) -> EvaluationItem:
    cta_needed = blueprint.slide_goal in {SlideGoal.NEXT_ACTION.value, SlideGoal.CLOSING.value}
    has_cta = blueprint.cta.cta_type != CTAType.NONE.value and bool(blueprint.cta.cta_label)
    score = 10 if not cta_needed or has_cta else 3
    return EvaluationItem(
        name="CTA Readiness",
        score=score,
        issues=[] if score == 10 else ["cta_missing"],
        reason="CTA is required for next-action or closing slides.",
        recommendations=["Add a clear next action."] if score < 10 else [],
    )


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    return "D"


def evaluate_blueprint(payload: SlideBlueprint | Dict[str, Any], *, normalize: bool = False) -> EvaluationReport:
    validation = validate_blueprint(payload, normalize=normalize)
    if isinstance(payload, SlideBlueprint):
        blueprint = payload
    else:
        from .normalizers import normalize_blueprint_dict

        data, _changed = normalize_blueprint_dict(payload) if normalize else (payload, [])
        blueprint = SlideBlueprint.parse_obj(data)

    items = [
        _score_contract(validation.issues),
        _score_message(blueprint, validation.issues),
        _score_intent(blueprint),
        _score_visual(blueprint, validation.issues),
        _score_content(blueprint),
        _score_hierarchy(blueprint),
        _score_rendering(blueprint, validation.issues),
        _score_cleanliness(blueprint, validation.issues),
        _score_numeric(blueprint, validation.issues),
        _score_cta(blueprint),
    ]
    total = sum(item.score for item in items)
    return EvaluationReport(
        total_score=total,
        grade=_grade(total),
        items=items,
        blocking_issue_count=len(validation.errors),
        warning_count=len(validation.warnings),
    )
