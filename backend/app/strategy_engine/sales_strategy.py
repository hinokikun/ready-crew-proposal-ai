from __future__ import annotations

from typing import Iterable

from .enums import Persona, ProjectCategory, StoryType, StrategyType
from .models import (
    DecisionMakerProfile,
    EvidenceClassification,
    ExpectedObjection,
    ProposalStrategyInput,
    SalesStrategyBrief,
    SalesStrategyRisk,
)
from .rules import choose_category, choose_persona, choose_strategy_and_story


DECISION_MAKER_PROFILES: dict[str, DecisionMakerProfile] = {
    Persona.CEO.value: DecisionMakerProfile(
        decision_maker=Persona.CEO.value,
        focus_points=["investment impact", "business risk", "speed to decision"],
        avoid_expressions=["tool-first explanation", "implementation detail first"],
        proposal_order=["business goal", "expected impact", "risk control", "decision request"],
    ),
    Persona.EXECUTIVE.value: DecisionMakerProfile(
        decision_maker=Persona.EXECUTIVE.value,
        focus_points=["ROI", "governance", "company-wide priority"],
        avoid_expressions=["unclear assumptions", "unverified numerical claims"],
        proposal_order=["executive summary", "investment logic", "roadmap", "approval items"],
    ),
    Persona.DEPARTMENT_HEAD.value: DecisionMakerProfile(
        decision_maker=Persona.DEPARTMENT_HEAD.value,
        focus_points=["department outcome", "resource impact", "implementation feasibility"],
        avoid_expressions=["too much vendor terminology"],
        proposal_order=["department issue", "solution scope", "operation plan", "approval criteria"],
    ),
    Persona.MANAGER.value: DecisionMakerProfile(
        decision_maker=Persona.MANAGER.value,
        focus_points=["team workload", "timeline", "practical action"],
        avoid_expressions=["abstract vision only"],
        proposal_order=["current workflow", "change points", "support plan", "next action"],
    ),
    Persona.FIELD_LEADER.value: DecisionMakerProfile(
        decision_maker=Persona.FIELD_LEADER.value,
        focus_points=["daily operation", "burden reduction", "exception handling"],
        avoid_expressions=["complete automation claims", "field burden hidden"],
        proposal_order=["current work", "human review design", "trial plan", "operation fit"],
    ),
    Persona.INFORMATION_SYSTEMS.value: DecisionMakerProfile(
        decision_maker=Persona.INFORMATION_SYSTEMS.value,
        focus_points=["security", "integration", "operations", "ownership"],
        avoid_expressions=["black-box AI", "unbounded data handling"],
        proposal_order=["system boundary", "integration", "security", "operation responsibility"],
    ),
    Persona.QUALITY_ASSURANCE.value: DecisionMakerProfile(
        decision_maker=Persona.QUALITY_ASSURANCE.value,
        focus_points=["criteria", "traceability", "variance reduction"],
        avoid_expressions=["accuracy guarantee without evidence"],
        proposal_order=["quality issue", "criteria", "review process", "measurement plan"],
    ),
    Persona.SALES.value: DecisionMakerProfile(
        decision_maker=Persona.SALES.value,
        focus_points=["customer value", "differentiation", "next action"],
        avoid_expressions=["internal-only benefit"],
        proposal_order=["customer pain", "positioning", "proof", "follow-up action"],
    ),
    Persona.UNKNOWN.value: DecisionMakerProfile(
        decision_maker=Persona.UNKNOWN.value,
        focus_points=["decision maker confirmation", "success criteria", "missing facts"],
        avoid_expressions=["assuming approval authority"],
        proposal_order=["known facts", "hypotheses", "questions", "review request"],
    ),
}


