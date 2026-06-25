from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
import logging
import re

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_VERTICAL_ANCHOR
from pptx.util import Inches, Pt

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest, WinProbability


logger = logging.getLogger(__name__)

MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

SLIDE_WIDTH = 13.333
SLIDE_HEIGHT = 7.5
MARGIN_X = 0.78
HEADER_Y = 0.42
FOOTER_Y = 6.92
CONTENT_TOP = 1.48
FONT_FACE = "Yu Gothic"

COLORS = {
    "white": "FFFFFF",
    "canvas": "F7F9FC",
    "navy": "10233F",
    "navy_2": "1D3557",
    "navy_3": "31445F",
    "text": "1B2430",
    "muted": "667085",
    "line": "D8DEE8",
    "line_dark": "B7C0CE",
    "teal": "0F766E",
    "teal_light": "E6F5F2",
    "blue": "2563EB",
    "blue_light": "EAF2FF",
    "orange": "F59E0B",
    "orange_light": "FFF7E6",
    "red": "B42318",
    "red_light": "FFF1F0",
    "green": "14845F",
    "green_light": "E7F7EF",
    "purple": "6658D3",
    "purple_light": "F0EEFF",
}

SECTION_COLORS = [COLORS["teal"], COLORS["blue"], COLORS["orange"], COLORS["purple"], COLORS["green"]]


@dataclass(frozen=True)
class EstimateSummary:
    page_count: int
    total_min: int
    total_max: int
    total_label: str
    budget_label: str
    budget_fit: str
    lines: list[dict[str, object]]
    required: list[str]
    recommended: list[str]
    optional: list[str]


@dataclass(frozen=True)
class PptxContext:
    client_name: str
    concept: str
    current_understanding: dict[str, str]
    journey_points: list[tuple[str, str]]
    sitemap_items: list[str]
    kpi_rows: list[tuple[str, str]]
    kpi_targets: dict[str, float]
    competitor_rows: list[list[str]]
    competitor_site_url: str
    competitor_company_name: str
    winning_strategy: str
    target_user_rows: list[tuple[str, str]]
    content_items: list[str]
    web_strategy_items: list[str]
    case_studies: list[str]
    case_triplets: list[dict[str, str]]
    project_points: list[str]
    solution_points: list[str]
    service_points: list[str]
    schedule_points: list[str]
    team_points: list[str]
    cost_points: list[str]
    estimate: EstimateSummary
    confirmation_items: list[str]
    win_probability: WinProbability | None


def build_pptx_bytes(payload: PptxDownloadRequest) -> bytes:
    return _build_pptx_bytes(payload, summary_mode=payload.summary)


def build_summary_pptx_bytes(payload: PptxDownloadRequest) -> bytes:
    return _build_pptx_bytes(payload, summary_mode=True)


def _build_pptx_bytes(payload: PptxDownloadRequest, *, summary_mode: bool) -> bytes:
    try:
        prs = Presentation()
        prs.slide_width = Inches(SLIDE_WIDTH)
        prs.slide_height = Inches(SLIDE_HEIGHT)

        data = payload.powerpoint_generation_data
        context = build_pptx_context(payload)
        slides = data.slides or [_fallback_slide(data)]
        slides = insert_competitor_analysis_slide(slides, context)
        slides = insert_case_studies_slide(slides, context)
        slides = insert_estimate_slides(slides, context)
        slides = insert_win_probability_slide(slides, context)
        if summary_mode:
            slides = build_summary_slides(slides, context)

        display_slide_no = 1
        for index, slide_data in enumerate(slides):
            if index > 0 and not summary_mode:
                add_chapter_title_slide(prs, slide_data, index + 1, display_slide_no, context)
                display_slide_no += 1
            numbered_slide = slide_data.model_copy(update={"slide_no": display_slide_no})
            add_designed_slide(prs, numbered_slide, data, index, context)
            display_slide_no += 1

        buffer = BytesIO()
        prs.save(buffer)
        return buffer.getvalue()
    except Exception:
        logger.exception("Failed to build proposal PowerPoint deck.")
        raise


def build_pptx_context(payload: PptxDownloadRequest) -> PptxContext:
    data = payload.powerpoint_generation_data
    all_input = "\n".join(
        [
            payload.project_brief,
            payload.client_company_info,
            payload.competitor_site_url,
            payload.competitor_company_name,
            payload.estimated_page_count,
            payload.cms_required,
            payload.contact_form_required,
            payload.special_function_required,
            payload.seo_required,
            payload.content_creation_required,
            payload.desired_launch_timing,
            payload.budget_range,
            payload.hearing_result,
            payload.own_service_info,
            payload.past_proposal_template,
            payload.case_studies,
        ]
    )
    concept = derive_concept(all_input)
    estimate = derive_estimate_summary(payload, all_input)
    return PptxContext(
        client_name=extract_client_name(payload.client_company_info, data.client_name),
        concept=concept,
        current_understanding=derive_current_understanding(payload.project_brief, concept),
        journey_points=derive_journey_points(concept),
        sitemap_items=derive_sitemap_items(all_input),
        kpi_rows=derive_kpi_rows(all_input, concept),
        kpi_targets=derive_kpi_targets(all_input, concept),
        competitor_rows=derive_competitor_rows(all_input),
        competitor_site_url=payload.competitor_site_url.strip(),
        competitor_company_name=payload.competitor_company_name.strip(),
        winning_strategy=derive_winning_strategy(all_input),
        target_user_rows=derive_target_user_rows(all_input, concept),
        content_items=derive_content_items(all_input, concept),
        web_strategy_items=derive_web_strategy_items(all_input, concept),
        case_studies=extract_case_study_items(payload.case_studies),
        case_triplets=extract_case_triplets(payload.case_studies),
        project_points=extract_project_points(payload.project_brief),
        solution_points=extract_solution_points(all_input),
        service_points=extract_service_points(payload.own_service_info),
        schedule_points=extract_schedule_points(all_input),
        team_points=extract_team_points(payload.own_service_info),
        cost_points=extract_cost_points(all_input),
        estimate=estimate,
        confirmation_items=extract_confirmation_items(all_input),
        win_probability=payload.win_probability,
    )


def build_pptx_filename(data: PowerPointData, client_company_info: str = "", *, summary_mode: bool = False) -> str:
    base_name = data.deck_title or "ready-crew-proposal"
    client_name = extract_client_name(client_company_info, data.client_name)
    if client_name != "提案先企業" and client_name not in base_name:
        base_name = f"{client_name}_{base_name}"
    if summary_mode:
        suffix = "_要約版"
        sanitized_base = sanitize_filename(base_name, max_length=80 - len(suffix))
        return f"{sanitized_base}{suffix}.pptx"
    return f"{sanitize_filename(base_name)}.pptx"


def sanitize_filename(value: str, *, max_length: int = 80) -> str:
    sanitized = re.sub(r'[\\/:*?"<>|]', "-", value)
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized[:max_length].strip() or "ready-crew-proposal"


def insert_case_studies_slide(slides: list[PowerPointSlide], context: PptxContext) -> list[PowerPointSlide]:
    if not context.case_triplets and not context.case_studies:
        return slides
    if any("実績" in slide.title for slide in slides):
        return slides

    next_slide_no = max((slide.slide_no for slide in slides), default=0) + 1
    case_slide = PowerPointSlide(
        slide_no=next_slide_no,
        layout="content",
        title="関連実績",
        bullets=context.case_studies or [case["title"] for case in context.case_triplets],
        speaker_notes="入力された成功事例データをもとに、現状、施策、成果の順で実績を紹介します。",
        visual_suggestion="現状、施策、成果を整理した実績カード",
    )

    insert_at = next((idx for idx, slide in enumerate(slides) if "体制" in slide.title), len(slides))
    return [*slides[:insert_at], case_slide, *slides[insert_at:]]


def insert_competitor_analysis_slide(slides: list[PowerPointSlide], context: PptxContext) -> list[PowerPointSlide]:
    if not has_competitor_context(context):
        return slides
    if any("競合比較分析" in slide.title for slide in slides):
        return slides

    competitor_name = context.competitor_company_name or "競合サイト"
    bullets = ensure_items(
        [
            f"比較対象: {competitor_name}",
            f"競合サイト: {context.competitor_site_url}" if context.competitor_site_url else "",
            f"勝ち筋: {context.winning_strategy}",
            "デザイン、SEO、導線設計、コンテンツ量、更新性、CTAの6観点で比較",
        ],
        ["競合比較をもとに、勝てる訴求軸と改善優先度を明確化"],
        4,
    )
    next_slide_no = max((slide.slide_no for slide in slides), default=0) + 1
    competitor_slide = PowerPointSlide(
        slide_no=next_slide_no,
        layout="content",
        title="競合比較分析",
        bullets=bullets,
        speaker_notes="競合サイトの比較観点と勝ち筋を提示し、提案内容の優先順位に反映します。",
        visual_suggestion="6観点の競合比較表と勝ち筋の強調表示",
    )

    insert_at = next(
        (
            idx + 1
            for idx, slide in enumerate(slides)
            if ("市場" in slide.title or "競合" in slide.title) and "競合比較分析" not in slide.title
        ),
        None,
    )
    if insert_at is None:
        insert_at = next((idx + 1 for idx, slide in enumerate(slides) if "課題" in slide.title), min(5, len(slides)))
    return [*slides[:insert_at], competitor_slide, *slides[insert_at:]]


def insert_estimate_slides(slides: list[PowerPointSlide], context: PptxContext) -> list[PowerPointSlide]:
    existing_titles = {slide.title for slide in slides}
    additions: list[PowerPointSlide] = []
    next_slide_no = max((slide.slide_no for slide in slides), default=0) + 1

    if "概算見積" not in existing_titles:
        additions.append(
            PowerPointSlide(
                slide_no=next_slide_no,
                layout="content",
                title="概算見積",
                bullets=[
                    f"合計概算: {context.estimate.total_label}",
                    f"想定ページ数: {context.estimate.page_count}ページ",
                    "固定金額ではなく、要件確定前のレンジとして提示",
                ],
                speaker_notes="案件条件から概算見積レンジを整理します。",
                visual_suggestion="見積内訳と合計レンジの表",
            )
        )
        next_slide_no += 1

    if "予算適合判定" not in existing_titles:
        additions.append(
            PowerPointSlide(
                slide_no=next_slide_no,
                layout="content",
                title="予算適合判定",
                bullets=[
                    f"判定: {context.estimate.budget_fit}",
                    f"予算感: {context.estimate.budget_label}",
                    f"概算見積: {context.estimate.total_label}",
                ],
                speaker_notes="予算感と概算見積レンジの差分を示します。",
                visual_suggestion="予算適合判定カード",
            )
        )
        next_slide_no += 1

    if "必須・推奨・オプション対応" not in existing_titles:
        additions.append(
            PowerPointSlide(
                slide_no=next_slide_no,
                layout="content",
                title="必須・推奨・オプション対応",
                bullets=[
                    f"必須対応: {'、'.join(context.estimate.required[:4])}",
                    f"推奨対応: {'、'.join(context.estimate.recommended[:4]) or '次回確認'}",
                    f"オプション対応: {'、'.join(context.estimate.optional[:4]) or '次回確認'}",
                ],
                speaker_notes="予算内で優先すべき対応範囲を分類します。",
                visual_suggestion="必須・推奨・オプションの3カラム",
            )
        )

    if not additions:
        return slides

    insert_at = next((idx + 1 for idx, slide in enumerate(slides) if "費用" in slide.title or "概算" in slide.title), None)
    if insert_at is None:
        insert_at = next((idx for idx, slide in enumerate(slides) if "今後" in slide.title or "進め方" in slide.title), len(slides))
    return [*slides[:insert_at], *additions, *slides[insert_at:]]


def insert_win_probability_slide(slides: list[PowerPointSlide], context: PptxContext) -> list[PowerPointSlide]:
    win = context.win_probability
    if win is None:
        return slides
    if any("受注確率" in slide.title or "案件ランク" in slide.title for slide in slides):
        return slides

    probability = win.probability or rank_probability_for(win.rank)
    risk_score = max(1, min(5, win.risk_score or risk_score_for_probability(probability, len(win.risk_factors))))
    risk_label = win.risk_label or risk_label_for(risk_score)
    projected = win.projected_probability_after_actions or projected_probability_for(probability, risk_score, len(win.improvement_actions))
    next_slide_no = max((slide.slide_no for slide in slides), default=0) + 1
    win_slide = PowerPointSlide(
        slide_no=next_slide_no,
        layout="content",
        title="受注確率判定",
        bullets=[
            f"受注確率: {probability}%",
            f"受注リスク: {risk_label}",
            f"リスク要因: {'、'.join(unique_items(win.risk_factors, 3))}",
            f"改善アクション: {'、'.join(unique_items(win.improvement_actions or win.recommended_next_actions, 3))}",
            f"受注確率向上予測: {probability}% → {projected}%",
        ],
        speaker_notes="受注確率、リスク要因、改善アクション、向上予測を営業判断材料として提示します。",
        visual_suggestion="受注確率カード、リスク要因、改善アクション、向上予測の3カラム",
    )

    insert_at = next((idx for idx, slide in enumerate(slides) if "今後" in slide.title or "進め方" in slide.title), len(slides))
    return [*slides[:insert_at], win_slide, *slides[insert_at:]]


