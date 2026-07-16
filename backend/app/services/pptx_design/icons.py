from __future__ import annotations

ICON_LABELS = {
    "web": ("UX", "SEO", "CV"),
    "image_recognition": ("IMG", "AI", "OPS"),
    "ai_ocr": ("OCR", "AI", "CSV"),
    "rpa": ("RPA", "BOT", "OPS"),
    "crm_sfa": ("CRM", "SFA", "KPI"),
    "other": ("AI", "KPI", "OPS"),
}


def icon_labels_for_category(category: str) -> tuple[str, str, str]:
    return ICON_LABELS.get(category, ICON_LABELS["other"])