PROJECT_CATEGORY_SLIDES: dict[str, list[str]] = {
    ProjectCategory.VISION_OCR.value: ["Cover", "Problem", "Before / After", "Architecture", "PoC", "KPI", "Estimate", "Next Action"],
    ProjectCategory.AUTOMATION.value: ["Cover", "Current State", "Flow", "Before / After", "PoC", "KPI", "Risk", "Next Action"],
    ProjectCategory.CRM_SALES_INTELLIGENCE.value: ["Cover", "Problem", "Pipeline Analysis", "Proposal", "KPI", "Roadmap", "Estimate", "Next Action"],
    ProjectCategory.DIGITAL_EXPERIENCE.value: ["Cover", "Problem", "Customer Journey", "Proposal", "Comparison", "Timeline", "KPI", "Next Action"],
    ProjectCategory.GENERATIVE_AI_TRANSFORMATION.value: ["Cover", "Governance", "Use Case", "Architecture", "PoC", "Risk", "Roadmap", "Next Action"],
    ProjectCategory.CONVERSATIONAL_AI.value: ["Cover", "Problem", "Conversation Flow", "Escalation", "KPI", "Roadmap", "Risk", "Next Action"],
    ProjectCategory.KNOWLEDGE_AI.value: ["Cover", "Problem", "Knowledge Flow", "Architecture", "KPI", "Risk", "Roadmap", "Next Action"],
    ProjectCategory.GENERIC_CONSULTING.value: ["Cover", "Problem", "Analysis", "Proposal", "Roadmap", "KPI", "Estimate", "Next Action"],
}


def generate_sales_strategy_brief(strategy_input: ProposalStrategyInput) -> SalesStrategyBrief:
    text = strategy_input.combined_text()
    category, secondary_category, category_reasons, category_conflict = choose_category(text)
    persona, secondary_personas, decision_maker, persona_reasons, persona_unknown = choose_persona(
        text, strategy_input.audience_hint
    )
    strategy, secondary_strategies, story_type, strategy_reasons = choose_strategy_and_story(text, category, persona)
    competitive_situation = classify_competitive_situation(strategy_input, text)
    proposal_position = choose_proposal_position(strategy_input, category, strategy, text)
    tone = choose_presentation_tone(decision_maker, proposal_position, competitive_situation, text)
    evidence_classification = classify_evidence(strategy_input, persona_unknown=persona_unknown)
    objections = expected_objections_for(strategy_input, competitive_situation, proposal_position)
    risk_factors = risk_factors_for(strategy_input, category, evidence_classification)
    recommended_story_type = choose_recommended_story_type(story_type, decision_maker, proposal_position, text)
    recommended_slide_types = recommended_slides_for(category, objections, competitive_situation)
    confidence = calculate_sales_strategy_confidence(
        strategy_input=strategy_input,
        category=category,
        persona=persona,
        category_conflict=category_conflict,
        evidence_classification=evidence_classification,
    )
    human_review_reasons = human_review_reasons_for(
        confidence=confidence,
        category=category,
        persona=persona,
        category_conflict=category_conflict,
        evidence_classification=evidence_classification,
        objections=objections,
    )
    decision_process = decision_process_for(decision_maker, strategy_input)
    winning_strategy = winning_strategy_for(
        category=category,
        strategy=strategy,
        proposal_position=proposal_position,
        competitive_situation=competitive_situation,
        decision_maker=decision_maker,
    )
    summary = executive_summary_for(
        strategy_input=strategy_input,
        category=category,
        proposal_position=proposal_position,
        winning_strategy=winning_strategy,
    )
    selection_reasons = [
        *category_reasons,
        *persona_reasons,
        *strategy_reasons,
        f"competitive situation: {competitive_situation}",
        f"proposal position: {proposal_position}",
        f"presentation tone: {tone}",
    ]
    if secondary_category:
        selection_reasons.append(f"secondary category: {secondary_category.value}")
    if secondary_strategies:
        selection_reasons.append("secondary strategies: " + ", ".join(strategy.value for strategy in secondary_strategies))

    return SalesStrategyBrief(
        project_category=category.value,
        customer_industry=strategy_input.industry or "needs_confirmation",
        customer_size=customer_size_for(text),
        customer_maturity=customer_maturity_for(text),
        business_model=business_model_for(text),
        decision_maker=decision_maker.value,
        decision_process=decision_process,
        stakeholders=unique_strings([*strategy_input.stakeholders, *[item.value for item in secondary_personas]]),
        business_goal=first_or_default(strategy_input.business_goals, "needs_confirmation"),
        current_situation=strategy_input.project_summary or strategy_input.source_text[:240] or "needs_confirmation",
        pain_points=unique_strings(strategy_input.current_problems or evidence_classification.needs_confirmation[:3]),
        urgency=urgency_for(strategy_input),
        budget_status=budget_status_for(strategy_input),
        timeline=strategy_input.schedule or "needs_confirmation",
        competitive_situation=competitive_situation,
        proposal_position=proposal_position,
        winning_strategy=winning_strategy,
        expected_objections=objections,
        risk_factors=risk_factors,
        differentiation=differentiation_for(category, proposal_position, competitive_situation),
        recommended_story_type=recommended_story_type,
        recommended_slide_types=recommended_slide_types,
        recommended_presentation_tone=tone,
        executive_summary=summary,
        confidence=confidence,
        human_review_required=bool(human_review_reasons),
        human_review_reasons=human_review_reasons,
        decision_maker_profile=DECISION_MAKER_PROFILES.get(decision_maker.value, DECISION_MAKER_PROFILES[Persona.UNKNOWN.value]),
        evidence_classification=evidence_classification,
        selection_reasons=selection_reasons,
    )


