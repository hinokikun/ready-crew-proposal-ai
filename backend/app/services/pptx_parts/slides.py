from __future__ import annotations

from datetime import date

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN

from app.models import PowerPointData, PowerPointSlide, WinProbability
from app.services.pptx_parts.models import PptxContext
from app.services.pptx_parts.content import (
    _contains_any,
    _trim,
    build_case_triplets_from_items,
    build_solution_rows,
    concept_statement,
    derive_kpi_rows,
    display_case_title,
    ensure_items,
    has_competitor_context,
    journey_action,
    kpi_metric_for,
    merge_understanding_items,
    projected_probability_for,
    rank_color_for,
    rank_light_color_for,
    rank_probability_for,
    risk_label_for,
    risk_score_for_probability,
    sitemap_note,
    unique_items,
)
from app.services.pptx_parts.drawing import (
    add_bullet_list,
    add_card,
    add_case_line,
    add_factor_column,
    add_footer,
    add_header,
    add_icon_badge,
    add_insight_band,
    add_section_label,
    add_shape,
    add_side_panel,
    add_step_flow,
    add_table,
    add_text,
    add_title,
    add_visual_frame,
    blank_slide,
    chapter_icon,
    chapter_message,
    content_title,
    set_background,
)
from app.services.pptx_design.components import (
    add_architecture_diagram,
    add_estimate_overview,
    add_metric_card,
    add_next_action_cards,
    add_timeline,
)
from app.services.pptx_design.icons import icon_labels_for_category
from app.services.pptx_design.diagrams import architecture_nodes_for_category
from app.services.pptx_theme import COLORS, MARGIN_X, SECTION_COLORS, SLIDE_HEIGHT, SLIDE_WIDTH


