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
    if any(keyword in joined for keyword in ["表紙", "cover", "タイトル", "title"]):
        return "full-bleed cover with strong title and subtle corporate accent"
    if any(keyword in joined for keyword in ["summary", "overview", "サマリー", "まとめ"]):
        return "executive summary with three concise value cards"
    if any(keyword in joined for keyword in ["課題", "issue", "risk", "problem"]):
        return "priority issue cards with muted accent labels"
    if any(keyword in joined for keyword in ["競合", "比較", "competition", "competitor", "comparison"]):
        return "competitive comparison table with clear winning points"
    if any(keyword in joined for keyword in ["schedule", "スケジュール", "工程", "timeline", "process"]):
        return "simple timeline or gantt style process"
    if any(keyword in joined for keyword in ["費用", "見積", "estimate", "budget", "cost"]):
        return "estimate overview table with highlighted total range"
    if any(keyword in joined for keyword in ["kpi", "効果", "effect", "roi"]):
        return "KPI cards with measurable outcomes"
    if any(keyword in joined for keyword in ["サイトマップ", "構成", "sitemap", "structure"]):
        return "sitemap diagram with hierarchy"
    return "clean two-column business proposal slide"


def _image_prompt(title: str, visual_suggestion: str, client_name: str) -> str:
    visual = _safe_text(visual_suggestion, 200)
    if visual:
        return visual
    return f"Clean corporate web production proposal visual for {client_name or 'client'}, section: {title}"


def _append_confirmation_marker(text: str) -> str:
    marker_words = ["未定", "要確認", "不明", "未確認", "unconfirmed", "needs confirmation", "tbd"]
    if any(keyword in text.lower() for keyword in marker_words):
        return f"{text} (needs confirmation)" if "needs confirmation" not in text.lower() else text
    return text


def _blocks(title: str, bullets: list[str], notes: str = "") -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [{"type": "heading", "content": _safe_text(title, 180)}]
    if bullets:
        blocks.append({"type": "bulleted_list", "items": bullets})
    if notes:
        blocks.append({"type": "paragraph", "content": _safe_text(notes, 500)})
    return blocks


def _build_slide_payload(title: str, bullets: list[str], notes: str = "") -> dict[str, Any]:
    safe_title = _safe_text(title, 180)
    blocks = _blocks(safe_title, bullets, notes)
    return {
        "title": safe_title,
        "content": {"blocks": blocks},
        "sections": [{"title": safe_title, "content": {"blocks": blocks}, "blocks": blocks}],
        "blocks": blocks,
    }


def _deck_outline(title: str, slides: list[dict[str, Any]]) -> str:
    lines = [f"# {_safe_text(title, 180)}"]
    for index, slide in enumerate(slides, start=1):
        lines.append(f"## {index}. {_safe_text(str(slide.get('title', '')), 180)}")
        for block in slide.get("blocks", []):
            if block.get("type") == "bulleted_list":
                for item in block.get("items", []):
                    lines.append(f"- {_safe_text(str(item), 240)}")
            elif block.get("type") == "paragraph" and block.get("content"):
                lines.append(_safe_text(str(block["content"]), 300))
    return "\n".join(lines)


def _build_prompt(
    request: BeautifulAiPresentationRequest,
    *,
    title: str,
    client_name: str,
    slides: list[dict[str, Any]],
    outline: str,
) -> str:
    next_actions = request.win_probability.recommended_next_actions if request.win_probability else []
    lines = [
        "日本語で、法人向けの洗練された営業提案書プレゼンテーションを作成してください。",
        "デザインは上品で信頼感があり、B2B提案に適した余白・見出し・図解を使ってください。",
        "入力されていない数値、実績、契約条件、事実は勝手に作らないでください。不明な点は要確認として扱ってください。",
        "",
        f"提案書タイトル: {title}",
        f"顧客名: {client_name}",
        f"提案コンセプト: {_safe_text(slides[1]['title'] if len(slides) > 1 else title, 240)}",
        f"提案目的: {_safe_text(request.project_brief, 900)}",
        f"想定スケジュール: {_append_confirmation_marker(_safe_text(request.desired_launch_timing or 'TBD', 200))}",
        f"費用概算: {_append_confirmation_marker(_safe_text(request.budget_range or 'TBD', 200))}",
        "",
        "スライドごとのタイトルと本文:",
        outline,
        "",
        "次のアクション:",
    ]
    if next_actions:
        lines.extend(f"- {_safe_text(action, 240)}" for action in next_actions[:5])
    else:
        lines.extend(
            [
                "- 提案内容を社内で確認する",
                "- 金額、納期、AI推測項目を人が確認する",
                "- 顧客へ提出する前に最終レビューを行う",
            ]
        )
    lines.extend(
        [
            "",
            "出力条件:",
            "- 1枚目は表紙",
            "- 課題、提案方針、具体施策、スケジュール、費用概算、次のアクションを含める",
            "- 各スライドは短い見出しと読みやすい箇条書きにする",
            "- 架空の数値や顧客情報を追加しない",
        ]
    )
    return "\n".join(lines)


