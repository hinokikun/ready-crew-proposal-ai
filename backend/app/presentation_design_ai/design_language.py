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
            "hero_typography": "important slides may use typography as the main graphic object",
            "scale_contrast": "avoid placing title, key message, body, and caption at near-equal sizes",
        },
        "layout": {
            "margin": "consistent wide margin",
            "chapter_pages": "low density with clear section intent",
            "body_pages": "dominant visual first, compact support",
            "footer": "page number and client area are consistent",
            "one_dominant_idea": "each slide should have one primary visual anchor",
            "asymmetric_whitespace": "empty space should amplify the hero object, not just fill a safe margin",
            "delete_before_add": "remove repeated panels, labels, and decoration before adding new elements",
            "diagram_necessity_gate": "do not draw a diagram unless it is the fastest way to understand the decision",
            "act_level_rhythm": "vary density, dark mass, photography, and tension by story act",
            "red_semantic": "red carries one meaning per slide: boundary, difference, threshold, or decision",
        },
        "anti_template_rules": {
            "avoid_adjacent_silhouette": True,
            "avoid_equal_card_repetition": True,
            "avoid_dashboard_escape": True,
            "avoid_smartart_like_process": True,
            "avoid_repeated_bottom_band": True,
            "avoid_repeated_dark_mass": True,
            "avoid_repeated_title_geometry": True,
        },
        "evidence_visualization": {
            "fake_kpi_forbidden": True,
            "fake_roi_forbidden": True,
            "fake_results_forbidden": True,
            "table_escape_forbidden": True,
            "preferred_forms": (
                "decision_threshold",
                "evidence_architecture",
                "measurement_logic",
                "condition_map",
                "proof_requirement",
                "decision_gate",
            ),
        },
        "quality_retention_contract": {
            "message_before_layout": True,
            "business_object_preservation": True,
            "decision_role_preservation": True,
            "dominant_visual_strength_required": True,
            "generic_diagram_escape_penalty": True,
            "deck_art_direction_repetition_penalty": True,
            "forbidden_escapes": (
                "generic 3-step process",
                "equal cards",
                "timeline used as default",
                "matrix used as default",
                "small photo plus ordinary title on cover",
            ),
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
