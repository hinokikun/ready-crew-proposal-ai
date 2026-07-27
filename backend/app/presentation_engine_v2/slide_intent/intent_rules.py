"""Deterministic rules for Phase 2D Slide Intent."""

from __future__ import annotations

from dataclasses import dataclass

from ..deck_models import DeckBlueprint, SlidePlanItem
from ..deck_planner.planner_models import ProposalContext
from ..evidence_planner.evidence_models import EvidenceConfidence, SlideEvidencePlan
from ..message_designer.designer_models import SlideMessageDesign
from .intent_contracts import (
    SECTION_TO_CHART,
    SECTION_TO_INTENT,
    SECTION_TO_SLIDE_TYPE,
    SECTION_TO_VISUAL,
    VISUAL_TO_DIAGRAM,
    VISUAL_TO_READING_ORDER,
)
from .intent_enums import (
    ChartCandidate,
    DiagramCandidate,
    InformationDensity,
    IntentConfidence,
    LayoutConstraint,
    ReadingOrder,
    SlideIntentType,
    SlideType,
    VisualPattern,
)
from .intent_models import InformationPriority, IntentInputMetrics, IntentWarning
from .intent_normalizers import collapse_whitespace


@dataclass(frozen=True)
class IntentRuleDecision:
    slide_intent: SlideIntentType
    slide_type: SlideType
    information_priority: InformationPriority
    reading_order: ReadingOrder
    visual_pattern: VisualPattern
    diagram_candidate: DiagramCandidate
    chart_candidate: ChartCandidate
    layout_constraints: list[LayoutConstraint]
    rendering_hint: str
    confidence: IntentConfidence
    metrics: IntentInputMetrics
    warnings: list[IntentWarning]


def section_type_for(deck: DeckBlueprint, slide: SlidePlanItem, evidence: SlideEvidencePlan) -> str:
    if evidence.section_type:
        return str(evidence.section_type)
    section = next((item for item in deck.sections if item.section_id == slide.section_id), None)
    return str(section.section_type) if section else "unknown"


def density_for(message: SlideMessageDesign) -> InformationDensity:
    total = (
        len(message.headline)
        + len(message.main_message)
        + len(message.key_takeaway)
        + sum(len(item.text) for item in message.supporting_messages)
    )
    if total < 80 and not message.supporting_messages:
        return InformationDensity.INSUFFICIENT
    if total < 160:
        return InformationDensity.LOW
    if total < 320:
        return InformationDensity.MEDIUM
    if total < 460:
        return InformationDensity.HIGH
    return InformationDensity.EXCESSIVE


def metrics_for(
    *,
    context: ProposalContext,
    evidence: SlideEvidencePlan,
    message: SlideMessageDesign,
    section_type: str,
) -> IntentInputMetrics:
    text_chars = (
        len(message.headline)
        + len(message.main_message)
        + len(message.key_takeaway)
        + sum(len(item.text) for item in message.supporting_messages)
    )
    evidence_types = {str(item.source_type) for item in [*evidence.required_evidence, *evidence.optional_evidence]}
    comparison_basis_present = bool(context.competitive_information) or "competitor_analysis" in evidence_types
    time_sequence_present = bool(context.timeline) or section_type in {"timeline", "roadmap", "approach"}
    hierarchy_basis_present = section_type in {"team", "scope", "deliverables"} or len(evidence.required_evidence) >= 3
    checklist_item_count = len(message.supporting_messages) + len(message.missing_evidence_disclosure)
    image_evidence_present = any(
        str(item.source_type) in {"customer_document", "public_information"} for item in evidence.required_evidence
    )
    return IntentInputMetrics(
        total_text_chars=text_chars,
        supporting_message_count=len(message.supporting_messages),
        required_evidence_count=len(evidence.required_evidence),
        missing_evidence_count=len(evidence.missing_evidence_warnings),
        numeric_claim_count=len(message.numeric_claims),
        comparison_basis_present=comparison_basis_present,
        time_sequence_present=time_sequence_present,
        hierarchy_basis_present=hierarchy_basis_present,
        checklist_item_count=checklist_item_count,
        image_evidence_present=image_evidence_present,
    )


def visual_pattern_for(section_type: str, slide: SlidePlanItem, message: SlideMessageDesign) -> VisualPattern:
    visual = SECTION_TO_VISUAL.get(section_type, VisualPattern.TEXT_DOMINANT)
    if message.numeric_claims and section_type == "roi":
        return VisualPattern.NUMBER_DOMINANT
    if str(slide.slide_type) == "before_after":
        return VisualPattern.COMPARISON
    return visual


def confidence_for(evidence: SlideEvidencePlan, message: SlideMessageDesign) -> IntentConfidence:
    if message.unsupported_claims:
        return IntentConfidence.LOW
    if evidence.evidence_confidence == EvidenceConfidence.MISSING.value:
        return IntentConfidence.LOW
    if evidence.missing_evidence_warnings:
        return IntentConfidence.MEDIUM
    return IntentConfidence.HIGH


