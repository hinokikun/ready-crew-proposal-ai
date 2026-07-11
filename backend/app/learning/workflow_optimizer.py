from __future__ import annotations

from typing import Any


def build_workflow_improvements(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    review = metrics.get("review", {})
    quality_gate = metrics.get("quality_gate", {})
    outcome = metrics.get("outcome", {})
    orchestrator = metrics.get("orchestrator", {})

    improvements: list[dict[str, Any]] = []
    review_total = int(review.get("total") or 0)
    changes_requested = int(review.get("changes_requested") or 0)
    quality_total = int(quality_gate.get("total") or 0)
    quality_done = int(quality_gate.get("completed_or_bypassed") or 0)
    lost_reasons = outcome.get("lost_reasons", {})
    retry_count = int(orchestrator.get("retry_count") or 0)
    queue_total = int(orchestrator.get("total") or 0)
    needs_human = int(orchestrator.get("needs_human") or 0)

    if review_total and changes_requested / review_total >= 0.25:
        improvements.append(
            {
                "improvement_type": "workflow",
                "agent": "AIディレクター",
                "category": "レビュー前Knowledge検索",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "AIディレクターのレビュー前に、approvedかつ高評価の類似Knowledge検索を必ず実行します。",
                "expected_effect": "差し戻し前に成功パターンを反映し、レビュー回数を減らします。",
                "confidence": 82,
                "priority": 88,
                "simulation": {"win_rate_delta": 5, "review_count_delta": -12, "quality_gate_pass_delta": 5, "proposal_time_delta": 1},
            }
        )

    if quality_total and quality_done / quality_total < 0.75:
        improvements.append(
            {
                "improvement_type": "workflow",
                "agent": "AI社長",
                "category": "品質ゲート前レビュー",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "PPT/PDF生成前に、AI社長が品質ゲート項目を先読みして不足箇所をWorkspaceに表示します。",
                "expected_effect": "品質ゲート未完了を減らし、ダウンロード前の安心感を高めます。",
                "confidence": 76,
                "priority": 80,
                "simulation": {"win_rate_delta": 2, "review_count_delta": -4, "quality_gate_pass_delta": 10, "proposal_time_delta": 0},
            }
        )

    if lost_reasons.get("deadline", 0) >= 1 or needs_human >= 1:
        improvements.append(
            {
                "improvement_type": "workflow",
                "agent": "AI PM",
                "category": "PM早期介入",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "AI営業の提案ストーリー作成前に、AI PMが納期・予算・制作範囲を先に確認します。",
                "expected_effect": "納期確認漏れと見積の手戻りを減らします。",
                "confidence": 84,
                "priority": 86,
                "simulation": {"win_rate_delta": 4, "review_count_delta": -6, "quality_gate_pass_delta": 7, "proposal_time_delta": -2},
            }
        )

    if queue_total and retry_count / queue_total >= 0.1:
        improvements.append(
            {
                "improvement_type": "workflow",
                "agent": "Project Orchestrator",
                "category": "Retry前の原因分類",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "自動リトライ前に、入力不足、Backend、PPT/PDF、権限のどれが原因かを分類してから再実行します。",
                "expected_effect": "無駄なリトライを減らし、失敗時の復旧時間を短縮します。",
                "confidence": 74,
                "priority": 74,
                "simulation": {"win_rate_delta": 1, "review_count_delta": 0, "quality_gate_pass_delta": 2, "proposal_time_delta": -5},
            }
        )

    if not improvements:
        improvements.append(
            {
                "improvement_type": "workflow",
                "agent": "Project Orchestrator",
                "category": "継続観測",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "現時点では重大な偏りは少ないため、レビュー・受注・品質ゲートのデータを継続して蓄積します。",
                "expected_effect": "改善判断の精度を上げます。",
                "confidence": 55,
                "priority": 45,
                "simulation": {"win_rate_delta": 1, "review_count_delta": 0, "quality_gate_pass_delta": 1, "proposal_time_delta": 0},
            }
        )

    return improvements
