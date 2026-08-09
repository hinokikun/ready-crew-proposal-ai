"""Audience rules for Version 10.0 Presentation Director."""

from __future__ import annotations

from .models import AudienceAnalysis, AudienceType, PresentationDirectorInput


def _audience_type(text: str) -> AudienceType:
    if any(word in text for word in ("社長", "経営", "経営者", "役員", "CEO", "稟議")):
        return "executive"
    if any(word in text for word in ("部長", "部門責任者", "責任者", "本部長", "室長")):
        return "department_leader"
    if any(word in text for word in ("現場", "工場", "運用", "監督")):
        return "field_leader"
    if any(word in text for word in ("情報システム", "情シス", "IT", "技術", "セキュリティ")):
        return "it_leader"
    if any(word in text for word in ("購買", "管理", "経理")):
        return "procurement"
    return "unknown"


def analyze_audience(input_data: PresentationDirectorInput) -> AudienceAnalysis:
    text = input_data.decision_maker
    primary_type = _audience_type(text)
    if primary_type == "executive" and any(word in text for word in ("部長", "責任者")):
        primary = "部門責任者 / 役員"
        primary_type = "department_leader"
    elif primary_type == "executive":
        primary = "経営者 / 役員"
    elif primary_type == "field_leader":
        primary = "現場責任者"
    elif primary_type == "it_leader":
        primary = "情報システム / 技術責任者"
    else:
        primary = input_data.decision_maker or "unknown"

    secondary = input_data.secondary_audience
    secondary_type = _audience_type(secondary)
    needs = {
        "executive": ("なぜ今か", "投資対効果", "競争優位", "意思決定事項", "リスク"),
        "department_leader": ("部門課題", "KPI", "導入体制", "スケジュール", "運用責任"),
        "field_leader": ("As-Is / To-Be", "人とAIの役割", "例外処理", "教育", "現場KPI"),
        "it_leader": ("システム構成", "データ連携", "権限", "保守", "技術リスク"),
        "procurement": ("費用", "契約範囲", "前提条件", "見積内訳", "支払条件"),
        "unknown": ("目的", "期待効果", "次の合意事項"),
        "mixed": ("意思決定事項", "現場影響", "運用リスク"),
    }
    weaken = {
        "department_leader": ("細かい技術仕様", "詳細FAQ", "長い操作説明"),
        "executive": ("詳細な操作説明", "長い業務手順", "細かい技術仕様"),
        "field_leader": ("経営抽象論", "詳細な財務モデル", "過度な競合比較"),
        "it_leader": ("抽象的な価値訴求だけのページ", "根拠のないROI断定"),
        "procurement": ("技術詳細のみの説明", "効果だけで前提がない説明"),
        "unknown": ("過度な詳細",),
        "mixed": ("一部門だけに寄りすぎた説明",),
    }
    review = []
    if input_data.company_size == "unknown":
        review.append("顧客企業規模は未確認のため、提案ボリュームは人間確認が必要")
    if input_data.roi_availability != "known":
        review.append("ROIはPoCで確認する前提として扱う")
    return AudienceAnalysis(
        primary_audience=primary,
        primary_audience_type=primary_type,
        secondary_audience=secondary,
        secondary_audience_type=secondary_type,
        decision_needs=needs[primary_type],
        information_to_weaken=weaken[primary_type],
        human_review_reasons=tuple(review),
    )