def _split_metric_text(value: str) -> tuple[str, str]:
    if ":" in value:
        label, body = value.split(":", 1)
        return label.strip(), body.strip()
    if "：" in value:
        label, body = value.split("：", 1)
        return label.strip(), body.strip()
    return value, "要確認"


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
    if "Web戦略" in title or "WEB戦略" in title or "導入戦略" in title:
        return "web_strategy"
    if "サイトマップ" in title or "サイト構成" in title or "導入構成" in title:
        return "sitemap"
    if "コンテンツ" in title or "施策設計" in title:
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

    add_shape(slide, MSO_SHAPE.RECTANGLE, 0.02, 0.02, SLIDE_WIDTH - 0.04, SLIDE_HEIGHT - 0.04, fill=COLORS["navy"], line=COLORS["navy"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 0.02, 0.02, 0.14, SLIDE_HEIGHT - 0.04, fill=COLORS["teal"], line=COLORS["teal"])
    add_shape(slide, MSO_SHAPE.RIGHT_TRIANGLE, 8.55, 0.02, 4.72, 7.46, fill=COLORS["navy_2"], line=COLORS["navy_2"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 9.15, 0.02, 4.12, SLIDE_HEIGHT - 0.04, fill=COLORS["canvas"], line=COLORS["canvas"])
    add_shape(slide, MSO_SHAPE.OVAL, 9.65, 0.92, 3.05, 3.05, fill=COLORS["teal_light"], line=COLORS["teal_light"])
    add_shape(slide, MSO_SHAPE.OVAL, 10.82, 3.55, 1.72, 1.72, fill=COLORS["blue_light"], line=COLORS["blue_light"])
    cover_badges = icon_labels_for_category(context.proposal_category)
    add_icon_badge(slide, cover_badges[0], 9.82, 1.68, COLORS["teal"])
    add_icon_badge(slide, cover_badges[1], 11.05, 2.78, COLORS["blue"])
    add_icon_badge(slide, cover_badges[2], 9.9, 4.75, COLORS["orange"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 9.75, 5.92, 2.7, 0.13, fill=COLORS["teal"], line=COLORS["teal"])
    add_shape(slide, MSO_SHAPE.RECTANGLE, 9.75, 6.2, 1.9, 0.13, fill=COLORS["orange"], line=COLORS["orange"])

    section_label = "WEB PROPOSAL" if context.proposal_category == "web" else f"{context.proposal_label.upper()} PROPOSAL"
    add_section_label(slide, section_label[:24], 0.88, 0.8, fill=COLORS["teal"], color=COLORS["white"])
    add_title(slide, slide_data.title or data.deck_title, 0.88, 1.55, 7.35, 1.24, size=42, color=COLORS["white"])
    add_text(slide, f"{context.client_name} 御中", 0.92, 3.02, 6.9, 0.36, size=18, color=COLORS["teal_light"], bold=True)
    add_text(
        slide,
        "成果につながるWebサイト制作・改善のご提案" if context.proposal_category == "web" else f"{context.concept}のご提案",
        0.92,
        3.68,
        7.25,
        0.5,
        size=20,
        color=COLORS["white"],
        bold=True,
    )
    add_text(slide, f"提案日 {date.today().strftime('%Y.%m.%d')}", 0.92, 5.95, 3.5, 0.26, size=12, color=COLORS["teal_light"])
    add_text(slide, "ProposalPilot / AI営業秘書", 0.92, 6.58, 4.0, 0.24, size=11, color=COLORS["teal_light"])
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
        ["現状課題を実行方針へ落とし込む", "導入範囲と施策を再構成", "KPIを定義して導入後改善につなげる"],
        3,
    )
    titles = ["解決する課題", "主要施策", "期待成果"]
    for idx, item in enumerate(summary_items[:3]):
        add_card(slide, titles[idx], item, 0.95 + idx * 4.02, 3.36, 3.35, 1.68, SECTION_COLORS[idx], COLORS["white"], number=str(idx + 1))
    conclusion = "顧客理解、競合比較、KPI設計を起点に、公開後も成果を追えるWebサイトへ改善します。"
    if context.proposal_category != "web":
        conclusion = "顧客理解、比較軸、KPI設計を起点に、導入後も成果を追える実行計画へ整理します。"
    add_insight_band(slide, "提案の結論", conclusion, 0.92, 5.82, 11.4, 0.54)
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
        f"{context.winning_strategy}を軸に、競合が強い領域を踏まえて重点改善領域を明確化します。",
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
    target_note = "ターゲットの不安をFAQ・実績・サービス詳細で解消し、問い合わせ前の比較検討を支援します。"
    if context.proposal_category != "web":
        target_note = "利用者、意思決定者、運用担当の不安を整理し、導入判断と定着を支援します。"
    add_insight_band(slide, "設計方針", target_note, 0.92, 5.92, 11.4, 0.5)
    add_footer(slide, slide_data.slide_no)


def add_web_strategy_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or ("Web戦略" if context.proposal_category == "web" else "導入戦略"), "STRATEGY", accent=COLORS["blue"])
    items = ensure_items(context.web_strategy_items + slide_data.bullets, ["現状整理", "導入設計", "小規模検証", "運用改善"], 4)
    labels = ["集客", "比較検討", "問い合わせ", "運用改善"] if context.proposal_category == "web" else ["現状", "設計", "検証", "運用"]
    badges = ["SEO", "INFO", "CV", "PDCA"] if context.proposal_category == "web" else ["ASIS", "PLAN", "TEST", "OPS"]
    for idx, item in enumerate(items[:4]):
        x = 0.86 + idx * 3.05
        accent = SECTION_COLORS[idx]
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.82, 2.58, 3.0, fill=COLORS["white"], line=COLORS["line"])
        add_icon_badge(slide, badges[idx], x + 0.75, 2.12, accent, size=0.72)
        add_text(slide, labels[idx], x + 0.26, 3.14, 2.04, 0.28, size=16, color=accent, bold=True, align=PP_ALIGN.CENTER)
        add_text(slide, _trim(item, 40), x + 0.28, 3.72, 2.02, 0.54, size=13, color=COLORS["text"], bold=True, align=PP_ALIGN.CENTER)
        if idx < 3:
            add_shape(slide, MSO_SHAPE.CHEVRON, x + 2.5, 3.0, 0.36, 0.5, fill=COLORS["line_dark"], line=COLORS["line_dark"])
    strategy_note = f"{context.concept}を軸に、入口設計からCV改善、公開後運用まで一貫して設計します。"
    if context.proposal_category != "web":
        strategy_note = f"{context.concept}を軸に、現状整理、導入設計、検証、運用改善まで一貫して設計します。"
    add_insight_band(slide, "戦略の要点", strategy_note, 0.92, 5.62, 11.4, 0.58)
    add_footer(slide, slide_data.slide_no)


