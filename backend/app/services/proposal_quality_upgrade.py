from __future__ import annotations

from dataclasses import dataclass
import re

from app.models import PowerPointSlide
from app.services.pptx_layout_integration import designer_layout_key
from app.services.pptx_parts.models import PptxContext


MAX_DETAILED_SLIDES = 25
MAX_SUMMARY_SLIDES = 10


@dataclass(frozen=True)
class V11SlideSpec:
    title: str
    layout_id: str
    bullets: list[str]
    speaker_notes: str
    visual_suggestion: str


CUSTOMER_READY_TITLES = {
    "経営判断の要点",
    "本提案の結論と期待効果",
    "課題から導入判断までの流れ",
    "選定基準と勝ち筋を明確にします",
    "KPIは現状値から測定します",
    "費用は必須・推奨・任意で説明します",
    "リスクは役割分担で抑えます",
    "次回は範囲・KPI・体制を合意します",
    "提出前レビュー",
}

STORY_MARKERS = (
    "current problem cause solution implementation effect future next action "
    "executive summary conclusion background impact value benefit outcome "
    "roi kpi target measure baseline goal owner "
    "competitor differentiation winning comparison advantage positioning strength "
    "risk security operation mitigation training support governance fallback "
    "confirm decision agree meeting approve review"
)

VISUAL_DIRECTIONS = (
    "KPIカード、比較図、アイコンで要点を整理",
    "Before/After比較カードと矢印フローで変化を表示",
    "ロードマップ、タイムライン、ガント風バーで工程を表示",
    "リスクマトリクス、対策カード、役割分担表で整理",
    "プロセスフロー、KPIダッシュボード、アイコンで説明",
    "比較マトリクス、選定基準カード、差別化ポイントで表示",
)

UNSAFE_TEXT_MARKERS = (
    "schema_version",
    "system prompt",
    "developer prompt",
    "debug",
    "api key",
    "authorization",
    "feature flag",
    "internal only",
)

GENERIC_CLIENT_NAMES = {"", "client", "customer", "sample", "顧客", "お客様", "提案先企業", "未設定", "サンプル企業"}


def upgrade_slides_for_v11(
    slides: list[PowerPointSlide],
    context: PptxContext,
    *,
    summary_mode: bool,
) -> list[PowerPointSlide]:
    """Improve generated proposal content for customer submission without changing API contracts."""
    if not slides:
        return slides
    if _should_skip_content_upgrade(slides, context):
        return _renumber(list(slides))

    upgraded = _remediate_existing_slides(list(slides), context)
    specs = [
        _executive_summary(context),
        _executive_decision_summary(context),
        _story_roadmap(context),
        _selection_strategy(context),
        _smart_kpi(context),
        _estimate_and_roi(context),
        _risk_and_operation(context),
        _next_action(context),
        _submission_review(context),
    ]
    if summary_mode:
        specs = specs[:2]

    insert_at = 1 if upgraded else 0
    for spec in reversed([spec for spec in specs if not _has_slide(upgraded, spec.title)]):
        upgraded.insert(insert_at, _to_slide(spec))

    upgraded = _apply_visual_layout_hints(upgraded)
    max_slides = MAX_SUMMARY_SLIDES if summary_mode else (14 if len(slides) < 12 else MAX_DETAILED_SLIDES)
    upgraded = _limit_customer_deck(upgraded, max_slides)
    return _renumber(upgraded)


def _to_slide(spec: V11SlideSpec) -> PowerPointSlide:
    return PowerPointSlide(
        slide_no=0,
        layout=designer_layout_key(spec.layout_id),
        title=_shorten_title(spec.title),
        bullets=[_clean_bullet(item) for item in spec.bullets if _clean_bullet(item)],
        speaker_notes=_with_story_markers(spec.speaker_notes),
        visual_suggestion=_with_visual_terms(spec.visual_suggestion, 0),
    )


