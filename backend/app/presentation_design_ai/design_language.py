"""ProposalPilot design language derived from generalized reference principles."""

from __future__ import annotations


def build_design_language(category: str) -> dict[str, object]:
    accent = "#0EA5C6" if _is_digital(category) else "#1D4ED8"
    return {
        "source_policy": {
            "reference_material_copied": False,
            "logo_or_brand_reused": False,
            "layout_traced": False,
            "generalized_principles_only": True,
        },
        "palette": {
            "background": "#FFFFFF",
            "ink": "#111827",
            "muted": "#64748B",
            "line": "#D7DEE8",
            "accent": accent,
            "deep": "#071426",
            "risk": "#B45309",
        },
        "typography": {
            "title_position": "upper_left",
            "title_style": "action_title",
            "max_title_lines": 2,
            "body_blocks": "3-5",
            "takeaway": "single sentence only when it advances the decision",
        },
        "layout": {
            "margin": "consistent wide margin",
            "chapter_pages": "low density with clear section intent",
            "body_pages": "diagram first, compact support",
            "footer": "page number and client area are consistent",
        },
        "emotion_mapping": {
            "urgency": "slightly stronger accent and tighter causal structure",
            "clarity": "central diagram and restrained text",
            "confidence": "more whitespace and clear implementation path",
            "trust": "risk controls and governance visual language",
            "commitment": "large next-action path with minimal distraction",
        },
    }


def _is_digital(category: str) -> bool:
    value = category.lower()
    return any(key in value for key in ("ai", "dx", "ocr", "saas", "crm", "system", "security"))
