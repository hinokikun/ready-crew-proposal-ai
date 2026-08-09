"""Deterministic consulting page composer for Version 7.0."""

from __future__ import annotations

from app.design_system import CONSULTING_DESIGN_SYSTEM
from app.presentation_components import select_component_sequence

from .models import CaseContext, PageSpec, PresentationPlan


_STORY_BEATS: tuple[tuple[str, str, str], ...] = (
    ("提案の判断材料を1枚で整理する", "背景・課題・効果を経営判断の順に接続します", "提案範囲と意思決定者を確認する"),
    ("最初に投資判断の結論を示す", "効果、回収、進め方を先に提示します", "ROI前提の確認に進む"),
    ("現状課題を構造で見る", "課題を並べず、原因と影響の関係で整理します", "影響が大きい課題を合意する"),
    ("根本原因を絞り込む", "個別事象ではなく再発する構造に着目します", "原因仮説を現場に確認する"),
    ("目指す姿を現在との差で示す", "現在と将来の差分を導入価値として表現します", "将来像の優先度を決める"),
    ("改善後の業務像を描く", "利用者の行動がどう変わるかを一目で示します", "対象業務を確定する"),
    ("顧客体験の変化を流れで示す", "誰が、いつ、何を判断するかを可視化します", "関係部門を確認する"),
    ("AI・DXの処理を業務に接続する", "技術ではなく業務の中での役割を示します", "接続範囲を決める"),
    ("優先順位を判断できる形にする", "効果と実行難易度で着手順を決めます", "初期対象を選ぶ"),
    ("KPIを経営・現場の両方で見る", "成果指標をダッシュボードとして扱います", "現状値の取得方法を決める"),
    ("投資と効果の回収線を示す", "費用ではなく回収までの道筋を見せます", "金額換算の前提を確認する"),
    ("リスクを先回りして管理する", "不安要素を隠さず、対応策と一緒に提示します", "PoCで潰すリスクを決める"),
    ("判断分岐を明確にする", "進む・止める・広げる条件を可視化します", "判定基準を合意する"),
    ("競合に対する勝ち筋を示す", "価格以外の評価軸で差別化します", "競合比較の不足情報を確認する"),
    ("機能ではなく選ばれる理由を示す", "比較軸を顧客価値へ変換します", "評価基準をすり合わせる"),
    ("事業モデルへの効き方を示す", "業務改善が売上・品質・速度へつながる構造を示します", "期待効果の優先順位を決める"),
    ("価値の連鎖を途切れなく見せる", "入力から成果までを一本の流れで示します", "データ取得点を確認する"),
    ("運用設計を現場視点で示す", "フロント・バック・支援の役割を分けます", "運用責任者を決める"),
    ("体制と役割を明確にする", "誰が判断し、誰が動くかを先に決めます", "承認者と担当者を確認する"),
    ("ガバナンスを重くせず設計する", "確認と承認の流れを簡潔に保ちます", "承認フローを合意する"),
    ("導入計画をロードマップにする", "段階導入で失敗リスクを抑えます", "初回フェーズを確定する"),
    ("スケジュールを実行単位で見る", "主要タスクと判断点を時間軸で揃えます", "キックオフ日を決める"),
    ("運用・保守の安心材料を示す", "導入後に止まらない体制を示します", "保守範囲を確認する"),
    ("想定質問へ先に答える", "懸念を会議前に潰し、合意形成を早めます", "追加確認事項を回収する"),
    ("次回打ち合わせで合意する", "次に決めることを明確にして提案を前に進めます", "PoC範囲と日程を合意する"),
)


def _compact(text: str, limit: int) -> str:
    value = " ".join(str(text or "").replace("\n", " ").split())
    return value[: limit - 1] + "…" if len(value) > limit else value


def _labels_for_page(case: CaseContext, slide_no: int) -> tuple[str, ...]:
    pain = list(case.pain_points) or ["現状把握", "判断基準", "運用負荷"]
    outcomes = list(case.expected_outcomes) or ["時間短縮", "品質向上", "判断迅速化"]
    banks = [
        (case.client_name, case.industry, case.category),
        tuple(pain[:3]),
        ("現状", "課題", "原因", "解決策"),
        ("入力", "判断", "実行", "改善"),
        ("投資", "効果", "回収", "拡張"),
        tuple(outcomes[:4]),
        ("Phase 1", "Phase 2", "Phase 3", "Decision"),
        ("低リスク", "高効果", "早期着手", "拡張余地"),
        ("必須", "推奨", "オプション", "将来"),
        ("確認", "合意", "開始", "評価"),
    ]
    labels = banks[(slide_no - 1) % len(banks)]
    return tuple(_compact(label, 16) for label in labels if label)


def compose_consulting_presentation(case: CaseContext, slide_count: int = 25) -> PresentationPlan:
    components = select_component_sequence(case.category, slide_count=slide_count)
    palette = CONSULTING_DESIGN_SYSTEM.palette_for_category(case.category)
    pages: list[PageSpec] = []
    for index, component in enumerate(components, start=1):
        beat = _STORY_BEATS[(index - 1) % len(_STORY_BEATS)]
        action, conclusion, next_action = beat
        evidence_seed = case.expected_outcomes[(index - 1) % len(case.expected_outcomes)] if case.expected_outcomes else case.project_summary
        pages.append(
            PageSpec(
                slide_no=index,
                component_id=component.component_id,
                component_name=component.name,
                visual_type=component.visual_type,
                layout_family=component.layout_family,
                action_title=_compact(action, component.max_title_chars),
                conclusion=_compact(conclusion, component.max_body_chars),
                diagram_labels=_labels_for_page(case, index),
                evidence=_compact(evidence_seed, 58),
                next_action=_compact(next_action, 48),
                diagram_ratio=component.diagram_ratio,
                text_ratio=component.text_ratio,
                speaker_notes={
                    "conclusion": conclusion,
                    "talk_order": "結論、図解、根拠、次アクションの順に説明します。",
                    "emphasis": action,
                    "customer_question": next_action,
                    "caution": "未確認の数値は仮説として扱い、商談で確認してください。",
                    "transition": "次ページで判断材料を具体化します。",
                },
            )
        )
    return PresentationPlan(
        case=case,
        pages=tuple(pages),
        palette_id=palette.name,
        design_system_version=CONSULTING_DESIGN_SYSTEM.version,
    )
