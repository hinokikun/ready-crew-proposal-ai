"""Narrative planning for the whole deck."""

from __future__ import annotations

from .models import InformationItem


STORY_ORDER = (
    "background",
    "current_state",
    "problem",
    "root_cause",
    "target_state",
    "solution_policy",
    "proposal_content",
    "execution_method",
    "kpi",
    "roi",
    "risk",
    "investment",
    "decision",
    "next_action",
)


def select_story_items(items: tuple[InformationItem, ...]) -> tuple[InformationItem, ...]:
    by_id = {item.item_id: item for item in items}
    selected = [
        by_id[item_id]
        for item_id in STORY_ORDER
        if item_id in by_id and by_id[item_id].disposition not in {"delete", "merge", "speaker_notes"}
    ]
    if "decision" in by_id and "next_action" in by_id:
        selected = [item for item in selected if item.item_id != "decision"]
    return tuple(selected)


def previous_connection(index: int, items: tuple[InformationItem, ...]) -> str:
    if index == 0:
        return "なぜ今かを示します。"
    return f"前ページの{items[index - 1].label}を受けます。"


def next_transition(index: int, items: tuple[InformationItem, ...]) -> str:
    if index >= len(items) - 1:
        return "次回の合意事項を確認します。"
    return f"次は{items[index + 1].label}を確認します。"