def classify_competitive_situation(strategy_input: ProposalStrategyInput, text: str) -> str:
    competitors = " ".join(strategy_input.constraints + strategy_input.risks).lower()
    source = f"{text} {competitors}"
    if not any(keyword in source for keyword in ["competitor", "competition", "competitive", "比較", "競合", "他社", "vendor"]):
        return "no_clear_competitor"
    if any(keyword in source for keyword in ["price", "cost", "budget", "安価", "価格", "費用", "予算"]):
        return "price_competition"
    if any(keyword in source for keyword in ["quality", "accuracy", "品質", "精度", "正確"]):
        return "quality_competition"
    if any(keyword in source for keyword in ["speed", "quick", "short", "急ぎ", "短納期", "スピード"]):
        return "speed_competition"
    if any(keyword in source for keyword in ["dx", "digital", "全社", "デジタル"]):
        return "dx_competition"
    if any(keyword in source for keyword in ["ai", "ocr", "llm", "生成ai"]):
        return "ai_adoption_competition"
    if any(keyword in source for keyword in ["brand", "branding", "採用", "認知", "ブランド"]):
        return "brand_competition"
    return "quality_competition"


def choose_proposal_position(
    strategy_input: ProposalStrategyInput,
    category: ProjectCategory,
    strategy: StrategyType,
    text: str,
) -> str:
    if any(keyword in text for keyword in ["採用", "recruit", "人材"]):
        return "hiring"
    if any(keyword in text for keyword in ["brand", "branding", "認知", "ブランド"]):
        return "branding"
    if "ec" in text or "e-commerce" in text or "通販" in text:
        return "ec_improvement"
    if category == ProjectCategory.DIGITAL_EXPERIENCE:
        return "web_improvement"
    if category in {ProjectCategory.VISION_OCR, ProjectCategory.GENERATIVE_AI_TRANSFORMATION, ProjectCategory.KNOWLEDGE_AI}:
        return "ai_enablement"
    if strategy == StrategyType.COST_REDUCTION:
        return "cost_reduction"
    if strategy == StrategyType.CUSTOMER_EXPERIENCE:
        return "marketing"
    if category == ProjectCategory.AUTOMATION:
        return "business_improvement"
    if category == ProjectCategory.CRM_SALES_INTELLIGENCE:
        return "sales_growth"
    if any(goal for goal in strategy_input.business_goals if any(keyword in goal.lower() for keyword in ["売上", "growth", "sales"])):
        return "sales_growth"
    return "business_improvement"


def choose_presentation_tone(decision_maker: Persona, proposal_position: str, competitive_situation: str, text: str) -> str:
    if decision_maker in {Persona.CEO, Persona.EXECUTIVE}:
        return "Executive"
    if "data" in text or "kpi" in text or "%" in text or competitive_situation in {"price_competition", "quality_competition"}:
        return "Data Driven"
    if proposal_position in {"branding", "web_improvement", "ec_improvement", "marketing"}:
        return "Agency"
    if decision_maker in {Persona.INFORMATION_SYSTEMS, Persona.QUALITY_ASSURANCE}:
        return "Consulting"
    if proposal_position in {"ai_enablement", "dx"}:
        return "Formal"
    return "Friendly"


