"""Deterministic message rules for Presentation Engine 2.0 Phase 2C."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..deck_enums import AudienceSeniority, SectionType, SlideRole
from ..deck_models import DeckBlueprint, SlidePlanItem
from ..deck_planner.planner_models import ProposalContext
from ..evidence_planner.evidence_models import (
    EvidenceConfidence,
    EvidencePriority,
    EvidenceRequirement,
    MissingEvidenceSeverity,
    SlideEvidencePlan,
)
from .designer_contracts import STYLE_PROFILES
from .designer_enums import (
    DisclosureType,
    EvidenceAlignmentLevel,
    MessageConfidence,
    MessagePurpose,
    MessageRiskLevel,
    MessageStrength,
    MessageStyle,
    MessageTone,
)
from .designer_models import (
    EvidenceUsage,
    MessageConstraint,
    MessageSourceReference,
    MessageWarning,
    MissingEvidenceDisclosure,
    NumericClaim,
    SupportingMessage,
    UnsupportedClaim,
)
from .designer_normalizers import collapse_whitespace


@dataclass(frozen=True)
class MessageRuleDecision:
    style: MessageStyle
    tone: MessageTone
    purpose: MessagePurpose
    strength: MessageStrength
    confidence: MessageConfidence
    evidence_alignment: EvidenceAlignmentLevel
    reason: str


HEADLINE_BY_SECTION: dict[str, str] = {
    SectionType.COVER.value: "{project}の判断軸を明確にする",
    SectionType.EXECUTIVE_SUMMARY.value: "結論と判断材料を先にそろえる",
    SectionType.BACKGROUND.value: "背景を共有し検討の前提をそろえる",
    SectionType.CURRENT_STATE.value: "現状業務の確認点を一枚で整理する",
    SectionType.PROBLEM.value: "課題の影響を事実ベースで共有する",
    SectionType.INSIGHT.value: "課題の背景から提案方向を定める",
    SectionType.OPPORTUNITY.value: "今取り組む価値を判断材料に変える",
    SectionType.COMPETITOR.value: "比較軸をそろえて選定リスクを下げる",
    SectionType.STRATEGY.value: "採るべき方針を意思決定へつなげる",
    SectionType.SOLUTION.value: "提案内容を実行判断へつなげる",
    SectionType.APPROACH.value: "進め方を現場で確認できる形にする",
    SectionType.ROADMAP.value: "導入判断から実行手順までを見通す",
    SectionType.TIMELINE.value: "進行順と判断時点を先に合わせる",
    SectionType.KPI.value: "評価指標を先に決めて効果を確認する",
    SectionType.ROI.value: "投資対効果は前提を分けて判断する",
    SectionType.PRICING.value: "費用は範囲と前提条件で判断する",
    SectionType.ESTIMATE.value: "概算はPoC範囲と条件で判断する",
    SectionType.RISK.value: "懸念点を先に扱い導入リスクを下げる",
    SectionType.FAQ.value: "想定質問を先回りして不安を減らす",
    SectionType.NEXT_ACTION.value: "次回合意すべき行動を明確にする",
    SectionType.CLOSING.value: "合意事項と次の一歩を残す",
    SectionType.APPENDIX.value: "補足情報は判断の裏付けに限定する",
}


MAIN_BY_SECTION: dict[str, str] = {
    SectionType.COVER.value: "この資料では、案件の目的、検討理由、次の判断事項を営業説明しやすい順に整理します。",
    SectionType.EXECUTIVE_SUMMARY.value: "意思決定に必要な課題、提案方針、期待成果、次のアクションを先に確認できる構成です。",
    SectionType.PROBLEM.value: "顧客が抱える課題を確認済み事実と不足情報に分け、提案の前提を曖昧にしないことが狙いです。",
    SectionType.CURRENT_STATE.value: "現行業務の流れと詰まりどころを整理し、どの部分を改善対象にするかを確認します。",
    SectionType.INSIGHT.value: "課題の背景と判断材料を結び、単なる機能紹介ではなく選ぶ理由を明確にします。",
    SectionType.COMPETITOR.value: "代替案との比較軸を先に定め、価格だけでなく適合性とリスクで判断できるようにします。",
    SectionType.STRATEGY.value: "顧客の意思決定者に合わせ、採るべき方針と次に確認すべき条件を明確にします。",
    SectionType.SOLUTION.value: "提案内容は期待成果と確認条件に接続し、導入後の変化を説明できる形にします。",
    SectionType.APPROACH.value: "実行手順と確認ポイントを示し、導入負荷や現場適合性への不安を下げます。",
    SectionType.ROADMAP.value: "検討、PoC、判断、本番化までの流れを分け、どこで何を決めるかを明確にします。",
    SectionType.TIMELINE.value: "進行順、担当、判断時点を確認し、スケジュール面の不確実性を下げます。",
    SectionType.KPI.value: "成果を主観で語らず、現状値、目標値、判定基準を分けて確認します。",
    SectionType.ROI.value: "金額や効果は仮説と確認済み情報を分け、無理なROI断定を避けて判断材料化します。",
    SectionType.PRICING.value: "費用は対象範囲、前提条件、未確定事項と一緒に提示し、誤解を防ぎます。",
    SectionType.ESTIMATE.value: "概算見積は正式見積ではなく、検討範囲を合わせるためのたたき台として扱います。",
    SectionType.RISK.value: "想定リスクと対策を先に示し、導入判断で確認すべき論点を残します。",
    SectionType.NEXT_ACTION.value: "次に確認する情報、合意する範囲、担当を明確にし、商談後の停滞を防ぎます。",
    SectionType.CLOSING.value: "本日の判断材料をまとめ、次の合意に向けた行動を明確にします。",
}


SECTION_PURPOSES: dict[str, MessagePurpose] = {
    SectionType.COVER.value: MessagePurpose.FRAME_DECISION,
    SectionType.EXECUTIVE_SUMMARY.value: MessagePurpose.FRAME_DECISION,
    SectionType.BACKGROUND.value: MessagePurpose.ALIGN_CONTEXT,
    SectionType.CURRENT_STATE.value: MessagePurpose.EXPLAIN_PROBLEM,
    SectionType.PROBLEM.value: MessagePurpose.EXPLAIN_PROBLEM,
    SectionType.INSIGHT.value: MessagePurpose.SHARE_INSIGHT,
    SectionType.OPPORTUNITY.value: MessagePurpose.SHARE_INSIGHT,
    SectionType.COMPETITOR.value: MessagePurpose.COMPARE_OPTIONS,
    SectionType.STRATEGY.value: MessagePurpose.RECOMMEND_ACTION,
    SectionType.SOLUTION.value: MessagePurpose.RECOMMEND_ACTION,
    SectionType.APPROACH.value: MessagePurpose.RECOMMEND_ACTION,
    SectionType.ROADMAP.value: MessagePurpose.RECOMMEND_ACTION,
    SectionType.TIMELINE.value: MessagePurpose.RECOMMEND_ACTION,
    SectionType.KPI.value: MessagePurpose.PROVE_VALUE,
    SectionType.ROI.value: MessagePurpose.EXPLAIN_INVESTMENT,
    SectionType.PRICING.value: MessagePurpose.EXPLAIN_INVESTMENT,
    SectionType.ESTIMATE.value: MessagePurpose.EXPLAIN_INVESTMENT,
    SectionType.RISK.value: MessagePurpose.REDUCE_RISK,
    SectionType.NEXT_ACTION.value: MessagePurpose.CLOSE_NEXT_STEP,
    SectionType.CLOSING.value: MessagePurpose.CLOSE_NEXT_STEP,
}


def project_short_name(context: ProposalContext, fallback: str = "本案件") -> str:
    value = context.project_name or context.proposal_category or context.industry or fallback
    value = collapse_whitespace(value)
    if len(value) <= 22:
        return value
    return value[:21] + "…"


def section_type_for(deck: DeckBlueprint, slide: SlidePlanItem) -> str:
    section = next((item for item in deck.sections if item.section_id == slide.section_id), None)
    return str(section.section_type) if section else "unknown"


def style_for(deck: DeckBlueprint, slide: SlidePlanItem, evidence: SlideEvidencePlan) -> MessageStyle:
    section_type = evidence.section_type
    if deck.audience_seniority == AudienceSeniority.EXECUTIVE.value:
        return MessageStyle.EXECUTIVE
    if section_type in {SectionType.ROI.value, SectionType.PRICING.value, SectionType.ESTIMATE.value}:
        return MessageStyle.FINANCIAL
    if section_type in {SectionType.KPI.value, SectionType.INSIGHT.value, SectionType.COMPETITOR.value}:
        return MessageStyle.CONSULTING
    if section_type in {SectionType.ROADMAP.value, SectionType.TIMELINE.value, SectionType.APPROACH.value}:
        return MessageStyle.OPERATIONAL
    if "technical" in str(deck.primary_audience) or section_type in {SectionType.SOLUTION.value, SectionType.SCOPE.value}:
        return MessageStyle.TECHNICAL
    if slide.slide_role in {SlideRole.RECOMMENDATION.value, SlideRole.CLOSING.value}:
        return MessageStyle.SALES
    return MessageStyle.NEUTRAL


def confidence_from_evidence(evidence: SlideEvidencePlan) -> MessageConfidence:
    if any(warning.severity == MissingEvidenceSeverity.BLOCKING.value for warning in evidence.missing_evidence_warnings):
        return MessageConfidence.LOW
    if evidence.evidence_confidence == EvidenceConfidence.MISSING.value:
        return MessageConfidence.LOW
    if evidence.evidence_confidence in {EvidenceConfidence.VERIFIED.value, EvidenceConfidence.LIKELY.value}:
        return MessageConfidence.HIGH
    return MessageConfidence.MEDIUM


def alignment_from_evidence(evidence: SlideEvidencePlan) -> EvidenceAlignmentLevel:
    if any(warning.severity == MissingEvidenceSeverity.BLOCKING.value for warning in evidence.missing_evidence_warnings):
        return EvidenceAlignmentLevel.EVIDENCE_MISSING
    if evidence.evidence_confidence == EvidenceConfidence.MISSING.value:
        return EvidenceAlignmentLevel.EVIDENCE_MISSING
    if evidence.missing_evidence_warnings:
        return EvidenceAlignmentLevel.ASSUMPTION_REQUIRED
    if evidence.required_evidence and all(
        item.confidence in {EvidenceConfidence.VERIFIED.value, EvidenceConfidence.LIKELY.value}
        for item in evidence.required_evidence
    ):
        return EvidenceAlignmentLevel.EVIDENCE_SUPPORTED
    return EvidenceAlignmentLevel.PARTIALLY_SUPPORTED


def purpose_for(section_type: str) -> MessagePurpose:
    return SECTION_PURPOSES.get(section_type, MessagePurpose.ALIGN_CONTEXT)


def headline_for(deck: DeckBlueprint, slide: SlidePlanItem, context: ProposalContext, evidence: SlideEvidencePlan) -> str:
    template = HEADLINE_BY_SECTION.get(evidence.section_type, "{project}の検討論点を整理する")
    text = template.format(project=project_short_name(context))
    if len(text) <= 60:
        return text
    return text[:59] + "…"


def main_message_for(deck: DeckBlueprint, slide: SlidePlanItem, context: ProposalContext, evidence: SlideEvidencePlan) -> str:
    text = MAIN_BY_SECTION.get(evidence.section_type) or slide.key_message or deck.core_thesis
    text = collapse_whitespace(text)
    if len(text) <= 120:
        return text
    return text[:119] + "…"


def key_takeaway_for(deck: DeckBlueprint, slide: SlidePlanItem, context: ProposalContext, evidence: SlideEvidencePlan) -> str:
    if evidence.section_type in {SectionType.PRICING.value, SectionType.ESTIMATE.value, SectionType.ROI.value}:
        text = "金額・効果は前提条件と確認事項を分けて判断します。"
    elif evidence.section_type == SectionType.NEXT_ACTION.value:
        text = "次に合意する情報と担当を明確にします。"
    elif evidence.missing_evidence_warnings:
        text = "不足情報を確認すれば、提案の説得力を高められます。"
    elif deck.key_takeaways:
        text = deck.key_takeaways[0]
    else:
        text = "判断に必要な論点を一枚で確認します。"
    return text[:80]


def speaker_note_for(deck: DeckBlueprint, slide: SlidePlanItem, context: ProposalContext, evidence: SlideEvidencePlan) -> str:
    warnings = evidence.missing_evidence_warnings
    if warnings:
        warning_text = "、".join(w.message for w in warnings[:2])
        text = f"営業担当は、このページを説明する前に不足情報を確認してください。確認論点: {warning_text}"
    else:
        text = (
            "営業担当は、顧客の関心に合わせて見出し、判断材料、次の確認事項の順で説明してください。"
            "数値や比較は根拠がある範囲だけを扱います。"
        )
    return collapse_whitespace(text)[:300]


def supporting_messages_for(evidence: SlideEvidencePlan) -> list[SupportingMessage]:
    messages: list[SupportingMessage] = []
    for index, item in enumerate(evidence.required_evidence[:3]):
        purpose = MessagePurpose.PROVE_VALUE
        if item.source_type == "competitor_analysis":
            purpose = MessagePurpose.COMPARE_OPTIONS
        elif item.source_type == "financial_estimate":
            purpose = MessagePurpose.EXPLAIN_INVESTMENT
        elif item.customer_proof_required:
            purpose = MessagePurpose.EXPLAIN_PROBLEM
        label = collapse_whitespace(item.label)
        messages.append(
            SupportingMessage(
                supporting_message_id=f"support-{evidence.slide_blueprint_id}-{index + 1:02d}",
                text=f"{label}を確認する"[:80],
                purpose=purpose,
                evidence_ids=[item.requirement_id],
            )
        )
    return messages


def evidence_usage_for(evidence: SlideEvidencePlan) -> list[EvidenceUsage]:
    usages: list[EvidenceUsage] = []
    for item in evidence.required_evidence:
        if item.confidence == EvidenceConfidence.MISSING.value:
            continue
        usages.append(
            EvidenceUsage(
                evidence_id=item.requirement_id,
                usage=f"{item.label}を主張の裏付けとして参照",
                source_type=str(item.source_type),
                confidence=confidence_from_requirement(item),
            )
        )
    return usages


def confidence_from_requirement(item: EvidenceRequirement) -> MessageConfidence:
    if item.confidence in {EvidenceConfidence.VERIFIED.value, EvidenceConfidence.LIKELY.value}:
        return MessageConfidence.HIGH
    if item.confidence == EvidenceConfidence.MISSING.value:
        return MessageConfidence.LOW
    return MessageConfidence.MEDIUM


def numeric_claims_for(context: ProposalContext, evidence: SlideEvidencePlan) -> list[NumericClaim]:
    numeric_requirements = [
        item
        for item in evidence.required_evidence
        if item.numeric_required and item.confidence != EvidenceConfidence.MISSING.value
    ]
    if not numeric_requirements or not context.budget_range:
        return []
    first = numeric_requirements[0]
    return [
        NumericClaim(
            claim_id=f"num-{evidence.slide_blueprint_id}-budget",
            label="予算・費用前提",
            value=context.budget_range[:80],
            unit=None,
            is_trial_calculation=True,
            basis_evidence_ids=[first.requirement_id],
            confidence=MessageConfidence.MEDIUM,
        )
    ]


def missing_disclosures_for(evidence: SlideEvidencePlan) -> list[MissingEvidenceDisclosure]:
    disclosures: list[MissingEvidenceDisclosure] = []
    for index, warning in enumerate(evidence.missing_evidence_warnings[:10]):
        disclosures.append(
            MissingEvidenceDisclosure(
                disclosure_id=f"disc-{evidence.slide_blueprint_id}-{index + 1:02d}",
                disclosure_type=DisclosureType.NEEDS_CONFIRMATION
                if warning.severity != MissingEvidenceSeverity.BLOCKING.value
                else DisclosureType.ASSUMPTION,
                message=warning.message[:220],
                related_evidence_ids=warning.related_requirement_ids,
                blocking=warning.severity == MissingEvidenceSeverity.BLOCKING.value,
            )
        )
    return disclosures


def warnings_for(evidence: SlideEvidencePlan) -> list[MessageWarning]:
    return [
        MessageWarning(
            warning_id=f"msg-{warning.warning_id}-{evidence.slide_blueprint_id}",
            message=warning.message,
            risk_level=MessageRiskLevel.BLOCKING
            if warning.severity == MissingEvidenceSeverity.BLOCKING.value
            else MessageRiskLevel.MEDIUM,
            related_evidence_ids=warning.related_requirement_ids,
        )
        for warning in evidence.missing_evidence_warnings
    ]


def source_references_for(evidence: SlideEvidencePlan) -> list[MessageSourceReference]:
    return [
        MessageSourceReference(
            source_id=item.requirement_id,
            source_type=str(item.source_type),
            label=item.label,
            related_evidence_ids=[item.requirement_id],
        )
        for item in evidence.required_evidence[:8]
    ]


def unsupported_claims_for(evidence: SlideEvidencePlan) -> list[UnsupportedClaim]:
    if not evidence.missing_evidence_warnings:
        return []
    return [
        UnsupportedClaim(
            claim_id=f"unsupported-{evidence.slide_blueprint_id}-{index + 1:02d}",
            text=warning.message[:160],
            reason="Evidence Planner marked required evidence as missing.",
            recommended_action=warning.suggested_action[:220],
        )
        for index, warning in enumerate(evidence.missing_evidence_warnings[:2])
        if warning.severity == MissingEvidenceSeverity.BLOCKING.value
    ]


def constraints_for() -> list[MessageConstraint]:
    return [
        MessageConstraint(
            constraint_id="msg-boundary-no-slide-blueprint",
            label="Slide Blueprint generation is out of scope.",
            detail="Phase 2C can emit message fields only.",
            blocking=True,
        ),
        MessageConstraint(
            constraint_id="msg-boundary-no-visual-rendering",
            label="Visual, diagram, layout, theme, typography, and PPTX are out of scope.",
            detail="Renderer-facing details are reserved for later phases.",
            blocking=True,
        ),
    ]


def unused_required_evidence_ids(evidence: SlideEvidencePlan, used_ids: Iterable[str]) -> list[str]:
    used = set(used_ids)
    return [item.requirement_id for item in evidence.required_evidence if item.requirement_id not in used]


def message_rule_decision(deck: DeckBlueprint, slide: SlidePlanItem, evidence: SlideEvidencePlan) -> MessageRuleDecision:
    style = style_for(deck, slide, evidence)
    profile = STYLE_PROFILES[style.value]
    confidence = confidence_from_evidence(evidence)
    alignment = alignment_from_evidence(evidence)
    strength = MessageStrength.CLEAR if confidence != MessageConfidence.LOW else MessageStrength.MODERATE
    if any(warning.severity == MissingEvidenceSeverity.BLOCKING.value for warning in evidence.missing_evidence_warnings):
        strength = MessageStrength.WEAK
    return MessageRuleDecision(
        style=style,
        tone=profile.tone,
        purpose=purpose_for(evidence.section_type),
        strength=strength,
        confidence=confidence,
        evidence_alignment=alignment,
        reason=f"{evidence.section_type} section and {deck.audience_seniority} audience selected {style.value} style.",
    )


def evidence_alignment_summary_for(evidence: SlideEvidencePlan, alignment: EvidenceAlignmentLevel) -> str:
    if alignment == EvidenceAlignmentLevel.EVIDENCE_SUPPORTED:
        return "Required evidence is available enough to support the message direction."
    if alignment == EvidenceAlignmentLevel.PARTIALLY_SUPPORTED:
        return "Some evidence is usable, but additional confirmation can improve persuasiveness."
    if alignment == EvidenceAlignmentLevel.ASSUMPTION_REQUIRED:
        return "The message can be drafted, but missing evidence must be disclosed and confirmed."
    if alignment == EvidenceAlignmentLevel.EVIDENCE_MISSING:
        return "Critical evidence is missing; avoid strong claims until the missing items are confirmed."
    return "Evidence is not required for this slide message."