def constraints_for(
    *,
    visual: VisualPattern,
    chart: ChartCandidate,
    density: InformationDensity,
    evidence: SlideEvidencePlan,
    section_type: str,
) -> list[LayoutConstraint]:
    constraints = [LayoutConstraint.KEEP_SINGLE_MESSAGE, LayoutConstraint.NO_LAYOUT_GENERATED]
    if density in {InformationDensity.HIGH, InformationDensity.EXCESSIVE}:
        constraints.append(LayoutConstraint.SPLIT_IF_DENSE)
    if evidence.missing_evidence_warnings:
        constraints.append(LayoutConstraint.SHOW_EVIDENCE_GAP)
    if chart != ChartCandidate.NONE or section_type in {"kpi", "roi", "pricing", "estimate"}:
        constraints.append(LayoutConstraint.REQUIRE_NUMERIC_EVIDENCE)
        constraints.append(LayoutConstraint.AVOID_FAKE_NUMBERS)
    if visual in {VisualPattern.HERO, VisualPattern.IMAGE_DOMINANT}:
        constraints.append(LayoutConstraint.IMAGE_PLACEHOLDER_ONLY)
    if section_type in {"next_action", "closing"}:
        constraints.append(LayoutConstraint.KEEP_CTA_VISIBLE)
    ordered: list[LayoutConstraint] = []
    for item in constraints:
        if item not in ordered:
            ordered.append(item)
    return ordered


def warnings_for(metrics: IntentInputMetrics, density: InformationDensity, visual: VisualPattern) -> list[IntentWarning]:
    warnings: list[IntentWarning] = []
    if density == InformationDensity.EXCESSIVE:
        warnings.append(
            IntentWarning(
                warning_id="intent-density-excessive",
                message="The message payload is dense for a single-slide intent.",
                suggestion="Split content or ask Message Designer to compress before visual design.",
            )
        )
    if density == InformationDensity.INSUFFICIENT:
        warnings.append(
            IntentWarning(
                warning_id="intent-density-insufficient",
                message="The slide may not have enough information for a clear visual decision.",
                suggestion="Confirm the main message and required evidence before Phase 3.",
            )
        )
    if metrics.missing_evidence_count:
        warnings.append(
            IntentWarning(
                warning_id="intent-evidence-gap",
                message="Missing evidence must be shown as a review gap, not hidden by visual design.",
                suggestion="Keep an evidence-gap callout or review note in the downstream blueprint.",
            )
        )
    if visual == VisualPattern.COMPARISON and not metrics.comparison_basis_present:
        warnings.append(
            IntentWarning(
                warning_id="intent-comparison-basis-missing",
                message="Comparison visual was selected without a clear comparison basis.",
                suggestion="Collect competitor, current/future, or option comparison evidence.",
            )
        )
    return warnings


def information_priority_for(message: SlideMessageDesign, density: InformationDensity) -> InformationPriority:
    muted = [claim.text for claim in message.unsupported_claims[:3]]
    secondary = [collapse_whitespace(item.text)[:100] for item in message.supporting_messages[:5]]
    if message.missing_evidence_disclosure:
        muted.extend(item.message[:100] for item in message.missing_evidence_disclosure[:2])
    return InformationPriority(
        primary_focus=collapse_whitespace(message.main_message or message.headline)[:160],
        secondary_focus=secondary,
        muted_content=muted[:5],
        density=density,
        emphasis="numeric_claim" if message.numeric_claims else "main_message",
    )


def rendering_hint_for(intent: SlideIntentType, visual: VisualPattern, diagram: DiagramCandidate, chart: ChartCandidate) -> str:
    parts = [
        f"Show the slide as {visual.value}",
        f"communicating {intent.value}",
        "without generating coordinates, fonts, colors, or PowerPoint objects.",
    ]
    if diagram != DiagramCandidate.NONE:
        parts.append(f"Visual Director may consider {diagram.value}.")
    if chart != ChartCandidate.NONE:
        parts.append(f"Chart planning may consider {chart.value} only when numeric evidence is present.")
    return " ".join(parts)[:280]


def decide_intent(
    *,
    context: ProposalContext,
    deck: DeckBlueprint,
    slide: SlidePlanItem,
    evidence: SlideEvidencePlan,
    message: SlideMessageDesign,
) -> IntentRuleDecision:
    section_type = section_type_for(deck, slide, evidence)
    intent = SECTION_TO_INTENT.get(section_type, SlideIntentType.ALIGN_CONTEXT)
    slide_type = SECTION_TO_SLIDE_TYPE.get(section_type, SlideType.ANALYSIS)
    visual = visual_pattern_for(section_type, slide, message)
    diagram = VISUAL_TO_DIAGRAM.get(visual, DiagramCandidate.NONE)
    reading_order = VISUAL_TO_READING_ORDER.get(visual, ReadingOrder.TITLE_FIRST)
    density = density_for(message)
    metrics = metrics_for(context=context, evidence=evidence, message=message, section_type=section_type)
    chart = SECTION_TO_CHART.get(section_type, ChartCandidate.NONE)
    if metrics.missing_evidence_count or not metrics.numeric_claim_count:
        chart = ChartCandidate.NONE
    if chart != ChartCandidate.NONE:
        diagram = DiagramCandidate.NONE
    constraints = constraints_for(visual=visual, chart=chart, density=density, evidence=evidence, section_type=section_type)
    confidence = confidence_for(evidence, message)
    return IntentRuleDecision(
        slide_intent=intent,
        slide_type=slide_type,
        information_priority=information_priority_for(message, density),
        reading_order=reading_order,
        visual_pattern=visual,
        diagram_candidate=diagram,
        chart_candidate=chart,
        layout_constraints=constraints,
        rendering_hint=rendering_hint_for(intent, visual, diagram, chart),
        confidence=confidence,
        metrics=metrics,
        warnings=warnings_for(metrics, density, visual),
    )