def classify_evidence(strategy_input: ProposalStrategyInput, *, persona_unknown: bool) -> EvidenceClassification:
    missing: list[str] = []
    needs_confirmation: list[str] = []
    hypothesis: list[str] = []
    ai_inferred: list[str] = []

    if not strategy_input.industry:
        missing.append("customer_industry")
    if persona_unknown:
        needs_confirmation.append("decision_maker")
    if not strategy_input.budget:
        needs_confirmation.append("budget")
    if not strategy_input.schedule:
        needs_confirmation.append("timeline")
    if not strategy_input.current_problems:
        missing.append("pain_points")
    if not strategy_input.expected_kpis:
        needs_confirmation.append("kpi")
    if not strategy_input.stakeholders:
        hypothesis.append("stakeholders")
    if not strategy_input.expected_deliverables:
        needs_confirmation.append("deliverables")
    if not strategy_input.integrations:
        hypothesis.append("integration_scope")
    if not strategy_input.risks:
        ai_inferred.append("risk_factors")
    return EvidenceClassification(
        missing=missing,
        hypothesis=hypothesis,
        needs_confirmation=needs_confirmation,
        ai_inferred=ai_inferred,
    )


def expected_objections_for(
    strategy_input: ProposalStrategyInput,
    competitive_situation: str,
    proposal_position: str,
) -> list[ExpectedObjection]:
    objections: list[ExpectedObjection] = []
    if not strategy_input.budget or competitive_situation == "price_competition":
        objections.append(
            ExpectedObjection(
                objection="price",
                reason="Budget fit or price comparison may become a decision blocker.",
                recommended_slide="Estimate",
                recommended_evidence="Scope, assumptions, and phased options.",
            )
        )
    if not strategy_input.schedule or any(keyword in (strategy_input.schedule or "").lower() for keyword in ["急", "short", "soon"]):
        objections.append(
            ExpectedObjection(
                objection="schedule",
                reason="Timeline feasibility needs explicit confirmation.",
                recommended_slide="Timeline",
                recommended_evidence="Milestones, decision gates, and dependency list.",
            )
        )
    if not strategy_input.expected_kpis:
        objections.append(
            ExpectedObjection(
                objection="ROI",
                reason="Outcome measurement is not confirmed.",
                recommended_slide="KPI",
                recommended_evidence="Baseline, target, and measurement method.",
            )
        )
    if proposal_position in {"ai_enablement", "business_improvement"} or strategy_input.integrations:
        objections.append(
            ExpectedObjection(
                objection="implementation_load",
                reason="Operational change and integration load may be questioned.",
                recommended_slide="Architecture",
                recommended_evidence="Human review boundary, integration method, and rollout scope.",
            )
        )
    if competitive_situation != "no_clear_competitor":
        objections.append(
            ExpectedObjection(
                objection="competitor_comparison",
                reason="The client may compare price, quality, or speed with other options.",
                recommended_slide="Comparison",
                recommended_evidence="Decision criteria and differentiation points.",
            )
        )
    return unique_objections(objections)[:6]


def risk_factors_for(
    strategy_input: ProposalStrategyInput,
    category: ProjectCategory,
    evidence_classification: EvidenceClassification,
) -> list[SalesStrategyRisk]:
    risks = [
        SalesStrategyRisk(category="provided", item=risk, reason="Provided in the source input.")
        for risk in strategy_input.risks[:5]
    ]
    for item in evidence_classification.missing:
        risks.append(SalesStrategyRisk(category="missing", item=item, reason="Required fact is not provided."))
    for item in evidence_classification.hypothesis:
        risks.append(SalesStrategyRisk(category="hypothesis", item=item, reason="The strategy can only assume this until confirmed."))
    for item in evidence_classification.needs_confirmation:
        risks.append(SalesStrategyRisk(category="needs_confirmation", item=item, reason="Sales should confirm before final proposal."))
    if category in {ProjectCategory.VISION_OCR, ProjectCategory.GENERATIVE_AI_TRANSFORMATION}:
        risks.append(
            SalesStrategyRisk(
                category="ai_inferred",
                item="ai_accuracy_and_human_review",
                reason="AI output should be positioned as support, not an unverified final judgment.",
            )
        )
    return risks[:10]