def build_summary_slides(slides: list[PowerPointSlide], context: PptxContext) -> list[PowerPointSlide]:
    def existing_bullets(*keywords: str) -> list[str]:
        slide = find_slide_by_keywords(slides, *keywords)
        return slide.bullets if slide else []

    def summary_slide(title: str, bullets: list[str], fallback: list[str], visual: str = "") -> PowerPointSlide:
        return PowerPointSlide(
            slide_no=0,
            layout="content",
            title=title,
            bullets=ensure_items([bullet for bullet in bullets if bullet], fallback, 3),
            speaker_notes=f"{title}を要約版向けに簡潔に説明します。",
            visual_suggestion=visual or f"{title}を図解する要約レイアウト",
        )

    cover_bullets = slides[0].bullets if slides else []
    selected = [
        PowerPointSlide(
            slide_no=1,
            layout="title",
            title="",
            bullets=ensure_items(
                cover_bullets,
                [f"{context.client_name}向け提案", concept_statement(context.concept), "重要論点を短時間で共有"],
                3,
            ),
            speaker_notes="要約版の表紙です。",
            visual_suggestion="表紙",
        ),
        summary_slide(
            "提案サマリー",
            [*existing_bullets("提案サマリー"), concept_statement(context.concept), *(context.project_points[:2] or context.solution_points[:2])],
            ["提案の狙いを端的に共有", "成果につながる導線と情報設計を改善", "公開後の運用改善まで見据えて設計"],
            "提案価値を3点で示すサマリーカード",
        ),
        summary_slide(
            "現状理解",
            [*existing_bullets("現状理解"), *list(context.current_understanding.values())],
            ["現行サイトの情報整理と導線に改善余地", "ターゲットに伝えるべき強みを再整理", "問い合わせ・応募につながる導線を強化"],
            "現状・課題・機会を並べるカード",
        ),
        summary_slide(
            "主要課題",
            [*existing_bullets("課題"), *context.project_points, *context.solution_points],
            ["問い合わせ導線を分かりやすく再設計", "サービス・実績の訴求を整理", "CMS運用と改善サイクルを設計"],
            "優先度順の課題カード",
        ),
        summary_slide(
            "提案コンセプト",
            [
                f"提案コンセプト: {context.concept}",
                concept_statement(context.concept),
                "情報設計、導線改善、コンテンツ、運用改善を一体で実施",
            ],
            ["サイトの目的を1つの提案軸に集約", "成果導線を中心に設計", "運用改善まで含めて推進"],
            "提案コンセプトを中心にしたメッセージボード",
        ),
        summary_slide(
            "Web戦略",
            [*existing_bullets("Web戦略"), *context.web_strategy_items],
            ["集客から問い合わせまでの流れを設計", "比較検討に必要な情報を整備", "公開後の改善運用を前提に構築"],
            "集客・比較検討・問い合わせをつなぐ戦略図",
        ),
        summary_slide(
            "サイトマップ",
            [*existing_bullets("サイトマップ"), *context.sitemap_items],
            ["トップ", "サービス", "お問い合わせ"],
            "主要ページを階層で示すサイトマップ図",
        ),
        summary_slide(
            "KPI設計",
            [*existing_bullets("KPI"), *[f"{name}: {value}" for name, value in context.kpi_rows]],
            ["問い合わせ数: 月20件", "CV率: 2.8%", "自然検索流入: 月3,500セッション"],
            "問い合わせ数・CV率・自然検索流入のKPIグラフ",
        ),
        summary_slide(
            "スケジュール",
            [*existing_bullets("スケジュール"), *context.schedule_points],
            ["要件整理・設計", "デザイン・実装", "検証・公開"],
            "短期共有向けの簡易タイムライン",
        ),
        summary_slide(
            "費用概算",
            [
                f"合計概算: {context.estimate.total_label}",
                f"予算適合: {context.estimate.budget_fit}",
                f"必須対応: {'、'.join(context.estimate.required[:3])}",
                *existing_bullets("費用"),
                *context.cost_points,
            ],
            ["必須範囲とオプションを分けて提示", "CMS・SEO・運用保守の範囲を整理", "次回確認後に見積精度を更新"],
            "必須範囲とオプションを分けた費用表",
        ),
        summary_slide(
            "今後の進め方",
            [*existing_bullets("今後"), *context.confirmation_items],
            ["次回ヒアリングで要件を確定", "制作範囲と優先順位を合意", "概算費用とスケジュールを更新"],
            "次回アクションのステップカード",
        ),
    ]

    return [slide.model_copy(update={"slide_no": index}) for index, slide in enumerate(selected, start=1)]


def find_slide_by_keywords(slides: list[PowerPointSlide], *keywords: str) -> PowerPointSlide | None:
    for slide in slides:
        if all(keyword in slide.title for keyword in keywords):
            return slide
    return None


def add_designed_slide(
    prs: Presentation,
    slide_data: PowerPointSlide,
    data: PowerPointData,
    index: int,
    context: PptxContext,
) -> None:
    kind = resolve_slide_kind(slide_data, index)
    if kind == "cover":
        add_cover_slide(prs, slide_data, data, context)
    elif kind == "proposal_summary":
        add_proposal_summary_slide(prs, slide_data, context)
    elif kind == "proposal_concept":
        add_concept_slide(prs, slide_data, context)
    elif kind == "current_understanding":
        add_current_understanding_slide(prs, slide_data, context)
    elif kind == "competitor":
        add_competitor_slide(prs, slide_data, context)
    elif kind == "target_user":
        add_target_user_slide(prs, slide_data, context)
    elif kind == "customer_journey":
        add_customer_journey_slide(prs, slide_data, context)
    elif kind == "web_strategy":
        add_web_strategy_slide(prs, slide_data, context)
    elif kind == "sitemap":
        add_sitemap_slide(prs, slide_data, context)
    elif kind == "content":
        add_content_design_slide(prs, slide_data, context)
    elif kind == "kpi":
        add_kpi_slide(prs, slide_data, context)
    elif kind == "understanding":
        add_understanding_slide(prs, slide_data)
    elif kind == "issues":
        add_issues_slide(prs, slide_data, context)
    elif kind == "solution":
        add_solution_slide(prs, slide_data, context)
    elif kind == "process":
        add_process_slide(prs, slide_data, context)
    elif kind == "schedule":
        add_schedule_slide(prs, slide_data, context)
    elif kind == "case_studies":
        add_case_studies_slide(prs, slide_data, context)
    elif kind == "team":
        add_team_slide(prs, slide_data, context)
    elif kind == "estimate":
        add_estimate_slide(prs, slide_data, context)
    elif kind == "budget_fit":
        add_budget_fit_slide(prs, slide_data, context)
    elif kind == "estimate_priority":
        add_estimate_priority_slide(prs, slide_data, context)
    elif kind == "cost":
        add_cost_slide(prs, slide_data, context)
    elif kind == "win_probability":
        if context.win_probability is not None:
            add_win_probability_slide(prs, context.win_probability, slide_data.slide_no)
        else:
            add_generic_slide(prs, slide_data)
    elif kind == "next_steps":
        add_next_steps_slide(prs, slide_data, context)
    elif kind == "summary":
        add_summary_slide(prs, slide_data, context)
    else:
        add_generic_slide(prs, slide_data)


def resolve_slide_kind(slide_data: PowerPointSlide, index: int) -> str:
    title = slide_data.title
    if index == 0 or slide_data.layout == "title":
        return "cover"
    if "提案サマリー" in title:
        return "proposal_summary"
    if "提案コンセプト" in title:
        return "proposal_concept"
    if "現状理解" in title:
        return "current_understanding"
    if "市場" in title or "競合" in title:
        return "competitor"
    if "ターゲット" in title or "ユーザー分析" in title:
        return "target_user"
    if "カスタマージャーニー" in title or "ユーザー行動" in title:
        return "customer_journey"
    if "Web戦略" in title or "WEB戦略" in title:
        return "web_strategy"
    if "サイトマップ" in title or "サイト構成" in title:
        return "sitemap"
    if "コンテンツ" in title:
        return "content"
    if "KPI" in title or "指標" in title:
        return "kpi"
    if "貴社理解" in title or "企業理解" in title:
        return "understanding"
    if "課題" in title and "解決" not in title:
        return "issues"
    if "解決" in title:
        return "solution"
    if "制作方針" in title or "方針" in title:
        return "process"
    if "スケジュール" in title:
        return "schedule"
    if "実績" in title:
        return "case_studies"
    if "体制" in title:
        return "team"
    if "予算適合" in title:
        return "budget_fit"
    if "必須" in title and "推奨" in title and "オプション" in title:
        return "estimate_priority"
    if "見積" in title:
        return "estimate"
    if "費用" in title or "概算" in title:
        return "cost"
    if "受注確率" in title or "案件ランク" in title:
        return "win_probability"
    if "今後" in title or "進め方" in title or "まとめ" in title:
        return "next_steps"

    order_map = {
        1: "proposal_summary",
        2: "current_understanding",
        3: "issues",
        4: "competitor",
        5: "target_user",
        6: "customer_journey",
        7: "web_strategy",
        8: "sitemap",
        9: "content",
        10: "kpi",
        11: "process",
        12: "schedule",
        13: "team",
        14: "cost",
        15: "next_steps",
    }
    return order_map.get(index, "generic")


