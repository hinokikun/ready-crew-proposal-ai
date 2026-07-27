"""Deterministic rules used by the offline Deck Planner.

These rules intentionally stop at deck structure. They select section and slide
planning metadata, but they do not write final headlines, body copy, diagrams,
coordinates, fonts, colors, or PowerPoint shapes.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..deck_enums import (
    AudienceSeniority,
    DecisionStage,
    DecisionUrgency,
    DeckGoal,
    DeckLengthType,
    DeckType,
    EvidenceStrategy,
    NarrativeFunction,
    PersuasionStrategy,
    SectionType,
    SlideRole,
    StoryArcType,
    TransitionType,
)
from ..enums import AudienceType, SlideGoal, SlideType, VisualType
from .planner_models import PlannerRuleDecision, ProposalContext


@dataclass(frozen=True)
class SectionPlanSpec:
    section_type: SectionType
    section_title: str
    section_goal: str
    slide_role: SlideRole
    slide_type: SlideType
    slide_goal: SlideGoal
    narrative_function: NarrativeFunction
    recommended_visual: VisualType
    evidence_requirement: EvidenceStrategy
    decision_relevance: str = "medium"
    required: bool = True
    optional: bool = False


SECTION_LIBRARY: dict[SectionType, SectionPlanSpec] = {
    SectionType.COVER: SectionPlanSpec(
        SectionType.COVER,
        "Cover",
        "Frame the proposal theme and expected decision.",
        SlideRole.OPENING,
        SlideType.COVER,
        SlideGoal.COVER,
        NarrativeFunction.HOOK,
        VisualType.HERO,
        EvidenceStrategy.LIGHT,
        "high",
    ),
    SectionType.EXECUTIVE_SUMMARY: SectionPlanSpec(
        SectionType.EXECUTIVE_SUMMARY,
        "Executive Summary",
        "Summarize the decision logic before details.",
        SlideRole.SUMMARY,
        SlideType.EXECUTIVE_SUMMARY,
        SlideGoal.EXECUTIVE_SUMMARY,
        NarrativeFunction.FRAME,
        VisualType.METRIC_CARDS,
        EvidenceStrategy.EXECUTIVE_SUMMARY,
        "high",
    ),
    SectionType.BACKGROUND: SectionPlanSpec(
        SectionType.BACKGROUND,
        "Background",
        "Confirm the business context and why the discussion matters now.",
        SlideRole.CONTEXT,
        SlideType.CUSTOMER_CONTEXT,
        SlideGoal.BACKGROUND,
        NarrativeFunction.FRAME,
        VisualType.TWO_COLUMN,
        EvidenceStrategy.LIGHT,
    ),
    SectionType.CURRENT_STATE: SectionPlanSpec(
        SectionType.CURRENT_STATE,
        "Current State",
        "Show how the current process or situation creates friction.",
        SlideRole.CONTEXT,
        SlideType.CURRENT_STATE,
        SlideGoal.CURRENT_STATE,
        NarrativeFunction.DIAGNOSE,
        VisualType.PROCESS_FLOW,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.PROBLEM: SectionPlanSpec(
        SectionType.PROBLEM,
        "Problem",
        "Align on the priority problem before recommending a solution.",
        SlideRole.PROBLEM,
        SlideType.PROBLEM_STATEMENT,
        SlideGoal.PROBLEM_SHARING,
        NarrativeFunction.DIAGNOSE,
        VisualType.THREE_COLUMN,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.INSIGHT: SectionPlanSpec(
        SectionType.INSIGHT,
        "Insight",
        "Explain the finding that makes the proposal direction credible.",
        SlideRole.INSIGHT,
        SlideType.RECOMMENDED_STRATEGY,
        SlideGoal.CUSTOMER_INSIGHT,
        NarrativeFunction.EXPLAIN,
        VisualType.MATRIX_2X2,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.OPPORTUNITY: SectionPlanSpec(
        SectionType.OPPORTUNITY,
        "Opportunity",
        "Connect the current issue to business value.",
        SlideRole.INSIGHT,
        SlideType.DIFFERENTIATION,
        SlideGoal.CUSTOMER_INSIGHT,
        NarrativeFunction.EXPLAIN,
        VisualType.LARGE_NUMBER if hasattr(VisualType, "LARGE_NUMBER") else VisualType.METRIC_CARDS,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.COMPETITOR: SectionPlanSpec(
        SectionType.COMPETITOR,
        "Competitive Position",
        "Show how the proposal should win against alternatives.",
        SlideRole.PROOF,
        SlideType.COMPETITOR_COMPARISON,
        SlideGoal.COMPETITIVE_ANALYSIS,
        NarrativeFunction.COMPARE,
        VisualType.COMPARISON_TABLE,
        EvidenceStrategy.DATA_DRIVEN,
    ),
    SectionType.STRATEGY: SectionPlanSpec(
        SectionType.STRATEGY,
        "Strategy",
        "State the recommended way to win the decision.",
        SlideRole.RECOMMENDATION,
        SlideType.RECOMMENDED_STRATEGY,
        SlideGoal.PROPOSAL_OVERVIEW,
        NarrativeFunction.RECOMMEND,
        VisualType.TWO_COLUMN,
        EvidenceStrategy.BALANCED,
        "high",
    ),
    SectionType.SOLUTION: SectionPlanSpec(
        SectionType.SOLUTION,
        "Solution",
        "Describe the proposed direction at a concept level.",
        SlideRole.RECOMMENDATION,
        SlideType.PROPOSAL_OVERVIEW,
        SlideGoal.PROPOSAL_OVERVIEW,
        NarrativeFunction.RECOMMEND,
        VisualType.ARCHITECTURE_MAP,
        EvidenceStrategy.BALANCED,
        "high",
    ),
    SectionType.APPROACH: SectionPlanSpec(
        SectionType.APPROACH,
        "Approach",
        "Explain how the work should proceed.",
        SlideRole.PLAN,
        SlideType.BUSINESS_PROCESS,
        SlideGoal.PROCESS,
        NarrativeFunction.EXPLAIN,
        VisualType.PROCESS_FLOW,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.KPI: SectionPlanSpec(
        SectionType.KPI,
        "KPI",
        "Define how success should be evaluated.",
        SlideRole.PROOF,
        SlideType.KPI_DEFINITION,
        SlideGoal.KPI_DEFINITION,
        NarrativeFunction.QUANTIFY,
        VisualType.KPI_DASHBOARD,
        EvidenceStrategy.DATA_DRIVEN,
        "high",
    ),
    SectionType.ROI: SectionPlanSpec(
        SectionType.ROI,
        "ROI",
        "Connect outcomes to investment judgment.",
        SlideRole.PROOF,
        SlideType.ROI_ESTIMATE,
        SlideGoal.ROI_EXPLANATION,
        NarrativeFunction.QUANTIFY,
        VisualType.CHART,
        EvidenceStrategy.DATA_DRIVEN,
        "high",
    ),
    SectionType.ROADMAP: SectionPlanSpec(
        SectionType.ROADMAP,
        "Roadmap",
        "Show the path from decision to implementation.",
        SlideRole.PLAN,
        SlideType.ROADMAP,
        SlideGoal.ROADMAP,
        NarrativeFunction.EXPLAIN,
        VisualType.ROADMAP,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.TIMELINE: SectionPlanSpec(
        SectionType.TIMELINE,
        "Timeline",
        "Clarify milestones and decision timing.",
        SlideRole.PLAN,
        SlideType.TIMELINE,
        SlideGoal.TIMELINE,
        NarrativeFunction.EXPLAIN,
        VisualType.TIMELINE,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.PRICING: SectionPlanSpec(
        SectionType.PRICING,
        "Pricing",
        "Give a decision-ready investment view.",
        SlideRole.DECISION,
        SlideType.ESTIMATE_OVERVIEW,
        SlideGoal.PRICING,
        NarrativeFunction.QUANTIFY,
        VisualType.TABLE,
        EvidenceStrategy.BALANCED,
        "high",
    ),
    SectionType.ESTIMATE: SectionPlanSpec(
        SectionType.ESTIMATE,
        "Estimate",
        "Frame expected cost ranges and conditions.",
        SlideRole.DECISION,
        SlideType.ESTIMATE_OVERVIEW,
        SlideGoal.ESTIMATE,
        NarrativeFunction.QUANTIFY,
        VisualType.TABLE,
        EvidenceStrategy.BALANCED,
        "high",
    ),
    SectionType.RISK: SectionPlanSpec(
        SectionType.RISK,
        "Risk",
        "Anticipate concerns and show mitigation direction.",
        SlideRole.SUPPORT,
        SlideType.RISK_REGISTER,
        SlideGoal.RISK_HANDLING,
        NarrativeFunction.DE_RISK,
        VisualType.RISK_MATRIX,
        EvidenceStrategy.BALANCED,
    ),
    SectionType.NEXT_ACTION: SectionPlanSpec(
        SectionType.NEXT_ACTION,
        "Next Action",
        "Make the next decision and owner explicit.",
        SlideRole.CLOSING,
        SlideType.NEXT_ACTION,
        SlideGoal.NEXT_ACTION,
        NarrativeFunction.ASK,
        VisualType.CLOSING,
        EvidenceStrategy.LIGHT,
        "high",
    ),
    SectionType.APPENDIX: SectionPlanSpec(
        SectionType.APPENDIX,
        "Appendix",
        "Hold detail outside the main decision flow.",
        SlideRole.APPENDIX,
        SlideType.APPENDIX,
        SlideGoal.APPENDIX,
        NarrativeFunction.EXPLAIN,
        VisualType.TABLE,
        EvidenceStrategy.BALANCED,
        required=False,
        optional=True,
    ),
}


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "ai": ("ai", "ocr", "image recognition", "vision", "llm", "chatbot", "generative"),
    "automation": ("rpa", "automation", "workflow", "manual work", "back office"),
    "crm": ("crm", "sfa", "salesforce", "customer management", "pipeline"),
    "dx": ("dx", "digital transformation", "digitalization", "data platform"),
    "hiring": ("recruit", "hiring", "hr", "talent", "candidate"),
    "branding": ("brand", "branding", "creative", "identity"),
    "web": ("web", "website", "web site", "cms", "seo", "landing page", "homepage", "e-commerce", "ec site"),
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


def classify_category(context: ProposalContext) -> tuple[str, PlannerRuleDecision]:
    explicit = str(context.proposal_category or "").strip().lower()
    text = context_text(context)
    if explicit:
        text = f"{explicit} {text}"
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category, PlannerRuleDecision(
                rule_name="proposal_category",
                selected_value=category,
                reason=f"Matched category keywords for {category}.",
                confidence=0.86,
            )
    return "generic", PlannerRuleDecision(
        rule_name="proposal_category",
        selected_value="generic",
        reason="No strong category keyword was found, so the deck stays industry-neutral.",
        confidence=0.62,
    )


def infer_audience(context: ProposalContext) -> tuple[AudienceType, AudienceSeniority, PlannerRuleDecision]:
    text = f"{context.decision_maker or ''} {context.persona or ''}".lower()
    if any(key in text for key in ("ceo", "president", "executive", "owner", "founder", "cfo", "cto")):
        return AudienceType.EXECUTIVE, AudienceSeniority.EXECUTIVE, PlannerRuleDecision(
            rule_name="audience",
            selected_value="executive",
            reason="Decision maker wording indicates an executive audience.",
            confidence=0.86,
        )
    if any(key in text for key in ("department", "director", "division", "head", "manager")):
        return AudienceType.DEPARTMENT_HEAD, AudienceSeniority.SENIOR_MANAGER, PlannerRuleDecision(
            rule_name="audience",
            selected_value="department_head",
            reason="Decision maker appears to be a department or senior manager.",
            confidence=0.8,
        )
    if any(key in text for key in ("field", "operation", "quality", "factory", "store", "site")):
        return AudienceType.FIELD_LEADER, AudienceSeniority.FIELD_LEADER, PlannerRuleDecision(
            rule_name="audience",
            selected_value="field_leader",
            reason="Persona is close to an operational or field leader.",
            confidence=0.74,
        )
    if any(key in text for key in ("it", "system", "information")):
        return AudienceType.INFORMATION_SYSTEMS, AudienceSeniority.MANAGER, PlannerRuleDecision(
            rule_name="audience",
            selected_value="information_systems",
            reason="Persona indicates information systems involvement.",
            confidence=0.74,
        )
    return AudienceType.GENERAL, AudienceSeniority.MIXED, PlannerRuleDecision(
        rule_name="audience",
        selected_value="general",
        reason="No specific persona was strong enough, so a mixed business audience is used.",
        confidence=0.62,
    )


def infer_decision_stage(context: ProposalContext) -> tuple[DecisionStage, DecisionUrgency, PlannerRuleDecision]:
    text = context_text(context)
    if any(key in text for key in ("renewal", "contract renewal")):
        return DecisionStage.RENEWAL, DecisionUrgency.NORMAL, PlannerRuleDecision(
            rule_name="decision_stage",
            selected_value="renewal",
            reason="Renewal wording indicates a renewal decision.",
            confidence=0.84,
        )
    if any(key in text for key in ("approval", "board", "稟議", "決裁")):
        return DecisionStage.APPROVAL, DecisionUrgency.HIGH, PlannerRuleDecision(
            rule_name="decision_stage",
            selected_value="approval",
            reason="Approval or decision wording indicates a decision-ready deck.",
            confidence=0.82,
        )
    if context.budget_range:
        return DecisionStage.COMPARISON, DecisionUrgency.NORMAL, PlannerRuleDecision(
            rule_name="decision_stage",
            selected_value="comparison",
            reason="Budget information is present, so the buyer is likely comparing options.",
            confidence=0.72,
        )
    return DecisionStage.DISCOVERY, DecisionUrgency.NORMAL, PlannerRuleDecision(
        rule_name="decision_stage",
        selected_value="discovery",
        reason="Insufficient buying-stage signals; use a discovery-oriented plan.",
        confidence=0.62,
    )


def infer_deck_type(category: str, seniority: AudienceSeniority) -> tuple[DeckType, PlannerRuleDecision]:
    if seniority == AudienceSeniority.EXECUTIVE:
        return DeckType.EXECUTIVE_PROPOSAL, PlannerRuleDecision(
            rule_name="deck_type",
            selected_value="executive_proposal",
            reason="Executive audience requires concise decision framing.",
            confidence=0.82,
        )
    if category == "web":
        return DeckType.WEB_PRODUCTION_PROPOSAL, PlannerRuleDecision(
            rule_name="deck_type",
            selected_value="web_production_proposal",
            reason="The category is web or digital experience.",
            confidence=0.82,
        )
    if category in {"crm", "dx"}:
        return DeckType.SAAS_INTRODUCTION, PlannerRuleDecision(
            rule_name="deck_type",
            selected_value="saas_introduction",
            reason="The category is platform or software introduction.",
            confidence=0.78,
        )
    return DeckType.CONSULTING_PROPOSAL, PlannerRuleDecision(
        rule_name="deck_type",
        selected_value="consulting_proposal",
        reason="The proposal needs problem framing and implementation planning.",
        confidence=0.7,
    )


def infer_story_arc(category: str, context: ProposalContext, stage: DecisionStage) -> tuple[StoryArcType, PlannerRuleDecision]:
    text = context_text(context)
    if stage == DecisionStage.APPROVAL:
        return StoryArcType.EXECUTIVE_DECISION, PlannerRuleDecision(
            rule_name="story_arc",
            selected_value="executive_decision",
            reason="Approval-stage decks should move quickly from issue to decision.",
            confidence=0.82,
        )
    if category in {"ai", "automation", "dx", "crm"}:
        return StoryArcType.DIAGNOSIS_STRATEGY_EXECUTION, PlannerRuleDecision(
            rule_name="story_arc",
            selected_value="diagnosis_strategy_execution",
            reason="Operational or AI proposals need diagnosis, strategy, and execution logic.",
            confidence=0.82,
        )
    if any(key in text for key in ("competitor", "competition", "compare", "alternative")):
        return StoryArcType.INSIGHT_RECOMMENDATION, PlannerRuleDecision(
            rule_name="story_arc",
            selected_value="insight_recommendation",
            reason="Competitive signals require insight-led recommendation.",
            confidence=0.78,
        )
    if category in {"web", "branding", "hiring"}:
        return StoryArcType.OPPORTUNITY_SOLUTION_IMPACT, PlannerRuleDecision(
            rule_name="story_arc",
            selected_value="opportunity_solution_impact",
            reason="Market-facing proposals should connect opportunity, solution, and impact.",
            confidence=0.76,
        )
    return StoryArcType.PROBLEM_SOLUTION, PlannerRuleDecision(
        rule_name="story_arc",
        selected_value="problem_solution",
        reason="Default sales structure is problem to solution.",
        confidence=0.66,
    )


def infer_persuasion_strategy(category: str, context: ProposalContext) -> tuple[PersuasionStrategy, PlannerRuleDecision]:
    text = context_text(context)
    if any(key in text for key in ("cost", "reduce", "efficiency", "shorten", "time")):
        return PersuasionStrategy.COST_REDUCTION, PlannerRuleDecision(
            rule_name="persuasion_strategy",
            selected_value="cost_reduction",
            reason="The context emphasizes time or cost reduction.",
            confidence=0.78,
        )
    if category == "ai":
        return PersuasionStrategy.AI_ADOPTION, PlannerRuleDecision(
            rule_name="persuasion_strategy",
            selected_value="ai_adoption",
            reason="The category is AI adoption.",
            confidence=0.78,
        )
    if category == "web":
        return PersuasionStrategy.GROWTH, PlannerRuleDecision(
            rule_name="persuasion_strategy",
            selected_value="growth",
            reason="Web proposals often need growth and conversion framing.",
            confidence=0.7,
        )
    return PersuasionStrategy.ROI, PlannerRuleDecision(
        rule_name="persuasion_strategy",
        selected_value="roi",
        reason="ROI is the safest general executive decision frame.",
        confidence=0.68,
    )


def infer_deck_length(
    context: ProposalContext,
    seniority: AudienceSeniority,
    stage: DecisionStage,
) -> tuple[DeckLengthType, int, int, PlannerRuleDecision]:
    complexity = len(context.problems) + len(context.expected_outcomes)
    if seniority == AudienceSeniority.EXECUTIVE:
        return DeckLengthType.EXECUTIVE, 5, 10, PlannerRuleDecision(
            rule_name="deck_length",
            selected_value="executive",
            reason="Executive audiences need a concise deck with optional detail outside the main flow.",
            confidence=0.84,
        )
    if complexity >= 8 or stage == DecisionStage.PROCUREMENT:
        return DeckLengthType.DETAILED, 12, 25, PlannerRuleDecision(
            rule_name="deck_length",
            selected_value="detailed",
            reason="The context includes many problem and outcome signals.",
            confidence=0.78,
        )
    return DeckLengthType.STANDARD, 8, 14, PlannerRuleDecision(
        rule_name="deck_length",
        selected_value="standard",
        reason="A standard decision deck is sufficient for the provided context.",
        confidence=0.74,
    )


def section_sequence(
    *,
    category: str,
    story_arc: StoryArcType,
    seniority: AudienceSeniority,
    budget_present: bool,
    competition_present: bool,
    expected_outcomes_present: bool,
    length_type: DeckLengthType,
) -> tuple[list[SectionType], PlannerRuleDecision]:
    include_summary = seniority in {AudienceSeniority.EXECUTIVE, AudienceSeniority.SENIOR_MANAGER}
    include_roi = budget_present and seniority in {AudienceSeniority.EXECUTIVE, AudienceSeniority.SENIOR_MANAGER}
    include_pricing = budget_present
    include_competitor = competition_present and seniority != AudienceSeniority.EXECUTIVE
    include_appendix = length_type in {DeckLengthType.DETAILED, DeckLengthType.APPENDIX_HEAVY}

    if story_arc == StoryArcType.EXECUTIVE_DECISION:
        sequence = [
            SectionType.COVER,
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.PROBLEM,
            SectionType.SOLUTION,
            SectionType.KPI,
            SectionType.ROADMAP,
            SectionType.PRICING,
            SectionType.RISK,
            SectionType.NEXT_ACTION,
        ]
    elif story_arc == StoryArcType.DIAGNOSIS_STRATEGY_EXECUTION:
        sequence = [
            SectionType.COVER,
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.CURRENT_STATE,
            SectionType.PROBLEM,
            SectionType.STRATEGY,
            SectionType.SOLUTION,
            SectionType.KPI,
            SectionType.ROADMAP,
            SectionType.PRICING,
            SectionType.RISK,
            SectionType.NEXT_ACTION,
        ]
    elif story_arc == StoryArcType.OPPORTUNITY_SOLUTION_IMPACT:
        sequence = [
            SectionType.COVER,
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.PROBLEM,
            SectionType.OPPORTUNITY,
            SectionType.SOLUTION,
            SectionType.KPI,
            SectionType.ROADMAP,
            SectionType.PRICING,
            SectionType.NEXT_ACTION,
        ]
    elif story_arc == StoryArcType.INSIGHT_RECOMMENDATION:
        sequence = [
            SectionType.COVER,
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.PROBLEM,
            SectionType.INSIGHT,
            SectionType.STRATEGY,
            SectionType.SOLUTION,
            SectionType.KPI,
            SectionType.ROADMAP,
            SectionType.PRICING,
            SectionType.NEXT_ACTION,
        ]
    else:
        sequence = [
            SectionType.COVER,
            SectionType.EXECUTIVE_SUMMARY,
            SectionType.BACKGROUND,
            SectionType.PROBLEM,
            SectionType.INSIGHT,
            SectionType.SOLUTION,
            SectionType.KPI,
            SectionType.ROADMAP,
            SectionType.PRICING,
            SectionType.NEXT_ACTION,
        ]

    if not include_summary:
        sequence = [item for item in sequence if item != SectionType.EXECUTIVE_SUMMARY]
    if not expected_outcomes_present:
        sequence = [item for item in sequence if item not in {SectionType.KPI, SectionType.ROI}]
    if include_roi and SectionType.KPI in sequence:
        kpi_index = sequence.index(SectionType.KPI)
        sequence.insert(kpi_index + 1, SectionType.ROI)
    if not include_pricing:
        sequence = [item for item in sequence if item != SectionType.PRICING]
    if include_competitor:
        insert_after = SectionType.INSIGHT if SectionType.INSIGHT in sequence else SectionType.PROBLEM
        index = sequence.index(insert_after) + 1
        if SectionType.COMPETITOR not in sequence:
            sequence.insert(index, SectionType.COMPETITOR)
    if (
        category in {"ai", "automation", "dx", "crm"}
        and seniority != AudienceSeniority.EXECUTIVE
        and SectionType.APPROACH not in sequence
    ):
        insert_after = SectionType.SOLUTION
        index = sequence.index(insert_after) + 1 if insert_after in sequence else max(1, len(sequence) - 2)
        sequence.insert(index, SectionType.APPROACH)
    if include_appendix:
        sequence.append(SectionType.APPENDIX)

    return sequence, PlannerRuleDecision(
        rule_name="section_sequence",
        selected_value=",".join(item.value for item in sequence),
        reason=(
            "Sections were selected from story arc, audience seniority, budget, "
            "competition, expected outcomes, and category signals."
        ),
        confidence=0.8,
    )


def transition_for(previous: SectionType | None, current: SectionType, next_section: SectionType | None) -> TransitionType:
    if previous is None:
        return TransitionType.NONE
    if previous in {SectionType.PROBLEM, SectionType.CURRENT_STATE} and current in {
        SectionType.INSIGHT,
        SectionType.STRATEGY,
        SectionType.SOLUTION,
    }:
        return TransitionType.PROBLEM_TO_SOLUTION
    if previous in {SectionType.ROI, SectionType.KPI} and current in {SectionType.PRICING, SectionType.ESTIMATE}:
        return TransitionType.VALUE_TO_PRICE
    if previous == SectionType.RISK:
        return TransitionType.RISK_TO_MITIGATION
    if current == SectionType.NEXT_ACTION or next_section == SectionType.NEXT_ACTION:
        return TransitionType.SUMMARY_TO_ACTION
    return TransitionType.CONTINUE