def add_content_design_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "コンテンツ設計", "CONTENT", accent=COLORS["green"])
    fallback_content = ["サービス詳細", "実績・事例", "FAQ", "お問い合わせ"] if context.proposal_category == "web" else ["課題整理", "導入範囲", "効果測定", "運用設計"]
    items = ensure_items(context.content_items + slide_data.bullets, fallback_content, 4)
    for idx, item in enumerate(items[:4]):
        x = 0.92 + (idx % 2) * 5.88
        y = 1.68 + (idx // 2) * 2.0
        add_card(slide, content_title(item, idx), item, x, y, 5.24, 1.45, SECTION_COLORS[idx], COLORS["white"], number=str(idx + 1))
    content_note = "認知、比較検討、問い合わせ前の不安解消まで、各コンテンツに明確な役割を持たせます。"
    if context.proposal_category != "web":
        content_note = "各施策に役割を持たせ、導入判断、実行、効果測定、運用定着を支援します。"
    add_insight_band(slide, "施策の役割", content_note, 0.92, 5.88, 11.4, 0.54)
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

    journey_note = "認知から問い合わせまでの離脱点を減らし、情報設計・CTA・実績訴求を一連の導線として改善します。"
    if context.proposal_category != "web":
        journey_note = "導入前後の流れを整理し、例外処理、連携、運用改善まで一連の業務として設計します。"
    add_insight_band(slide, "提案との関係", journey_note, 0.92, 5.58, 11.4, 0.58)
    add_footer(slide, slide_data.slide_no)


def add_sitemap_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or ("推奨サイト構成" if context.proposal_category == "web" else "導入構成"), "サイトマップ" if context.proposal_category == "web" else "構成案", accent=COLORS["green"])
    fallback_structure = ["TOP", "会社案内", "サービス", "実績", "お知らせ", "FAQ", "お問い合わせ"] if context.proposal_category == "web" else ["対象業務", "課題", "導入範囲", "連携先", "運用体制", "効果測定"]
    items = ensure_items(context.sitemap_items, fallback_structure, 8)
    if context.proposal_category != "web":
        add_architecture_diagram(slide, architecture_nodes_for_category(context.proposal_category), 0.9, 2.04, 11.35, 1.86)
        add_insight_band(
            slide,
            "構成の考え方",
            "入力、AI判定、人による確認、既存業務への連携、運用改善までを一連の流れとして設計します。",
            0.92,
            5.55,
            11.4,
            0.62,
        )
        add_footer(slide, slide_data.slide_no)
        return
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
    structure_note = "サービス・実績・FAQで比較検討を支え、CMS更新領域から最新情報を継続発信します。"
    if context.proposal_category != "web":
        structure_note = "対象業務、連携先、運用体制、効果測定を分け、導入後の迷いを減らします。"
    add_insight_band(slide, "構成意図", structure_note, 0.92, 5.92, 11.4, 0.5)
    add_footer(slide, slide_data.slide_no)


