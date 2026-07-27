"""Deterministic evidence rules for Phase 2B."""

from __future__ import annotations

from dataclasses import dataclass

from ..deck_enums import SectionType, SlideRole
from ..deck_models import SlidePlanItem
from ..deck_planner.planner_models import ProposalContext
from .evidence_models import (
    EvidenceConfidence,
    EvidencePriority,
    EvidenceRequirement,
    EvidenceSourceType,
    MissingEvidenceSeverity,
    MissingEvidenceWarning,
    VisualEvidenceRecommendation,
)


@dataclass(frozen=True)
class EvidenceRuleSpec:
    source_type: EvidenceSourceType
    label: str
    priority: EvidencePriority
    numeric_required: bool = False
    customer_proof_required: bool = False
    case_study_required: bool = False
    visual: VisualEvidenceRecommendation = VisualEvidenceRecommendation.NONE
    rationale: str = "Required to make the slide evidence-backed."


SECTION_EVIDENCE_RULES: dict[str, list[EvidenceRuleSpec]] = {
    SectionType.COVER.value: [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Customer context confirmation", EvidencePriority.MEDIUM),
    ],
    SectionType.EXECUTIVE_SUMMARY.value: [
        EvidenceRuleSpec(EvidenceSourceType.INTERNAL_KPI, "Executive-level success criteria", EvidencePriority.HIGH, numeric_required=True, visual=VisualEvidenceRecommendation.METRIC_CARD),
        EvidenceRuleSpec(EvidenceSourceType.FINANCIAL_ESTIMATE, "Investment or value summary", EvidencePriority.HIGH, numeric_required=True),
    ],
    SectionType.BACKGROUND.value: [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Background interview notes", EvidencePriority.MEDIUM, customer_proof_required=True),
        EvidenceRuleSpec(EvidenceSourceType.PUBLIC_INFORMATION, "Public context", EvidencePriority.LOW),
    ],
    SectionType.CURRENT_STATE.value: [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Current process evidence", EvidencePriority.HIGH, customer_proof_required=True, visual=VisualEvidenceRecommendation.PROCESS_EVIDENCE),
        EvidenceRuleSpec(EvidenceSourceType.USER_FEEDBACK, "Operational feedback", EvidencePriority.MEDIUM, customer_proof_required=True),
    ],
    SectionType.PROBLEM.value: [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Problem statement proof", EvidencePriority.CRITICAL, customer_proof_required=True),
        EvidenceRuleSpec(EvidenceSourceType.INTERNAL_KPI, "Problem impact metric", EvidencePriority.HIGH, numeric_required=True, visual=VisualEvidenceRecommendation.METRIC_CARD),
    ],
    SectionType.INSIGHT.value: [
        EvidenceRuleSpec(EvidenceSourceType.MARKET_RESEARCH, "Insight support", EvidencePriority.HIGH, visual=VisualEvidenceRecommendation.COMPARISON_TABLE),
        EvidenceRuleSpec(EvidenceSourceType.INDUSTRY_STATISTICS, "Industry benchmark", EvidencePriority.MEDIUM, numeric_required=True),
    ],
    SectionType.OPPORTUNITY.value: [
        EvidenceRuleSpec(EvidenceSourceType.MARKET_RESEARCH, "Opportunity evidence", EvidencePriority.HIGH, numeric_required=True, visual=VisualEvidenceRecommendation.METRIC_CARD),
        EvidenceRuleSpec(EvidenceSourceType.PUBLIC_INFORMATION, "External opportunity signal", EvidencePriority.MEDIUM),
    ],
    SectionType.COMPETITOR.value: [
        EvidenceRuleSpec(EvidenceSourceType.COMPETITOR_ANALYSIS, "Competitor comparison basis", EvidencePriority.CRITICAL, visual=VisualEvidenceRecommendation.COMPARISON_TABLE),
        EvidenceRuleSpec(EvidenceSourceType.MARKET_RESEARCH, "Market alternative evidence", EvidencePriority.HIGH),
    ],
    SectionType.STRATEGY.value: [
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Strategy feasibility basis", EvidencePriority.HIGH, case_study_required=True),
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Strategic priority confirmation", EvidencePriority.HIGH, customer_proof_required=True),
    ],
    SectionType.SOLUTION.value: [
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Solution feasibility evidence", EvidencePriority.HIGH, case_study_required=True),
        EvidenceRuleSpec(EvidenceSourceType.IMPLEMENTATION_RESULT, "Implementation outcome evidence", EvidencePriority.MEDIUM, case_study_required=True),
    ],
    SectionType.APPROACH.value: [
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Implementation approach evidence", EvidencePriority.HIGH, visual=VisualEvidenceRecommendation.PROCESS_EVIDENCE),
        EvidenceRuleSpec(EvidenceSourceType.IMPLEMENTATION_RESULT, "Past delivery result", EvidencePriority.MEDIUM, case_study_required=True),
    ],
    SectionType.KPI.value: [
        EvidenceRuleSpec(EvidenceSourceType.INTERNAL_KPI, "KPI baseline and target", EvidencePriority.CRITICAL, numeric_required=True, visual=VisualEvidenceRecommendation.KPI_TABLE),
        EvidenceRuleSpec(EvidenceSourceType.FINANCIAL_ESTIMATE, "Measurement formula", EvidencePriority.HIGH, numeric_required=True),
    ],
    SectionType.ROI.value: [
        EvidenceRuleSpec(EvidenceSourceType.FINANCIAL_ESTIMATE, "ROI model", EvidencePriority.CRITICAL, numeric_required=True, visual=VisualEvidenceRecommendation.METRIC_CARD),
        EvidenceRuleSpec(EvidenceSourceType.INTERNAL_KPI, "Current baseline for ROI", EvidencePriority.HIGH, numeric_required=True),
    ],
    SectionType.ROADMAP.value: [
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Roadmap feasibility evidence", EvidencePriority.HIGH, visual=VisualEvidenceRecommendation.ROADMAP),
        EvidenceRuleSpec(EvidenceSourceType.IMPLEMENTATION_RESULT, "Milestone precedent", EvidencePriority.MEDIUM),
    ],
    SectionType.TIMELINE.value: [
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Timeline basis", EvidencePriority.HIGH, visual=VisualEvidenceRecommendation.TIMELINE),
        EvidenceRuleSpec(EvidenceSourceType.IMPLEMENTATION_RESULT, "Past schedule evidence", EvidencePriority.MEDIUM),
    ],
    SectionType.PRICING.value: [
        EvidenceRuleSpec(EvidenceSourceType.FINANCIAL_ESTIMATE, "Pricing basis", EvidencePriority.CRITICAL, numeric_required=True, visual=VisualEvidenceRecommendation.KPI_TABLE),
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Scope and cost assumption", EvidencePriority.HIGH),
    ],
    SectionType.ESTIMATE.value: [
        EvidenceRuleSpec(EvidenceSourceType.FINANCIAL_ESTIMATE, "Estimate basis", EvidencePriority.CRITICAL, numeric_required=True, visual=VisualEvidenceRecommendation.KPI_TABLE),
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Estimation precedent", EvidencePriority.HIGH),
    ],
    SectionType.RISK.value: [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Risk confirmation", EvidencePriority.HIGH, customer_proof_required=True, visual=VisualEvidenceRecommendation.RISK_MATRIX),
        EvidenceRuleSpec(EvidenceSourceType.PROJECT_EXPERIENCE, "Mitigation precedent", EvidencePriority.MEDIUM, case_study_required=True),
    ],
    SectionType.NEXT_ACTION.value: [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Next action agreement", EvidencePriority.CRITICAL, customer_proof_required=True),
    ],
    SectionType.APPENDIX.value: [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_DOCUMENT, "Supporting detail reference", EvidencePriority.LOW),
    ],
}


