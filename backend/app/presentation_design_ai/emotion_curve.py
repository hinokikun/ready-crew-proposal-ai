"""Emotion curve rules used by the renderer contract."""

from __future__ import annotations


def emotion_for_item(item_id: str, index: int, total: int) -> tuple[str, str]:
    if item_id in {"background", "current_state"}:
        return "interest", "neutral_orientation"
    if item_id in {"problem", "root_cause", "business_impact"}:
        return "urgency", "controlled_warning"
    if item_id in {"target_state", "solution_policy", "proposal_content"}:
        return "expectation", "accent_confidence"
    if item_id in {"execution_method", "risk"}:
        return "reassurance", "trust_control"
    if item_id in {"kpi", "roi", "investment"}:
        return "conviction", "decision_blue"
    if index >= total - 2:
        return "commitment", "decision_focus"
    return "clarity", "neutral_structure"
