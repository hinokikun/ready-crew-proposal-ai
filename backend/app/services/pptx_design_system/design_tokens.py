from __future__ import annotations

from dataclasses import dataclass

from .colors import palette_for_template
from .spacing import CONTENT_BOTTOM, CONTENT_TOP, SAFE_MARGIN_BOTTOM, SAFE_MARGIN_TOP, SAFE_MARGIN_X, SLIDE_HEIGHT_IN, SLIDE_WIDTH_IN


@dataclass(frozen=True)
class TypographyScale:
    cover_title: int = 44
    section_title: int = 38
    headline: int = 32
    key_message: int = 24
    body: int = 16
    label: int = 13
    caption: int = 10
    footnote: int = 9


@dataclass(frozen=True)
class DesignTokens:
    token_id: str
    slide_width: float
    slide_height: float
    margin_x: float
    safe_top: float
    safe_bottom: float
    content_top: float
    content_bottom: float
    title_max_lines: int
    body_min_font: int
    bullet_max_items: int
    body_max_chars: int
    typography: TypographyScale
    palette: dict[str, str]


def tokens_for_template(template_id: str | None, *, summary_mode: bool = False) -> DesignTokens:
    compact = summary_mode
    typography = TypographyScale(
        cover_title=46 if compact else 50,
        section_title=38 if compact else 42,
        headline=32 if compact else 36,
        key_message=24 if compact else 27,
        body=16,
        label=12 if compact else 13,
        caption=10,
        footnote=9,
    )
    return DesignTokens(
        token_id=f"consulting-excellence-v4:{template_id or 'corporate_clean'}:{'summary' if summary_mode else 'detailed'}",
        slide_width=SLIDE_WIDTH_IN,
        slide_height=SLIDE_HEIGHT_IN,
        margin_x=SAFE_MARGIN_X,
        safe_top=SAFE_MARGIN_TOP,
        safe_bottom=SAFE_MARGIN_BOTTOM,
        content_top=CONTENT_TOP,
        content_bottom=CONTENT_BOTTOM,
        title_max_lines=2,
        body_min_font=16,
        bullet_max_items=3,
        body_max_chars=260 if not compact else 180,
        typography=typography,
        palette=palette_for_template(template_id),
    )


CONSULTING_DESIGN_TOKENS = tokens_for_template("corporate_clean")
