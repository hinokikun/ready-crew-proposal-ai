from typing import Dict, List, Optional

from .enums import BudgetType, EvidenceLevel, Persona, PresentationPack, ProjectCategory
from .models import ProposalStrategyInput, StrategyBrief
from .rules import (
    category_to_pack,
    choose_category,
    choose_persona,
    choose_strategy_and_story,
    estimate_pack_for,
    kpi_pack_for,
)
from .term_guard import build_term_rules, find_prohibited_terms


REQUIRED_SLIDES = [
    "hero",
    "executive_summary",
    "current_problem",
    "before_after",
    "architecture",
    "poc_plan",
    "kpi_measurement",
    "estimate_next_action",
]


OPTIONAL_SLIDES = ["risk", "roadmap", "appendix"]


def evaluate_strategy(strategy_input: ProposalStrategyInput) -> StrategyBrief:
    text = strategy_input.combined_text()
    category, secondary_category, category_reasons, category_conflict = choose_category(text)
    persona, secondary_personas, decision_maker, persona_reasons, persona_unknown = choose_persona(
        text, strategy_input.audience_hint
    )
    primary_strategy, secondary_strategies, story_type, strategy_reasons = choose_strategy_and_story(
        text, category, persona
    )
    primary_pack = category_to_pack(category)
    secondary_pack = (
        category_to_pack(secondary_category)
        if secondary_category and secondary_category != ProjectCategory.GENERIC_CONSULTING
        else None
    )
    allowed_terms, conditional_terms, prohibited_terms = build_term_rules(primary_pack, secondary_pack)
    source_term_hits = find_prohibited_terms(text, prohibited_terms)
    evidence_summary = _evidence_summary(strategy_input)
    missing_information = _missing_information(strategy_input, evidence_summary)
    confidence = _calculate_confidence(
        category=category,
        secondary_category=secondary_category,
        persona=persona,
        category_conflict=category_conflict,
        evidence_summary=evidence_summary,
        missing_information=missing_information,
        source_term_hits=source_term_hits,
        strategy_input=strategy_input,
    )
    human_review_required, human_review_reasons = _human_review_gate(
        confidence=confidence,
        category=category,
        persona=persona,
        category_conflict=category_conflict,
        missing_information=missing_information,
        source_term_hits=source_term_hits,
        strategy_input=strategy_input,
    )
    selection_reasons = (
        category_reasons
        + persona_reasons
        + strategy_reasons
        + [f"presentation pack {primary_pack.value} selected"]
    )
    if secondary_pack:
        selection_reasons.append(f"secondary pack {secondary_pack.value} selected")
    return StrategyBrief(
        project_category=category,
        secondary_category=secondary_category,
        primary_persona=persona,
        secondary_personas=secondary_personas,
        decision_maker=decision_maker,
        primary_strategy=primary_strategy,
        secondary_strategies=secondary_strategies,
        story_type=story_type,
        primary_pack=primary_pack,
        secondary_pack=secondary_pack,
        confidence=confidence,
        selection_reasons=selection_reasons,
        assumptions=_assumptions(strategy_input, persona_unknown),
        missing_information=missing_information,
        evidence_summary=evidence_summary,
        hero_theme=_hero_theme(category, primary_strategy),
        main_message=_main_message(category, primary_strategy),
        problem_theme=_problem_theme(category),
        before_after_type=_before_after_type(category),
        architecture_type=_architecture_type(category),
        roadmap_type=_roadmap_type(strategy_input, category),
        kpi_pack=kpi_pack_for(category, primary_strategy),
        estimate_pack=estimate_pack_for(category, text),
        priority_messages=_priority_messages(category, primary_strategy, persona),
        risk_messages=_risk_messages(category, strategy_input),
        next_actions=_next_actions(category, strategy_input),
        required_slide_types=REQUIRED_SLIDES,
        optional_slide_types=OPTIONAL_SLIDES,
        allowed_terms=allowed_terms,
        conditional_terms=conditional_terms,
        prohibited_terms=prohibited_terms,
        human_review_required=human_review_required,
        human_review_reasons=human_review_reasons,
    )


def _evidence_summary(strategy_input: ProposalStrategyInput) -> Dict[str, EvidenceLevel]:
    summary: Dict[str, EvidenceLevel] = {
        "budget": _level_for_text(strategy_input.budget),
        "schedule": _level_for_text(strategy_input.schedule),
        "kpi": EvidenceLevel.PROVIDED if strategy_input.expected_kpis else EvidenceLevel.MISSING,
        "problem": EvidenceLevel.PROVIDED if strategy_input.current_problems or strategy_input.project_summary else EvidenceLevel.MISSING,
        "deliverables": EvidenceLevel.PROVIDED if strategy_input.expected_deliverables else EvidenceLevel.MISSING,
        "integration": EvidenceLevel.PROVIDED if strategy_input.integrations else EvidenceLevel.MISSING,
    }
    for key, value in strategy_input.evidence.items():
        summary[key] = value
    return summary