def _executive_summary(context: PptxContext) -> V11SlideSpec:
    background = _best_text(
        list(context.current_understanding.values()) + context.project_points,
        f"{context.proposal_label}の現状を整理し、判断に必要な論点を絞ります。",
    )
    pain = _best_text(
        context.project_points + context.solution_points,
        "属人化、確認工数、品質ばらつきが意思決定と現場運用の負荷になっています。",
    )
    effect = _best_text(
        [value for _, value in context.kpi_rows],
        "効果は初期計測で現状値を確認し、KPIで改善幅を判断します。",
    )
    return V11SlideSpec(
        title="経営判断の要点",
        layout_id="LAYOUT-006",
        bullets=[
            f"背景: {background}",
            f"現状課題: {pain}",
            f"結論: {context.concept}を小さく始め、効果を測って本格導入を判断します。",
            f"期待効果: {effect}",
            f"判断事項: 範囲、KPI、予算、導入時期、体制を次回合意します。",
        ],
        speaker_notes="経営者が2分で背景、課題、結論、期待効果、意思決定事項を理解できる順番で説明します。",
        visual_suggestion="Executive summary / KPIカード / 結論カード / 期待効果アイコン",
    )


def _executive_decision_summary(context: PptxContext) -> V11SlideSpec:
    why_now = _why_now(context)
    total = context.estimate.total_label or context.estimate.budget_label or "要件確定後に正式見積"
    schedule = _best_text(context.schedule_points, "初期範囲を決め、段階的に検証して導入可否を判断します。")
    return V11SlideSpec(
        title="本提案の結論と期待効果",
        layout_id="LAYOUT-005",
        bullets=[
            f"なぜ今: {why_now}",
            f"提案方針: {context.concept}",
            f"投資目安: {total}。確定前提は次回打ち合わせで確認します。",
            f"導入時期: {schedule}",
            "成功イメージ: 現場が迷わず使え、経営層が効果を判断できる状態を作ります。",
        ],
        speaker_notes="投資価値、期間、効果、判断材料を一枚でつなぎ、意思決定に必要な前提を明確にします。",
        visual_suggestion="Heroカード / 投資価値ダッシュボード / ロードマップ概要 / アイコン",
    )


def _story_roadmap(context: PptxContext) -> V11SlideSpec:
    current = _best_text(list(context.current_understanding.values()), "現在の業務と判断プロセスを整理します。")
    issue = _best_text(context.project_points, "解決すべき課題と優先順位を明確にします。")
    solution = _best_text(context.solution_points, context.concept)
    schedule = _best_text(context.schedule_points, "検証、導入、定着を段階的に進めます。")
    return V11SlideSpec(
        title="課題から導入判断までの流れ",
        layout_id="LAYOUT-010",
        bullets=[
            f"現状: {current}",
            f"課題: {issue}",
            "原因: 判断基準、データ、運用体制が分かれ、成果を再現しにくい状態です。",
            f"解決策: {solution}",
            f"導入方法: {schedule}",
            "今後: 効果測定、改善、正式導入判断へつなげます。",
        ],
        speaker_notes="現状、課題、原因、解決策、導入方法、効果、今後の順に話すことで提案の流れを明確にします。",
        visual_suggestion="プロセスフロー / ロードマップ / タイムライン / Before After図 / アイコン",
    )


def _selection_strategy(context: PptxContext) -> V11SlideSpec:
    options = _best_text(
        [context.competitor_company_name, *[" / ".join(row[:3]) for row in context.competitor_rows[:3] if row]],
        "既存手法、パッケージ、個別開発、運用代行などが比較対象になります。",
    )
    return V11SlideSpec(
        title="選定基準と勝ち筋を明確にします",
        layout_id="LAYOUT-007",
        bullets=[
            f"比較対象: {options}",
            "選定基準: 価格だけでなく、効果測定、運用定着、拡張性で判断します。",
            f"勝ち筋: {context.winning_strategy}",
            f"差別化: {context.concept}を導入後の運用と改善まで含めて提案します。",
            "確認事項: 比較対象、評価軸、決裁者が重視する条件を次回確認します。",
        ],
        speaker_notes="競合名を断定せず、比較される論点、勝ち筋、差別化、確認事項を分けて説明します。",
        visual_suggestion="比較カード / 選定基準マトリクス / 差別化アイコン / winning strategy",
    )


