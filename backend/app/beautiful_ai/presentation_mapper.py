from __future__ import annotations

import re
from typing import Any

from app.beautiful_ai.schemas import BeautifulAiPayload, BeautifulAiPresentationRequest
from app.config import settings


MAX_SLIDES = 12
MAX_BULLETS_PER_SLIDE = 5


def _safe_text(value: str | None, limit: int = 800) -> str:
    text = re.sub(r"\s+", " ", (value or "").strip())
    return text[:limit]


def _safe_lines(values: list[str], limit: int = MAX_BULLETS_PER_SLIDE) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    for value in values:
        line = _safe_text(value, 240)
        if not line:
            continue
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def _layout_hint(title: str, original_layout: str) -> str:
    joined = f"{title} {original_layout}".lower()
    if any(keyword in joined for keyword in ["表紙", "cover", "タイトル"]):
        return "full-bleed cover with strong title and subtle corporate accent"
    if any(keyword in joined for keyword in ["summary", "サマリー", "まとめ"]):
        return "executive summary with three concise value cards"
    if any(keyword in joined for keyword in ["課題", "issue", "risk"]):
        return "priority issue cards with muted accent labels"
    if any(keyword in joined for keyword in ["競合", "比較"]):
        return "competitive comparison table with clear winning points"
    if any(keyword in joined for keyword in ["schedule", "スケジュール", "工程"]):
        return "simple timeline or gantt style process"
    if any(keyword in joined for keyword in ["費用", "見積", "budget"]):
        return "estimate overview table with highlighted total range"
    if any(keyword in joined for keyword in ["kpi", "効果", "roi"]):
        return "KPI cards with measurable outcomes"
    if any(keyword in joined for keyword in ["サイトマップ", "構成"]):
        return "sitemap diagram with hierarchy"
    return "clean two-column business proposal slide"


def _image_prompt(title: str, visual_suggestion: str, client_name: str) -> str:
    visual = _safe_text(visual_suggestion, 200)
    if visual:
        return visual
    return f"Clean corporate web production proposal visual for {client_name or 'client'}, section: {title}"


def _append_confirmation_marker(text: str) -> str:
    if any(keyword in text for keyword in ["未定", "要確認", "不明", "未確認"]):
        return f"{text}（要確認）" if "要確認" not in text else text
    return text


def _build_context_slide(request: BeautifulAiPresentationRequest) -> dict[str, Any] | None:
    bullets = _safe_lines(
        [
            f"案件概要: {_safe_text(request.project_brief, 220)}",
            f"予算: {_append_confirmation_marker(_safe_text(request.budget_range or '未定', 120))}",
            f"納期: {_append_confirmation_marker(_safe_text(request.desired_launch_timing or '要確認', 120))}",
            f"CMS: {_append_confirmation_marker(_safe_text(request.cms_required or '要確認', 120))}",
            f"競合: {_append_confirmation_marker(_safe_text(request.competitor_company_name or request.competitor_site_url or '未確認', 160))}",
        ],
        5,
    )
    if not bullets:
        return None
    return {
        "title": "提案条件サマリー",
        "body": "\n".join(bullets),
        "content": bullets,
        "presenterNotes": "入力情報をもとにした提案条件です。AI推測または未確定の項目は要確認として扱います。",
        "layoutHint": "compact project condition cards",
        "imagePrompt": "Minimal business dashboard cards for proposal conditions",
        "sourceLabel": "AI営業秘書 / 入力情報",
    }


def map_to_beautiful_ai_payload(request: BeautifulAiPresentationRequest) -> BeautifulAiPayload:
    deck = request.powerpoint_generation_data
    client_name = _safe_text(deck.client_name or request.client_company_info or "提案先企業", 160)
    title = _safe_text(deck.deck_title or f"{client_name} Webサイト制作ご提案書", 180)
    slides: list[dict[str, Any]] = []

    context_slide = _build_context_slide(request)
    if context_slide:
        slides.append(context_slide)

    for slide in deck.slides:
        bullets = _safe_lines([_append_confirmation_marker(item) for item in slide.bullets], MAX_BULLETS_PER_SLIDE)
        if not bullets and not _safe_text(slide.title):
            continue
        title_text = _safe_text(slide.title or f"Slide {slide.slide_no}", 160)
        slides.append(
            {
                "title": title_text,
                "body": "\n".join(bullets),
                "content": bullets,
                "presenterNotes": _safe_text(slide.speaker_notes, 800),
                "layoutHint": _layout_hint(title_text, slide.layout),
                "imagePrompt": _image_prompt(title_text, slide.visual_suggestion, client_name),
                "sourceLabel": f"AI営業秘書 / Slide {slide.slide_no}",
            }
        )
        if len(slides) >= MAX_SLIDES:
            break

    if not slides:
        slides.append(
            {
                "title": title,
                "body": "提案内容は既存PPTXで確認できます。",
                "content": ["提案内容は既存PPTXで確認できます。"],
                "presenterNotes": "Beautiful.ai連携用の最低限スライドです。",
                "layoutHint": "simple title and body",
                "imagePrompt": "Clean corporate proposal title slide",
                "sourceLabel": "AI営業秘書",
            }
        )

    return BeautifulAiPayload(
        title=title,
        language=request.language or "ja",
        preserveExactText=request.preserve_exact_text,
        themeId=request.theme_id or settings.beautiful_ai_default_theme_id,
        workspaceId=request.workspace_id or settings.beautiful_ai_workspace_id,
        folderId=request.folder_id or settings.beautiful_ai_folder_id,
        imageSource=request.image_source or settings.beautiful_ai_image_source,
        imageStyle=request.image_style or settings.beautiful_ai_image_style,
        slides=slides,
    )


def build_request_summary(request: BeautifulAiPresentationRequest, slide_count: int) -> str:
    deck = request.powerpoint_generation_data
    parts = [
        f"title={_safe_text(deck.deck_title, 80)}",
        f"client={_safe_text(deck.client_name, 80)}",
        f"project_id={_safe_text(request.project_id, 80)}",
        f"slides={slide_count}",
        f"theme={_safe_text(request.theme_id or settings.beautiful_ai_default_theme_id, 80)}",
    ]
    return ";".join(part for part in parts if part.split("=", 1)[1])