def _level_for_text(value: str) -> EvidenceLevel:
    return EvidenceLevel.PROVIDED if (value or "").strip() else EvidenceLevel.MISSING


def _missing_information(
    strategy_input: ProposalStrategyInput, evidence_summary: Dict[str, EvidenceLevel]
) -> List[str]:
    missing = [key for key, level in evidence_summary.items() if level == EvidenceLevel.MISSING]
    if strategy_input.budget and strategy_input.budget_type == BudgetType.UNKNOWN:
        missing.append("budget_type")
    return sorted(set(missing))


def _calculate_confidence(
    *,
    category: ProjectCategory,
    secondary_category: Optional[ProjectCategory],
    persona: Persona,
    category_conflict: bool,
    evidence_summary: Dict[str, EvidenceLevel],
    missing_information: List[str],
    source_term_hits: List[str],
    strategy_input: ProposalStrategyInput,
) -> float:
    confidence = 0.34
    if category != ProjectCategory.GENERIC_CONSULTING:
        confidence += 0.22
    if secondary_category:
        confidence += 0.04
    if persona != Persona.UNKNOWN:
        confidence += 0.14
    if strategy_input.current_problems and strategy_input.proposed_solution:
        confidence += 0.10
    provided_count = sum(
        1
        for level in evidence_summary.values()
        if level in {EvidenceLevel.PROVIDED, EvidenceLevel.CONFIRMED}
    )
    confidence += min(provided_count * 0.025, 0.12)
    if category_conflict:
        confidence -= 0.08
    if source_term_hits:
        confidence -= 0.10
    confidence -= min(len(missing_information) * 0.025, 0.12)
    if _is_sparse(strategy_input):
        confidence = min(confidence, 0.48)
    return round(max(0.15, min(confidence, 0.94)), 2)


def _human_review_gate(
    *,
    confidence: float,
    category: ProjectCategory,
    persona: Persona,
    category_conflict: bool,
    missing_information: List[str],
    source_term_hits: List[str],
    strategy_input: ProposalStrategyInput,
) -> (bool, List[str]):
    reasons: List[str] = []
    if confidence < 0.62:
        reasons.append("confidence below review threshold")
    if category == ProjectCategory.GENERIC_CONSULTING:
        reasons.append("generic fallback selected")
    if persona == Persona.UNKNOWN:
        reasons.append("persona unknown")
    if category_conflict:
        reasons.append("category conflict detected")
    if source_term_hits:
        reasons.append("prohibited or conflicting category terms present in source")
    if "budget_type" in missing_information:
        reasons.append("budget exists but budget_type is unclear")
    if _is_sparse(strategy_input):
        reasons.append("input information is sparse")
    return bool(reasons), reasons


def _is_sparse(strategy_input: ProposalStrategyInput) -> bool:
    content_parts = [
        strategy_input.project_title,
        strategy_input.project_summary,
        strategy_input.proposed_solution,
        *strategy_input.business_goals,
        *strategy_input.current_problems,
        *strategy_input.expected_deliverables,
    ]
    return sum(1 for part in content_parts if str(part).strip()) <= 2


def _assumptions(strategy_input: ProposalStrategyInput, persona_unknown: bool) -> List[str]:
    assumptions: List[str] = []
    if persona_unknown:
        assumptions.append("audience is inferred as unknown because no reliable signal was provided")
    if strategy_input.budget_type in {BudgetType.UPPER_LIMIT, BudgetType.REFERENCE}:
        assumptions.append("budget is treated as planning guidance, not a formal estimate")
    if not strategy_input.expected_kpis:
        assumptions.append("KPI targets must be confirmed before final proposal")
    return assumptions


def _hero_theme(category: ProjectCategory, strategy) -> str:
    if category == ProjectCategory.VISION_OCR:
        return "assisted_recognition"
    if category == ProjectCategory.AUTOMATION:
        return "controlled_automation"
    if category == ProjectCategory.DIGITAL_EXPERIENCE:
        return "experience_improvement"
    if category == ProjectCategory.GENERIC_CONSULTING:
        return "decision_work_frame"
    return f"{strategy.value}_theme"


