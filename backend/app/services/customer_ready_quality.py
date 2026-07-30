from __future__ import annotations

from dataclasses import dataclass, replace
import re
from typing import Literal

from app.models import PowerPointSlide
from app.services.pptx_layout_integration import designer_layout_key
from app.services.pptx_parts.models import PptxContext
from app.services.pptx_quality import PptxQualityReport
from app.services.customer_ready_judgement import assess_customer_ready_deck


CustomerReadyStatus = Literal["READY", "REVIEW_REQUIRED", "BLOCKED"]

INTERNAL_TITLE_KEYWORDS = (
    "提出前レビュー",
    "Customer-Ready Quality Gate",
    "品質ゲート",
    "内部レビュー",
    "Debug",
    "System Prompt",
)
INTERNAL_TEXT_KEYWORDS = (
    "schema_version",
    "system prompt",
    "developer prompt",
    "debug",
    "api key",
    "authorization",
    "feature flag",
    "internal only",
)
PLACEHOLDER_PATTERNS = (
    "TBD",
    "未定",
    "要確認",
    "未確認",
    "N/A",
)
GENERIC_CLIENT_NAMES = {
    "",
    "Client",
    "顧客",
    "お客様",
    "提案先企業",
    "未設定",
    "サンプル企業",
}


class CustomerReadyBlockedError(RuntimeError):
    def __init__(self, result: CustomerReadyResult) -> None:
        self.result = result
        super().__init__("Customer-ready quality gate blocked the PPTX output.")


@dataclass(frozen=True)
class CustomerReadyResult:
    slides: list[PowerPointSlide]
    status: CustomerReadyStatus
    score: int
    reasons: list[str]
    blockers: list[str]
    auto_fixes: list[str]
    excluded_internal_items: list[str]
    sales_summary: list[str]
    expected_questions: list[dict[str, str]]
    rubric: dict[str, int]


def run_customer_ready_quality_gate(
    slides: list[PowerPointSlide],
    context: PptxContext,
    *,
    summary_mode: bool,
) -> CustomerReadyResult:
    """Prepare the final customer-facing deck and judge whether it is submit-ready."""
    current = list(slides)
    excluded: list[str] = []
    auto_fixes: list[str] = []

    for _ in range(2):
        reviewed = review_customer_ready(current, context)
        if reviewed.status == "READY":
            return _with_accumulated(reviewed, auto_fixes=auto_fixes, excluded=excluded)
        current, fixes, removed = auto_fix_customer_ready(current, context, summary_mode=summary_mode)
        auto_fixes.extend(fix for fix in fixes if fix not in auto_fixes)
        excluded.extend(item for item in removed if item not in excluded)
        if not fixes and not removed:
            break

    reviewed = review_customer_ready(current, context)
    return CustomerReadyResult(
        slides=reviewed.slides,
        status=reviewed.status,
        score=reviewed.score,
        reasons=reviewed.reasons,
        blockers=reviewed.blockers,
        auto_fixes=auto_fixes,
        excluded_internal_items=excluded,
        sales_summary=reviewed.sales_summary,
        expected_questions=reviewed.expected_questions,
        rubric=reviewed.rubric,
    )


def _with_accumulated(
    result: CustomerReadyResult,
    *,
    auto_fixes: list[str],
    excluded: list[str],
) -> CustomerReadyResult:
    return CustomerReadyResult(
        slides=result.slides,
        status=result.status,
        score=result.score,
        reasons=result.reasons,
        blockers=result.blockers,
        auto_fixes=_unique(auto_fixes, 12),
        excluded_internal_items=_unique(excluded, 12),
        sales_summary=result.sales_summary,
        expected_questions=result.expected_questions,
        rubric=result.rubric,
    )


def review_customer_ready(slides: list[PowerPointSlide], context: PptxContext) -> CustomerReadyResult:
    blockers = _critical_blockers(slides, context)
    assessment = assess_customer_ready_deck(slides, context, blockers=blockers)
    return CustomerReadyResult(
        slides=_renumber(slides),
        status=assessment.gate_status,
        score=assessment.score,
        reasons=_unique(assessment.reasons, 8),
        blockers=_unique(assessment.blockers, 8),
        auto_fixes=[],
        excluded_internal_items=[],
        sales_summary=_sales_summary(context, assessment.gate_status, assessment.score, assessment.reasons),
        expected_questions=_expected_questions(context),
        rubric=assessment.category_scores,
    )