def add_cover_slide(prs: Presentation, slide_data: PowerPointSlide, data: PowerPointData, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)

    add_shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT, fill=COLORS["navy"], line=COLORS["navy"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, 0.16, SLIDE_HEIGHT, fill=COLORS["teal"], line=COLORS["teal"])
    add_shape(slide, MSO_SHAPE.RIGHT_TRIANGLE, 8.55, 0, 4.78, 7.5, fill=COLORS["navy_2"], line=COLORS["navy_2"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 9.15, 0, 4.18, SLIDE_HEIGHT, fill=COLORS["canvas"], line=COLORS["canvas"])
    add_shape(slide, MSO_SHAPE.OVAL, 9.65, 0.92, 3.05, 3.05, fill=COLORS["teal_light"], line=COLORS["teal_light"])
    add_shape(slide, MSO_SHAPE.OVAL, 10.82, 3.55, 1.72, 1.72, fill=COLORS["blue_light"], line=COLORS["blue_light"])
    add_icon_badge(slide, "UX", 9.82, 1.68, COLORS["teal"])
    add_icon_badge(slide, "SEO", 11.05, 2.78, COLORS["blue"])
    add_icon_badge(slide, "CV", 9.9, 4.75, COLORS["orange"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 9.75, 5.92, 2.7, 0.13, fill=COLORS["teal"], line=COLORS["teal"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 9.75, 6.2, 1.9, 0.13, fill=COLORS["orange"], line=COLORS["orange"])

    add_section_label(slide, "WEB PROPOSAL", 0.88, 0.8, fill=COLORS["teal"], color=COLORS["white"])
    add_title(slide, slide_data.title or data.deck_title, 0.88, 1.55, 7.35, 1.24, size=42, color=COLORS["white"])
    add_text(slide, f"{context.client_name} 御中", 0.92, 3.02, 6.9, 0.36, size=18, color=COLORS["teal_light"], bold=True)
    add_text(
        slide,
        "成果につながるWebサイト制作・改善のご提案",
        0.92,
        3.68,
        7.25,
        0.5,
        size=20,
        color=COLORS["white"],
        bold=True,
    )
    add_text(slide, f"提案日 {date.today().strftime('%Y.%m.%d')}", 0.92, 5.95, 3.5, 0.26, size=12, color=COLORS["teal_light"])
    add_text(slide, "Ready Crew Proposal AI", 0.92, 6.58, 4.0, 0.24, size=11, color=COLORS["teal_light"])
    add_text(slide, f"{slide_data.slide_no:02}", 11.58, 6.86, 0.76, 0.22, size=10, color=COLORS["muted"], align=PP_ALIGN.RIGHT)

    add_text(slide, "Strategy", 9.45, 1.0, 2.6, 0.32, size=16, color=COLORS["navy"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Design", 10.28, 3.2, 1.9, 0.3, size=14, color=COLORS["navy"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, "Growth", 9.95, 5.18, 2.2, 0.3, size=14, color=COLORS["navy"], bold=True, align=PP_ALIGN.CENTER)


def add_chapter_title_slide(prs: Presentation, slide_data: PowerPointSlide, chapter_no: int, display_slide_no: int, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    accent = SECTION_COLORS[(chapter_no - 1) % len(SECTION_COLORS)]
    add_shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_WIDTH, SLIDE_HEIGHT, fill=COLORS["navy"], line=COLORS["navy"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 0.0, 0, 0.18, SLIDE_HEIGHT, fill=accent, line=accent)
    add_shape(slide, MSO_SHAPE.RIGHT_TRIANGLE, 8.4, 0, 4.94, 7.5, fill=COLORS["navy_2"], line=COLORS["navy_2"])
    add_text(slide, f"Chapter {chapter_no:02}", 0.92, 1.65, 2.4, 0.28, size=14, color=COLORS["teal_light"], bold=True)
    add_text(slide, slide_data.title, 0.92, 2.14, 7.9, 0.72, size=34, color=COLORS["white"], bold=True)
    add_text(slide, _trim(chapter_message(slide_data.title, context), 86), 0.95, 3.22, 7.55, 0.56, size=17, color=COLORS["teal_light"], bold=True)
    add_icon_badge(slide, chapter_icon(slide_data.title), 10.18, 2.38, accent, size=1.3)
    add_text(slide, context.concept, 9.42, 4.1, 2.85, 0.32, size=17, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide, display_slide_no)


def add_proposal_summary_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "提案サマリー", "SUMMARY", accent=COLORS["blue"])
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.92, 1.62, 11.48, 1.26, fill=COLORS["navy"], line=COLORS["navy"])
    add_text(slide, "提案コンセプト", 1.25, 1.88, 1.7, 0.24, size=12, color=COLORS["teal_light"], bold=True)
    add_text(slide, context.concept, 3.0, 1.8, 3.2, 0.36, size=24, color=COLORS["white"], bold=True)
    add_text(slide, _trim(concept_statement(context.concept), 62), 6.35, 1.78, 5.25, 0.48, size=15, color=COLORS["white"], bold=True)

    summary_items = ensure_items(
        slide_data.bullets + context.web_strategy_items,
        ["現状課題を成果導線へ落とし込む", "情報設計とコンテンツを再構成", "KPIを定義して公開後改善につなげる"],
        3,
    )
    titles = ["解決する課題", "主要施策", "期待成果"]
    for idx, item in enumerate(summary_items[:3]):
        add_card(slide, titles[idx], item, 0.95 + idx * 4.02, 3.36, 3.35, 1.68, SECTION_COLORS[idx], COLORS["white"], number=str(idx + 1))
    add_insight_band(slide, "提案の結論", "顧客理解、競合比較、KPI設計を起点に、公開後も成果を追えるWebサイトへ改善します。", 0.92, 5.82, 11.4, 0.54)
    add_footer(slide, slide_data.slide_no)


def add_current_understanding_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "現状理解と事業課題", "顧客理解")
    understanding = merge_understanding_items(context.current_understanding, slide_data.bullets)
    items = [
        ("現状", understanding["現状"], COLORS["teal"]),
        ("課題", understanding["課題"], COLORS["red"]),
        ("機会", understanding["機会"], COLORS["blue"]),
        ("目指す状態", understanding["目指す状態"], COLORS["green"]),
    ]
    positions = [(0.9, 1.72), (6.78, 1.72), (0.9, 4.08), (6.78, 4.08)]

    for idx, ((title, body, accent), (x, y)) in enumerate(zip(items, positions), start=1):
        add_card(slide, title, body, x, y, 5.25, 1.64, accent, COLORS["white"], number=str(idx))
    add_footer(slide, slide_data.slide_no)


def add_competitor_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "市場・競合分析", "COMPETITOR", accent=COLORS["purple"])
    competitor_name = context.competitor_company_name or "競合サイト"
    target_label = "競合あり" if has_competitor_context(context) else "競合未確認"
    target_text = f"比較対象: {competitor_name}"
    if context.competitor_site_url:
        target_text = f"{target_text} / {context.competitor_site_url}"
    add_text(slide, target_label, 0.9, 1.16, 1.25, 0.28, size=11, color=COLORS["purple"], bold=True)
    add_text(slide, _trim(target_text, 70), 2.05, 1.13, 7.6, 0.32, size=12, color=COLORS["muted"], bold=True)
    add_text(slide, "5段階評価", 10.2, 1.18, 1.8, 0.22, size=12, color=COLORS["muted"], bold=True, align=PP_ALIGN.RIGHT)
    add_table(
        slide,
        headers=["比較項目", "現状仮説", competitor_name[:12], "提案後"],
        rows=context.competitor_rows,
        x=0.85,
        y=1.64,
        w=11.65,
        h=3.55,
        col_widths=[2.35, 2.8, 2.65, 3.85],
    )
    add_insight_band(
        slide,
        "競合に対する勝ち筋",
        f"{context.winning_strategy}を軸に、競合が強い領域を踏まえて情報設計・検索性・CTAを重点改善します。",
        0.92,
        5.48,
        11.4,
        0.72,
    )
    add_footer(slide, slide_data.slide_no)


def add_target_user_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "ターゲットユーザー分析", "TARGET", accent=COLORS["teal"])
    rows = context.target_user_rows[:4]
    for idx, (label, body) in enumerate(rows):
        x = 0.92 + (idx % 2) * 5.88
        y = 1.72 + (idx // 2) * 2.05
        add_card(slide, label, body, x, y, 5.24, 1.48, SECTION_COLORS[idx], COLORS["white"], number=str(idx + 1))
    add_insight_band(slide, "設計方針", "ターゲットの不安をFAQ・実績・サービス詳細で解消し、問い合わせ前の比較検討を支援します。", 0.92, 5.92, 11.4, 0.5)
    add_footer(slide, slide_data.slide_no)


def add_web_strategy_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "Web戦略", "STRATEGY", accent=COLORS["blue"])
    items = ensure_items(context.web_strategy_items + slide_data.bullets, ["集客入口を整備", "比較検討を支援", "問い合わせ導線を強化", "運用改善を継続"], 4)
    for idx, item in enumerate(items[:4]):
        x = 0.86 + idx * 3.05
        accent = SECTION_COLORS[idx]
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.82, 2.58, 3.0, fill=COLORS["white"], line=COLORS["line"])
        add_icon_badge(slide, ["SEO", "INFO", "CV", "PDCA"][idx], x + 0.75, 2.12, accent, size=0.72)
        add_text(slide, ["集客", "比較検討", "問い合わせ", "運用改善"][idx], x + 0.26, 3.14, 2.04, 0.28, size=16, color=accent, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, _trim(item, 40), x + 0.28, 3.72, 2.02, 0.54, size=13, color=COLORS["text"], bold=True, align=PP_ALIGN.CENTER)
        if idx < 3:
            add_shape(slide, MSO_SHAPE.CHEVRON, x + 2.5, 3.0, 0.36, 0.5, fill=COLORS["line_dark"], line=COLORS["line_dark"])
    add_insight_band(slide, "戦略の要点", f"{context.concept}を軸に、入口設計からCV改善、公開後運用まで一貫して設計します。", 0.92, 5.62, 11.4, 0.58)
    add_footer(slide, slide_data.slide_no)


def add_content_design_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "コンテンツ設計", "CONTENT", accent=COLORS["green"])
    items = ensure_items(context.content_items + slide_data.bullets, ["サービス詳細", "実績・事例", "FAQ", "お問い合わせ"], 4)
    for idx, item in enumerate(items[:4]):
        x = 0.92 + (idx % 2) * 5.88
        y = 1.68 + (idx // 2) * 2.0
        add_card(slide, content_title(item, idx), item, x, y, 5.24, 1.45, SECTION_COLORS[idx], COLORS["white"], number=str(idx + 1))
    add_insight_band(slide, "コンテンツの役割", "認知、比較検討、問い合わせ前の不安解消まで、各コンテンツに明確な役割を持たせます。", 0.92, 5.88, 11.4, 0.54)
    add_footer(slide, slide_data.slide_no)


def add_concept_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "本提案の方向性", "提案方針", accent=COLORS["blue"])

    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.92, 1.72, 11.48, 1.88, fill=COLORS["navy"], line=COLORS["navy"])
    add_text(slide, "Proposal Concept", 1.28, 2.0, 2.6, 0.28, size=13, color=COLORS["teal_light"], bold=True)
    add_text(slide, context.concept, 1.28, 2.36, 5.6, 0.58, size=32, color=COLORS["white"], bold=True)
    add_text(slide, _trim(concept_statement(context.concept), 62), 7.0, 2.06, 4.65, 0.78, size=16, color=COLORS["white"], bold=True)

    focus_items = ensure_items(
        context.solution_points + slide_data.bullets,
        ["情報設計と導線を再設計", "成果指標に沿って改善", "公開後の運用まで見据える"],
        3,
    )
    for idx, item in enumerate(focus_items[:3]):
        x = 0.95 + idx * 4.0
        add_card(slide, ["重点施策", "実行方針", "成果設計"][idx], item, x, 4.26, 3.35, 1.34, SECTION_COLORS[idx], COLORS["white"], number=str(idx + 1))
    add_footer(slide, slide_data.slide_no)


def add_customer_journey_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "カスタマージャーニー", "ユーザー行動", accent=COLORS["purple"])
    stages = context.journey_points[:3]
    stage_width = 3.48
    stage_y = 2.0

    for idx, (stage, description) in enumerate(stages):
        x = 0.9 + idx * 4.04
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, stage_y, stage_width, 2.25, fill=COLORS["white"], line=COLORS["line"])
        add_shape(slide, MSO_SHAPE.OVAL, x + 0.26, stage_y + 0.28, 0.52, 0.52, fill=SECTION_COLORS[idx], line=SECTION_COLORS[idx])
        add_text(slide, str(idx + 1), x + 0.26, stage_y + 0.4, 0.52, 0.16, size=11, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, stage, x + 0.92, stage_y + 0.34, 2.2, 0.3, size=20, color=COLORS["navy"], bold=True)
        add_text(slide, _trim(description, 48), x + 0.34, stage_y + 1.0, stage_width - 0.68, 0.62, size=14, color=COLORS["text"], bold=True)
        add_text(slide, _trim(journey_action(stage, context.concept), 34), x + 0.34, stage_y + 1.78, stage_width - 0.68, 0.32, size=12, color=COLORS["muted"])
        if idx < len(stages) - 1:
            add_shape(slide, MSO_SHAPE.CHEVRON, x + stage_width + 0.18, stage_y + 0.88, 0.38, 0.46, fill=COLORS["line_dark"], line=COLORS["line_dark"])

    add_insight_band(slide, "提案との関係", "認知から問い合わせまでの離脱点を減らし、情報設計・CTA・実績訴求を一連の導線として改善します。", 0.92, 5.58, 11.4, 0.58)
    add_footer(slide, slide_data.slide_no)


def add_sitemap_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "推奨サイト構成", "サイトマップ", accent=COLORS["green"])
    items = ensure_items(context.sitemap_items, ["TOP", "会社案内", "サービス", "実績", "お知らせ", "FAQ", "お問い合わせ"], 8)
    top_label = items[0] if items else "TOP"
    children = [item for item in items[1:8] if item != top_label]

    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 5.12, 1.62, 3.1, 0.68, fill=COLORS["navy"], line=COLORS["navy"])
    add_text(slide, top_label, 5.36, 1.82, 2.62, 0.22, size=18, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
    add_shape(slide, MSO_SHAPE.RECTANGLE, 6.62, 2.3, 0.04, 0.46, fill=COLORS["line_dark"], line=COLORS["line_dark"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 1.6, 2.76, 10.08, 0.04, fill=COLORS["line_dark"], line=COLORS["line_dark"])

    for idx, item in enumerate(children[:7]):
        row = idx // 4
        col = idx % 4
        x = 0.92 + col * 3.08 + (0.78 if row else 0)
        y = 3.1 + row * 1.24
        accent = SECTION_COLORS[idx % len(SECTION_COLORS)]
        add_shape(slide, MSO_SHAPE.RECTANGLE, x + 1.24, 2.78, 0.04, y - 2.78, fill=COLORS["line_dark"], line=COLORS["line_dark"])
        add_card(slide, item, sitemap_note(item), x, y, 2.54, 0.88, accent, COLORS["white"])
    add_insight_band(slide, "構成意図", "サービス・実績・FAQで比較検討を支え、CMS更新領域から最新情報を継続発信します。", 0.92, 5.92, 11.4, 0.5)
    add_footer(slide, slide_data.slide_no)


def add_kpi_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "KPI設計", "成果設計", accent=COLORS["orange"])
    metrics = [
        ("問い合わせ数", f"月{int(context.kpi_targets['inquiries'])}件", context.kpi_targets["inquiries"] / 30, COLORS["teal"]),
        ("CV率", f"{context.kpi_targets['cv_rate']}%", context.kpi_targets["cv_rate"] / 5, COLORS["blue"]),
        ("自然検索流入", f"月{int(context.kpi_targets['organic'])}セッション", context.kpi_targets["organic"] / 6000, COLORS["green"]),
        ("資料DL数", f"月{int(context.kpi_targets['downloads'])}件", context.kpi_targets["downloads"] / 40, COLORS["orange"]),
    ]
    for idx, (label, value, ratio, accent) in enumerate(metrics):
        y = 1.72 + idx * 0.9
        add_text(slide, label, 0.98, y + 0.11, 2.0, 0.24, size=13, color=COLORS["text"], bold=True)
        add_text(slide, value, 3.0, y + 0.1, 1.8, 0.24, size=13, color=accent, bold=True)
        add_shape(slide, MSO_SHAPE.RECTANGLE, 4.95, y + 0.17, 6.35, 0.16, fill=COLORS["line"], line=COLORS["line"])
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 4.95, y + 0.08, max(0.6, min(6.35, 6.35 * ratio)), 0.34, fill=accent, line=accent)

    add_table(
        slide,
        headers=["設計観点", "見る指標", "改善アクション"],
        rows=[
            ["集客", kpi_metric_for(context.concept, "集客"), "検索流入と入口ページを改善"],
            ["比較検討", kpi_metric_for(context.concept, "行動"), "サービス・実績・FAQを強化"],
            ["成果", kpi_metric_for(context.concept, "成果"), "CTAとフォーム導線を改善"],
        ],
        x=0.92,
        y=5.12,
        w=11.4,
        h=1.05,
        col_widths=[2.0, 4.0, 5.4],
    )
    add_footer(slide, slide_data.slide_no)


