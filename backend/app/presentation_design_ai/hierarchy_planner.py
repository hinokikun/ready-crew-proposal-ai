"""Visual hierarchy planner."""

from __future__ import annotations

from .models import DiagramDecision, InformationItem, VisualHierarchy


def plan_visual_hierarchy(item: InformationItem, action_title: str, diagram: DiagramDecision) -> VisualHierarchy:
    priority_2 = _priority_2(item, diagram)
    priority_3 = tuple(part for part in (item.label, item.evidence_status, diagram.selected_diagram) if part)[:3]
    priority_4 = ("conditions", "source basis") if item.evidence_status == "sufficient" else ("assumption", "confirmation required")
    return VisualHierarchy(
        priority_1=action_title,
        priority_2=priority_2,
        priority_3=priority_3,
        priority_4=priority_4,
        reading_order=("action_title", "central_visual", "key_number_or_signal", "takeaway", "note"),
        focal_point=priority_2,
        secondary_point=_short_secondary(item),
    )


def _priority_2(item: InformationItem, diagram: DiagramDecision) -> str:
    if item.item_id in {"kpi", "roi", "investment"}:
        return "判断に使う数値"
    if item.item_id in {"problem", "root_cause", "risk"}:
        return "原因とリスクの構造"
    if item.item_id in {"decision", "next_action"}:
        return "承認までの道筋"
    return "中心図解"


def _short_secondary(item: InformationItem) -> str:
    if item.evidence_status == "hypothesis":
        return "確認が必要な仮説"
    if item.item_id in {"kpi", "roi", "investment"}:
        return "判断に使う数値"
    if item.item_id in {"problem", "root_cause"}:
        return "構造化した論点"
    return "要点のみ表示"
