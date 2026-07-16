from __future__ import annotations

from datetime import date
from html import escape
from io import BytesIO
import logging
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import PptxDownloadRequest
from app.services.pptx_service import (
    derive_concept,
    derive_estimate_summary,
    extract_client_name,
    extract_confirmation_items,
    sanitize_filename,
)


logger = logging.getLogger(__name__)

PDF_MEDIA_TYPE = "application/pdf"
FONT_GOTHIC = "ReadyCrewYuGothic"
FONT_MINCHO = "ReadyCrewYuGothic"
CID_GOTHIC = "HeiseiKakuGo-W5"
CID_MINCHO = "HeiseiMin-W3"
NAVY = colors.HexColor("#10233F")
TEAL = colors.HexColor("#0F766E")
BLUE = colors.HexColor("#1D4ED8")
ORANGE = colors.HexColor("#D97706")
RED = colors.HexColor("#B42318")
TEXT = colors.HexColor("#1B2430")
MUTED = colors.HexColor("#667085")
LINE = colors.HexColor("#D8DEE8")
CANVAS = colors.HexColor("#F7F9FC")
LIGHT_TEAL = colors.HexColor("#E6F5F2")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
LIGHT_ORANGE = colors.HexColor("#FFF7E6")


def build_estimate_pdf_bytes(payload: PptxDownloadRequest) -> bytes:
    try:
        register_japanese_fonts()
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=16 * mm,
            title="概算見積書",
        )
        story = build_estimate_pdf_story(payload, doc.width)
        doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
        return buffer.getvalue()
    except Exception:
        logger.exception("Failed to build estimate PDF.")
        raise


def build_estimate_pdf_filename(payload: PptxDownloadRequest) -> str:
    client_name = extract_client_name(payload.client_company_info, payload.powerpoint_generation_data.client_name)
    return f"{sanitize_filename(client_name)}_概算見積書.pdf"


def register_japanese_fonts() -> None:
    global FONT_GOTHIC, FONT_MINCHO
    if FONT_GOTHIC in pdfmetrics.getRegisteredFontNames():
        return

    for font_path in [
        Path(r"C:\Windows\Fonts\YuGothM.ttc"),
        Path(r"C:\Windows\Fonts\YuGothR.ttc"),
        Path(r"C:\Windows\Fonts\meiryo.ttc"),
    ]:
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(FONT_GOTHIC, str(font_path), subfontIndex=0))
            FONT_MINCHO = FONT_GOTHIC
            return
        except Exception:
            logger.debug("Failed to register TrueType font for PDF: %s", font_path, exc_info=True)

    FONT_GOTHIC = CID_GOTHIC
    FONT_MINCHO = CID_MINCHO
    if FONT_GOTHIC not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_GOTHIC))
    if FONT_MINCHO not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_MINCHO))


def build_estimate_pdf_story(payload: PptxDownloadRequest, page_width: float) -> list[object]:
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
    client_name = extract_client_name(payload.client_company_info, data.client_name)
    concept = derive_concept(all_input)
    estimate = derive_estimate_summary(payload, all_input)
    confirmations = extract_confirmation_items(all_input)
    project_name = data.deck_title or f"{client_name} 業務改善ご提案"

    styles = build_styles()
    story: list[object] = [
        title_block(client_name, project_name, concept, styles),
        Spacer(1, 8),
        total_block(estimate.total_label, estimate.budget_fit, estimate.budget_label, page_width, styles),
        Spacer(1, 12),
        section_heading("見積内訳", styles),
        estimate_table(estimate.lines, page_width, styles),
        Spacer(1, 12),
        section_heading("提案範囲の優先順位", styles),
        priority_cards(estimate.required, estimate.recommended, estimate.optional, page_width, styles),
        Spacer(1, 12),
        section_heading("前提条件", styles),
        bullet_box(
            [
                f"案件名: {project_name}",
                f"提案コンセプト: {concept}",
                estimate.scope_label,
                f"予算感: {estimate.budget_label}",
                *(estimate.premise_items[:5] or [f"公開希望時期: {payload.desired_launch_timing or '次回確認'}"]),
                "金額は税別の概算レンジです。",
            ],
            page_width,
            styles,
        ),
        Spacer(1, 10),
        section_heading("次回確認事項", styles),
        bullet_box(confirmations[:5] or ["制作範囲、機能要件、素材準備、公開希望時期を確認"], page_width, styles),
        Spacer(1, 10),
        section_heading("注意書き", styles),
        bullet_box(
            [
                "本見積は概算です。",
                "正式見積は要件確定後に提示します。",
                "金額は税別です。税込金額は消費税率に応じて別途算出します。",
                *estimate.notes,
            ],
            page_width,
            styles,
        ),
    ]
    return story


