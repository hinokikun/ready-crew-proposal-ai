"""Deck objective selection."""

from __future__ import annotations

from .models import DeckObjective, DecisionStage, PresentationDirectorInput


def decide_deck_objective(input_data: PresentationDirectorInput, stage: DecisionStage) -> DeckObjective:
    if stage == "poc_proposal":
        return DeckObjective(
            objective="PoC条件と次回合意事項を確定する",
            sub_objectives=("課題構造に合意してもらう", "評価指標と対象範囲を確認する"),
            expected_decision="PoC範囲・評価指標・開始条件の合意",
            must_not_try_to_do=("詳細な本番設計まで確定する", "未確認ROIを断定する", "技術仕様を本編へ詰め込む"),
        )
    if stage == "final_approval":
        return DeckObjective(
            objective="投資判断と正式承認に必要な材料を提供する",
            sub_objectives=("リスクと対応を確認する", "投資対効果の前提を合意する"),
            expected_decision="正式契約へ進む判断",
            must_not_try_to_do=("操作説明を長く入れる", "不確実な効果を事実化する"),
        )
    return DeckObjective(
        objective=input_data.meeting_purpose,
        sub_objectives=("課題と提案方向を確認する", "次のアクションを合意する"),
        expected_decision=input_data.expected_outcome,
        must_not_try_to_do=("本編へ詳細資料を入れすぎる", "複数目的を同時に追いすぎる"),
    )