def context_text(context: ProposalContext) -> str:
    values = [
        context.project_summary,
        context.industry,
        context.proposal_category,
        context.competitive_information,
        context.budget_range,
        context.decision_maker,
        context.persona,
        context.implementation_purpose,
        context.timeline,
        *context.problems,
        *context.expected_outcomes,
    ]
    return " ".join(str(value or "").lower() for value in values)


def context_has_numeric_signal(context: ProposalContext) -> bool:
    text = context_text(context)
    return bool(context.budget_range) or any(char.isdigit() for char in text) or any(
        word in text for word in ("kpi", "roi", "rate", "cost", "budget", "time", "minutes", "hours")
    )


def context_has_customer_proof(context: ProposalContext) -> bool:
    return bool(context.problems or context.implementation_purpose or context.decision_maker or context.persona)


def context_has_competitor_signal(context: ProposalContext) -> bool:
    text = context_text(context)
    return bool(context.competitive_information) or any(
        word in text for word in ("competitor", "competition", "alternative", "vendor", "compare")
    )


def confidence_for(spec: EvidenceRuleSpec, context: ProposalContext) -> EvidenceConfidence:
    if spec.numeric_required:
        return EvidenceConfidence.LIKELY if context_has_numeric_signal(context) else EvidenceConfidence.MISSING
    if spec.customer_proof_required:
        return EvidenceConfidence.LIKELY if context_has_customer_proof(context) else EvidenceConfidence.MISSING
    if spec.source_type == EvidenceSourceType.COMPETITOR_ANALYSIS:
        return EvidenceConfidence.LIKELY if context_has_competitor_signal(context) else EvidenceConfidence.MISSING
    if spec.source_type in {EvidenceSourceType.PROJECT_EXPERIENCE, EvidenceSourceType.IMPLEMENTATION_RESULT}:
        return EvidenceConfidence.ESTIMATED
    return EvidenceConfidence.UNKNOWN


