"""Offline evaluator for Phase 2B Evidence Planner results."""

from __future__ import annotations

from .evidence_models import (
    EvidenceConfidence,
    EvidenceEvaluationDimension,
    EvidenceEvaluationResult,
    EvidencePlannerResult,
    EvidencePriority,
    MissingEvidenceSeverity,
)


EVIDENCE_EVALUATOR_NOTE = (
    "This score evaluates evidence planning readiness only. It does not evaluate "
    "headlines, body copy, Slide Blueprints, diagrams, PPTX rendering, or sales outcome."
)


def _dimension(
    name: str,
    score: int,
    reason: str,
    issues: list[str] | None = None,
    recommendations: list[str] | None = None,
) -> EvidenceEvaluationDimension:
    return EvidenceEvaluationDimension(
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


def evaluate_evidence_plan(result: EvidencePlannerResult) -> EvidenceEvaluationResult:
    slide_count = len(result.slide_evidence)
    required_counts = [len(item.required_evidence) for item in result.slide_evidence]
    all_requirements = [
        requirement
        for slide in result.slide_evidence
        for requirement in [*slide.required_evidence, *slide.optional_evidence]
    ]
    all_warnings = [warning for slide in result.slide_evidence for warning in slide.missing_evidence_warnings]
    blocking = [warning for warning in all_warnings if warning.severity == MissingEvidenceSeverity.BLOCKING.value]
    warning_count = len(all_warnings)
    source_types = {source for slide in result.slide_evidence for source in slide.evidence_source_types}
    numeric_required = [item for item in all_requirements if item.numeric_required]
    numeric_missing = [item for item in numeric_required if item.confidence == EvidenceConfidence.MISSING.value]
    critical_items = [item for item in all_requirements if item.priority == EvidencePriority.CRITICAL.value]
    traceable_items = [item for item in all_requirements if item.traceability_required]

    completeness_score = 10 if slide_count and min(required_counts) >= 1 else 4
    quality_score = max(4, min(10, len(source_types)))
    traceability_score = 10 if traceable_items and len(traceable_items) == len(all_requirements) else 6
    numeric_score = 10 if not numeric_missing else max(3, 10 - len(numeric_missing) * 2)
    sales_score = 8 + min(2, len(critical_items))
    cleanliness_score = 10 if not (
        result.generated_headlines
        or result.generated_main_messages
        or result.generated_body_text
        or result.generated_slide_blueprints
        or result.connected_to_runtime
    ) else 4

    dimensions = [
        _dimension(
            "Evidence Completeness",
            completeness_score,
            "Every planned slide should have at least one required evidence item.",
            [] if completeness_score == 10 else ["A slide has no required evidence."],
            [] if completeness_score == 10 else ["Add required evidence for every slide."],
        ),
        _dimension(
            "Evidence Quality",
            quality_score,
            "Evidence plans should use enough source variety for credible review.",
            [],
            [] if quality_score >= 8 else ["Increase source diversity where useful."],
        ),
        _dimension(
            "Evidence Traceability",
            traceability_score,
            "Evidence requirements are traceability-aware.",
            [],
            [] if traceability_score == 10 else ["Require traceability for every evidence item."],
        ),
        _dimension(
            "Numeric Integrity Readiness",
            numeric_score,
            "Numeric claims should be backed by explicit numeric evidence requirements.",
            [item.requirement_id for item in numeric_missing[:6]],
            [] if not numeric_missing else ["Collect numeric baselines, targets, or financial assumptions."],
        ),
        _dimension(
            "Sales Persuasiveness",
            sales_score,
            "Critical evidence is assigned to decision, value, and CTA slides.",
            [],
            [] if critical_items else ["Mark decision-critical evidence as critical."],
        ),
        _dimension(
            "Customer-facing Readiness",
            cleanliness_score,
            "Planner output remains evidence-only and avoids generated copy or slide blueprints.",
            [],
            [] if cleanliness_score == 10 else ["Remove generated copy or runtime connection from evidence output."],
        ),
    ]
    total = round(sum(item.score for item in dimensions) / (len(dimensions) * 10) * 100)
    return EvidenceEvaluationResult(
        total_score=total,
        grade=_grade(total),
        dimensions=dimensions,
        blocking_warning_count=len(blocking),
        warning_count=warning_count,
        note=EVIDENCE_EVALUATOR_NOTE,
    )

