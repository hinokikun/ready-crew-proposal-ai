from __future__ import annotations

CHART_PRIMITIVES = {
    "kpi_bar": "KPI比較バー",
    "current_target_progress": "現状対目標プログレス",
    "phase_step": "段階効果ステップ",
    "investment_stack": "投資内訳スタック",
    "risk_heatmap": "リスクヒートマップ",
    "schedule_gantt": "ガント風ロードマップ",
}


def chart_for_numeric_context(text: str) -> str | None:
    if not any(ch.isdigit() for ch in text):
        return None
    if any(key in text for key in ("リスク", "影響", "発生")):
        return "risk_heatmap"
    if any(key in text for key in ("週", "月", "フェーズ", "Phase")):
        return "schedule_gantt"
    if any(key in text for key in ("費用", "見積", "円", "万円")):
        return "investment_stack"
    if any(key in text for key in ("現状", "目標", "KPI")):
        return "current_target_progress"
    return "kpi_bar"
