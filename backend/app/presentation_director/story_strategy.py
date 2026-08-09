"""Story strategy rules."""

from __future__ import annotations

from .models import AudienceAnalysis, DecisionStage, PresentationDirectorInput, StoryStrategyDecision


def select_story_strategy(
    input_data: PresentationDirectorInput,
    audience: AudienceAnalysis,
    stage: DecisionStage,
) -> StoryStrategyDecision:
    if stage == "poc_proposal":
        selected = "PoC Hypothesis → Test → Evaluation → Scale"
        narrative = "現状の判断ばらつきから入り、PoC仮説、検証条件、評価指標、次の合意へ進む"
        rejected = (
            "Executive Decision → Options → Recommendation → Commitment",
            "Opportunity → Strategy → Execution → Return",
            "Customer Journey → Pain → Intervention → Outcome",
        )
        reason = "今回の目的は本番導入の即決ではなく、検証範囲と評価条件への合意であるため"
        evidence_fit = "KPIは存在するがROIはrequires_confirmationのため、効果断定より検証設計を優先"
    elif audience.primary_audience_type == "executive":
        selected = "Why Now → Risk → Proposal → Decision"
        narrative = "なぜ今か、放置リスク、提案、意思決定事項の順で短く判断材料を提示する"
        rejected = ("PoC Hypothesis → Test → Evaluation → Scale", "Customer Journey → Pain → Intervention → Outcome")
        reason = "経営者は詳細より投資判断とリスクを重視するため"
        evidence_fit = "重要数値の近くに根拠を置き、詳細根拠はAppendixへ移す"
    else:
        selected = "Problem → Cause → Solution → Value"
        narrative = "課題、原因、解決策、価値の順で部門判断を支援する"
        rejected = ("Evidence → Insight → Recommendation → Action", "Executive Decision → Options → Recommendation → Commitment")
        reason = "部門責任者が納得しやすい因果の流れを優先するため"
        evidence_fit = "顧客ヒアリング事実と仮説を分けて配置する"
    return StoryStrategyDecision(
        selected_story_strategy=selected,
        narrative_arc=narrative,
        rejected_story_strategies=rejected,
        selection_reason=reason,
        audience_fit=f"{audience.primary_audience}が必要とする判断材料に合わせる",
        sales_stage_fit=f"{stage}の目的に合わせ、次の合意事項を最後に置く",
        evidence_fit=evidence_fit,
        risk="未確認のROIや競合情報は断定せず、確認事項としてNotesまたはAppendixへ移す",
    )
