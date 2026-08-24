from __future__ import annotations

CONSULTING_COLORS = {
    "ink": "0B1F3A",
    "navy": "102A43",
    "blue": "155EEF",
    "cyan": "06AED4",
    "white": "FFFFFF",
    "paper": "F8FAFC",
    "line": "D0D5DD",
    "muted": "667085",
    "success": "12B76A",
    "warning": "F59E0B",
    "danger": "B42318",
    "purple": "7A5AF8",
}

CONSULTING_ACCENTS = [
    CONSULTING_COLORS["blue"],
    CONSULTING_COLORS["cyan"],
    CONSULTING_COLORS["success"],
    CONSULTING_COLORS["purple"],
    CONSULTING_COLORS["warning"],
]

THEME_PALETTES = {
    "corporate_clean": ("white", "navy", "blue", "cyan"),
    "executive_minimal": ("white", "ink", "blue", "cyan"),
    "data_driven": ("white", "ink", "blue", "success"),
    "japanese_business": ("white", "navy", "cyan", "warning"),
}


def palette_for_template(template_id: str | None) -> dict[str, str]:
    names = THEME_PALETTES.get(template_id or "corporate_clean", THEME_PALETTES["corporate_clean"])
    surface, text, primary, accent = names
    return {
        "surface": CONSULTING_COLORS[surface],
        "text": CONSULTING_COLORS[text],
        "primary": CONSULTING_COLORS[primary],
        "accent": CONSULTING_COLORS[accent],
        "line": CONSULTING_COLORS["line"],
        "muted": CONSULTING_COLORS["muted"],
    }