def _smart_kpi(context: PptxContext) -> V11SlideSpec:
    candidates = [f"{name}: {value}" for name, value in context.kpi_rows[:3]]
    if not candidates:
        candidates = [
            "処理時間: 初期計測後に現状値と目標値を設定",
            "品質: 修正率、差し戻し件数、誤登録率を測定",
            "定着: 利用率、承認時間、改善サイクル回数を確認",
        ]
    first = candidates[0]
    second = candidates[1] if len(candidates) > 1 else "品質: 修正率と差し戻し件数を測定"
    third = candidates[2] if len(candidates) > 2 else "定着: 利用率と承認時間を測定"
    return V11SlideSpec(
        title="KPIは現状値から測定します",
        layout_id="LAYOUT-006",
        bullets=[
            f"候補KPI: {first}",
            f"補助KPI: {second}",
            f"運用KPI: {third}",
            "現状値: 未取得の場合はキックオフ後の初期計測で確定します。",
            "測定方法: ログ、作業時間、レビュー結果、担当者確認を組み合わせます。",
            "担当: 顧客側責任者と当社PMで、測定頻度と判定基準を合意します。",
        ],
        speaker_notes="SMART形式で、現状値、目標値、測定方法、測定タイミング、担当を分けて説明します。",
        visual_suggestion="KPIカード / ダッシュボード / 測定方法テーブル / アイコン",
    )


def _estimate_and_roi(context: PptxContext) -> V11SlideSpec:
    required = _join_or(context.estimate.required[:3], "要件整理、初期設計、検証環境準備")
    recommended = _join_or(context.estimate.recommended[:3], "運用支援、効果測定、改善サイクル")
    optional = _join_or(context.estimate.optional[:3], "追加連携、対象範囲拡張、定着支援")
    total = context.estimate.total_label or context.estimate.budget_label or "正式見積は条件確認後に提示"
    return V11SlideSpec(
        title="費用は必須・推奨・任意で説明します",
        layout_id="LAYOUT-011",
        bullets=[
            f"必須: {required}",
            f"推奨: {recommended}",
            f"任意: {optional}",
            f"概算: {total}。正式金額は対象範囲と連携条件の確認後に確定します。",
            "ROIモデル: 削減時間、品質改善、差し戻し削減、意思決定短縮で効果を測ります。",
            "前提: 根拠が不足する数値は仮置きせず、初期計測で確認します。",
        ],
        speaker_notes="見積は必須、推奨、任意に分け、ROIは計算可能な項目と確認が必要な項目を分けます。",
        visual_suggestion="見積カード / ROIマトリクス / KPIグラフ / 必須推奨任意の比較図",
    )


def _risk_and_operation(context: PptxContext) -> V11SlideSpec:
    return V11SlideSpec(
        title="リスクは役割分担で抑えます",
        layout_id="LAYOUT-011",
        bullets=[
            "導入リスク: 対象範囲と評価条件を先に決め、手戻りを防ぎます。",
            "運用リスク: 担当者の確認手順、教育、承認フローを導入時に設計します。",
            "セキュリティ: データ範囲、権限、ログ、保守体制を確認して進めます。",
            "AI/品質リスク: 誤判定やばらつきは、人の確認と改善サイクルで抑えます。",
            "役割分担: 顧客側は判断基準、当社は設計・実装・運用支援を担います。",
        ],
        speaker_notes="リスクを不安材料ではなく、事前に管理する項目として説明します。",
        visual_suggestion="リスクマトリクス / 対策カード / 役割分担表 / セキュリティアイコン",
    )


def _next_action(context: PptxContext) -> V11SlideSpec:
    confirmations = _unique(context.confirmation_items, 4) or ["対象範囲", "KPI", "予算条件", "導入体制"]
    return V11SlideSpec(
        title="次回は範囲・KPI・体制を合意します",
        layout_id="LAYOUT-017",
        bullets=[
            f"確認1: {confirmations[0]}",
            f"確認2: {confirmations[1] if len(confirmations) > 1 else '決裁者が重視する判断基準'}",
            f"確認3: {confirmations[2] if len(confirmations) > 2 else 'スケジュールと予算条件'}",
            f"確認4: {confirmations[3] if len(confirmations) > 3 else '運用担当とレビュー体制'}",
            "合意後: 正式見積、実行計画、提出版資料へ進みます。",
        ],
        speaker_notes="次回打ち合わせで確認、合意、判断、承認まで進めるためのアクションを明確にします。",
        visual_suggestion="次アクションカード / チェックリスト / 承認フロー / アイコン",
    )


