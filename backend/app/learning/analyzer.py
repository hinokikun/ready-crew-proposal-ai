from __future__ import annotations

from typing import Any

from app.learning.prompt_optimizer import build_prompt_improvements
from app.learning.workflow_optimizer import build_workflow_improvements


def analyze_learning_signals(metrics: dict[str, Any]) -> dict[str, Any]:
    prompt_improvements = build_prompt_improvements(metrics)
    workflow_improvements = build_workflow_improvements(metrics)
    rule_improvements = build_rule_improvements(metrics)
    improvements = sorted(
        prompt_improvements + workflow_improvements + rule_improvements,
        key=lambda item: (int(item.get("priority") or 0), int(item.get("confidence") or 0)),
        reverse=True,
    )
    release_candidate = build_release_candidate(improvements)
    return {
        "metrics": metrics,
        "improvements": improvements,
        "release_candidate": release_candidate,
    }


def build_rule_improvements(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    outcome = metrics.get("outcome", {})
    quality_gate = metrics.get("quality_gate", {})
    knowledge = metrics.get("knowledge", {})
    presentation_review = metrics.get("presentation_review", {})
    lost_reasons = outcome.get("lost_reasons", {})
    improvements: list[dict[str, Any]] = []

    if lost_reasons.get("price", 0) >= 1:
        improvements.append(
            {
                "improvement_type": "rule",
                "agent": "AI PM",
                "category": "価格失注対策",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "見積提示時は、必須範囲とオプション範囲を分け、予算調整案を必ず1つ提示します。",
                "expected_effect": "価格理由の失注を減らします。",
                "confidence": 72,
                "priority": 78,
                "simulation": {"win_rate_delta": 4, "review_count_delta": -2, "quality_gate_pass_delta": 3, "proposal_time_delta": 1},
            }
        )

    if int(quality_gate.get("bypassed") or 0) >= 1:
        improvements.append(
            {
                "improvement_type": "rule",
                "agent": "AI社長",
                "category": "品質ゲートバイパス抑制",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "管理者バイパス時は、次回同種案件で事前に確認すべき項目をAI社長がWorkspaceに表示します。",
                "expected_effect": "緊急バイパスの再発を減らします。",
                "confidence": 69,
                "priority": 70,
                "simulation": {"win_rate_delta": 1, "review_count_delta": -1, "quality_gate_pass_delta": 5, "proposal_time_delta": 0},
            }
        )

    if int(knowledge.get("high_confidential_risk") or 0) >= 1:
        improvements.append(
            {
                "improvement_type": "rule",
                "agent": "AIディレクター",
                "category": "Knowledge参照制御",
                "current_version": "13.5",
                "suggested_prompt": "",
                "recommendation": "Knowledge参照時はapprovedかつconfidential_riskがlow/mediumのものだけを利用します。",
                "expected_effect": "ナレッジ活用時の機密情報リスクを抑えます。",
                "confidence": 88,
                "priority": 92,
                "simulation": {"win_rate_delta": 0, "review_count_delta": 0, "quality_gate_pass_delta": 6, "proposal_time_delta": 0},
            }
        )

    if int(presentation_review.get("reviews") or 0) >= 1 and float(presentation_review.get("average_score") or 0) < 4.0:
        improvements.append(
            {
                "improvement_type": "rule",
                "agent": "AIディレクター",
                "category": "Presentation Review",
                "current_version": "19.0",
                "suggested_prompt": "",
                "recommendation": "提案書完成後にROI、比較分析、導入計画、次アクションの不足を確認し、Beautiful.aiへ送る前にRevision候補を作ります。",
                "expected_effect": "レビュー指摘数を減らし、社外提出前の修正回数を減らします。",
                "confidence": 78,
                "priority": 82,
                "simulation": {
                    "win_rate_delta": 3,
                    "review_count_delta": -2,
                    "quality_gate_pass_delta": 4,
                    "proposal_time_delta": 1,
                },
            }
        )

    return improvements


def build_release_candidate(improvements: list[dict[str, Any]]) -> dict[str, str]:
    top_items = improvements[:5]
    if not top_items:
        return {
            "version": "13.6候補",
            "summary": "継続観測を中心とした小規模改善候補です。データ蓄積後に優先度を再判定します。",
        }
    lines = [
        "Version 13.6候補: Learning Engineが推奨する改善案",
        *[
            f"- {item.get('agent', 'AI')}: {item.get('recommendation') or item.get('suggested_prompt')}"
            for item in top_items
        ],
    ]
    return {"version": "13.6候補", "summary": "\n".join(lines)[:2000]}