def _main_message(category: ProjectCategory, strategy) -> str:
    if category == ProjectCategory.VISION_OCR:
        return "AI候補提示と人の確認で判断を速く、安定させる"
    if category == ProjectCategory.AUTOMATION:
        return "定型業務を自動化し、例外対応に人の時間を戻す"
    if category == ProjectCategory.CONVERSATIONAL_AI:
        return "問い合わせ対応を標準化し、人へつなぐ判断を明確にする"
    if category == ProjectCategory.KNOWLEDGE_AI:
        return "必要な知識へすばやく到達し、判断の根拠を残す"
    if category == ProjectCategory.CRM_SALES_INTELLIGENCE:
        return "顧客情報から次の営業行動を見える化する"
    if category == ProjectCategory.GENERATIVE_AI_TRANSFORMATION:
        return "生成AIを安全に業務へ組み込み、作成と確認を速くする"
    if category == ProjectCategory.DIGITAL_EXPERIENCE:
        return "顧客接点を整理し、改善を継続できる体験へ変える"
    return "課題を整理し、実行判断へ進める"


def _problem_theme(category: ProjectCategory) -> str:
    return {
        ProjectCategory.VISION_OCR: "manual_variance_and_review_burden",
        ProjectCategory.AUTOMATION: "manual_repetition_and_exception_delay",
        ProjectCategory.CONVERSATIONAL_AI: "response_variance_and_escalation_gap",
        ProjectCategory.KNOWLEDGE_AI: "knowledge_access_and_source_uncertainty",
        ProjectCategory.CRM_SALES_INTELLIGENCE: "sales_visibility_and_followup_gap",
        ProjectCategory.GENERATIVE_AI_TRANSFORMATION: "uncontrolled_ai_use_and_review_burden",
        ProjectCategory.DIGITAL_EXPERIENCE: "fragmented_customer_journey",
    }.get(category, "unclear_problem_structure")


def _before_after_type(category: ProjectCategory) -> str:
    if category == ProjectCategory.GENERIC_CONSULTING:
        return "current_future_decision_model"
    return f"{category.value}_before_after"


def _architecture_type(category: ProjectCategory) -> str:
    if category == ProjectCategory.VISION_OCR:
        return "human_in_the_loop_ai"
    if category == ProjectCategory.AUTOMATION:
        return "trigger_bot_exception_approval"
    if category == ProjectCategory.GENERIC_CONSULTING:
        return "decision_operating_model"
    return f"{category.value}_architecture"


def _roadmap_type(strategy_input: ProposalStrategyInput, category: ProjectCategory) -> str:
    text = strategy_input.combined_text()
    if "poc" in text or "実証" in text:
        return "poc_to_production"
    if category == ProjectCategory.GENERIC_CONSULTING:
        return "discovery_to_decision"
    return "phased_rollout"


def _priority_messages(category: ProjectCategory, strategy, persona: Persona) -> List[str]:
    messages = [_main_message(category, strategy)]
    if persona in {Persona.CEO, Persona.EXECUTIVE}:
        messages.append("投資判断に必要な効果、リスク、次の承認事項を先に示す")
    elif persona == Persona.FIELD_LEADER:
        messages.append("日々の運用がどう変わるかを先に示す")
    elif persona == Persona.INFORMATION_SYSTEMS:
        messages.append("連携、権限、運用責任を明確にする")
    return messages


def _risk_messages(category: ProjectCategory, strategy_input: ProposalStrategyInput) -> List[str]:
    risks = list(strategy_input.risks)
    if category in {ProjectCategory.VISION_OCR, ProjectCategory.GENERATIVE_AI_TRANSFORMATION}:
        risks.append("AIの判断を最終決定にせず、人の確認を残す")
    if not risks:
        risks.append("未確定条件はPoCまたは要件確認で明確化する")
    return risks


def _next_actions(category: ProjectCategory, strategy_input: ProposalStrategyInput) -> List[str]:
    if category == ProjectCategory.GENERIC_CONSULTING:
        return ["対象範囲を確認する", "現状課題と意思決定者を確認する", "評価基準を合意する"]
    if "poc" in strategy_input.combined_text() or category in {
        ProjectCategory.VISION_OCR,
        ProjectCategory.GENERATIVE_AI_TRANSFORMATION,
        ProjectCategory.KNOWLEDGE_AI,
    }:
        return ["PoC対象範囲を確定する", "評価基準を合意する", "必要データと連携条件を確認する"]
    return ["対象業務を確定する", "導入範囲とスケジュールを確認する", "成功基準を合意する"]
