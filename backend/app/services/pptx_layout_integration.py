from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from app.models import PowerPointSlide, PresentationLayoutDecisionContract
from app.services.pptx_quality import QualityFinding, extract_numbers

SUPPORTED_LAYOUT_IDS: frozenset[str] = frozenset(
    {
        "LAYOUT-001",
        "LAYOUT-002",
        "LAYOUT-003",
        "LAYOUT-004",
        "LAYOUT-005",
        "LAYOUT-006",
        "LAYOUT-007",
        "LAYOUT-008",
        "LAYOUT-009",
        "LAYOUT-010",
        "LAYOUT-011",
        "LAYOUT-012",
        "LAYOUT-013",
        "LAYOUT-014",
        "LAYOUT-015",
        "LAYOUT-016",
        "LAYOUT-017",
    }
)

REQUIRED_RENDERED_LAYOUT_IDS: frozenset[str] = frozenset(
    {
        "LAYOUT-001",
        "LAYOUT-002",
        "LAYOUT-003",
        "LAYOUT-004",
        "LAYOUT-005",
        "LAYOUT-006",
        "LAYOUT-007",
        "LAYOUT-008",
        "LAYOUT-009",
        "LAYOUT-010",
        "LAYOUT-011",
        "LAYOUT-015",
        "LAYOUT-016",
        "LAYOUT-017",
    }
)

SUPPORTED_STATUSES: frozenset[str] = frozenset({"suggested", "applied", "rejected", "backend_fallback", "unsupported"})
SUPPORTED_APPLIED_BY: frozenset[str] = frozenset({"user", "designer_ai", "quality_engine", "backend_fallback"})

DESIGNER_LAYOUT_PREFIX = "designer:"

SLIDE_TYPE_FALLBACKS: dict[str, tuple[str, str]] = {
    "Cover": ("LAYOUT-005", "LAYOUT-001"),
    "Agenda": ("LAYOUT-016", "LAYOUT-002"),
    "Problem": ("LAYOUT-003", "LAYOUT-004"),
    "Current State": ("LAYOUT-003", "LAYOUT-006"),
    "Analysis": ("LAYOUT-006", "LAYOUT-011"),
    "Comparison": ("LAYOUT-007", "LAYOUT-003"),
    "Proposal": ("LAYOUT-005", "LAYOUT-004"),
    "Feature": ("LAYOUT-004", "LAYOUT-003"),
    "Benefit": ("LAYOUT-006", "LAYOUT-015"),
    "Timeline": ("LAYOUT-008", "LAYOUT-002"),
    "Roadmap": ("LAYOUT-009", "LAYOUT-002"),
    "Estimate": ("LAYOUT-007", "LAYOUT-006"),
    "KPI": ("LAYOUT-006", "LAYOUT-015"),
    "Case Study": ("LAYOUT-003", "LAYOUT-006"),
    "Risk": ("LAYOUT-011", "LAYOUT-016"),
    "FAQ": ("LAYOUT-016", "LAYOUT-002"),
    "Summary": ("LAYOUT-006", "LAYOUT-016"),
    "Next Action": ("LAYOUT-010", "LAYOUT-016"),
    "Closing": ("LAYOUT-017", "LAYOUT-005"),
}


@dataclass(frozen=True)
class LayoutPreviewDifference:
    slide_no: int
    slide_id: str
    category: str
    before: str
    after: str
    message: str


@dataclass(frozen=True)
class NumericIntegrityReport:
    preserved: bool
    checked_slide_count: int
    mismatches: list[dict[str, object]] = field(default_factory=list)


@dataclass(frozen=True)
class LayoutIntegrationResult:
    slides: list[PowerPointSlide]
    layout_decisions: list[dict[str, object]]
    layout_fallbacks: list[dict[str, object]]
    preview_pptx_differences: list[dict[str, object]]
    unsupported_layouts: list[str]
    numeric_integrity: dict[str, object]
    template_token_application: dict[str, object]
    human_review_items: list[str]
    predicted_score: int | None
    findings: list[QualityFinding]


