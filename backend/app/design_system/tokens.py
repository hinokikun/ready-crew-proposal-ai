"""Version 7.0 Consulting Design System tokens.

These tokens are intentionally independent from external PowerPoint
templates. They define reusable consulting-style primitives that can be
composed into native editable PPTX shapes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Palette:
    name: str
    background: str
    surface: str
    ink: str
    muted: str
    primary: str
    secondary: str
    accent: str
    accent_2: str
    line: str
    success: str
    warning: str
    danger: str


@dataclass(frozen=True)
class TypographyScale:
    font_face: str = "Aptos"
    japanese_font_face: str = "Yu Gothic"
    deck_title: int = 46
    slide_title: int = 28
    claim: int = 18
    label: int = 11
    body: int = 13
    caption: int = 9
    number: int = 30


@dataclass(frozen=True)
class SpacingScale:
    page_margin_x: float = 0.42
    page_margin_y: float = 0.34
    title_top: float = 0.34
    title_gap: float = 0.16
    content_top: float = 1.22
    gutter: float = 0.16
    card_padding: float = 0.12
    section_gap: float = 0.22


@dataclass(frozen=True)
class GridSystem:
    slide_width: float = 13.333
    slide_height: float = 7.5
    columns: int = 12
    rows: int = 8
    safe_left: float = 0.42
    safe_right: float = 12.91
    safe_top: float = 0.34
    safe_bottom: float = 7.14


@dataclass(frozen=True)
class ShapeSystem:
    radius_small: float = 0.08
    radius_medium: float = 0.14
    line_width: float = 1.2
    connector_width: float = 1.5
    icon_size: float = 0.26
    arrow_size: float = 0.18


@dataclass(frozen=True)
class DensityRules:
    max_visible_chars: int = 210
    max_title_chars: int = 42
    max_bullets: int = 4
    target_diagram_ratio: float = 0.70
    target_text_ratio: float = 0.30
    min_layout_families_for_25_slides: int = 20
    max_same_layout_streak: int = 2


@dataclass(frozen=True)
class ConsultingDesignSystem:
    version: str
    palettes: dict[str, Palette]
    typography: TypographyScale = field(default_factory=TypographyScale)
    spacing: SpacingScale = field(default_factory=SpacingScale)
    grid: GridSystem = field(default_factory=GridSystem)
    shapes: ShapeSystem = field(default_factory=ShapeSystem)
    density: DensityRules = field(default_factory=DensityRules)

    def palette_for_category(self, category: str) -> Palette:
        text = (category or "").lower()
        if any(key in text for key in ("ai", "dx", "ocr", "it", "saas", "digital")):
            return self.palettes["digital_modern"]
        if any(key in text for key in ("medical", "education", "public", "自治体", "医療", "教育")):
            return self.palettes["trust_minimal"]
        if any(key in text for key in ("executive", "roi", "strategy", "経営")):
            return self.palettes["executive_navy"]
        return self.palettes["consulting_navy"]


CONSULTING_DESIGN_SYSTEM = ConsultingDesignSystem(
    version="7.0",
    palettes={
        "consulting_navy": Palette(
            name="Consulting Navy",
            background="#F6F8FB",
            surface="#FFFFFF",
            ink="#102033",
            muted="#64748B",
            primary="#0B1F3A",
            secondary="#294B73",
            accent="#2F80ED",
            accent_2="#14B8A6",
            line="#D8E2EF",
            success="#129669",
            warning="#B7791F",
            danger="#C2410C",
        ),
        "executive_navy": Palette(
            name="Executive Navy",
            background="#071426",
            surface="#10233D",
            ink="#F8FAFC",
            muted="#C7D2E1",
            primary="#EAF2FF",
            secondary="#A8C7FA",
            accent="#4DB6FF",
            accent_2="#7DD3C7",
            line="#314862",
            success="#5DE1B2",
            warning="#FFD166",
            danger="#FF8A65",
        ),
        "digital_modern": Palette(
            name="Digital Transformation Modern",
            background="#F7FAFC",
            surface="#FFFFFF",
            ink="#111827",
            muted="#64748B",
            primary="#172554",
            secondary="#2563EB",
            accent="#06B6D4",
            accent_2="#8B5CF6",
            line="#DDE7F3",
            success="#10B981",
            warning="#F59E0B",
            danger="#EF4444",
        ),
        "trust_minimal": Palette(
            name="Japanese Business Minimal",
            background="#FAFAF8",
            surface="#FFFFFF",
            ink="#1F2937",
            muted="#6B7280",
            primary="#1D3557",
            secondary="#457B9D",
            accent="#2A9D8F",
            accent_2="#E9C46A",
            line="#E5E7EB",
            success="#2F855A",
            warning="#B7791F",
            danger="#C53030",
        ),
    },
)