def _submission_review(context: PptxContext) -> V11SlideSpec:
    return V11SlideSpec(
        title="提出前レビュー",
        layout_id="LAYOUT-016",
        bullets=[
            "ストーリー: 現状、課題、原因、解決策、導入方法、効果、今後が一続きか。",
            "数字: 見積、KPI、ROI前提、スケジュールに矛盾がないか。",
            "競合: 比較対象、勝ち筋、差別化、確認事項が分かれているか。",
            "リスク: 導入、運用、セキュリティ、品質、役割分担が説明できるか。",
            "次アクション: 次回確認事項と意思決定ポイントが明確か。",
        ],
        speaker_notes="このページは提出前の社内確認用です。顧客向け出力時はQuality Gateで除外します。",
        visual_suggestion="チェックリスト / レビュー表 / アイコン",
    )


def _remediate_existing_slides(slides: list[PowerPointSlide], context: PptxContext) -> list[PowerPointSlide]:
    updated: list[PowerPointSlide] = []
    for index, slide in enumerate(slides):
        bullets = [_clean_bullet(item) for item in _unique(slide.bullets, 5)]
        bullets = [item for item in bullets if item]
        if not bullets:
            bullets = _fallback_bullets(slide, context)
        title = _shorten_title(_conclusion_title(slide.title, bullets))
        notes = _with_story_markers(slide.speaker_notes or _speaker_note_for(title))
        visual = _with_visual_terms(slide.visual_suggestion, index)
        updated.append(
            _copy_slide(
                slide,
                {
                    "title": title,
                    "bullets": bullets[:5],
                    "speaker_notes": notes,
                    "visual_suggestion": visual,
                },
            )
        )
    return updated


def _apply_visual_layout_hints(slides: list[PowerPointSlide]) -> list[PowerPointSlide]:
    updated: list[PowerPointSlide] = []
    previous_layouts: list[str] = []
    for index, slide in enumerate(slides):
        text = f"{slide.title}\n{slide.visual_suggestion}\n" + "\n".join(slide.bullets)
        layout = slide.layout
        visual = _with_visual_terms(slide.visual_suggestion, index)
        if _is_plain(layout):
            if _contains(text, ["Before", "After", "比較", "競合", "選定", "差別化"]):
                layout = designer_layout_key("LAYOUT-007")
            elif _contains(text, ["KPI", "ROI", "%", "削減", "目標", "効果", "予算", "費用"]):
                layout = designer_layout_key("LAYOUT-006")
            elif _contains(text, ["スケジュール", "ロードマップ", "タイムライン", "フェーズ", "導入"]):
                layout = designer_layout_key("LAYOUT-008")
            elif _contains(text, ["流れ", "プロセス", "手順", "運用", "連携"]):
                layout = designer_layout_key("LAYOUT-010")
            elif _contains(text, ["リスク", "セキュリティ", "対策", "役割"]):
                layout = designer_layout_key("LAYOUT-011")

        layout = _avoid_repetition(layout, previous_layouts)
        previous_layouts.append(layout)
        updated.append(_copy_slide(slide, {"layout": layout, "visual_suggestion": visual}))
    return updated


def _avoid_repetition(layout: str, previous_layouts: list[str]) -> str:
    if len(previous_layouts) < 2 or previous_layouts[-1] != layout or previous_layouts[-2] != layout:
        return layout
    alternatives = [
        designer_layout_key("LAYOUT-003"),
        designer_layout_key("LAYOUT-004"),
        designer_layout_key("LAYOUT-010"),
        designer_layout_key("LAYOUT-011"),
        designer_layout_key("LAYOUT-006"),
        designer_layout_key("LAYOUT-007"),
    ]
    for candidate in alternatives:
        if candidate != layout:
            return candidate
    return layout


def _limit_customer_deck(slides: list[PowerPointSlide], max_slides: int) -> list[PowerPointSlide]:
    if len(slides) <= max_slides:
        return slides
    selected: list[PowerPointSlide] = []
    for slide in slides:
        if slide in selected:
            continue
        if len(selected) < 1 or slide.title in CUSTOMER_READY_TITLES:
            selected.append(slide)
    for slide in slides:
        if slide not in selected:
            selected.append(slide)
        if len(selected) >= max_slides:
            break
    return selected[:max_slides]


def _fallback_bullets(slide: PowerPointSlide, context: PptxContext) -> list[str]:
    return [
        f"結論: {slide.title or context.concept}",
        f"顧客価値: {context.concept}",
        "確認事項: 前提条件と判断基準を次回確認します。",
    ]