def add_understanding_slide(prs: Presentation, slide_data: PowerPointSlide) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "企業理解")
    points = ensure_items(slide_data.bullets, ["事業内容とターゲットを整理", "Webサイトに期待される役割を仮説化", "確認すべき前提条件を明確化"], 3)

    for idx, item in enumerate(points[:3]):
        x = MARGIN_X + idx * 4.1
        add_card(
            slide,
            title=f"理解ポイント {idx + 1}",
            body=item,
            x=x,
            y=2.0,
            w=3.55,
            h=2.6,
            accent=SECTION_COLORS[idx],
            fill=COLORS["white"],
            number=str(idx + 1),
        )
    add_insight_band(slide, "提案の前提", slide_data.visual_suggestion or "事業・ターゲット・Webの役割を整理した図", 0.9, 5.25, 11.5, 0.72)
    add_footer(slide, slide_data.slide_no)


def add_issues_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "課題整理")
    issues = ensure_items(context.project_points + slide_data.bullets, ["目的とKPIの明確化", "ターゲット別導線の整理", "公開後の改善運用の検討"], 4)

    for idx, issue in enumerate(issues[:4]):
        y = 1.64 + idx * 1.08
        add_card(
            slide,
            title=f"Priority {idx + 1}",
            body=issue,
            x=0.9,
            y=y,
            w=7.6,
            h=0.82,
            accent=SECTION_COLORS[idx % len(SECTION_COLORS)],
            fill=COLORS["white"],
            number=str(idx + 1),
        )

    add_side_panel(slide, "整理観点", ["影響度", "緊急度", "提案適合度"], 9.05, 1.64, 3.25, 4.35, COLORS["navy"])
    add_footer(slide, slide_data.slide_no)


def add_solution_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "解決策")
    items = ensure_items(context.solution_points + slide_data.bullets, ["情報設計の再整理", "訴求軸とコンテンツ方針の策定", "問い合わせにつながる導線設計"], 4)
    rows = build_solution_rows(items)
    add_table(
        slide,
        headers=["区分", "想定課題", "提案する解決策"],
        rows=rows,
        x=0.85,
        y=1.68,
        w=11.65,
        h=4.25,
        col_widths=[1.35, 4.4, 5.9],
    )
    add_footer(slide, slide_data.slide_no)


def add_process_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "制作方針")
    steps = ensure_items(context.service_points + slide_data.bullets, ["初期設計を重視した制作プロセス", "確認しやすいワイヤーフレーム作成", "公開後の改善を見据えた設計"], 4)
    add_step_flow(slide, steps[:4], 0.82, 2.12, 11.7, 1.85)
    add_insight_band(slide, "品質担保の考え方", "要件整理・設計・制作・検証を段階的に進め、認識齟齬を抑えます。", 0.92, 5.18, 11.4, 0.8)
    add_footer(slide, slide_data.slide_no)


def add_schedule_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "スケジュール")
    phases = ensure_items(context.schedule_points + slide_data.bullets, ["要件整理", "設計・デザイン", "実装・検証", "公開・改善"], 4)
    week_labels = ["1-2週", "3-4週", "5-7週", "8週"]

    add_text(slide, "工程", 0.92, 1.48, 1.5, 0.25, size=13, color=COLORS["muted"], bold=True)
    for idx, label in enumerate(week_labels):
        add_text(slide, label, 3.15 + idx * 2.15, 1.48, 1.25, 0.25, size=13, color=COLORS["muted"], bold=True, align=PP_ALIGN.CENTER)

    for idx, phase in enumerate(phases[:4]):
        y = 2.0 + idx * 0.88
        add_text(slide, _trim(phase, 18), 0.92, y + 0.12, 2.0, 0.25, size=14, color=COLORS["text"], bold=True)
        add_shape(slide, MSO_SHAPE.RECTANGLE, 3.02, y + 0.22, 8.85, 0.08, fill=COLORS["line"], line=COLORS["line"])
        add_shape(
            slide,
            MSO_SHAPE.ROUNDED_RECTANGLE,
            3.05 + idx * 1.55,
            y,
            2.25,
            0.46,
            fill=SECTION_COLORS[idx % len(SECTION_COLORS)],
            line=SECTION_COLORS[idx % len(SECTION_COLORS)],
        )
    add_insight_band(slide, "進行イメージ", "詳細スケジュールは要件・素材準備・確認体制により調整します。", 0.92, 5.78, 11.4, 0.55)
    add_footer(slide, slide_data.slide_no)


def add_case_studies_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "実績紹介")
    case_triplets = context.case_triplets or build_case_triplets_from_items(context.case_studies + slide_data.bullets)
    if not case_triplets:
        case_triplets = [
            {
                "title": "関連実績",
                "current": "近しい課題の成功事例を提案時に差し替え",
                "action": "情報設計、導線改善、運用支援の実績を整理",
                "result": "成果につながった進め方を提案へ反映",
            }
        ]

    for idx, case in enumerate(case_triplets[:3]):
        x = 0.9 + idx * 4.05
        accent = SECTION_COLORS[idx]
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.72, 3.48, 4.15, fill=COLORS["white"], line=COLORS["line"])
        add_shape(slide, MSO_SHAPE.RECTANGLE, x, 1.72, 3.48, 0.08, fill=accent, line=accent)
        add_text(slide, _trim(display_case_title(case["title"], idx + 1), 24), x + 0.26, 1.98, 2.94, 0.28, size=14, color=accent, bold=True)
        add_case_line(slide, "現状", case["current"], x + 0.26, 2.62, accent)
        add_case_line(slide, "施策", case["action"], x + 0.26, 3.62, accent)
        add_case_line(slide, "成果", case["result"], x + 0.26, 4.62, accent)
    add_footer(slide, slide_data.slide_no)


def add_team_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "体制紹介")
    roles = ["PM/ディレクター", "デザイナー", "エンジニア", "運用・改善支援"]
    details = ensure_items(context.team_points + slide_data.bullets, ["進行管理", "UI・ビジュアル設計", "実装・検証", "公開後の更新・改善相談"], 4)

    center_x, center_y = 6.1, 3.55
    add_shape(slide, MSO_SHAPE.OVAL, center_x - 0.82, center_y - 0.62, 1.65, 1.25, fill=COLORS["navy"], line=COLORS["navy"])
    add_text(slide, "Project\nCore", center_x - 0.55, center_y - 0.32, 1.1, 0.55, size=14, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)

    positions = [(1.0, 1.85), (8.85, 1.85), (1.0, 4.65), (8.85, 4.65)]
    for idx, (x, y) in enumerate(positions):
        add_card(slide, roles[idx], details[idx], x, y, 3.25, 1.35, SECTION_COLORS[idx], COLORS["white"])
        add_shape(slide, MSO_SHAPE.RECTANGLE, 4.35 if idx % 2 == 0 else 8.15, y + 0.62, 1.05, 0.04, fill=COLORS["line_dark"], line=COLORS["line_dark"])
    add_footer(slide, slide_data.slide_no)


def add_cost_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "費用概算")
    items = ensure_items(
        [
            f"合計概算: {context.estimate.total_label}",
            f"予算適合: {context.estimate.budget_fit}",
            f"必須対応: {'、'.join(context.estimate.required[:3])}",
            *context.cost_points,
            *slide_data.bullets,
        ],
        ["必須範囲とオプションを分離", "ページ数と機能要件に応じて調整", "詳細見積はヒアリング後に提示"],
        4,
    )
    rows = [
        ["合計概算", context.estimate.total_label, f"想定{context.estimate.page_count}ページ"],
        ["予算適合", context.estimate.budget_fit, f"予算感: {context.estimate.budget_label}"],
        ["必須対応", _trim("、".join(context.estimate.required[:4]), 36), "要件整理・設計・制作・検証"],
        ["調整範囲", _trim(items[3] if len(items) > 3 else "推奨・オプションを段階化", 36), "CMS・SEO・特殊機能・撮影原稿"],
    ]
    add_table(
        slide,
        headers=["区分", "考え方", "主な内容"],
        rows=rows,
        x=0.85,
        y=1.55,
        w=11.65,
        h=4.0,
        col_widths=[2.0, 4.3, 5.35],
    )
    add_insight_band(slide, "見積方針", "必須範囲を先に確保し、推奨・オプション対応を予算と納期に合わせて段階提案します。", 0.92, 5.84, 11.4, 0.55)
    add_footer(slide, slide_data.slide_no)


def add_estimate_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "概算見積", "ESTIMATE", accent=COLORS["teal"])
    add_text(slide, f"合計概算 {context.estimate.total_label}", 0.9, 1.1, 5.8, 0.35, size=20, color=COLORS["teal"], bold=True)
    add_text(slide, f"想定ページ数: {context.estimate.page_count}ページ / 予算感: {context.estimate.budget_label}", 7.1, 1.16, 5.0, 0.24, size=12, color=COLORS["muted"], bold=True, align=PP_ALIGN.RIGHT)
    rows = [
        [
            str(line["name"]),
            f"{line['min']}万〜{line['max']}万円" if bool(line["enabled"]) else "対象外",
            str(line["priority"]),
        ]
        for line in context.estimate.lines
    ]
    add_table(
        slide,
        headers=["見積項目", "金額レンジ", "分類"],
        rows=rows,
        x=0.76,
        y=1.62,
        w=11.8,
        h=4.75,
        col_widths=[5.1, 3.2, 3.5],
    )
    add_footer(slide, slide_data.slide_no)


def add_budget_fit_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "予算適合判定", "BUDGET FIT", accent=COLORS["orange"])
    fit_color = COLORS["green"] if context.estimate.budget_fit == "予算内" else COLORS["orange"] if context.estimate.budget_fit == "やや調整必要" else COLORS["red"]
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.95, 1.62, 4.0, 3.2, fill=COLORS["white"], line=COLORS["line"])
    add_text(slide, "判定", 1.25, 2.05, 3.4, 0.3, size=16, color=COLORS["muted"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, context.estimate.budget_fit, 1.2, 2.55, 3.5, 0.55, size=25, color=fit_color, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, f"予算感: {context.estimate.budget_label}", 1.25, 3.46, 3.4, 0.28, size=14, color=COLORS["text"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, f"概算見積: {context.estimate.total_label}", 1.25, 3.9, 3.4, 0.28, size=14, color=COLORS["text"], bold=True, align=PP_ALIGN.CENTER)

    cards = [
        ("差分の見方", "上限予算と概算上限を比較し、調整要否を判断"),
        ("調整方針", "必須対応を優先し、推奨・オプションを段階化"),
        ("次回確認", "ページ数、CMS範囲、特殊機能、素材準備を確定"),
    ]
    for idx, (title, body) in enumerate(cards):
        add_card(slide, title, body, 5.38, 1.55 + idx * 1.38, 6.9, 1.08, SECTION_COLORS[idx], COLORS["white"], number=str(idx + 1))
    add_insight_band(slide, "営業判断", "予算と見積の差分を早期に共有し、提出前に必須範囲とオプション範囲を合意します。", 0.92, 5.72, 11.4, 0.58)
    add_footer(slide, slide_data.slide_no)


def add_estimate_priority_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "必須・推奨・オプション対応", "SCOPE", accent=COLORS["blue"])
    columns = [
        ("必須対応", context.estimate.required, COLORS["teal"], COLORS["teal_light"]),
        ("推奨対応", context.estimate.recommended or ["次回確認"], COLORS["blue"], COLORS["blue_light"]),
        ("オプション対応", context.estimate.optional or ["次回確認"], COLORS["orange"], COLORS["orange_light"]),
    ]
    for idx, (title, items, accent, fill) in enumerate(columns):
        x = 0.86 + idx * 4.1
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.62, 3.65, 4.4, fill=fill, line=COLORS["white"])
        add_text(slide, title, x + 0.25, 1.98, 3.15, 0.3, size=17, color=accent, bold=True, align=PP_ALIGN.CENTER)
        add_bullet_list(slide, items, x + 0.34, 2.62, 2.95, 2.7, max_items=5, size=13)
    add_footer(slide, slide_data.slide_no)