def auto_fix_customer_ready(
    slides: list[PowerPointSlide],
    context: PptxContext,
    *,
    summary_mode: bool,
) -> tuple[list[PowerPointSlide], list[str], list[str]]:
    fixed: list[PowerPointSlide] = []
    fixes: list[str] = []
    removed: list[str] = []

    for slide in slides:
        if _is_internal_slide(slide):
            removed.append(slide.title or "internal slide")
            continue

        cleaned_bullets = [_customer_safe_line(item) for item in _unique(slide.bullets, 5)]
        cleaned_bullets = [item for item in cleaned_bullets if item]
        if cleaned_bullets != slide.bullets:
            fixes.append("顧客向け表現に合わない未確定表現・重複表現を整理")

        title = _conclusion_title(slide.title, cleaned_bullets)
        if title != slide.title:
            fixes.append("スライドタイトルを結論型へ調整")

        notes = slide.speaker_notes or _speaker_note_for(title, cleaned_bullets)
        if not slide.speaker_notes:
            fixes.append("営業担当者向けの発表者ノートを追加")

        fixed.append(
            slide.copy(
                update={
                    "title": title,
                    "bullets": cleaned_bullets[:4] if not _is_checklist_slide(title) else cleaned_bullets[:6],
                    "speaker_notes": notes,
                }
            )
        )

    if not summary_mode:
        fixed = _ensure_customer_slides(fixed, context, fixes)
    fixed = _apply_layout_safety(fixed, fixes)
    return _renumber(fixed), _unique(fixes, 12), removed


def attach_customer_ready_report(report: PptxQualityReport, result: CustomerReadyResult) -> PptxQualityReport:
    human_items = list(report.human_review_items)
    human_items.extend(result.sales_summary[:4])
    if result.status != "READY":
        human_items.extend(result.reasons[:3])
    return replace(
        report,
        human_review_required=report.human_review_required or result.status != "READY",
        human_review_items=_unique(human_items, 12),
        customer_ready_status=result.status,
        customer_ready_score=result.score,
        customer_ready_reasons=result.reasons,
        customer_ready_blockers=result.blockers,
        customer_ready_auto_fixes=result.auto_fixes,
        customer_ready_excluded_internal_items=result.excluded_internal_items,
        customer_ready_sales_summary=result.sales_summary,
        customer_ready_expected_questions=result.expected_questions,
        customer_ready_rubric=result.rubric,
    )


def _critical_blockers(slides: list[PowerPointSlide], context: PptxContext) -> list[str]:
    blockers: list[str] = []
    if not slides:
        blockers.append("スライドが生成されていません。")
    if not context.client_name or _normalize(context.client_name) in GENERIC_CLIENT_NAMES:
        blockers.append("顧客名が未入力または汎用名のままです。")
    title_text = " ".join(slide.title for slide in slides if slide.title)
    if not title_text.strip():
        blockers.append("案件名または提案タイトルがありません。")
    internal_hits = [slide.title for slide in slides if _is_internal_slide(slide)]
    if internal_hits:
        blockers.append(f"顧客向け資料に内部レビュー情報が混入しています: {'、'.join(internal_hits[:3])}")
    deck_text = _deck_text(slides).lower()
    if any(keyword in deck_text for keyword in INTERNAL_TEXT_KEYWORDS):
        blockers.append("顧客向け資料に内部プロンプト、設定、または機密に近い表現が含まれています。")
    return blockers


def _ensure_customer_slides(slides: list[PowerPointSlide], context: PptxContext, fixes: list[str]) -> list[PowerPointSlide]:
    updated = list(slides)
    if not _has_any(updated, ["リスク", "対応"]):
        updated.append(_risk_slide(context))
        fixes.append("リスクと対応策スライドを追加")
    if not _has_any(updated, ["次のアクション", "次に"]):
        updated.append(_next_action_slide(context))
        fixes.append("次のアクションを明確化")
    return updated


def _risk_slide(context: PptxContext) -> PowerPointSlide:
    return PowerPointSlide(
        slide_no=0,
        layout=designer_layout_key("LAYOUT-011"),
        title="導入リスクは事前に管理できます",
        bullets=[
            "情報不足: 対象範囲と評価基準を初回打ち合わせで確認します。",
            "スケジュール: 顧客確認期間を含めた現実的な工程で進めます。",
            "運用定着: 担当者の確認フローと教育を含めて設計します。",
            "追加要件: 必須・推奨・オプションに分け、見積範囲を明確にします。",
        ],
        speaker_notes="顧客を不安にさせるのではなく、事前に管理可能な論点として説明します。",
        visual_suggestion="リスクと対応策をペアで見せる2列カード",
    )


def _next_action_slide(context: PptxContext) -> PowerPointSlide:
    confirmations = context.confirmation_items[:2] or ["対象範囲", "予算条件"]
    return PowerPointSlide(
        slide_no=0,
        layout=designer_layout_key("LAYOUT-017"),
        title="次回は提案方針と実施範囲を合意します",
        bullets=[
            "提案方針の合意",
            f"{'・'.join(confirmations)}の確認",
            "概算見積とスケジュール前提の確認",
            "次回ヒアリング日程の決定",
        ],
        speaker_notes="最後に顧客へ決めてほしいことを明確に伝え、次の商談につなげます。",
        visual_suggestion="次回合意事項を4つのアクションカードで表示",
    )