def requirements_for(section_type: str, slide: SlidePlanItem, context: ProposalContext) -> list[EvidenceRequirement]:
    specs = SECTION_EVIDENCE_RULES.get(section_type, [
        EvidenceRuleSpec(EvidenceSourceType.CUSTOMER_INTERVIEW, "Customer confirmation", EvidencePriority.MEDIUM)
    ])
    requirements: list[EvidenceRequirement] = []
    for index, spec in enumerate(specs):
        requirement_id = f"ev-{slide.slide_blueprint_id}-{index + 1:02d}"
        requirements.append(
            EvidenceRequirement(
                requirement_id=requirement_id,
                label=spec.label,
                source_type=spec.source_type,
                priority=spec.priority,
                confidence=confidence_for(spec, context),
                numeric_required=spec.numeric_required,
                customer_proof_required=spec.customer_proof_required,
                case_study_required=spec.case_study_required,
                traceability_required=True,
                rationale=spec.rationale,
            )
        )
    return requirements


def optional_requirements_for(section_type: str, slide: SlidePlanItem) -> list[EvidenceRequirement]:
    if section_type in {SectionType.SOLUTION.value, SectionType.APPROACH.value, SectionType.ROADMAP.value}:
        return [
            EvidenceRequirement(
                requirement_id=f"ev-{slide.slide_blueprint_id}-optional-case",
                label="Relevant project example",
                source_type=EvidenceSourceType.PROJECT_EXPERIENCE,
                priority=EvidencePriority.LOW,
                confidence=EvidenceConfidence.ESTIMATED,
                case_study_required=True,
                rationale="Useful if available, but not required for deck-level planning.",
            )
        ]
    if section_type in {SectionType.PROBLEM.value, SectionType.CURRENT_STATE.value}:
        return [
            EvidenceRequirement(
                requirement_id=f"ev-{slide.slide_blueprint_id}-optional-quote",
                label="Customer quote or voice-of-customer note",
                source_type=EvidenceSourceType.USER_FEEDBACK,
                priority=EvidencePriority.LOW,
                confidence=EvidenceConfidence.UNKNOWN,
                customer_proof_required=True,
                rationale="A quote can make the issue more concrete if approved for use.",
            )
        ]
    return []