def add_summary_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "まとめ")
    confirmation = f"次回確認事項: {'・'.join(context.confirmation_items[:3])}" if context.confirmation_items else "次回確認事項を整理"
    values = ensure_items(unique_items(slide_data.bullets, 2) + [confirmation], ["課題仮説に基づく制作方針", "成果につながる導線設計", "次回確認事項の整理"], 3)

    for idx, item in enumerate(values[:3]):
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.95 + idx * 4.02, 2.08, 3.35, 2.55, fill=[COLORS["teal_light"], COLORS["blue_light"], COLORS["orange_light"]][idx], line=COLORS["white"])
        add_text(slide, f"Value {idx + 1}", 1.2 + idx * 4.02, 2.38, 2.85, 0.32, size=16, color=SECTION_COLORS[idx], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, _trim(item, 42), 1.25 + idx * 4.02, 3.15, 2.75, 0.72, size=18, color=COLORS["text"], bold=True, align=PP_ALIGN.CENTER)
    add_footer(slide, slide_data.slide_no)


def add_next_steps_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "今後の進め方", "NEXT STEP", accent=COLORS["blue"])
    steps = [
        "1. 目的・KPI・優先範囲の合意",
        "2. サイト構成・必要コンテンツの確定",
        "3. 見積・スケジュール・体制の最終化",
        "4. キックオフ・素材準備・制作開始",
    ]
    add_step_flow(slide, steps, 0.82, 1.9, 11.7, 1.65)
    confirmations = ensure_items(context.confirmation_items + slide_data.bullets, ["予算内で優先する必須範囲", "希望納期に対する素材準備状況", "CMS権限と更新担当範囲"], 4)
    for idx, item in enumerate(confirmations[:4]):
        x = 0.92 + (idx % 2) * 5.88
        y = 4.08 + (idx // 2) * 1.04
        add_card(slide, f"確認事項 {idx + 1}", item, x, y, 5.24, 0.9, SECTION_COLORS[idx], COLORS["white"])
    add_footer(slide, slide_data.slide_no)


def add_generic_slide(prs: Presentation, slide_data: PowerPointSlide) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "提案内容")
    add_bullet_list(slide, slide_data.bullets, 0.9, 1.78, 7.55, 3.9, max_items=5)
    add_visual_frame(slide, slide_data.visual_suggestion or "図表・画面イメージ・実績画像を配置", 9.0, 1.78, 3.25, 3.9)
    add_footer(slide, slide_data.slide_no)