def add_kpi_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title or "KPI設計", "成果設計", accent=COLORS["orange"])
    if context.proposal_category == "web":
        metrics = [
            ("問い合わせ数", f"月{int(context.kpi_targets['inquiries'])}件", context.kpi_targets["inquiries"] / 30, COLORS["teal"]),
            ("CV率", f"{context.kpi_targets['cv_rate']}%", context.kpi_targets["cv_rate"] / 5, COLORS["blue"]),
            ("自然検索流入", f"月{int(context.kpi_targets['organic'])}セッション", context.kpi_targets["organic"] / 6000, COLORS["green"]),
            ("資料DL数", f"月{int(context.kpi_targets['downloads'])}件", context.kpi_targets["downloads"] / 40, COLORS["orange"]),
        ]
    else:
        metric_lines = ensure_items(
            [f"{label}: {value}" for label, value in context.kpi_rows],
            ["業務時間削減: 要確認", "処理品質向上: 要確認", "運用定着率: 要確認", "改善サイクル: 要確認"],
            4,
        )
        metrics = [
            (label, value, min(1.0, 0.48 + idx * 0.12), SECTION_COLORS[idx])
            for idx, metric in enumerate(metric_lines)
            for label, value in [_split_metric_text(metric)]
        ]
    for idx, (label, value, ratio, accent) in enumerate(metrics):
        x = 0.9 + idx * 3.02
        add_metric_card(slide, label, value, x, 1.62, 2.55, 1.28, accent)
        y = 3.28 + idx * 0.34
        add_shape(slide, MSO_SHAPE.RECTANGLE, 1.08, y + 0.08, 10.9, 0.08, fill=COLORS["line"], line=COLORS["line"])
        add_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 1.08, y, max(0.7, min(10.9, 10.9 * ratio)), 0.24, fill=accent, line=accent)

    add_table(
        slide,
        headers=["設計観点", "見る指標", "改善アクション"],
        rows=[
            ["入口", kpi_metric_for(context.concept, "集客"), "対象範囲と入力条件を整理"],
            ["行動", kpi_metric_for(context.concept, "行動"), "施策と運用フローを強化"],
            ["成果", kpi_metric_for(context.concept, "成果"), "KPIと改善サイクルを設計"],
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
    points = ensure_items(slide_data.bullets, ["事業内容とターゲットを整理", "提案に期待される役割を仮説化", "確認すべき前提条件を明確化"], 3)

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
    add_insight_band(slide, "提案の前提", slide_data.visual_suggestion or "事業・ターゲット・提案範囲を整理した図", 0.9, 5.25, 11.5, 0.72)
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
    items = ensure_items(context.solution_points + slide_data.bullets, ["要件整理の再整理", "導入範囲と施策方針の策定", "効果測定につながる運用設計"], 4)
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
    add_header(slide, slide_data.title, "制作方針" if context.proposal_category == "web" else "実行方針")
    steps = ensure_items(context.service_points + slide_data.bullets, ["初期設計を重視した実行プロセス", "確認しやすい要件整理", "導入後の改善を見据えた設計"], 4)
    add_step_flow(slide, steps[:4], 0.82, 2.12, 11.7, 1.85)
    add_insight_band(slide, "品質担保の考え方", "要件整理・設計・制作・検証を段階的に進め、認識齟齬を抑えます。", 0.92, 5.18, 11.4, 0.8)
    add_footer(slide, slide_data.slide_no)


def add_schedule_slide(prs: Presentation, slide_data: PowerPointSlide, context: PptxContext) -> None:
    slide = blank_slide(prs)
    set_background(slide)
    add_header(slide, slide_data.title, "スケジュール")
    phases = ensure_items(context.schedule_points + slide_data.bullets, ["要件整理", "設計・計画", "実装・検証", "運用開始・改善"], 4)
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
    roles = ["PM/ディレクター", "設計担当", "実装担当", "運用・改善支援"] if context.proposal_category != "web" else ["PM/ディレクター", "デザイナー", "エンジニア", "運用・改善支援"]
    details = ensure_items(context.team_points + slide_data.bullets, ["進行管理", "要件・構成設計", "実装・検証", "導入後の改善相談"], 4)

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
        ["必須範囲とオプションを分離", "規模と機能要件に応じて調整", "詳細見積はヒアリング後に提示"],
        4,
    )
    scope_label = context.estimate.scope_label
    required_detail = "要件整理・設計・制作・検証" if context.proposal_category == "web" else "要件整理・設計・実装・検証"
    adjustable_detail = "CMS・SEO・特殊機能・撮影原稿" if context.proposal_category == "web" else "連携・学習・運用支援・追加検証"
    rows = [
        ["合計概算", context.estimate.total_label, scope_label],
        ["予算適合", context.estimate.budget_fit, f"予算感: {context.estimate.budget_label}"],
        ["必須対応", _trim("、".join(context.estimate.required[:4]), 36), required_detail],
        ["調整範囲", _trim(items[3] if len(items) > 3 else "推奨・オプションを段階化", 36), adjustable_detail],
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
    estimate_scope = context.estimate.scope_label
    add_text(slide, f"合計概算 {context.estimate.total_label}", 3.35, 0.98, 3.15, 0.28, size=16, color=COLORS["teal"], bold=True, align=PP_ALIGN.RIGHT)
    add_text(slide, f"{estimate_scope} / 予算感: {context.estimate.budget_label}", 6.72, 0.98, 5.5, 0.28, size=12, color=COLORS["muted"], bold=True, align=PP_ALIGN.RIGHT)
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
        ("次回確認", "規模、導入範囲、連携条件、運用体制を確定" if context.proposal_category != "web" else "ページ数、CMS範囲、特殊機能、素材準備を確定"),
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
    values = ensure_items(unique_items(slide_data.bullets, 2) + [confirmation], ["課題仮説に基づく実行方針", "成果につながる導入設計", "次回確認事項の整理"], 3)

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
        "2. 提案範囲・必要データの確定" if context.proposal_category != "web" else "2. サイト構成・必要コンテンツの確定",
        "3. 見積・スケジュール・体制の最終化",
        "4. キックオフ・データ準備・実行開始" if context.proposal_category != "web" else "4. キックオフ・素材準備・制作開始",
    ]
    add_next_action_cards(slide, steps, 0.82, 1.9, 11.7)
    confirmations = ensure_items(context.confirmation_items + slide_data.bullets, ["予算内で優先する必須範囲", "希望納期に対する準備状況", "運用担当と確認フロー"], 4)
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