def apply_layout_decisions_to_slides(
    slides: list[PowerPointSlide],
    decisions: Iterable[PresentationLayoutDecisionContract] | None,
    *,
    template: str,
    summary_mode: bool,
    predicted_score: int | None,
) -> LayoutIntegrationResult:
    decision_list = list(decisions or [])
    before_numbers = _numbers_by_slide(slides)
    updated_slides = list(slides)
    applied: list[dict[str, object]] = []
    fallbacks: list[dict[str, object]] = []
    differences: list[LayoutPreviewDifference] = []
    unsupported: list[str] = []
    findings: list[QualityFinding] = []
    human_review_items: list[str] = []

    for decision in decision_list:
        normalized = normalize_decision(decision, template=template)
        if normalized["status"] == "rejected":
            human_review_items.append(f"{normalized['slide_id']}: rejected by user")
            applied.append(normalized)
            continue
        if normalized["status"] != "applied":
            applied.append(normalized)
            continue

        slide_index = _resolve_slide_index(normalized, updated_slides)
        if slide_index is None:
            normalized["status"] = "unsupported"
            normalized["applied_by"] = "backend_fallback"
            unsupported.append(str(normalized["selected_layout_id"]))
            fallbacks.append({**normalized, "fallback_reason": "slide_not_found"})
            findings.append(_layout_finding(None, "", "Layout Decisionの対象スライドが見つかりません。", "PPTX生成は既存Layoutで継続しました。", "warning"))
            applied.append(normalized)
            continue

        slide = updated_slides[slide_index]
        selected_layout_id = str(normalized["selected_layout_id"])
        if selected_layout_id not in SUPPORTED_LAYOUT_IDS:
            fallback_id = fallback_layout_for_slide_type(str(normalized["slide_type"]), summary_mode=summary_mode)
            unsupported.append(selected_layout_id)
            fallbacks.append({**normalized, "fallback_layout_id": fallback_id, "fallback_reason": "unsupported_layout"})
            normalized = {**normalized, "selected_layout_id": fallback_id, "status": "backend_fallback", "applied_by": "backend_fallback"}
            selected_layout_id = fallback_id
            findings.append(
                _layout_finding(
                    slide.slide_no,
                    slide.title,
                    "未対応Layoutを安全なLayoutへfallbackしました。",
                    "Presentation Designer AIのLayout LibraryとPPTX Renderer Registryを確認してください。",
                    "warning",
                )
            )

        updated = slide.copy(
            update={
                "layout": designer_layout_key(selected_layout_id),
                "visual_suggestion": _merge_visual_suggestion(slide.visual_suggestion, selected_layout_id),
            }
        )
        updated_slides[slide_index] = updated
        differences.append(
            LayoutPreviewDifference(
                slide_no=slide.slide_no,
                slide_id=str(normalized["slide_id"]),
                category="layout_mismatch" if slide.layout != updated.layout else "fallback_applied",
                before=slide.layout,
                after=updated.layout,
                message=f"Designer AIの{selected_layout_id}をPPTX描画Layoutへ接続しました。",
            )
        )
        applied.append(normalized)

    numeric = _numeric_integrity(before_numbers, updated_slides)
    if not numeric.preserved:
        findings.append(
            _layout_finding(
                None,
                "",
                "Layout変換前後で数値の差異を検出しました。",
                "安全のためPPTX出力内容を人間が確認してください。",
                "critical",
            )
        )
        human_review_items.append("numeric_integrity_mismatch")

    return LayoutIntegrationResult(
        slides=updated_slides,
        layout_decisions=applied,
        layout_fallbacks=fallbacks,
        preview_pptx_differences=[difference.__dict__ for difference in differences],
        unsupported_layouts=sorted(set(unsupported)),
        numeric_integrity=numeric.__dict__,
        template_token_application=design_token_application(template, summary_mode=summary_mode),
        human_review_items=human_review_items,
        predicted_score=predicted_score,
        findings=findings,
    )