def missing_warnings(requirements: list[EvidenceRequirement], context: ProposalContext) -> list[MissingEvidenceWarning]:
    warnings: list[MissingEvidenceWarning] = []
    missing_numeric = [item.requirement_id for item in requirements if item.numeric_required and item.confidence == EvidenceConfidence.MISSING.value]
    missing_customer = [
        item.requirement_id
        for item in requirements
        if item.customer_proof_required and item.confidence == EvidenceConfidence.MISSING.value
    ]
    missing_competitor = [
        item.requirement_id
        for item in requirements
        if item.source_type == EvidenceSourceType.COMPETITOR_ANALYSIS.value and not context_has_competitor_signal(context)
    ]
    if missing_numeric:
        warnings.append(
            MissingEvidenceWarning(
                warning_id="missing-numeric",
                severity=MissingEvidenceSeverity.BLOCKING,
                message="Numeric evidence is required but no numeric signal is available in Proposal Context.",
                suggested_action="Confirm baseline, target, budget, time, or KPI values before creating slide content.",
                related_requirement_ids=missing_numeric,
            )
        )
    if missing_customer:
        warnings.append(
            MissingEvidenceWarning(
                warning_id="missing-customer-proof",
                severity=MissingEvidenceSeverity.WARNING,
                message="Customer proof is required but the context has weak customer confirmation.",
                suggested_action="Collect interview notes, approved customer statements, or operational observations.",
                related_requirement_ids=missing_customer,
            )
        )
    if missing_competitor:
        warnings.append(
            MissingEvidenceWarning(
                warning_id="missing-competitor-analysis",
                severity=MissingEvidenceSeverity.WARNING,
                message="Competitor evidence is required but competitive information is missing.",
                suggested_action="Confirm alternatives, vendors, or current manual operation before comparison slides.",
                related_requirement_ids=missing_competitor,
            )
        )
    return warnings


def primary_priority(requirements: list[EvidenceRequirement], slide: SlidePlanItem) -> EvidencePriority:
    if any(item.priority == EvidencePriority.CRITICAL.value for item in requirements):
        return EvidencePriority.CRITICAL
    if slide.slide_role in {SlideRole.DECISION.value, SlideRole.CLOSING.value}:
        return EvidencePriority.HIGH
    if any(item.priority == EvidencePriority.HIGH.value for item in requirements):
        return EvidencePriority.HIGH
    return EvidencePriority.MEDIUM


def aggregate_confidence(requirements: list[EvidenceRequirement]) -> EvidenceConfidence:
    confidences = [item.confidence for item in requirements]
    if EvidenceConfidence.MISSING.value in confidences:
        return EvidenceConfidence.MISSING
    if EvidenceConfidence.UNKNOWN.value in confidences:
        return EvidenceConfidence.UNKNOWN
    if EvidenceConfidence.ESTIMATED.value in confidences:
        return EvidenceConfidence.ESTIMATED
    return EvidenceConfidence.LIKELY


def visual_recommendation(section_type: str, requirements: list[EvidenceRequirement]) -> VisualEvidenceRecommendation:
    for item in requirements:
        source_specs = SECTION_EVIDENCE_RULES.get(section_type, [])
        for spec in source_specs:
            if spec.label == item.label and spec.visual != VisualEvidenceRecommendation.NONE:
                return spec.visual
    if any(item.numeric_required for item in requirements):
        return VisualEvidenceRecommendation.METRIC_CARD
    return VisualEvidenceRecommendation.NONE


def risk_if_missing(section_type: str) -> str:
    if section_type in {SectionType.KPI.value, SectionType.ROI.value, SectionType.PRICING.value, SectionType.ESTIMATE.value}:
        return "The customer may not trust value, cost, or investment claims."
    if section_type in {SectionType.PROBLEM.value, SectionType.CURRENT_STATE.value}:
        return "The proposal may feel generic because the customer's actual situation is not proven."
    if section_type == SectionType.COMPETITOR.value:
        return "The differentiation logic may be weak against alternatives."
    if section_type == SectionType.NEXT_ACTION.value:
        return "The deck may end without a decision-ready next step."
    return "The slide may be less persuasive or harder to verify."

