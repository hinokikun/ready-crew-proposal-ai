from __future__ import annotations

from typing import Any


def build_prompt_improvements(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    review = metrics.get("review", {})
    quality_gate = metrics.get("quality_gate", {})
    outcome = metrics.get("outcome", {})
    knowledge = metrics.get("knowledge", {})
    notification = metrics.get("notification", {})

    keyword_counts = review.get("keyword_counts", {})
    quality_keywords = quality_gate.get("keyword_counts", {})
    lost_reasons = outcome.get("lost_reasons", {})
    improvements: list[dict[str, Any]] = []

    if keyword_counts.get("competitor", 0) >= 1 or lost_reasons.get("competitor", 0) >= 1:
        improvements.append(
            {
                "improvement_type": "prompt",
                "agent": "AI営業",
                "category": "競合分析",
                "current_version": "13.5",
                "suggested_prompt": "比較分析では、機能適合、導入効果、運用負荷、費用対効果、支援体制を案件カテゴリに合わせて比較し、顧客が選ぶ理由を1枚で説明してください。",
                "recommendation": "AI営業の提案作成前に競合比較の観点を強めます。",
                "expected_effect": "差別化不足による差し戻しと失注を減らします。",
                "confidence": 82,
                "priority": 90,
                "simulation": {"win_rate_delta": 6, "review_count_delta": -8, "quality_gate_pass_delta": 4, "proposal_time_delta": 2},
            }
        )

    if keyword_counts.get("roi", 0) >= 1 or keyword_counts.get("budget", 0) >= 1:
        improvements.append(
            {
                "improvement_type": "prompt",
                "agent": "AI社長",
                "category": "ROI説明",
                "current_version": "13.5",
                "suggested_prompt": "最終レビューでは、費用対効果、投資回収の考え方、成果指標を3点で説明し、見積金額の納得感を補強してください。",
                "recommendation": "AI社長レビューにROI説明の必須チェックを追加します。",
                "expected_effect": "価格・費用対効果に関する懸念を減らし、受注率向上を狙います。",
                "confidence": 78,
                "priority": 84,
                "simulation": {"win_rate_delta": 5, "review_count_delta": -5, "quality_gate_pass_delta": 3, "proposal_time_delta": 1},
            }
        )

    if keyword_counts.get("deadline", 0) >= 1 or quality_keywords.get("deadline", 0) >= 1:
        improvements.append(
            {
                "improvement_type": "prompt",
                "agent": "AI PM",
                "category": "納期確認",
                "current_version": "13.5",
                "suggested_prompt": "見積・スケジュール作成時は、希望時期、必要データ、確認回数、連携・検証期間を分けて納期リスクを明記してください。",
                "recommendation": "AI PMのチェック項目に納期リスク分解を追加します。",
                "expected_effect": "納期確認漏れと品質ゲートの警告を減らします。",
                "confidence": 80,
                "priority": 82,
                "simulation": {"win_rate_delta": 3, "review_count_delta": -4, "quality_gate_pass_delta": 7, "proposal_time_delta": 0},
            }
        )

    if knowledge.get("average_rating", 0) and knowledge.get("average_rating", 0) < 3.8:
        improvements.append(
            {
                "improvement_type": "prompt",
                "agent": "AIディレクター",
                "category": "Knowledge活用",
                "current_version": "13.5",
                "suggested_prompt": "レビュー時は、approvedの高評価Knowledgeだけを参照し、成功パターンと失注パターンをそれぞれ1つずつ反映してください。",
                "recommendation": "AIディレクターがKnowledge品質を見て提案ストーリーを補正します。",
                "expected_effect": "過去事例の再利用精度を高め、提案品質を標準化します。",
                "confidence": 70,
                "priority": 72,
                "simulation": {"win_rate_delta": 4, "review_count_delta": -3, "quality_gate_pass_delta": 4, "proposal_time_delta": -1},
            }
        )

    if notification.get("unread", 0) >= 3:
        improvements.append(
            {
                "improvement_type": "prompt",
                "agent": "AI秘書",
                "category": "通知整理",
                "current_version": "13.5",
                "suggested_prompt": "通知は重要度順に1件ずつ短く提示し、営業担当が次に押すべき操作を明確にしてください。",
                "recommendation": "AI秘書の通知文を短くし、未読通知の放置を減らします。",
                "expected_effect": "通知の既読率と対応率を改善します。",
                "confidence": 68,
                "priority": 65,
                "simulation": {"win_rate_delta": 1, "review_count_delta": -1, "quality_gate_pass_delta": 2, "proposal_time_delta": -3},
            }
        )

    return improvements