def _build_context_slide(request: BeautifulAiPresentationRequest) -> dict[str, Any] | None:
    bullets = _safe_lines(
        [
            f"Project summary: {_safe_text(request.project_brief, 220)}",
            f"Budget: {_append_confirmation_marker(_safe_text(request.budget_range or 'TBD', 120))}",
            f"Launch timing: {_append_confirmation_marker(_safe_text(request.desired_launch_timing or 'TBD', 120))}",
            f"CMS: {_append_confirmation_marker(_safe_text(request.cms_required or 'TBD', 120))}",
            f"Competitor: {_append_confirmation_marker(_safe_text(request.competitor_company_name or request.competitor_site_url or 'TBD', 160))}",
        ],
        5,
    )
    if not bullets:
        return None
    return _build_slide_payload("Proposal conditions summary", bullets, "Use these conditions as source context for the proposal deck.")


def map_to_beautiful_ai_payload(request: BeautifulAiPresentationRequest) -> BeautifulAiPayload:
    deck = request.powerpoint_generation_data
    client_name = _safe_text(deck.client_name or request.client_company_info or "Client", 160)
    title = _safe_text(deck.deck_title or f"{client_name} Web proposal", 180)
    slides: list[dict[str, Any]] = []

    context_slide = _build_context_slide(request)
    if context_slide:
        slides.append(context_slide)

    for slide in deck.slides:
        bullets = _safe_lines([_append_confirmation_marker(item) for item in slide.bullets], MAX_BULLETS_PER_SLIDE)
        if not bullets and not _safe_text(slide.title):
            continue
        title_text = _safe_text(slide.title or f"Slide {slide.slide_no}", 160)
        notes = " ".join(
            part
            for part in [
                _safe_text(slide.speaker_notes, 500),
                _layout_hint(title_text, slide.layout),
                _image_prompt(title_text, slide.visual_suggestion, client_name),
            ]
            if part
        )
        slides.append(_build_slide_payload(title_text, bullets, notes))
        if len(slides) >= MAX_SLIDES:
            break

    if not slides:
        slides.append(_build_slide_payload(title, ["Please review the generated proposal content in the existing PPTX output."], "Minimal Beautiful.ai fallback slide."))

    outline = _deck_outline(title, slides)
    top_level_sections = [
        {
            "title": "Proposal Outline",
            "slides": slides,
            "content": {"blocks": [{"type": "paragraph", "content": outline}]},
        }
    ]

    return BeautifulAiPayload(
        title=title,
        prompt=_build_prompt(request, title=title, client_name=client_name, slides=slides, outline=outline),
        content=outline,
        language=request.language or "ja",
        preserveExactText=request.preserve_exact_text,
        themeId=request.theme_id or settings.beautiful_ai_default_theme_id or "minimal",
        workspaceId=request.workspace_id or settings.beautiful_ai_workspace_id,
        folderId=request.folder_id or settings.beautiful_ai_folder_id,
        imageSource=request.image_source or settings.beautiful_ai_image_source,
        imageStyle=request.image_style or settings.beautiful_ai_image_style,
        sections=top_level_sections,
        slides=slides,
    )


def build_request_summary(request: BeautifulAiPresentationRequest, slide_count: int) -> str:
    deck = request.powerpoint_generation_data
    parts = [
        f"title={_safe_text(deck.deck_title, 80)}",
        f"client={_safe_text(deck.client_name, 80)}",
        f"project_id={_safe_text(request.project_id, 80)}",
        f"slides={slide_count}",
        f"theme={_safe_text(request.theme_id or settings.beautiful_ai_default_theme_id or 'minimal', 80)}",
    ]
    return ";".join(part for part in parts if part.split("=", 1)[1])