def _apply_layout_safety(slides: list[PowerPointSlide], fixes: list[str]) -> list[PowerPointSlide]:
    updated: list[PowerPointSlide] = []
    previous: list[str] = []
    for slide in slides:
        layout = slide.layout
        text = f"{slide.title}\n{slide.visual_suggestion}\n" + "\n".join(slide.bullets)
        if _is_plain_layout(layout):
            if _contains(text, ["比較", "Before", "After", "競合"]):
                layout = designer_layout_key("LAYOUT-007")
            elif _contains(text, ["KPI", "ROI", "目標", "%"]):
                layout = designer_layout_key("LAYOUT-006")
            elif _contains(text, ["スケジュール", "工程", "フェーズ"]):
                layout = designer_layout_key("LAYOUT-008")
            elif _contains(text, ["リスク", "優先度", "対応"]):
                layout = designer_layout_key("LAYOUT-011")
        if len(previous) >= 2 and previous[-1] == layout and previous[-2] == layout:
            layout = designer_layout_key("LAYOUT-003")
            fixes.append("同じレイアウトが3ページ続かないよう調整")
        previous.append(layout)
        updated.append(slide.copy(update={"layout": layout}))
    return updated


def _score_customer_understanding(slides: list[PowerPointSlide], context: PptxContext) -> int:
    text = _deck_text(slides)
    score = 6
    if context.client_name and context.client_name in text:
        score += 3
    if _has_any(slides, ["背景", "課題", "現状"]):
        score += 3
    if _contains(text, ["意思決定", "担当", "顧客", "利用者"]):
        score += 3
    return min(15, score)


def _score_story(slides: list[PowerPointSlide]) -> int:
    text = _deck_text(slides)
    keywords = ["現状", "課題", "原因", "解決", "導入", "効果", "次"]
    return min(15, 4 + sum(2 for keyword in keywords if keyword in text))


def _score_specificity(slides: list[PowerPointSlide], context: PptxContext) -> int:
    text = _deck_text(slides)
    score = 5
    if context.proposal_label and context.proposal_label in text:
        score += 2
    if context.project_points or context.solution_points:
        score += 4
    if _contains(text, ["必須", "推奨", "オプション", "確認"]):
        score += 4
    return min(15, score)


def _score_executive_value(slides: list[PowerPointSlide]) -> int:
    text = _deck_text(slides)
    return _score_keywords(text, ["エグゼクティブ", "結論", "期待効果", "成功", "投資", "ROI"], 10)


def _score_estimate_schedule(text: str) -> int:
    return _score_keywords(text, ["見積", "概算", "予算", "スケジュール", "工程", "期間", "必須", "推奨"], 10)


def _score_writing_quality(slides: list[PowerPointSlide]) -> int:
    score = 5
    long_items = sum(1 for slide in slides for item in slide.bullets if len(item) > 130)
    placeholder_count = _count_placeholders(_deck_text(slides))
    if long_items:
        score -= min(3, long_items)
    if placeholder_count > 2:
        score -= 2
    return max(0, score)


def _score_design(slides: list[PowerPointSlide]) -> int:
    score = 4
    layouts = [slide.layout for slide in slides]
    if any("LAYOUT-006" in layout for layout in layouts):
        score += 2
    if any("LAYOUT-007" in layout for layout in layouts):
        score += 2
    if any("LAYOUT-008" in layout or "LAYOUT-010" in layout or "LAYOUT-011" in layout for layout in layouts):
        score += 2
    if any(layouts[index] == layouts[index - 1] == layouts[index - 2] for index in range(2, len(layouts))):
        score -= 2
    return max(0, min(10, score))