def choose_recommended_story_type(
    story_type: StoryType,
    decision_maker: Persona,
    proposal_position: str,
    text: str,
) -> str:
    if decision_maker in {Persona.CEO, Persona.EXECUTIVE}:
        return StoryType.ROI.value
    if proposal_position in {"ai_enablement"}:
        return StoryType.AI.value
    if proposal_position in {"dx"} or "dx" in text:
        return StoryType.DX.value
    if proposal_position in {"business_improvement", "cost_reduction"}:
        return StoryType.AUTOMATION.value
    if proposal_position in {"marketing", "web_improvement", "ec_improvement", "branding", "hiring"}:
        return StoryType.CUSTOMER_EXPERIENCE.value
    return story_type.value


def recommended_slides_for(
    category: ProjectCategory,
    objections: Iterable[ExpectedObjection],
    competitive_situation: str,
) -> list[str]:
    slides = list(PROJECT_CATEGORY_SLIDES.get(category.value, PROJECT_CATEGORY_SLIDES[ProjectCategory.GENERIC_CONSULTING.value]))
    if competitive_situation != "no_clear_competitor" and "Comparison" not in slides:
        slides.insert(min(4, len(slides)), "Comparison")
    for objection in objections:
        if objection.recommended_slide not in slides:
            slides.insert(max(1, len(slides) - 2), objection.recommended_slide)
    return unique_strings(slides)[:10]


def calculate_sales_strategy_confidence(
    *,
    strategy_input: ProposalStrategyInput,
    category: ProjectCategory,
    persona: Persona,
    category_conflict: bool,
    evidence_classification: EvidenceClassification,
) -> float:
    score = 0.36
    if category != ProjectCategory.GENERIC_CONSULTING:
        score += 0.18
    if persona != Persona.UNKNOWN:
        score += 0.14
    if strategy_input.business_goals:
        score += 0.08
    if strategy_input.current_problems:
        score += 0.08
    if strategy_input.budget:
        score += 0.05
    if strategy_input.schedule:
        score += 0.05
    if strategy_input.expected_kpis:
        score += 0.04
    score -= min(len(evidence_classification.missing) * 0.04, 0.16)
    score -= min(len(evidence_classification.needs_confirmation) * 0.025, 0.12)
    if category_conflict:
        score -= 0.08
    return round(max(0.15, min(0.95, score)), 2)


def human_review_reasons_for(
    *,
    confidence: float,
    category: ProjectCategory,
    persona: Persona,
    category_conflict: bool,
    evidence_classification: EvidenceClassification,
    objections: list[ExpectedObjection],
) -> list[str]:
    reasons: list[str] = []
    if confidence < 0.62:
        reasons.append("sales strategy confidence is below review threshold")
    if category == ProjectCategory.GENERIC_CONSULTING:
        reasons.append("project category is generic fallback")
    if persona == Persona.UNKNOWN:
        reasons.append("decision maker is not confirmed")
    if category_conflict:
        reasons.append("multiple project categories have similar evidence")
    if evidence_classification.missing:
        reasons.append("required business facts are missing")
    if len(objections) >= 4:
        reasons.append("many expected objections require sales review")
    return reasons


def decision_process_for(decision_maker: Persona, strategy_input: ProposalStrategyInput) -> str:
    if decision_maker in {Persona.CEO, Persona.EXECUTIVE}:
        return "executive_approval"
    if decision_maker == Persona.INFORMATION_SYSTEMS:
        return "technical_security_review"
    if decision_maker == Persona.FIELD_LEADER:
        return "field_validation_then_department_approval"
    if decision_maker == Persona.UNKNOWN:
        return "needs_confirmation"
    if len(strategy_input.stakeholders) >= 3:
        return "multi_stakeholder_review"
    return "department_approval"


