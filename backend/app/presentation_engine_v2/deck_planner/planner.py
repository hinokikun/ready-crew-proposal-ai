"""Offline Deck Planner for Presentation Engine 2.0 Phase 2A."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from ..deck_enums import (
    AudienceSeniority,
    DecisionStage,
    DecisionUrgency,
    DeckGoal,
    DeckStatus,
    EvidenceStrategy,
    NarrativeFunction,
    PersuasionStrategy,
    RiskLevel,
    SectionType,
    StoryArcType,
    TransitionType,
)
from ..deck_models import (
    ApprovalRequirement,
    AudienceProfile,
    CTAPlan,
    DecisionPoint,
    DeckBlueprint,
    DeckConstraint,
    DeckSection,
    DeckSourceReference,
    DeckThemeDirection,
    DeckTransition,
    ObjectionResponse,
    SlideBlueprintReference,
    SlidePlanItem,
    StoryBeat,
)
from ..deck_validators import validate_deck_blueprint
from ..enums import ThemeType
from .planner_evaluator import evaluate_planner_result
from .planner_models import (
    DeckPlannerResult,
    DeckPlannerWarning,
    PlannedSlideRecommendation,
    PlannerRuleDecision,
    ProposalContext,
)
from .planner_rules import (
    SECTION_LIBRARY,
    classify_category,
    context_text,
    infer_audience,
    infer_decision_stage,
    infer_deck_length,
    infer_deck_type,
    infer_persuasion_strategy,
    infer_story_arc,
    section_sequence,
    transition_for,
)


PLANNER_FIXED_CREATED_AT = datetime(2026, 7, 27, tzinfo=timezone.utc)


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _compact(value: str | None, fallback: str, max_chars: int = 220) -> str:
    text = str(value or "").strip() or fallback
    return text if len(text) <= max_chars else f"{text[: max_chars - 3]}..."


def _project_title(context: ProposalContext, category: str) -> str:
    if context.project_name:
        return _compact(context.project_name, "Proposal Deck", 120)
    industry = context.industry or "Customer"
    return _compact(f"{industry} {category.title()} Proposal", "Proposal Deck", 120)


def _budget_present(context: ProposalContext) -> bool:
    text = context_text(context)
    return bool(context.budget_range) or any(key in text for key in ("budget", "cost", "price", "estimate", "roi"))


def _competition_present(context: ProposalContext) -> bool:
    text = context_text(context)
    return bool(context.competitive_information) or any(
        key in text for key in ("competitor", "competition", "alternative", "compare", "vendor")
    )


def _deck_goal(stage: DecisionStage, budget_present: bool) -> tuple[DeckGoal, PlannerRuleDecision]:
    if stage in {DecisionStage.APPROVAL, DecisionStage.PROCUREMENT}:
        return DeckGoal.APPROVE, PlannerRuleDecision(
            rule_name="deck_goal",
            selected_value="approve",
            reason="Decision stage indicates that approval is the target action.",
            confidence=0.82,
        )
    if stage == DecisionStage.COMPARISON:
        return DeckGoal.COMPARE, PlannerRuleDecision(
            rule_name="deck_goal",
            selected_value="compare",
            reason="Buyer appears to be comparing options.",
            confidence=0.74,
        )
    if budget_present:
        return DeckGoal.RECOMMEND, PlannerRuleDecision(
            rule_name="deck_goal",
            selected_value="recommend",
            reason="Budget information allows a recommendation-oriented plan.",
            confidence=0.7,
        )
    return DeckGoal.ALIGN, PlannerRuleDecision(
        rule_name="deck_goal",
        selected_value="align",
        reason="The context is early-stage, so alignment is the safest deck goal.",
        confidence=0.64,
    )


def _theme(category: str, seniority: AudienceSeniority) -> DeckThemeDirection:
    if seniority == AudienceSeniority.EXECUTIVE:
        return DeckThemeDirection(
            recommended_theme=ThemeType.EXECUTIVE,
            tone="executive",
            formality="formal",
            visual_density="medium",
            evidence_density=EvidenceStrategy.EXECUTIVE_SUMMARY,
            executive_summary_required=True,
        )
    if category in {"web", "branding"}:
        return DeckThemeDirection(
            recommended_theme=ThemeType.MODERN,
            tone="modern",
            formality="business",
            visual_density="medium",
            evidence_density=EvidenceStrategy.BALANCED,
            executive_summary_required=True,
        )
    return DeckThemeDirection(
        recommended_theme=ThemeType.CONSULTING,
        tone="consulting",
        formality="business",
        visual_density="medium",
        evidence_density=EvidenceStrategy.BALANCED,
        executive_summary_required=True,
    )


def _risk_level(context: ProposalContext, category: str, stage: DecisionStage) -> RiskLevel:
    text = context_text(context)
    if any(key in text for key in ("must", "urgent", "critical", "regulation", "security", "deadline")):
        return RiskLevel.HIGH
    if category in {"ai", "automation", "dx"} or stage in {DecisionStage.APPROVAL, DecisionStage.PROCUREMENT}:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _desired_decision(stage: DecisionStage) -> str:
    if stage == DecisionStage.APPROVAL:
        return "Approve the next evaluation or implementation step."
    if stage == DecisionStage.COMPARISON:
        return "Select the recommended direction for deeper evaluation."
    if stage == DecisionStage.PROCUREMENT:
        return "Confirm conditions needed to proceed to procurement."
    return "Agree on the problem, evaluation criteria, and next discussion."


def _section_id(section_type: SectionType, index: int) -> str:
    return f"sec-{index:02d}-{section_type.value}"


def _slide_id(deck_id: str, index: int, section_type: SectionType) -> str:
    return f"{deck_id}-slide-{index:02d}-{section_type.value}"


def _build_sections_and_slides(
    *,
    deck_id: str,
    sections: list[SectionType],
) -> tuple[list[DeckSection], list[SlidePlanItem], list[SlideBlueprintReference], list[PlannedSlideRecommendation]]:
    deck_sections: list[DeckSection] = []
    slide_plan: list[SlidePlanItem] = []
    slide_refs: list[SlideBlueprintReference] = []
    recommendations: list[PlannedSlideRecommendation] = []

    for index, section_type in enumerate(sections):
        spec = SECTION_LIBRARY[section_type]
        section_id = _section_id(section_type, index)
        slide_blueprint_id = _slide_id(deck_id, index, section_type)
        previous_type = sections[index - 1] if index > 0 else None
        next_type = sections[index + 1] if index + 1 < len(sections) else None
        transition = transition_for(previous_type, section_type, next_type)
        transition_to_next = transition_for(section_type, next_type, sections[index + 2] if index + 2 < len(sections) else None) if next_type else TransitionType.NONE

        deck_sections.append(
            DeckSection(
                section_id=section_id,
                section_type=section_type,
                section_title=spec.section_title,
                section_goal=spec.section_goal,
                section_order=index,
                required=spec.required,
                minimum_slides=1,
                maximum_slides=2 if section_type != SectionType.APPENDIX else 4,
                slide_ids=[slide_blueprint_id],
                entry_message=f"Plan the {spec.section_title} section.",
                exit_message=f"Move from {spec.section_title} to the next decision point.",
                transition_type=transition,
                decision_relevance=spec.decision_relevance,
            )
        )
        slide_plan.append(
            SlidePlanItem(
                slide_order=index,
                slide_role=spec.slide_role,
                slide_type=spec.slide_type,
                section_id=section_id,
                slide_goal=spec.slide_goal,
                narrative_function=spec.narrative_function,
                working_title=f"{spec.section_title} planning slide",
                key_message=f"Plan the purpose of the {spec.section_title} slide without final body copy.",
                required=spec.required,
                optional=spec.optional,
                decision_relevance=spec.decision_relevance,
                evidence_requirement=spec.evidence_requirement,
                transition_from_previous=transition,
                transition_to_next=transition_to_next,
                slide_blueprint_id=slide_blueprint_id,
            )
        )
        slide_refs.append(
            SlideBlueprintReference(
                slide_blueprint_id=slide_blueprint_id,
                slide_id=slide_blueprint_id,
                slide_order=index,
                expected_slide_type=spec.slide_type,
                expected_slide_goal=spec.slide_goal,
                section_id=section_id,
                required=spec.required,
                embedded_slide_blueprint=None,
            )
        )
        recommendations.append(
            PlannedSlideRecommendation(
                slide_blueprint_id=slide_blueprint_id,
                slide_order=index,
                section_id=section_id,
                slide_role=spec.slide_role.value,
                slide_purpose=spec.section_goal,
                recommended_visual=spec.recommended_visual,
                recommended_evidence=spec.evidence_requirement.value,
                cta_candidate=section_type == SectionType.NEXT_ACTION,
            )
        )

    return deck_sections, slide_plan, slide_refs, recommendations


def _story_beats(sections: list[DeckSection], slides: list[SlidePlanItem]) -> list[StoryBeat]:
    by_section = {section.section_type: section for section in sections}
    by_section_slide = {slide.section_id: slide for slide in slides}
    beats: list[StoryBeat] = []
    beat_specs = [
        ("hook", NarrativeFunction.HOOK, SectionType.COVER, "Frame the decision context."),
        ("diagnose", NarrativeFunction.DIAGNOSE, SectionType.PROBLEM, "Diagnose the priority issue."),
        ("recommend", NarrativeFunction.RECOMMEND, SectionType.SOLUTION, "Recommend the proposal direction."),
        ("quantify", NarrativeFunction.QUANTIFY, SectionType.KPI, "Define how value will be measured."),
        ("ask", NarrativeFunction.ASK, SectionType.NEXT_ACTION, "Ask for the next action."),
    ]
    for beat_id, function, section_type, message in beat_specs:
        section = by_section.get(section_type)
        if not section:
            continue
        slide = by_section_slide.get(section.section_id)
        beats.append(
            StoryBeat(
                beat_id=f"beat-{beat_id}",
                narrative_function=function,
                message=message,
                related_section_ids=[section.section_id],
                related_slide_ids=[slide.slide_blueprint_id] if slide and slide.slide_blueprint_id else [],
            )
        )
    return beats


def _transitions(slides: list[SlidePlanItem]) -> list[DeckTransition]:
    output: list[DeckTransition] = []
    for index, slide in enumerate(slides[:-1]):
        next_slide = slides[index + 1]
        output.append(
            DeckTransition(
                transition_type=next_slide.transition_from_previous,
                from_slide_id=slide.slide_blueprint_id,
                to_slide_id=next_slide.slide_blueprint_id,
                bridge_message=f"Bridge {slide.working_title} to {next_slide.working_title}.",
            )
        )
    return output


def _warnings(context: ProposalContext, sections: list[SectionType]) -> list[DeckPlannerWarning]:
    warnings: list[DeckPlannerWarning] = []
    if not context.problems:
        warnings.append(
            DeckPlannerWarning(
                code="PE2-PLANNER-CONTEXT-001",
                message="No explicit problem list was provided.",
                suggestion="Confirm the customer's top problems before generating slide-level content.",
            )
        )
    if not context.expected_outcomes:
        warnings.append(
            DeckPlannerWarning(
                code="PE2-PLANNER-CONTEXT-002",
                message="No expected outcomes were provided.",
                suggestion="Ask the sales owner to define success criteria.",
            )
        )
    if SectionType.PRICING in sections and not context.budget_range:
        warnings.append(
            DeckPlannerWarning(
                code="PE2-PLANNER-CONTEXT-003",
                message="Pricing was included because of context signals, but budget range is not explicit.",
                suggestion="Confirm budget range before customer submission.",
            )
        )
    return warnings


class DeckPlanner:
    """Rule-based offline planner that emits a DeckBlueprint."""

    def plan(self, context_input: ProposalContext | dict[str, Any]) -> DeckPlannerResult:
        context = context_input if isinstance(context_input, ProposalContext) else ProposalContext.parse_obj(context_input)
        context_payload = context.dict()
        deck_id = _stable_id("deck-plan", context_payload)

        category, category_decision = classify_category(context)
        audience, seniority, audience_decision = infer_audience(context)
        stage, urgency, stage_decision = infer_decision_stage(context)
        deck_type, deck_type_decision = infer_deck_type(category, seniority)
        story_arc, story_arc_decision = infer_story_arc(category, context, stage)
        persuasion, persuasion_decision = infer_persuasion_strategy(category, context)
        length_type, minimum_count, maximum_count, length_decision = infer_deck_length(context, seniority, stage)
        goal, goal_decision = _deck_goal(stage, _budget_present(context))
        sections, section_decision = section_sequence(
            category=category,
            story_arc=story_arc,
            seniority=seniority,
            budget_present=_budget_present(context),
            competition_present=_competition_present(context),
            expected_outcomes_present=bool(context.expected_outcomes),
            length_type=length_type,
        )

        deck_sections, slide_plan, slide_refs, slide_recommendations = _build_sections_and_slides(
            deck_id=deck_id,
            sections=sections,
        )
        target_slide_count = len(slide_plan)
        minimum_count = min(minimum_count, target_slide_count)
        maximum_count = max(maximum_count, target_slide_count)
        required_sections = [section.value for section in sections if section != SectionType.APPENDIX]
        optional_sections = [SectionType.FAQ.value, SectionType.APPENDIX.value]
        warnings = _warnings(context, sections)
        has_competitor = SectionType.COMPETITOR in sections
        has_pricing = SectionType.PRICING in sections
        value_signal = context.expected_outcomes[0] if context.expected_outcomes else "business value validation"
        problem_signal = context.problems[0] if context.problems else "the priority customer problem"

        deck = DeckBlueprint(
            deck_id=deck_id,
            project_id=context.project_id,
            deck_title=_project_title(context, category),
            deck_type=deck_type,
            status=DeckStatus.VALIDATED,
            language=context.language,
            created_at=PLANNER_FIXED_CREATED_AT,
            deck_goal=goal,
            primary_audience=audience,
            audience_seniority=seniority,
            decision_stage=stage,
            decision_question="What decision should the customer make after this proposal?",
            desired_decision=_desired_decision(stage),
            desired_reaction="The customer understands the value, risks, and next action.",
            decision_urgency=urgency,
            story_arc=story_arc,
            persuasion_strategy=persuasion,
            evidence_strategy=EvidenceStrategy.DATA_DRIVEN if context.expected_outcomes else EvidenceStrategy.BALANCED,
            core_thesis=f"The proposal should connect {problem_signal} to a practical next step.",
            value_proposition=f"The deck should show how the customer can achieve {value_signal}.",
            key_differentiator=(
                "Differentiate against known alternatives using fit, evidence, and implementation clarity."
                if has_competitor
                else "Differentiate by making value, risk, and next action easier to judge."
            ),
            primary_objection="Budget, ROI, schedule, internal workload, or competing alternatives may block progress.",
            objection_response=ObjectionResponse(
                objection_id="obj-primary",
                objection="Decision risk remains unclear.",
                response="Use KPI, risk, and next action sections to make the decision reviewable.",
                evidence_requirement=EvidenceStrategy.BALANCED,
                related_slide_ids=[slide.slide_blueprint_id for slide in slide_plan if slide.slide_goal in {"kpi_definition", "risk_handling", "next_action"}],
            ),
            sections=deck_sections,
            slide_plan=slide_plan,
            target_slide_count=target_slide_count,
            minimum_slide_count=minimum_count,
            maximum_slide_count=maximum_count,
            deck_length_type=length_type,
            appendix_allowed=True,
            optional_sections=optional_sections,
            required_sections=required_sections,
            opening_message="Open by framing the customer's decision context.",
            problem_statement=f"Use the problem section to clarify {problem_signal}.",
            insight_statement="Explain why the proposed direction is credible and timely.",
            recommendation_statement="Recommend the next practical step without over-claiming unverified facts.",
            impact_statement=f"Show expected impact through {value_signal} and measurable evaluation criteria.",
            closing_message="Close with owner, next action, and decision condition.",
            narrative_summary=(
                "The deck moves from context and problem framing to recommendation, evidence, investment view, "
                "risk handling, and a concrete next action."
            ),
            story_beats=_story_beats(deck_sections, slide_plan),
            key_takeaways=[
                "Problem and decision context are explicit.",
                "The recommendation is supported by evidence requirements.",
                "The next action is clear.",
            ],
            decision_points=[
                DecisionPoint(
                    decision_id="dec-next-step",
                    question=_desired_decision(stage),
                    required_evidence=["Problem priority", "Expected outcome", "Risk or constraint"],
                    related_slide_ids=[slide.slide_blueprint_id for slide in slide_plan if slide.slide_goal in {"kpi_definition", "pricing", "next_action"}],
                    urgency=urgency,
                )
            ],
            approval_requirements=[
                ApprovalRequirement(
                    requirement_id="approval-next-step",
                    approver=context.decision_maker or "Customer decision owner",
                    approval_condition="The next evaluation or implementation step is agreed.",
                    related_slide_ids=[slide.slide_blueprint_id for slide in slide_plan if slide.slide_goal == "next_action"],
                )
            ],
            cta_plan=CTAPlan(
                cta_strategy="Ask for a concrete next meeting or approval step.",
                next_action="Confirm evaluation scope, owner, timing, and success criteria.",
                owner=context.decision_maker or "Customer decision owner",
                due_timing=context.timeline or "Next meeting",
                success_condition="The customer agrees on the next evaluation action.",
            ),
            next_action="Confirm evaluation scope, owner, timing, and success criteria.",
            risk_level=_risk_level(context, category, stage),
            decision_dependencies=[
                "Problem priority",
                "Expected outcome",
                "Budget or evaluation constraint" if has_pricing else "Evaluation constraint",
            ],
            theme_direction=_theme(category, seniority),
            slide_blueprint_refs=slide_refs,
            generation_source="offline_deck_planner_phase2a",
            confidence=round(sum(decision.confidence for decision in [
                category_decision,
                audience_decision,
                stage_decision,
                deck_type_decision,
                story_arc_decision,
                persuasion_decision,
                length_decision,
                goal_decision,
                section_decision,
            ]) / 9, 2),
            warnings=[],
            validation_result=None,
            evaluation_result=None,
            source_references=[
                DeckSourceReference(
                    source_id="src-proposal-context",
                    label="Proposal Context",
                    source_type="user_input",
                    confidence="high",
                )
            ],
            created_by="deck_planner_phase2a",
            audience_profile=AudienceProfile(
                primary_audience=audience,
                seniority=seniority,
                decision_stage=stage,
                known_priorities=context.expected_outcomes[:8],
                avoid_topics=["Do not invent facts", "Do not overstate ROI without evidence"],
            ),
            constraints=[
                DeckConstraint(
                    constraint_id="con-no-slide-content",
                    label="Deck Planner must not generate final slide content.",
                    detail="Headlines, body copy, diagrams, colors, coordinates, fonts, and shapes remain out of scope.",
                    blocking=True,
                )
            ],
            transitions=_transitions(slide_plan),
        )

        validation = validate_deck_blueprint(deck)
        deck.validation_result = validation
        result = DeckPlannerResult(
            created_at=PLANNER_FIXED_CREATED_AT,
            context=context,
            deck_blueprint=deck,
            decisions=[
                category_decision,
                audience_decision,
                stage_decision,
                deck_type_decision,
                story_arc_decision,
                persuasion_decision,
                length_decision,
                goal_decision,
                section_decision,
            ],
            slide_recommendations=slide_recommendations,
            warnings=warnings,
            generated_slide_blueprints=False,
            connected_to_runtime=False,
        )
        result.evaluation_result = evaluate_planner_result(result)
        deck.evaluation_result = result.evaluation_result
        return result


def plan_deck(context_input: ProposalContext | dict[str, Any]) -> DeckPlannerResult:
    return DeckPlanner().plan(context_input)