def _score_keywords(text: str, keywords: list[str], max_score: int) -> int:
    base = max(0, max_score // 3)
    hit = sum(1 for keyword in keywords if keyword in text)
    return min(max_score, base + hit * max(1, max_score // 5))


def _sales_summary(context: PptxContext, status: str, score: int, reasons: list[str]) -> list[str]:
    confirmations = "、".join(context.confirmation_items[:3]) if context.confirmation_items else "対象範囲、予算、スケジュール"
    return _unique(
        [
            f"顧客提出判定: {status} / {score}点",
            f"提案の結論: {context.concept}",
            f"確認が必要な項目: {confirmations}",
            f"営業説明ポイント: {reasons[0] if reasons else '顧客価値と次のアクションを短く説明してください。'}",
        ],
        6,
    )


def _expected_questions(context: PptxContext) -> list[dict[str, str]]:
    budget_basis = "概算レンジです。対象範囲、連携条件、運用支援範囲を確認した後に正式見積へ更新します。"
    schedule_basis = "要件定義、顧客確認、修正、本番準備の工程を含めて再確認します。"
    return [
        {"question": "なぜこの金額なのですか？", "answer": budget_basis},
        {"question": "導入期間を短縮できますか？", "answer": schedule_basis},
        {"question": "既存システムと連携できますか？", "answer": "連携方式、API/CSV可否、権限、データ項目を確認したうえで判断します。"},
        {"question": "効果が出なかった場合はどうしますか？", "answer": "KPIを事前に合意し、初期検証で改善余地と継続判断を確認します。"},
        {"question": "競合との違いは何ですか？", "answer": f"{context.winning_strategy}を軸に、導入後の運用と成果測定まで含めて差別化します。"},
        {"question": "社内で誰が担当すべきですか？", "answer": "業務責任者、情報システム、現場担当、意思決定者の役割を分けて進めることを推奨します。"},
        {"question": "追加費用が発生する条件は何ですか？", "answer": "対象範囲の追加、連携仕様の変更、運用支援範囲の拡大が主な条件です。"},
        {"question": "次回までに何を準備すればよいですか？", "answer": "対象範囲、予算上限、希望時期、既存資料、関係者を確認してください。"},
        {"question": "セキュリティ面は問題ありませんか？", "answer": "権限、データ取扱い、接続方式、ログ管理を要件定義で確認します。"},
        {"question": "最初に何を決めればよいですか？", "answer": "提案方針、対象範囲、予算条件、次回ヒアリング日程の4点です。"},
    ]


def _customer_safe_line(value: str) -> str:
    line = re.sub(r"\s+", " ", value or "").strip()
    replacements = {
        "TBD": "ご相談のうえ確定",
        "未定": "ご相談のうえ確定",
        "要確認": "次回確認",
        "未確認": "次回確認",
        "N/A": "対象範囲外または次回確認",
    }
    for before, after in replacements.items():
        line = line.replace(before, after)
    if any(keyword in line.lower() for keyword in INTERNAL_TEXT_KEYWORDS):
        return ""
    return line[:150]


def _conclusion_title(title: str, bullets: list[str]) -> str:
    clean = re.sub(r"\s+", " ", title or "").strip()
    generic = {"現状課題", "解決策", "スケジュール", "KPI", "見積", "リスク", "まとめ"}
    if clean in generic and bullets:
        return _short_conclusion(bullets[0])
    return clean[:42] or _short_conclusion(bullets[0] if bullets else "提案内容を整理します")


def _short_conclusion(value: str) -> str:
    clean = re.sub(r"^(現状|課題|解決策|KPI|見積|リスク|次のアクション)[:：\s]*", "", value or "").strip()
    return clean[:38] or "提案価値を短時間で確認できます"


def _speaker_note_for(title: str, bullets: list[str]) -> str:
    message = bullets[0] if bullets else title
    return f"このページでは「{message[:45]}」を最初に伝え、詳細は必要な点だけ補足します。"


def _is_internal_slide(slide: PowerPointSlide) -> bool:
    title = slide.title or ""
    if any(keyword.lower() in title.lower() for keyword in INTERNAL_TITLE_KEYWORDS):
        return True
    text = f"{slide.title}\n{slide.speaker_notes}\n" + "\n".join(slide.bullets)
    return any(keyword in text.lower() for keyword in INTERNAL_TEXT_KEYWORDS)


def _is_checklist_slide(title: str) -> bool:
    return any(keyword in title for keyword in ["チェック", "確認", "次回", "次のアクション"])


def _is_plain_layout(layout: str) -> bool:
    normalized = (layout or "").strip().lower()
    return normalized in {"", "content", "summary", "title", "body", "default"}


def _deck_text(slides: list[PowerPointSlide]) -> str:
    parts: list[str] = []
    for slide in slides:
        parts.extend([slide.title, slide.speaker_notes, slide.visual_suggestion, *slide.bullets])
    return "\n".join(part for part in parts if part)


def _count_placeholders(text: str) -> int:
    return sum(text.count(pattern) for pattern in PLACEHOLDER_PATTERNS)


def _has_title(slides: list[PowerPointSlide], keyword: str) -> bool:
    return any(keyword in (slide.title or "") for slide in slides)


def _has_any(slides: list[PowerPointSlide], keywords: list[str]) -> bool:
    text = _deck_text(slides)
    return any(keyword in text for keyword in keywords)


def _contains(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def _renumber(slides: list[PowerPointSlide]) -> list[PowerPointSlide]:
    return [slide.copy(update={"slide_no": index}) for index, slide in enumerate(slides, start=1)]


def _unique(values: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = re.sub(r"\s+", " ", str(value or "").strip())
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
        if len(result) >= limit:
            break
    return result


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value or "").strip()