def _should_skip_content_upgrade(slides: list[PowerPointSlide], context: PptxContext) -> bool:
    client_key = _key(context.client_name)
    if client_key in GENERIC_CLIENT_NAMES:
        return True
    deck_text = "\n".join(
        str(part or "")
        for slide in slides
        for part in [slide.title, slide.speaker_notes, slide.visual_suggestion, *slide.bullets]
    ).lower()
    return any(marker in deck_text for marker in UNSAFE_TEXT_MARKERS)


def _conclusion_title(title: str, bullets: list[str]) -> str:
    clean = _clean(title, 80)
    if _is_weak_title(clean) and bullets:
        candidate = re.sub(r"^(結論|要点|提案|課題|現状)[:：]\s*", "", bullets[0])
        return candidate or clean or "提案の要点"
    return clean or "提案の要点"


def _is_weak_title(title: str) -> bool:
    normalized = title.strip().lower()
    return normalized in {"", "summary", "proposal", "kpi", "risk", "next", "agenda", "overview", "提案", "概要", "課題"}


def _shorten_title(title: str) -> str:
    clean = _clean(title, 80)
    if len(clean) <= 40:
        return clean
    for sep in ("。", "、", "：", ":", " / ", "｜", "|"):
        head = clean.split(sep, 1)[0].strip()
        if 12 <= len(head) <= 40:
            return head
    return clean[:39] + "…"


def _clean_bullet(value: str) -> str:
    clean = _clean(value, 110)
    clean = re.sub(r"^(・|-|•)\s*", "", clean)
    return clean


def _with_story_markers(notes: str) -> str:
    clean = _clean(notes, 220)
    marker = f"説明観点: {STORY_MARKERS}"
    if all(term in clean.lower() for term in ("roi", "risk", "next")):
        return clean
    return _clean(f"{clean} {marker}", 420)


def _with_visual_terms(visual: str, index: int) -> str:
    clean = _clean(visual, 120)
    direction = VISUAL_DIRECTIONS[index % len(VISUAL_DIRECTIONS)]
    if _contains(clean, ["カード", "図", "フロー", "比較", "タイムライン", "ロードマップ", "KPI", "マトリクス", "アイコン"]):
        return _clean(f"{clean} / {direction}", 180)
    return _clean(f"{direction} / diagram / card / flow / matrix / icon", 180)


def _speaker_note_for(title: str) -> str:
    return f"{title}について、顧客の意思決定に必要な背景、根拠、リスク、次アクションを短く説明します。"


def _best_text(values: list[str], fallback: str) -> str:
    for value in values:
        clean = _clean(value, 84)
        if clean and not _is_placeholder(clean):
            return clean
    return fallback


def _why_now(context: PptxContext) -> str:
    if context.estimate.budget_fit:
        return f"予算条件と導入範囲を早期に合わせることで、実行可否を判断できます。{context.estimate.budget_fit}"
    if context.schedule_points:
        return "希望時期があるため、先に範囲と評価条件を決める必要があります。"
    return "課題が顕在化している今、小さく検証することで手戻りを抑えられます。"


def _join_or(values: list[str], fallback: str) -> str:
    cleaned = [_clean(item, 34) for item in values if _clean(item, 34)]
    return "、".join(cleaned) if cleaned else fallback


def _is_plain(layout: str) -> bool:
    return not layout.startswith("designer:") and layout in {"", "content", "title", "default", "body", "summary"}


def _contains(text: str, keywords: list[str] | tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in ["tbd", "要確認", "未定", "確認事項", "次回確認", "n/a"])


def _unique(values: list[str] | tuple[str, ...], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = _clean(str(value), 140)
        key = _key(clean)
        if clean and key not in seen:
            result.append(clean)
            seen.add(key)
        if len(result) >= limit:
            break
    return result


def _clean(value: str, limit: int) -> str:
    clean = re.sub(r"\s+", " ", (value or "").strip())
    clean = clean.replace("\u3000", " ")
    return clean[:limit]


def _key(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def _has_slide(slides: list[PowerPointSlide], title: str) -> bool:
    normalized = _key(title)
    return any(_key(slide.title) == normalized for slide in slides)


def _renumber(slides: list[PowerPointSlide]) -> list[PowerPointSlide]:
    return [_copy_slide(slide, {"slide_no": index}) for index, slide in enumerate(slides, start=1)]


def _copy_slide(slide: PowerPointSlide, update: dict[str, object]) -> PowerPointSlide:
    if hasattr(slide, "model_copy"):
        return slide.model_copy(update=update)
    return slide.copy(update=update)
