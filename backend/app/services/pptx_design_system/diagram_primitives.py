from __future__ import annotations

DIAGRAM_PRIMITIVES = {
    "horizontal_flow": "横方向フロー",
    "vertical_flow": "縦方向フロー",
    "chevron_process": "シェブロン型プロセス",
    "circular_cycle": "循環プロセス",
    "layered_architecture": "レイヤー型構成図",
    "pyramid": "ピラミッド",
    "funnel": "ファネル",
    "matrix_2x2": "2x2マトリクス",
    "issue_tree": "課題ツリー",
    "value_chain": "バリューチェーン",
    "before_after": "Before/After変化図",
    "phased_roadmap": "段階ロードマップ",
    "milestone_timeline": "マイルストーンタイムライン",
    "swimlane": "スイムレーン",
    "stakeholder_map": "ステークホルダーマップ",
    "kpi_tree": "KPIツリー",
    "roi_bridge": "ROIブリッジ",
    "risk_heatmap": "リスクヒートマップ",
}


def primitive_for_text(text: str) -> str:
    if any(key in text for key in ("リスク", "懸念", "対策")):
        return "risk_heatmap"
    if any(key in text for key in ("ROI", "費用対効果", "投資")):
        return "roi_bridge"
    if any(key in text for key in ("API", "CSV", "連携", "システム")):
        return "layered_architecture"
    if any(key in text for key in ("課題", "原因", "要因")):
        return "issue_tree"
    if any(key in text for key in ("Phase", "フェーズ", "スケジュール", "ロードマップ")):
        return "phased_roadmap"
    if any(key in text for key in ("比較", "Before", "After", "現状", "改善後")):
        return "before_after"
    return "chevron_process"