def winning_strategy_for(
    *,
    category: ProjectCategory,
    strategy: StrategyType,
    proposal_position: str,
    competitive_situation: str,
    decision_maker: Persona,
) -> str:
    if competitive_situation == "price_competition":
        return "Win by phased scope, measurable value, and transparent assumptions instead of discounting first."
    if competitive_situation == "quality_competition":
        return "Win by showing evaluation criteria, review gates, and traceable quality control."
    if competitive_situation == "speed_competition":
        return "Win by proposing a narrow first release with clear dependencies and decision gates."
    if proposal_position == "ai_enablement":
        return "Win by positioning AI as decision support with human review, evidence, and safe rollout."
    if decision_maker in {Persona.CEO, Persona.EXECUTIVE} or strategy == StrategyType.ROI:
        return "Win by connecting the proposal to investment decision, risk control, and next approval action."
    if category == ProjectCategory.DIGITAL_EXPERIENCE:
        return "Win by connecting customer journey improvement to measurable conversion and operation outcomes."
    return "Win by turning the current issue into a concrete scope, measurement plan, and next action."


def executive_summary_for(
    *,
    strategy_input: ProposalStrategyInput,
    category: ProjectCategory,
    proposal_position: str,
    winning_strategy: str,
) -> str:
    title = strategy_input.project_title or "This proposal"
    goal = first_or_default(strategy_input.business_goals, "the client's confirmed business goal")
    problem = first_or_default(strategy_input.current_problems, "the current operational issue")
    return (
        f"{title} should be positioned as {proposal_position} for {category.value}. "
        f"The proposal should start from {problem}, connect to {goal}, and use this strategy: {winning_strategy}"
    )


def differentiation_for(category: ProjectCategory, proposal_position: str, competitive_situation: str) -> list[str]:
    points = ["clear decision criteria", "phased implementation", "human review for unconfirmed assumptions"]
    if category == ProjectCategory.VISION_OCR:
        points.append("human-in-the-loop accuracy improvement")
    if category == ProjectCategory.AUTOMATION:
        points.append("exception handling design")
    if proposal_position in {"web_improvement", "ec_improvement", "marketing"}:
        points.append("customer journey and conversion linkage")
    if competitive_situation != "no_clear_competitor":
        points.append("explicit competitor comparison axis")
    return unique_strings(points)


def customer_size_for(text: str) -> str:
    if any(keyword in text for keyword in ["enterprise", "large", "全社", "大規模", "複数部門"]):
        return "enterprise"
    if any(keyword in text for keyword in ["small", "startup", "少人数", "中小"]):
        return "small_or_mid"
    return "unknown"


def customer_maturity_for(text: str) -> str:
    if any(keyword in text for keyword in ["poc", "検証", "trial", "初期"]):
        return "exploration"
    if any(keyword in text for keyword in ["運用", "改善", "拡張", "標準化"]):
        return "improvement"
    if any(keyword in text for keyword in ["全社", "統制", "ガバナンス"]):
        return "scaling"
    return "unknown"


def business_model_for(text: str) -> str:
    if any(keyword in text for keyword in ["ec", "通販", "購入", "cart"]):
        return "commerce"
    if any(keyword in text for keyword in ["saas", "subscription", "月額"]):
        return "subscription"
    if any(keyword in text for keyword in ["製造", "工場", "物流", "在庫"]):
        return "operations"
    if any(keyword in text for keyword in ["採用", "人材", "教育"]):
        return "people_operations"
    return "unknown"


def urgency_for(strategy_input: ProposalStrategyInput) -> str:
    text = f"{strategy_input.schedule} {strategy_input.source_text}".lower()
    if any(keyword in text for keyword in ["urgent", "asap", "今月", "来月", "急ぎ"]):
        return "high"
    if strategy_input.schedule:
        return "scheduled"
    return "needs_confirmation"


def budget_status_for(strategy_input: ProposalStrategyInput) -> str:
    if not strategy_input.budget:
        return "needs_confirmation"
    return strategy_input.budget_type.value


def first_or_default(items: list[str], default: str) -> str:
    return next((item for item in items if item), default)


def unique_strings(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def unique_objections(items: Iterable[ExpectedObjection]) -> list[ExpectedObjection]:
    seen: set[str] = set()
    result: list[ExpectedObjection] = []
    for item in items:
        if item.objection in seen:
            continue
        seen.add(item.objection)
        result.append(item)
    return result