def normalize_decision(decision: PresentationLayoutDecisionContract, *, template: str) -> dict[str, object]:
    status = decision.status if decision.status in SUPPORTED_STATUSES else "unsupported"
    applied_by = decision.applied_by if decision.applied_by in SUPPORTED_APPLIED_BY else "designer_ai"
    selected_layout_id = normalize_layout_id(decision.selected_layout_id)
    recommended = [layout_id for layout_id in (normalize_layout_id(value) for value in decision.recommended_layout_ids) if layout_id]
    return {
        "slide_id": decision.slide_id,
        "slide_index": decision.slide_index,
        "slide_type": decision.slide_type,
        "selected_layout_id": selected_layout_id,
        "recommended_layout_ids": recommended,
        "selection_reason": decision.selection_reason,
        "expected_effect": decision.expected_effect,
        "template_id": decision.template_id or template,
        "design_token_id": decision.design_token_id or f"{template}:default",
        "applied_by": applied_by,
        "status": status,
        "confidence": max(0.0, min(1.0, decision.confidence)),
        "human_review_required": decision.human_review_required,
    }


def normalize_layout_id(value: str) -> str:
    match = re.search(r"LAYOUT-\d{3}", value or "")
    return match.group(0) if match else ""


def designer_layout_key(layout_id: str) -> str:
    return f"{DESIGNER_LAYOUT_PREFIX}{layout_id}"


def layout_id_from_layout_key(value: str) -> str | None:
    normalized = normalize_layout_id(value)
    return normalized if value.startswith(DESIGNER_LAYOUT_PREFIX) and normalized else None


def fallback_layout_for_slide_type(slide_type: str, *, summary_mode: bool) -> str:
    detailed, summary = SLIDE_TYPE_FALLBACKS.get(slide_type, ("LAYOUT-002", "LAYOUT-003"))
    return summary if summary_mode else detailed


def design_token_application(template: str, *, summary_mode: bool) -> dict[str, object]:
    compact = summary_mode or template in {"executive_minimal", "japanese_business"}
    return {
        "template": template,
        "mode": "summary" if summary_mode else "detailed",
        "background": "template_background",
        "surface": "editable_shapes",
        "primary": "template_primary",
        "secondary": "template_secondary",
        "accent": "template_accent",
        "text_primary": "template_text_primary",
        "text_secondary": "template_text_secondary",
        "title_font_size": 30 if compact else 34,
        "body_font_size": 13 if compact else 14,
        "caption_font_size": 9,
        "card_padding": "compact" if compact else "balanced",
        "section_gap": "compact" if compact else "balanced",
        "page_margin": "template_margin",
        "corner_radius": "rounded_rectangle_shape",
        "line_width": "standard_shape_line",
        "table_header_style": "filled_header",
        "emphasis_style": "accent_band_or_metric_card",
    }


def _resolve_slide_index(decision: dict[str, object], slides: list[PowerPointSlide]) -> int | None:
    slide_index = decision.get("slide_index")
    if isinstance(slide_index, int) and 1 <= slide_index <= len(slides):
        return slide_index - 1
    slide_id = str(decision.get("slide_id") or "")
    match = re.search(r"(\d+)$", slide_id)
    if match:
        index = int(match.group(1)) - 1
        if 0 <= index < len(slides):
            return index
    return None


def _numbers_by_slide(slides: list[PowerPointSlide]) -> dict[int, list[str]]:
    return {slide.slide_no: extract_numbers("\n".join(slide.bullets)) for slide in slides}


def _numeric_integrity(before: dict[int, list[str]], slides: list[PowerPointSlide]) -> NumericIntegrityReport:
    mismatches: list[dict[str, object]] = []
    for slide in slides:
        before_numbers = before.get(slide.slide_no, [])
        after_numbers = extract_numbers("\n".join(slide.bullets))
        if before_numbers != after_numbers:
            mismatches.append({"slide_no": slide.slide_no, "before": before_numbers, "after": after_numbers})
    return NumericIntegrityReport(preserved=not mismatches, checked_slide_count=len(slides), mismatches=mismatches)


def _merge_visual_suggestion(current: str, layout_id: str) -> str:
    note = f"Designer Layout {layout_id}"
    if not current:
        return note
    if note in current:
        return current
    return f"{current} / {note}"


def _layout_finding(slide_no: int | None, slide_title: str, message: str, recommendation: str, severity: str) -> QualityFinding:
    return QualityFinding(
        rule_id="PPT-LAYOUT-DESIGNER-001",
        category="layout_integration",
        severity=severity,  # type: ignore[arg-type]
        slide_no=slide_no,
        slide_title=slide_title,
        message=message,
        recommendation=recommendation,
        auto_fixable=False,
        confidence=0.9,
        human_review_required=severity != "info",
    )