def build_styles() -> dict[str, ParagraphStyle]:
    base = ParagraphStyle(
        "BaseJa",
        fontName=FONT_GOTHIC,
        fontSize=9,
        leading=13,
        textColor=TEXT,
        wordWrap="CJK",
    )
    return {
        "base": base,
        "title": ParagraphStyle(
            "TitleJa",
            parent=base,
            fontSize=24,
            leading=30,
            textColor=colors.white,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleJa",
            parent=base,
            fontSize=10,
            leading=15,
            textColor=colors.HexColor("#D7F3EF"),
        ),
        "heading": ParagraphStyle(
            "HeadingJa",
            parent=base,
            fontSize=13,
            leading=17,
            textColor=NAVY,
        ),
        "small": ParagraphStyle(
            "SmallJa",
            parent=base,
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "center": ParagraphStyle(
            "CenterJa",
            parent=base,
            alignment=TA_CENTER,
        ),
        "right": ParagraphStyle(
            "RightJa",
            parent=base,
            alignment=TA_RIGHT,
        ),
        "total": ParagraphStyle(
            "TotalJa",
            parent=base,
            fontSize=20,
            leading=25,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "card_title": ParagraphStyle(
            "CardTitleJa",
            parent=base,
            fontSize=10,
            leading=13,
            textColor=NAVY,
        ),
        "table_header": ParagraphStyle(
            "TableHeaderJa",
            parent=base,
            fontSize=9,
            leading=12,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
    }


def title_block(client_name: str, project_name: str, concept: str, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        [p("概算見積書", styles["title"])],
        [p(f"{client_name} 御中", styles["subtitle"])],
        [p(f"作成日: {date.today().strftime('%Y/%m/%d')}", styles["subtitle"])],
        [p(f"案件名: {project_name}", styles["subtitle"])],
        [p(f"提案コンセプト: {concept}", styles["subtitle"])],
    ]
    table = Table(rows, colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("BOX", (0, 0), (-1, -1), 0, NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, 0), 16),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
            ]
        )
    )
    return table


def total_block(total_label: str, budget_fit: str, budget_label: str, page_width: float, styles: dict[str, ParagraphStyle]) -> Table:
    fit_color = TEAL if budget_fit == "予算内" else RED if "超過" in budget_fit else ORANGE
    rows = [
        [p("概算見積合計レンジ", styles["center"]), p("予算適合判定", styles["center"]), p("予算感", styles["center"])],
        [p(total_label, styles["total"]), p(budget_fit, styles["total"]), p(budget_label, styles["total"])],
    ]
    table = Table(rows, colWidths=[page_width * 0.42, page_width * 0.32, page_width * 0.26])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CANVAS),
                ("BACKGROUND", (0, 1), (0, 1), LIGHT_TEAL),
                ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#FFF1F0") if "超過" in budget_fit else LIGHT_TEAL if budget_fit == "予算内" else LIGHT_ORANGE),
                ("BACKGROUND", (2, 1), (2, 1), LIGHT_BLUE),
                ("TEXTCOLOR", (1, 1), (1, 1), fit_color),
                ("BOX", (0, 0), (-1, -1), 0.8, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def section_heading(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    table = Table([[p(text, styles["heading"])]], colWidths=[174 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("LINEBELOW", (0, 0), (-1, -1), 1.2, NAVY),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def estimate_table(lines: list[dict[str, object]], page_width: float, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [[p("項目", styles["table_header"]), p("区分", styles["table_header"]), p("概算レンジ", styles["table_header"]), p("備考", styles["table_header"])]]
    for line in lines:
        enabled = bool(line.get("enabled"))
        amount = f"{line['min']}万〜{line['max']}万円" if enabled else "対象外"
        note = "見積範囲に含む" if enabled else "要件確定後に追加検討"
        rows.append(
            [
                p(str(line["name"]), styles["base"]),
                p(str(line["priority"]), styles["base"]),
                p(amount, styles["right"]),
                p(note, styles["small"]),
            ]
        )
    table = Table(rows, colWidths=[page_width * 0.38, page_width * 0.18, page_width * 0.22, page_width * 0.22], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def priority_cards(required: list[str], recommended: list[str], optional: list[str], page_width: float, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [
        [
            priority_card("必須対応", required, LIGHT_TEAL, styles),
            priority_card("推奨対応", recommended, LIGHT_BLUE, styles),
            priority_card("オプション対応", optional, LIGHT_ORANGE, styles),
        ]
    ]
    table = Table(rows, colWidths=[page_width / 3 - 4, page_width / 3 - 4, page_width / 3 - 4])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def priority_card(title: str, items: list[str], background, styles: dict[str, ParagraphStyle]) -> Table:
    body = "<br/>".join(f"・{escape(item)}" for item in (items[:5] or ["次回確認"]))
    table = Table([[p(title, styles["card_title"])], [Paragraph(body, styles["small"])]])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), background),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return table


def bullet_box(items: list[str], page_width: float, styles: dict[str, ParagraphStyle]) -> Table:
    body = "<br/>".join(f"・{escape(item)}" for item in items)
    table = Table([[Paragraph(body, styles["base"])]], colWidths=[page_width])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CANVAS),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def draw_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(FONT_GOTHIC, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10 * mm, "ProposalPilot / AI営業秘書")
    canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"{doc.page}")
    canvas.restoreState()
