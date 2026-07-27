MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

SLIDE_WIDTH = 13.333
SLIDE_HEIGHT = 7.5
MARGIN_X = 0.78
HEADER_Y = 0.42
FOOTER_Y = 6.92
CONTENT_TOP = 1.48
FONT_FACE = "Noto Sans JP"

COLORS = {
    "white": "FFFFFF",
    "canvas": "F8FAFC",
    "navy": "102A43",
    "navy_2": "1D3557",
    "navy_3": "31445F",
    "text": "1D2939",
    "muted": "667085",
    "line": "D0D5DD",
    "line_dark": "98A2B3",
    "teal": "06AED4",
    "teal_light": "EAFBFF",
    "blue": "155EEF",
    "blue_light": "EAF2FF",
    "orange": "F59E0B",
    "orange_light": "FFF7E6",
    "red": "B42318",
    "red_light": "FFF1F0",
    "green": "12B76A",
    "green_light": "E7F7EF",
    "purple": "7A5AF8",
    "purple_light": "F0EEFF",
}

SECTION_COLORS = [COLORS["blue"], COLORS["teal"], COLORS["green"], COLORS["purple"], COLORS["orange"]]

PPTX_TEMPLATE_THEMES = {
    "corporate_clean": {
        "background": COLORS["navy"],
        "surface": COLORS["canvas"],
        "primary": COLORS["blue"],
        "secondary": COLORS["navy_2"],
        "accent": COLORS["teal"],
        "support": COLORS["orange"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
    "modern_dark": {
        "background": "0B1220",
        "surface": "EAFBFF",
        "primary": COLORS["teal"],
        "secondary": "1E293B",
        "accent": COLORS["blue"],
        "support": COLORS["purple"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
    "creative_agency": {
        "background": "16213E",
        "surface": "FFF7E6",
        "primary": COLORS["orange"],
        "secondary": "243B53",
        "accent": COLORS["purple"],
        "support": COLORS["teal"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
    "executive_minimal": {
        "background": "111827",
        "surface": "F9FAFB",
        "primary": COLORS["navy_3"],
        "secondary": "1F2937",
        "accent": COLORS["blue"],
        "support": COLORS["green"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
    "data_driven": {
        "background": "0F172A",
        "surface": "EAF2FF",
        "primary": COLORS["blue"],
        "secondary": "1E40AF",
        "accent": COLORS["green"],
        "support": COLORS["teal"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
    "warm_professional": {
        "background": "1F2937",
        "surface": "FFF7E6",
        "primary": COLORS["orange"],
        "secondary": "475467",
        "accent": COLORS["green"],
        "support": COLORS["blue"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
    "japanese_business": {
        "background": "1D3557",
        "surface": "F8FAFC",
        "primary": COLORS["navy_2"],
        "secondary": COLORS["navy_3"],
        "accent": COLORS["teal"],
        "support": COLORS["orange"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
    "bold_vision": {
        "background": "0B1F3A",
        "surface": "F0EEFF",
        "primary": COLORS["purple"],
        "secondary": COLORS["blue"],
        "accent": COLORS["teal"],
        "support": COLORS["orange"],
        "text_on_dark": COLORS["white"],
        "text_on_light": COLORS["navy"],
    },
}


def resolve_template_colors(template_id: str | None) -> dict[str, str]:
    return PPTX_TEMPLATE_THEMES.get(template_id or "corporate_clean", PPTX_TEMPLATE_THEMES["corporate_clean"])
