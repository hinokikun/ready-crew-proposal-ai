"""Action-title generation rules."""

from __future__ import annotations

from app.presentation_composer import CaseContext

from .models import InformationItem


def design_action_title(case: CaseContext, item: InformationItem, index: int, total: int) -> str:
    templates = {
        "background": f"{case.client_name}は今、{case.category}を判断する段階にあります",
        "current_state": "現状の分散した確認作業が、判断速度を下げています",
        "problem": "主要な課題は、速度・品質・確認負荷に集中しています",
        "root_cause": "根本原因は、判断基準と業務フローの分断にあります",
        "business_impact": "課題は現場負荷だけでなく、事業判断にも影響します",
        "target_state": "目指す姿は、AIと人が役割分担する確認プロセスです",
        "solution_policy": "AIで判定を支援し、人が例外を確認する設計にします",
        "proposal_content": f"{case.category}を業務フローの中に無理なく組み込みます",
        "execution_method": "検証から運用まで、段階的に移行します",
        "kpi": "初期計測で、処理時間・品質・負荷の3指標を確定します",
        "roi": "投資対効果は、削減時間と品質改善の両面で確認します",
        "risk": "データ準備と例外処理を先に設計し、導入リスクを抑えます",
        "investment": "見積は、必須範囲と拡張範囲を分けて判断できます",
        "decision": "次回は、検証範囲と評価指標を合意してください",
        "next_action": "次の打ち合わせで、PoC条件を確定します",
    }
    title = templates.get(item.item_id, f"{item.label}を判断できる形に整理します")
    if index == 1:
        title = f"{case.category}で、業務判断を速く正確にします"
    elif index == total:
        title = "次回打ち合わせで、検証条件を合意します"
    return _limit_title(title)


def _limit_title(title: str) -> str:
    value = " ".join(title.split())
    if len(value) <= 40:
        return value
    replacements = (
        ("してください", "します"),
        ("判断できます", "判断します"),
        ("段階的に移行します", "段階移行します"),
        ("組み込みます", "入れます"),
    )
    for before, after in replacements:
        value = value.replace(before, after)
        if len(value) <= 40:
            return value
    return value[:40].rstrip("、。,. ")