def add_win_probability_slide(prs: Presentation, win: WinProbability, slide_no: int) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    rank_color = rank_color_for(win.rank)
    add_header(slide, "受注確率判定", "商談判断", accent=rank_color)
    probability = win.probability or rank_probability_for(win.rank)
    risk_score = max(1, min(5, win.risk_score or risk_score_for_probability(probability, len(win.risk_factors))))
    risk_label = win.risk_label or risk_label_for(risk_score)
    projected = win.projected_probability_after_actions or projected_probability_for(
        probability,
        risk_score,
        len(win.improvement_actions or win.recommended_next_actions),
    )

    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 0.95, 1.46, 3.28, 3.1, fill=rank_light_color_for(win.rank), line=rank_color)
    add_text(slide, "受注確率", 1.22, 1.76, 2.72, 0.24, size=13, color=COLORS["muted"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, f"{probability}%", 1.18, 2.1, 2.82, 0.68, size=42, color=rank_color, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, f"{win.rank}ランク", 1.32, 2.88, 2.48, 0.3, size=19, color=rank_color, bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, f"受注リスク {risk_label}", 1.16, 3.38, 2.86, 0.24, size=12, color=COLORS["red"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, f"向上予測 {probability}% → {projected}%", 1.12, 3.8, 2.96, 0.28, size=14, color=COLORS["blue"], bold=True, align=PP_ALIGN.CENTER)

    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 4.62, 1.58, 7.55, 1.58, fill=COLORS["white"], line=COLORS["line"])
    add_text(slide, "判定理由", 4.96, 1.84, 1.3, 0.26, size=13, color=rank_color, bold=True)
    add_text(slide, _trim(win.reason, 82), 6.18, 1.84, 5.55, 0.62, size=13, color=COLORS["text"], bold=True)

    add_factor_column(slide, "リスク要因", win.risk_factors, 0.95, 5.02, COLORS["red"])
    add_factor_column(slide, "改善アクション", win.improvement_actions or win.recommended_next_actions, 4.68, 5.02, COLORS["blue"])
    add_factor_column(slide, "加点要因", win.positive_factors, 8.41, 5.02, COLORS["teal"])
    add_footer(slide, slide_no)


def add_factor_column(slide, title: str, items: list[str], x: float, y: float, accent: str) -> None:
    add_card(slide, title, "", x, y, 3.05, 1.58, accent, COLORS["white"])
    add_bullet_list(slide, unique_items(items, 2), x + 0.22, y + 0.58, 2.6, 0.78, max_items=2, size=10)


def add_case_line(slide, label: str, body: str, x: float, y: float, accent: str) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, 0.66, 0.28, fill=accent, line=accent)
    add_text(slide, label, x + 0.08, y + 0.08, 0.5, 0.1, size=8, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
    add_text(slide, _trim(body, 42), x + 0.84, y - 0.02, 2.18, 0.48, size=11, color=COLORS["text"], bold=True)


def add_icon_badge(slide, label: str, x: float, y: float, accent: str, *, size: float = 0.82) -> None:
    add_shape(slide, MSO_SHAPE.OVAL, x, y, size, size, fill=accent, line=accent)
    add_text(slide, label, x + 0.06, y + size * 0.42, size - 0.12, 0.12, size=10 if len(label) <= 3 else 8, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)


def chapter_icon(title: str) -> str:
    if "競合" in title:
        return "VS"
    if "KPI" in title:
        return "KPI"
    if "サイト" in title:
        return "MAP"
    if "戦略" in title:
        return "STR"
    if "体制" in title:
        return "TEAM"
    return "WEB"


def chapter_message(title: str, context: PptxContext) -> str:
    if "提案サマリー" in title:
        return f"{context.concept}を軸に、成果につながるWebサイト改善の全体像を提示します。"
    if "現状理解" in title:
        return "案件概要から読み取れる現状、事業課題、改善機会を整理します。"
    if "課題" in title:
        return "成果に影響する課題を優先度順に絞り込み、提案の論点を明確にします。"
    if "競合" in title:
        return f"競合標準を超えるための改善余地を6つの観点で可視化し、{context.winning_strategy}を提案します。"
    if "ターゲット" in title:
        return "主要ユーザーのニーズと不安を整理し、必要な情報接点を定義します。"
    if "ジャーニー" in title:
        return "認知から問い合わせまでの行動を分解し、離脱を減らす接点を設計します。"
    if "Web戦略" in title or "WEB戦略" in title:
        return f"{context.concept}を実現するための集客、比較検討、CV、運用改善を設計します。"
    if "サイトマップ" in title or "サイト構成" in title:
        return "ユーザーが必要情報へ迷わず進み、運用もしやすいサイト構成を提示します。"
    if "コンテンツ" in title:
        return "サービス理解、比較検討、不安解消、問い合わせを支えるコンテンツを設計します。"
    if "KPI" in title:
        return "問い合わせ数、CV率、自然検索流入、資料DL数を目標化します。"
    if "制作方針" in title or "方針" in title:
        return "設計、デザイン、実装、検証を段階化し、品質と進行の見通しを示します。"
    if "スケジュール" in title:
        return "公開希望時期から逆算し、要件整理からリリースまでの進行を提示します。"
    if "関連実績" in title or "実績" in title:
        return "入力された成功事例を、現状、施策、成果の流れで提案の裏付けとして示します。"
    if "体制" in title:
        return "プロジェクトを安定して進める役割分担と支援範囲を明確にします。"
    if "見積" in title:
        return f"想定ページ数と機能条件をもとに、概算見積レンジ{context.estimate.total_label}を提示します。"
    if "予算適合" in title:
        return f"入力予算と概算見積を比較し、{context.estimate.budget_fit}として調整方針を整理します。"
    if "必須" in title and "推奨" in title and "オプション" in title:
        return "予算内で成果を出すため、対応範囲を必須・推奨・オプションに分類します。"
    if "費用" in title or "概算" in title:
        return "必須範囲とオプションを分け、予算判断しやすい費用構成を提示します。"
    if "今後" in title:
        return "意思決定に必要な確認事項と、制作開始までの進め方を明確にします。"
    return "本提案の実行内容と判断材料を、章ごとに具体化します。"


def content_title(item: str, index: int) -> str:
    if ":" in item:
        return item.split(":", 1)[0]
    if "：" in item:
        return item.split("：", 1)[0]
    return ["サービス訴求", "実績・事例", "FAQ", "CV導線"][index % 4]


def add_header(slide, title: str, section: str, accent: str = COLORS["teal"]) -> None:
    add_section_label(slide, section, MARGIN_X, HEADER_Y, fill=accent, color=COLORS["white"])
    add_title(slide, title, MARGIN_X, 0.8, 10.2, 0.48, size=30, color=COLORS["navy"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, MARGIN_X, 1.32, 11.76, 0.025, fill=COLORS["line"], line=COLORS["line"])


def add_footer(slide, slide_no: int) -> None:
    add_shape(slide, MSO_SHAPE.RECTANGLE, MARGIN_X, 6.76, 11.88, 0.02, fill=COLORS["line"], line=COLORS["line"])
    add_text(slide, "Ready Crew Proposal AI", MARGIN_X, FOOTER_Y, 3.4, 0.18, size=9, color=COLORS["muted"])
    add_text(slide, f"{slide_no:02}", 11.58, 6.86, 0.76, 0.22, size=10, color=COLORS["muted"], align=PP_ALIGN.RIGHT)


def add_title(slide, text: str, x: float, y: float, w: float, h: float, *, size: int, color: str) -> None:
    add_text(slide, _trim(text, 42), x, y, w, h, size=_fit_font_size(text, size), color=color, bold=True)


def add_card(
    slide,
    title: str,
    body: str,
    x: float,
    y: float,
    w: float,
    h: float,
    accent: str,
    fill: str,
    number: str | None = None,
) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=fill, line=COLORS["line"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, x, y, 0.08, h, fill=accent, line=accent)
    if number:
        add_shape(slide, MSO_SHAPE.OVAL, x + 0.22, y + 0.22, 0.36, 0.36, fill=accent, line=accent)
        add_text(slide, number, x + 0.22, y + 0.29, 0.36, 0.12, size=10, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
        title_x = x + 0.72
        title_w = w - 0.95
    else:
        title_x = x + 0.28
        title_w = w - 0.54
    add_text(slide, _trim(title, 28), title_x, y + 0.22, title_w, 0.26, size=12, color=accent, bold=True)
    if body:
        add_text(slide, _trim(body, 56), x + 0.28, y + 0.7, w - 0.54, h - 0.86, size=13, color=COLORS["text"])


def add_section_label(slide, text: str, x: float, y: float, *, fill: str, color: str) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, 1.55, 0.32, fill=fill, line=fill)
    add_text(slide, text, x + 0.13, y + 0.08, 1.3, 0.12, size=8, color=color, bold=True, align=PP_ALIGN.CENTER)


def add_bullet_list(
    slide,
    items: list[str],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    max_items: int = 5,
    size: int = 14,
) -> None:
    clean_items = unique_items(items, max_items) or ["次回確認事項として整理します。"]
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    set_frame_margins(frame, 0)

    for index, item in enumerate(clean_items[:max_items]):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = f"• {_trim(item, 52)}"
        paragraph.space_after = Pt(6)
        style_paragraph(paragraph, size=size, color=COLORS["text"], bold=False)


def add_table(slide, headers: list[str], rows: list[list[str]], x: float, y: float, w: float, h: float, col_widths: list[float]) -> None:
    table_shape = slide.shapes.add_table(len(rows) + 1, len(headers), Inches(x), Inches(y), Inches(w), Inches(h))
    table = table_shape.table

    for col_index, width in enumerate(col_widths):
        table.columns[col_index].width = Inches(width)

    for col_index, header in enumerate(headers):
        set_cell(table.cell(0, col_index), header, fill=COLORS["navy"], color=COLORS["white"], size=11, bold=True)

    for row_index, row in enumerate(rows, start=1):
        for col_index, value in enumerate(row):
            fill = COLORS["canvas"] if row_index % 2 == 0 else COLORS["white"]
            set_cell(table.cell(row_index, col_index), _trim(value, 52), fill=fill, color=COLORS["text"], size=11, bold=col_index == 0)


def add_step_flow(slide, steps: list[str], x: float, y: float, w: float, h: float) -> None:
    step_count = min(len(steps), 4)
    gap = 0.18
    step_w = (w - gap * (step_count - 1)) / step_count
    for index, step in enumerate(steps[:step_count]):
        sx = x + index * (step_w + gap)
        accent = SECTION_COLORS[index % len(SECTION_COLORS)]
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, sx, y, step_w, h, fill=COLORS["white"], line=COLORS["line"])
        add_shape(slide, MSO_SHAPE.OVAL, sx + 0.28, y + 0.28, 0.46, 0.46, fill=accent, line=accent)
        add_text(slide, str(index + 1), sx + 0.28, y + 0.38, 0.46, 0.14, size=10, color=COLORS["white"], bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, _trim(step, 36), sx + 0.32, y + 0.95, step_w - 0.64, 0.55, size=14, color=COLORS["text"], bold=True, align=PP_ALIGN.CENTER)
        if index < step_count - 1:
            add_shape(slide, MSO_SHAPE.CHEVRON, sx + step_w - 0.05, y + 0.72, 0.32, 0.42, fill=COLORS["line_dark"], line=COLORS["line_dark"])


def add_visual_frame(slide, label: str, x: float, y: float, w: float, h: float) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=COLORS["canvas"], line=COLORS["line"])
    add_shape(slide, MSO_SHAPE.OVAL, x + 0.35, y + 0.4, 0.55, 0.55, fill=COLORS["teal_light"], line=COLORS["teal_light"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, x + 1.05, y + 0.54, w - 1.55, 0.08, fill=COLORS["line_dark"], line=COLORS["line_dark"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, x + 0.35, y + 1.35, w - 0.7, 0.08, fill=COLORS["line"], line=COLORS["line"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, x + 0.35, y + 1.78, w - 1.15, 0.08, fill=COLORS["line"], line=COLORS["line"])
    add_text(slide, _trim(label, 56), x + 0.38, y + h - 0.82, w - 0.76, 0.36, size=12, color=COLORS["muted"], align=PP_ALIGN.CENTER)


def add_insight_band(slide, title: str, body: str, x: float, y: float, w: float, h: float) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=COLORS["navy"], line=COLORS["navy"])
    add_text(slide, title, x + 0.34, y + 0.2, 2.4, 0.25, size=13, color=COLORS["teal_light"], bold=True)
    add_text(slide, _trim(body, 82), x + 2.65, y + 0.19, w - 3.0, 0.3, size=13, color=COLORS["white"])


def add_side_panel(slide, title: str, items: list[str], x: float, y: float, w: float, h: float, accent: str) -> None:
    add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill=COLORS["navy"], line=COLORS["navy"])
    add_text(slide, title, x + 0.32, y + 0.34, w - 0.64, 0.3, size=17, color=COLORS["white"], bold=True)
    for idx, item in enumerate(items):
        add_shape(slide, MSO_SHAPE.OVAL, x + 0.36, y + 1.1 + idx * 0.78, 0.22, 0.22, fill=accent, line=accent)
        add_text(slide, item, x + 0.72, y + 1.05 + idx * 0.78, w - 1.0, 0.24, size=13, color=COLORS["white"], bold=True)


def blank_slide(prs: Presentation):
    return prs.slides.add_slide(prs.slide_layouts[6])


def set_background(slide) -> None:
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = rgb(COLORS["white"])


def add_shape(slide, shape_type, x: float, y: float, w: float, h: float, *, fill: str, line: str):
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.color.rgb = rgb(line)
    return shape


def add_text(
    slide,
    text: str,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    size: int,
    color: str,
    bold: bool = False,
    align: PP_ALIGN | None = None,
) -> None:
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.vertical_anchor = MSO_VERTICAL_ANCHOR.TOP
    set_frame_margins(frame, 0)

    paragraph = frame.paragraphs[0]
    paragraph.text = text
    if align is not None:
        paragraph.alignment = align
    style_paragraph(paragraph, size=size, color=color, bold=bold)


def set_cell(cell, text: str, *, fill: str, color: str, size: int, bold: bool) -> None:
    cell.fill.solid()
    cell.fill.fore_color.rgb = rgb(fill)
    frame = cell.text_frame
    frame.clear()
    frame.word_wrap = True
    set_frame_margins(frame, 0.06)
    paragraph = frame.paragraphs[0]
    paragraph.text = text
    style_paragraph(paragraph, size=size, color=color, bold=bold)


def set_frame_margins(frame, value: float) -> None:
    margin = Inches(value)
    frame.margin_left = margin
    frame.margin_right = margin
    frame.margin_top = margin
    frame.margin_bottom = margin


def style_paragraph(paragraph, *, size: int, color: str, bold: bool) -> None:
    for run in paragraph.runs:
        run.font.name = FONT_FACE
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = rgb(color)


def _fallback_slide(data: PowerPointData) -> PowerPointSlide:
    return PowerPointSlide(
        slide_no=1,
        layout="title",
        title=data.deck_title or "Webサイト制作ご提案書",
        bullets=[data.client_name or "提案先企業", "提案構成の生成結果をスライド化"],
        speaker_notes="生成結果をもとにした提案資料です。",
        visual_suggestion="表紙背景、企業名、自社ロゴ",
    )


def derive_concept(text: str) -> str:
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        return "物件検索強化"
    if _contains_any(text, ["採用", "応募", "求人", "求職"]):
        return "採用強化"
    if _contains_any(text, ["問い合わせ", "問合せ", "CV", "コンバージョン", "資料請求", "商談"]):
        return "問い合わせ最大化"
    if _contains_any(text, ["ブランド", "ブランディング", "認知", "信頼感"]):
        return "ブランディング強化"
    if _contains_any(text, ["SEO", "検索", "流入"]):
        return "検索流入強化"
    if _contains_any(text, ["CMS", "更新", "運用"]):
        return "CMS運用強化"
    return "Web成果最大化"


def derive_current_understanding(project_brief: str, concept: str) -> dict[str, str]:
    points = extract_project_points(project_brief)
    current = "Webサイトの役割を見直し、営業・採用・広報の成果接点として再設計する局面です。"
    if _contains_any(project_brief, ["古", "リニューアル", "刷新", "改修"]):
        current = "現行サイトの情報鮮度と見せ方が、現在の事業内容や営業活動に追いついていない状態です。"
    elif _contains_any(project_brief, ["新規", "立ち上げ", "初めて"]):
        current = "新しいWeb接点を立ち上げ、事業内容と強みを伝える土台を作る局面です。"
    elif _contains_any(project_brief, ["問い合わせ", "問合せ", "CV"]):
        current = "Webサイトを問い合わせ獲得の接点として強化する段階です。"

    issue = points[0] if points else "Webサイトの目的と優先ターゲットの明確化"
    opportunity = concept_statement(concept)
    target = f"{concept}を軸に、訪問者が理解、比較、問い合わせまで迷わず進める状態を作ります。"
    return {"現状": current, "課題": issue, "機会": opportunity, "目指す状態": target}


def merge_understanding_items(base: dict[str, str], bullets: list[str]) -> dict[str, str]:
    merged = dict(base)
    for bullet in bullets:
        match = re.match(r"^(現状|課題|機会|目指す状態)\s*[:：]\s*(.+)$", bullet.strip())
        if match:
            merged[match.group(1)] = match.group(2)
    return merged


def concept_statement(concept: str) -> str:
    statements = {
        "問い合わせ最大化": "導線、CTA、実績訴求を連動させ、商談につながる問い合わせを増やします。",
        "採用強化": "仕事内容、働く魅力、応募導線を整理し、候補者の理解と応募行動を促します。",
        "ブランディング強化": "強み、実績、メッセージを統一し、第一印象と信頼感を高めます。",
        "物件検索強化": "検索導線と物件情報を整理し、比較検討から問い合わせまでを短縮します。",
        "検索流入強化": "検索意図に合う構造とコンテンツを設計し、自然検索からの流入を伸ばします。",
        "CMS運用強化": "更新しやすいCMSと運用フローを整備し、情報鮮度を維持します。",
        "Web成果最大化": "情報設計、導線、運用を整え、Webサイトを成果創出の基盤にします。",
    }
    return statements.get(concept, statements["Web成果最大化"])


def derive_journey_points(concept: str) -> list[tuple[str, str]]:
    if concept == "採用強化":
        return [("認知", "企業の魅力と募集職種を伝える"), ("比較検討", "働き方・社員情報・制度で納得感を高める"), ("問い合わせ", "応募フォームまでの導線を短くする")]
    if concept == "物件検索強化":
        return [("認知", "エリア・物件情報への入口を増やす"), ("比較検討", "条件検索と物件詳細で比較しやすくする"), ("問い合わせ", "内見予約・資料請求へ迷わず進める")]
    if concept == "ブランディング強化":
        return [("認知", "企業の強みと世界観を第一印象で伝える"), ("比較検討", "実績・サービス・選ばれる理由を深く見せる"), ("問い合わせ", "相談テーマ別に導線を分ける")]
    return [("認知", "SEO・広告・紹介からの受け皿を整える"), ("比較検討", "サービス内容・実績・FAQで不安を減らす"), ("問い合わせ", "CTAとフォーム導線を最短化する")]


def journey_action(stage: str, concept: str) -> str:
    if stage == "認知":
        return "入口ページと訴求メッセージを最適化"
    if stage == "比較検討":
        return "実績、FAQ、料金観点で不安を解消"
    if concept == "採用強化":
        return "応募導線とフォーム到達を改善"
    if concept == "物件検索強化":
        return "内見予約と資料請求を促進"
    return "問い合わせCTAとフォーム導線を改善"


def derive_sitemap_items(text: str) -> list[str]:
    items = ["トップ", "会社案内", "サービス", "実績", "お知らせ", "お問い合わせ"]
    if _contains_any(text, ["採用", "求人", "応募"]):
        items.insert(-1, "採用情報")
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        items.insert(2, "物件検索")
    if _contains_any(text, ["CMS", "FAQ", "よくある質問"]):
        items.insert(-1, "FAQ")
    if _contains_any(text, ["資料請求", "ホワイトペーパー"]):
        items.insert(-1, "資料ダウンロード")
    return unique_items(items, 9)


def sitemap_note(item: str) -> str:
    if item == "サービス":
        return "提供価値と選ばれる理由"
    if item == "実績":
        return "比較検討を後押し"
    if item == "お知らせ":
        return "CMS更新の中心領域"
    if item == "FAQ":
        return "問い合わせ前の不安を解消"
    if item == "お問い合わせ":
        return "CV導線の最終接点"
    if item == "採用情報":
        return "候補者向け情報を集約"
    if item == "物件検索":
        return "条件検索と詳細導線"
    return "基本情報を整理"


def derive_kpi_rows(text: str, concept: str) -> list[tuple[str, str]]:
    targets = derive_kpi_targets(text, concept)
    if concept == "採用強化":
        return [("問い合わせ数", f"月{int(targets['inquiries'])}件"), ("CV率", f"{targets['cv_rate']}%"), ("自然検索流入", f"月{int(targets['organic'])}セッション"), ("資料DL数", f"月{int(targets['downloads'])}件")]
    if concept == "物件検索強化":
        return [("問い合わせ数", f"月{int(targets['inquiries'])}件"), ("CV率", f"{targets['cv_rate']}%"), ("自然検索流入", f"月{int(targets['organic'])}セッション"), ("資料DL数", f"月{int(targets['downloads'])}件")]
    return [("問い合わせ数", f"月{int(targets['inquiries'])}件"), ("CV率", f"{targets['cv_rate']}%"), ("自然検索流入", f"月{int(targets['organic'])}セッション"), ("資料DL数", f"月{int(targets['downloads'])}件")]


def derive_kpi_targets(text: str, concept: str) -> dict[str, float]:
    if concept == "採用強化":
        return {"inquiries": 8, "cv_rate": 2.0, "organic": 2500, "downloads": 10}
    if concept == "物件検索強化":
        return {"inquiries": 25, "cv_rate": 3.0, "organic": 4000, "downloads": 20}
    if _contains_any(text, ["SEO", "検索", "流入"]):
        return {"inquiries": 18, "cv_rate": 2.5, "organic": 5000, "downloads": 30}
    if _contains_any(text, ["問い合わせ", "問合せ", "CV"]):
        return {"inquiries": 20, "cv_rate": 2.8, "organic": 3500, "downloads": 25}
    return {"inquiries": 12, "cv_rate": 2.0, "organic": 2500, "downloads": 15}


def derive_competitor_rows(text: str) -> list[list[str]]:
    scores = {
        "デザイン": 2 if _contains_any(text, ["古", "リニューアル", "刷新", "改修", "ブランド", "信頼感"]) else 3,
        "SEO": 2 if _contains_any(text, ["SEO", "検索", "自然検索", "流入"]) else 3,
        "導線設計": 2 if _contains_any(text, ["問い合わせ", "問合せ", "CV", "資料請求", "導線"]) else 3,
        "コンテンツ量": 2 if _contains_any(text, ["情報不足", "実績", "事例", "FAQ", "コンテンツ"]) else 3,
        "更新性": 2 if _contains_any(text, ["CMS", "更新", "運用", "お知らせ"]) else 3,
        "CTA": 2 if _contains_any(text, ["CTA", "問い合わせ", "問合せ", "CV", "フォーム"]) else 3,
    }
    high_priority = {"デザイン", "SEO", "導線設計", "CTA"}
    return [[key, score_label(value), score_label(3), score_label(5 if key in high_priority else 4)] for key, value in scores.items()]


def derive_winning_strategy(text: str) -> str:
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        return "物件検索で勝つ"
    if _contains_any(text, ["SEO", "検索", "自然検索", "流入"]):
        return "SEOで勝つ"
    if _contains_any(text, ["実績", "事例", "導入", "信頼"]):
        return "実績訴求で勝つ"
    if _contains_any(text, ["問い合わせ", "問合せ", "CV", "CTA", "フォーム"]):
        return "検索導線で勝つ"
    return "実績訴求とCTA改善で勝つ"


def has_competitor_context(context: PptxContext) -> bool:
    return bool(context.competitor_site_url or context.competitor_company_name)


def derive_target_user_rows(text: str, concept: str) -> list[tuple[str, str]]:
    if concept == "採用強化":
        return [("主要ターゲット", "応募を検討する求職者"), ("ニーズ", "仕事内容、働く環境、成長機会を知りたい"), ("不安", "社風や選考後の働き方が見えにくい"), ("必要コンテンツ", "社員紹介、募集要項、FAQ、応募導線")]
    if concept == "物件検索強化":
        return [("主要ターゲット", "条件に合う物件を探す検討者"), ("ニーズ", "エリア、価格、条件で素早く比較したい"), ("不安", "問い合わせ後の流れや物件詳細が不足する"), ("必要コンテンツ", "物件検索、詳細ページ、FAQ、内見予約")]
    if _contains_any(text, ["BtoB", "法人", "企業"]):
        return [("主要ターゲット", "サービス導入を検討する法人担当者"), ("ニーズ", "支援内容、実績、費用対効果を把握したい"), ("不安", "導入後の運用負荷と成果が見えにくい"), ("必要コンテンツ", "サービス詳細、事例、料金観点、問い合わせ")]
    return [("主要ターゲット", "サービス比較中の見込み顧客"), ("ニーズ", "強み、実績、費用感を短時間で把握したい"), ("不安", "自社に合うか、依頼後の進め方が分かりにくい"), ("必要コンテンツ", "サービス、実績、FAQ、問い合わせ")]


def derive_content_items(text: str, concept: str) -> list[str]:
    items = ["サービス詳細: 強み、対象課題、提供範囲を明確化", "実績・事例: 成果とプロセスを見せて比較検討を後押し", "FAQ: 費用、納期、運用、CMSの不安を先回りして解消", "お問い合わせ: CTAとフォーム項目を最短化"]
    if concept == "採用強化":
        items[0] = "採用情報: 募集職種、働き方、社員の声を整理"
    if _contains_any(text, ["資料請求", "ホワイトペーパー"]):
        items.append("資料ダウンロード: 検討初期のリード獲得導線を設置")
    return unique_items(items, 4)


def derive_web_strategy_items(text: str, concept: str) -> list[str]:
    return unique_items(
        [
            "集客: SEO・広告・紹介流入の受け皿を整備",
            "比較検討: サービス、実績、FAQで判断材料を提供",
            "問い合わせ: CTAとフォーム導線を短く設計",
            "運用改善: CMS更新とアクセス解析で継続改善",
        ],
        4,
    )


def score_label(value: int) -> str:
    return f"{value}/5"


def kpi_metric_for(concept: str, category: str) -> str:
    if concept == "採用強化":
        return {"集客": "採用ページ流入", "行動": "募集要項閲覧・社員紹介閲覧", "成果": "応募数・応募率"}[category]
    if concept == "物件検索強化":
        return {"集客": "物件検索流入", "行動": "物件詳細閲覧・お気に入り", "成果": "内見予約・問い合わせ数"}[category]
    if concept == "検索流入強化":
        return {"集客": "自然検索流入", "行動": "主要ページ回遊・FAQ閲覧", "成果": "問い合わせ件数・CV率"}[category]
    return {"集客": "アクセス数・流入経路", "行動": "サービス/実績閲覧・CTAクリック", "成果": "問い合わせ件数・CV率"}[category]


def extract_case_triplets(case_studies: str) -> list[dict[str, str]]:
    return build_case_triplets_from_items(extract_case_study_items(case_studies))


def build_case_triplets_from_items(items: list[str]) -> list[dict[str, str]]:
    triplets: list[dict[str, str]] = []
    for idx, item in enumerate(unique_items(items, 3), start=1):
        title = extract_case_title(item, idx)
        result = extract_labeled_segment(item, "成果") or extract_unlabeled_case_result(item)
        current = extract_current_segment(item)
        triplets.append(
            {
                "title": title,
                "current": current or case_current_hint(item, title, result),
                "action": extract_labeled_segment(item, "施策") or case_action_hint(f"{title} {item} {result}"),
                "result": result or case_result_hint(item),
            }
        )
    return triplets


def extract_case_title(item: str, index: int) -> str:
    title_match = re.match(r"^([^:：。]+)[:：]", item.strip())
    if title_match and not title_match.group(1) in {"現状", "施策", "成果"}:
        return title_match.group(1).strip()
    return f"Case {index}"


def remove_case_title(item: str) -> str:
    if re.match(r"^([^:：。]+)[:：]", item.strip()):
        return re.sub(r"^([^:：。]+)[:：]\s*", "", item.strip())
    return item


def extract_labeled_segment(item: str, label: str) -> str:
    match = re.search(rf"{label}\s*[:：]\s*(.*?)(?=(?:現状|施策|成果)\s*[:：]|。|;|；|\n|$)", item)
    return _trim(match.group(1), 42) if match else ""


def extract_current_segment(item: str) -> str:
    current = extract_labeled_segment(item, "現状")
    if current and not looks_like_case_result(current):
        return current
    return ""


def extract_unlabeled_case_result(item: str) -> str:
    body = remove_case_title(item)
    result_phrase = extract_case_result_phrase(body)
    if result_phrase:
        return _trim(result_phrase, 42)
    return ""


def looks_like_case_result(text: str) -> bool:
    return bool(re.search(r"(\d+[%％]|[0-9.]+倍|\d+件|増加|向上|CV率|問い合わせ件数|自然検索流入)", text))


def extract_case_result_phrase(text: str) -> str:
    patterns = [
        r"問い合わせ件数\s*\d+[%％]?\s*(?:増加|向上|改善)?",
        r"CV率\s*[0-9.]+\s*倍",
        r"CV率\s*\d+[%％]?\s*(?:増加|向上|改善)?",
        r"自然検索流入\s*\d+[%％]?\s*(?:増加|向上|改善)?",
        r"\d+[%％]\s*(?:増加|向上|改善)",
        r"[0-9.]+\s*倍",
        r"\d+件\s*(?:増加|獲得|改善)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return ""


def case_current_hint(item: str, title: str, result: str) -> str:
    combined = f"{title} {item} {result}"
    if _contains_any(combined, ["CV率", "転換率", "コンバージョン"]):
        return "サイト訪問後の問い合わせ転換率に課題があった案件"
    if _contains_any(combined, ["不動産", "物件", "賃貸", "売買"]):
        return "問い合わせ導線や物件情報の見せ方に改善余地があった案件"
    if _contains_any(combined, ["問い合わせ", "問合せ"]):
        return "問い合わせ導線やサービス訴求に改善余地があった案件"
    if _contains_any(combined, ["SEO", "検索", "自然検索", "流入"]):
        return "検索流入後の回遊と問い合わせ導線に改善余地があった案件"
    if _contains_any(combined, ["採用", "応募"]):
        return "採用情報の理解促進と応募導線に課題があった案件"
    return "Webサイト上の情報設計と成果導線に改善余地があった案件"


def case_action_hint(item: str) -> str:
    if _contains_any(item, ["CV率", "転換率", "コンバージョン"]):
        return "CTA配置改善、FAQ整備、導線短縮、問い合わせフォーム最適化"
    if _contains_any(item, ["不動産", "物件", "賃貸", "売買"]):
        return "CTA改善、フォーム導線改善、物件情報整理、CMS運用改善"
    if _contains_any(item, ["問い合わせ", "問合せ", "フォーム"]):
        return "CTA改善、フォーム導線改善、サービス訴求整理、CMS運用改善"
    if _contains_any(item, ["採用", "応募"]):
        return "採用コンテンツ整備、応募導線改善、FAQ整備、フォーム最適化"
    if _contains_any(item, ["SEO", "検索", "流入"]):
        return "SEO構造改善、コンテンツ整理、内部導線改善、CTA改善"
    if _contains_any(item, ["CMS", "更新"]):
        return "CMS設計、更新フロー整備、掲載情報整理、運用ルール策定"
    return "情報設計改善、CTA改善、FAQ整備、問い合わせフォーム最適化"


def case_result_hint(item: str) -> str:
    result_phrase = extract_case_result_phrase(item)
    if result_phrase:
        return _trim(result_phrase, 42)
    if _contains_any(item, ["問い合わせ", "CV"]):
        return "問い合わせ数とCV率を改善"
    if _contains_any(item, ["採用", "応募"]):
        return "応募導線の到達率を改善"
    return "成果につながった進め方を本提案へ反映"


def display_case_title(title: str, index: int) -> str:
    if re.match(r"^Case\s*\d+", title):
        return title
    return f"Case {index}：{title}"


def extract_client_name(client_company_info: str, fallback: str) -> str:
    for source in (client_company_info, fallback):
        for line in source.splitlines():
            candidate = re.sub(r"^(企業名|会社名|提案先企業名|提案先企業|提案先|顧客名|クライアント)\s*[:：]\s*", "", line.strip())
            candidate = candidate.strip(" ・-　")
            if candidate and not _looks_generic_client_name(candidate) and not candidate.lower().startswith(("http://", "https://")):
                return _trim(candidate, 36)
    return "提案先企業"


def extract_case_study_items(case_studies: str) -> list[str]:
    if not case_studies.strip():
        return []

    lines = [line.strip() for line in case_studies.splitlines() if line.strip()]
    if len(lines) <= 1:
        lines = [line.strip() for line in re.split(r"[。;；]+", case_studies) if line.strip()]

    cleaned = []
    for line in lines:
        item = re.sub(r"^[・•\-\d\s.．、]+", "", line.strip())
        item = re.sub(r"^(実績|事例|成功事例)\s*[:：]\s*", "", item)
        if item:
            cleaned.append(item)
    return unique_items(cleaned, 3)


def extract_project_points(project_brief: str) -> list[str]:
    text = project_brief.strip()
    points = [
        "問い合わせ導線・CTAの改善" if _contains_any(text, ["問い合わせ", "問合せ", "CV", "コンバージョン"]) else "",
        "採用情報・応募導線の強化" if "採用" in text else "",
        "現行サイトの情報鮮度と構成整理" if _contains_any(text, ["情報が古", "古く", "リニューアル", "刷新"]) else "",
        "サービス内容が伝わる情報設計" if _contains_any(text, ["サービス内容", "伝わりにく", "訴求"]) else "",
        "予算・スコープの優先順位整理" if "予算" in text else "",
        "希望納期に合わせた進行設計" if _contains_any(text, ["納期", "早め", "急ぎ", "公開時期", "公開希望", "リリース希望"]) else "",
    ]
    return unique_items(points, 4)


def extract_solution_points(text: str) -> list[str]:
    points = [
        "問い合わせ導線を起点にCTAとページ遷移を再設計" if _contains_any(text, ["問い合わせ", "問合せ", "CV"]) else "",
        "採用候補者向けの情報整理と応募導線を強化" if "採用" in text else "",
        "情報設計とサービス訴求を再構成" if _contains_any(text, ["情報", "サービス内容", "訴求"]) else "",
        "CMS要件と更新運用フローを整理" if _contains_any(text, ["CMS", "更新"]) else "",
        "SEOを見据えたサイト構造とコンテンツを整理" if _contains_any(text, ["SEO", "検索"]) else "",
        "公開後の運用保守・改善サイクルを設計" if _contains_any(text, ["運用", "保守", "改善"]) else "",
    ]
    return unique_items(points, 4)


def extract_service_points(own_service_info: str) -> list[str]:
    extracted = extract_text_items(own_service_info, 3)
    points = extracted + [
        "CMS構築・更新しやすい管理設計" if _contains_any(own_service_info, ["CMS", "更新"]) else "",
        "SEOを考慮した情報設計" if _contains_any(own_service_info, ["SEO", "検索"]) else "",
        "公開後の改善運用まで支援" if _contains_any(own_service_info, ["運用", "保守", "改善"]) else "",
    ]
    return unique_items(points, 4)


def extract_schedule_points(text: str) -> list[str]:
    points = [
        "初回ヒアリング・要件整理",
        "情報設計・ワイヤーフレーム",
        "デザイン・実装・CMS設定" if _contains_any(text, ["CMS", "更新"]) else "デザイン・実装",
        "公開・運用改善" if _contains_any(text, ["運用", "保守", "改善"]) else "公開前検証・リリース",
    ]
    if _contains_any(text, ["早め", "急ぎ", "短納期"]):
        points[0] = "早期提案に向けた要件整理"
    return unique_items(points, 4)


def extract_team_points(own_service_info: str) -> list[str]:
    points = [
        "進行管理・要件整理",
        "情報設計・UI/ビジュアル設計",
        "フロントエンド実装・CMS構築" if _contains_any(own_service_info, ["CMS", "実装", "構築"]) else "実装・検証",
        "公開後の更新・改善運用支援" if _contains_any(own_service_info, ["運用", "保守", "改善", "更新"]) else "公開後の軽微な更新相談",
    ]
    return unique_items(points, 4)


def extract_cost_points(text: str) -> list[str]:
    has_budget_detail = "予算" in text and not _contains_any(text, ["予算は未定", "予算未定", "予算感未定"])
    points = [
        "予算に合わせて必須範囲を優先" if has_budget_detail else "予算確認後に必須範囲を確定",
        "ページ数・コンテンツ量で調整",
        "CMS・フォーム・SEOは要件に応じて別枠化" if _contains_any(text, ["CMS", "フォーム", "SEO", "検索"]) else "追加機能はオプション化",
        "運用保守・改善支援は月次範囲で検討" if _contains_any(text, ["運用", "保守", "改善"]) else "公開後支援は必要に応じて追加",
    ]
    return unique_items(points, 4)


def derive_estimate_summary(payload: PptxDownloadRequest, text: str) -> EstimateSummary:
    page_count = extract_page_count(payload.estimated_page_count, text)
    page_base = max(8, page_count)
    has_cms = estimate_flag(payload.cms_required, text, ["CMS", "WordPress", "更新"])
    has_form = estimate_flag(payload.contact_form_required, text, ["問い合わせフォーム", "問合せフォーム", "フォーム", "資料請求"])
    has_special = estimate_flag(payload.special_function_required, text, ["物件検索", "検索機能", "会員", "予約", "決済", "特殊機能"])
    has_seo = estimate_flag(payload.seo_required, text, ["SEO", "自然検索", "検索流入"])
    has_content = estimate_flag(payload.content_creation_required, text, ["撮影", "原稿", "ライティング", "取材"])

    lines: list[dict[str, object]] = [
        {"name": "要件整理・ディレクション", "min": 45 if page_count > 15 else 30, "max": 75 if page_count > 15 else 50, "priority": "必須対応", "enabled": True},
        {"name": "情報設計・ワイヤーフレーム", "min": 25 + page_base, "max": 45 + page_base * 2, "priority": "必須対応", "enabled": True},
        {"name": "デザイン制作", "min": 45 + page_base * 4, "max": 75 + page_base * 7, "priority": "必須対応", "enabled": True},
        {"name": "フロントエンド実装", "min": 50 + page_base * 5, "max": 85 + page_base * 8, "priority": "必須対応", "enabled": True},
        {"name": "CMS構築", "min": 50, "max": 90, "priority": "推奨対応", "enabled": has_cms},
        {"name": "フォーム実装", "min": 15, "max": 30, "priority": "必須対応", "enabled": has_form},
        {"name": "特殊機能開発", "min": 80, "max": 180, "priority": "オプション対応", "enabled": has_special},
        {"name": "SEO初期設計", "min": 20, "max": 40, "priority": "推奨対応", "enabled": has_seo},
        {"name": "撮影・原稿作成", "min": 30, "max": 80, "priority": "オプション対応", "enabled": has_content},
        {"name": "テスト・公開作業", "min": 20, "max": 35, "priority": "必須対応", "enabled": True},
        {"name": "運用保守", "min": 10, "max": 20, "priority": "オプション対応", "enabled": True},
    ]
    enabled_lines = [line for line in lines if bool(line["enabled"])]
    total_min = sum(int(line["min"]) for line in enabled_lines)
    total_max = sum(int(line["max"]) for line in enabled_lines)
    budget = extract_budget_amount(f"{payload.budget_range}\n{text}")
    if budget is None:
        budget_fit = "予算未入力"
        budget_label = "未入力"
    elif budget >= total_max:
        budget_fit = "予算内"
        budget_label = f"{budget}万円"
    elif budget >= total_min * 0.85:
        budget_fit = "やや調整必要"
        budget_label = f"{budget}万円"
    else:
        budget_fit = "予算超過の可能性あり"
        budget_label = f"{budget}万円"

    return EstimateSummary(
        page_count=page_count,
        total_min=total_min,
        total_max=total_max,
        total_label=f"{total_min}万〜{total_max}万円",
        budget_label=budget_label,
        budget_fit=budget_fit,
        lines=lines,
        required=[str(line["name"]) for line in enabled_lines if line["priority"] == "必須対応"],
        recommended=[str(line["name"]) for line in enabled_lines if line["priority"] == "推奨対応"],
        optional=[str(line["name"]) for line in enabled_lines if line["priority"] == "オプション対応"],
    )


def extract_page_count(primary: str, text: str) -> int:
    for source in (primary, text):
        normalized = normalize_number_text(source)
        match = re.search(r"(\d+)\s*(?:ページ|頁|p)", normalized, flags=re.IGNORECASE)
        if match:
            return max(1, min(60, int(match.group(1))))
        number = re.search(r"\d+", normalized)
        if source == primary and number:
            return max(1, min(60, int(number.group(0))))
    return 10


def extract_budget_amount(text: str) -> int | None:
    normalized = normalize_number_text(text)
    amounts: list[int] = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(万円|万|円)", normalized):
        amount = float(match.group(1))
        amounts.append(round(amount / 10000) if match.group(2) == "円" else round(amount))
    return max(amounts) if amounts else None


def normalize_number_text(text: str) -> str:
    return text.translate(str.maketrans("０１２３４５６７８９，", "0123456789,")).replace(",", "")


def estimate_flag(value: str, text: str, patterns: list[str]) -> bool:
    if _contains_any(value, ["なし", "不要", "無", "無し", "対象外"]):
        return False
    if _contains_any(value, ["あり", "有", "必要", "希望", "対象", "実施", "要"]):
        return True
    return _contains_any(text, patterns)


def extract_confirmation_items(text: str) -> list[str]:
    has_budget_detail = "予算" in text and not _contains_any(text, ["予算は未定", "予算未定", "予算感未定"])
    items = [
        "予算感・上限・見積粒度" if not has_budget_detail else "予算内で優先する必須範囲",
        "希望公開時期・社内確認フロー" if not _contains_any(text, ["納期", "公開時期", "公開希望", "リリース希望", "早め", "急ぎ"]) else "希望納期に対する素材準備状況",
        "CMS要否・更新担当・更新頻度" if not _contains_any(text, ["CMS", "更新"]) else "CMS権限と更新担当範囲",
        "SEO対象キーワード・既存流入状況" if not _contains_any(text, ["SEO", "検索"]) else "SEO対象範囲と成果指標",
        "公開後の運用保守範囲" if not _contains_any(text, ["運用", "保守", "改善"]) else "運用改善の支援範囲と頻度",
    ]
    return unique_items(items, 5)


def extract_text_items(text: str, max_count: int) -> list[str]:
    if not text.strip():
        return []
    parts = []
    for line in re.split(r"[\n。;；]+", text):
        item = re.sub(r"^[・•\-\d\s.．、]+", "", line.strip())
        if item:
            parts.append(_trim(item, 48))
    return unique_items(parts, max_count)


def ensure_items(items: list[str], fallback: list[str], max_count: int) -> list[str]:
    merged = unique_items(items, max_count)
    fallback_index = 0
    while len(merged) < max_count and fallback and fallback_index < len(fallback) * 2:
        candidate = fallback[fallback_index % len(fallback)]
        if not _is_duplicate_text(candidate, merged):
            merged.append(candidate.strip())
        fallback_index += 1
    return merged[:max_count]


def unique_items(items: list[str], max_count: int | None = None) -> list[str]:
    unique: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or _is_duplicate_text(cleaned, unique):
            continue
        unique.append(cleaned)
        if max_count and len(unique) >= max_count:
            break
    return unique


def build_solution_rows(items: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    used_hints: list[str] = []
    for idx, item in enumerate(unique_items(items, 4)):
        hint = _solution_hint(item, idx)
        if _is_duplicate_text(hint, used_hints):
            hint = _fallback_solution_hint(len(used_hints))
        used_hints.append(hint)
        rows.append([f"課題 {len(rows) + 1}", _trim(item, 32), _trim(hint, 46)])
    return rows


def _solution_hint(item: str, index: int = 0) -> str:
    if "導線" in item or "問い合わせ" in item:
        return "主要CTAとページ遷移を整理し、成果導線を明確化"
    if "情報" in item or "コンテンツ" in item:
        return "情報設計と訴求軸を再構成し、理解しやすい構成へ"
    if "運用" in item or "改善" in item:
        return "公開後の解析・改善サイクルを前提に設計"
    if "採用" in item:
        return "採用候補者向け情報と応募導線を整理"
    if "CMS" in item or "更新" in item:
        return "CMS要件と更新運用フローを設計"
    if "SEO" in item or "検索" in item:
        return "SEOを見据えたサイト構造とコンテンツを整理"
    return _fallback_solution_hint(index)


def _fallback_solution_hint(index: int) -> str:
    hints = [
        "要件整理を通じて優先度を明確化し、制作方針へ反映",
        "訴求軸を整理し、ユーザーに伝わる構成へ再設計",
        "成果につながる接点を整理し、行動導線を強化",
        "公開後の更新・改善を見据えた運用しやすい設計に整備",
    ]
    return hints[index % len(hints)]


def _is_duplicate_text(value: str, existing_items: list[str]) -> bool:
    key = _normalize_text(value)
    return not key or any(key == _normalize_text(item) for item in existing_items)


def _normalize_text(value: str) -> str:
    cleaned = re.sub(r"[\s　・•\-ー、。,.．:：/／「」『』（）()\[\]]+", "", value.lower())
    cleaned = cleaned.replace("課題", "").replace("解決策", "")
    return cleaned


def _looks_generic_client_name(value: str) -> bool:
    normalized = _normalize_text(value)
    generic_words = {"提案先企業", "提案先企業情報", "企業情報", "会社情報", "提案先", "貴社", "お客様", "クライアント", "未入力"}
    return normalized in {_normalize_text(word) for word in generic_words}


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _fit_font_size(text: str, base_size: int) -> int:
    if len(text) > 34:
        return max(base_size - 6, 25)
    if len(text) > 24:
        return max(base_size - 3, 28)
    return base_size


def sanitize_proposal_text(text: str) -> str:
    replacements = {
        "変動する可能性があります": "変動します",
        "できる可能性があります": "できます",
        "進めやすい可能性があります": "進めやすい案件です",
        "可能性があります": "見込みです",
        "可能性がある": "余地があります",
        "確認が必要です": "次回確認事項として扱います",
        "整理する必要があります": "整理します",
        "精度を高める必要があります": "精度を高めます",
        "と考えられます": "と判断します",
        "実績イメージ": "関連実績",
    }
    cleaned = text
    for before, after in replacements.items():
        cleaned = cleaned.replace(before, after)
    return cleaned


def _trim(text: str, max_length: int) -> str:
    cleaned = sanitize_proposal_text(text.strip().replace("\n", " "))
    if len(cleaned) <= max_length:
        return cleaned
    return f"{cleaned[: max_length - 1]}…"


def rank_probability_for(rank: str) -> int:
    if rank == "A":
        return 80
    if rank == "D":
        return 20
    if rank == "C":
        return 40
    return 60


def risk_score_for_probability(probability: int, risk_count: int) -> int:
    if probability <= 25:
        score = 5
    elif probability <= 40:
        score = 4
    elif probability <= 60:
        score = 3
    elif probability <= 75:
        score = 2
    else:
        score = 1
    if risk_count >= 4:
        score = min(5, score + 1)
    return score


def risk_label_for(score: int) -> str:
    normalized = max(1, min(5, score))
    return f"{'★' * normalized}{'☆' * (5 - normalized)}"


def projected_probability_for(probability: int, risk_score: int, action_count: int) -> int:
    if probability <= 25:
        uplift = 25
    elif probability <= 40:
        uplift = 20
    elif probability <= 60:
        uplift = 15
    else:
        uplift = 10
    if risk_score <= 2:
        uplift = min(uplift, 10)
    if action_count < 3:
        uplift = max(8, uplift - 5)
    return min(90, probability + uplift)


def strip_probability_label(label: str) -> str:
    cleaned = re.sub(r"受注確率\s*\d+[%％]\s*[|｜]\s*", "", label)
    return cleaned or label


def rank_color_for(rank: str) -> str:
    if rank == "A":
        return COLORS["green"]
    if rank in {"C", "D"}:
        return COLORS["red"]
    return COLORS["blue"]


def rank_light_color_for(rank: str) -> str:
    if rank == "A":
        return COLORS["green_light"]
    if rank in {"C", "D"}:
        return COLORS["red_light"]
    return COLORS["blue_light"]


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color)
