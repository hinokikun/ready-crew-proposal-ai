from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from app.models import PowerPointSlide
from app.strategy_engine.models import SalesStrategyBrief

SlideType = Literal[
    "Cover",
    "Agenda",
    "Problem",
    "Current State",
    "Analysis",
    "Comparison",
    "Proposal",
    "Feature",
    "Benefit",
    "Timeline",
    "Roadmap",
    "Estimate",
    "KPI",
    "Case Study",
    "Risk",
    "FAQ",
    "Summary",
    "Next Action",
    "Closing",
]


@dataclass(frozen=True)
class LayoutDefinition:
    id: str
    name: str
    best_for: tuple[SlideType, ...]
    density: Literal["low", "medium", "high"]
    visual_focus: Literal["message", "comparison", "timeline", "metrics", "flow", "image", "decision"]
    diagram_hint: str
    expected_effect: str


@dataclass(frozen=True)
class DesignToken:
    template: str
    color_role: str
    spacing: Literal["compact", "balanced", "generous"]
    title_size: int
    body_size: int
    card_padding: int
    diagram_gap: int
    table_padding: int
    icon_size: int


@dataclass(frozen=True)
class LayoutDecision:
    slide_no: int
    slide_title: str
    slide_type: SlideType
    current_layout: str
    recommended_layout: LayoutDefinition
    candidates: tuple[LayoutDefinition, ...]
    selection_reason: str
    expected_effect: str
    design_token: DesignToken
    score_before: int
    score_after: int
    variation_applied: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


LAYOUT_LIBRARY: tuple[LayoutDefinition, ...] = (
    LayoutDefinition("LAYOUT-001", "Title Only", ("Agenda", "Summary"), "low", "message", "Large title and sparse support text", "Focuses the opening message."),
    LayoutDefinition("LAYOUT-002", "Title + Body", ("Current State", "Analysis", "Feature", "FAQ"), "medium", "message", "Title, concise body, one supporting callout", "Keeps standard content readable."),
    LayoutDefinition("LAYOUT-003", "Two Column", ("Problem", "Proposal", "Risk"), "medium", "comparison", "Issue and response split into two areas", "Clarifies pairings between issues and responses."),
    LayoutDefinition("LAYOUT-004", "Three Column", ("Benefit", "Feature", "Case Study"), "medium", "decision", "Three grouped messages with icons", "Makes three points comparable."),
    LayoutDefinition("LAYOUT-005", "Hero", ("Cover", "Closing"), "low", "image", "Hero visual with strong message layer", "Strengthens first impression."),
    LayoutDefinition("LAYOUT-006", "KPI Cards", ("KPI", "Benefit"), "medium", "metrics", "Metric cards with status and basis", "Makes numbers and criteria visible."),
    LayoutDefinition("LAYOUT-007", "Comparison Table", ("Comparison",), "high", "comparison", "Criteria rows and option columns", "Explains differences and selection logic."),
    LayoutDefinition("LAYOUT-008", "Timeline", ("Timeline",), "medium", "timeline", "Horizontal milestones with decision gates", "Shows time and decisions together."),
    LayoutDefinition("LAYOUT-009", "Roadmap", ("Roadmap",), "medium", "timeline", "Phased roadmap with outcome labels", "Shows staged adoption clearly."),
    LayoutDefinition("LAYOUT-010", "Flow", ("Current State", "Proposal", "Next Action"), "medium", "flow", "Process boxes and arrows", "Makes process flow easier to explain."),
    LayoutDefinition("LAYOUT-011", "Matrix", ("Analysis", "Risk", "Comparison"), "high", "decision", "Two-axis matrix", "Positions priorities and risks."),
    LayoutDefinition("LAYOUT-012", "Quote", ("Summary", "Case Study"), "low", "message", "Key statement with evidence caption", "Makes one statement memorable."),
    LayoutDefinition("LAYOUT-013", "Image Left", ("Problem", "Current State", "Case Study"), "medium", "image", "Visual placeholder on left", "Adds context without locking image assets."),
    LayoutDefinition("LAYOUT-014", "Image Right", ("Proposal", "Feature", "Benefit"), "medium", "image", "Visual placeholder on right", "Supports the proposed solution visually."),
    LayoutDefinition("LAYOUT-015", "Large Number", ("KPI", "Benefit", "Estimate"), "low", "metrics", "One dominant metric with context", "Makes the key figure stand out."),
    LayoutDefinition("LAYOUT-016", "Checklist", ("Risk", "FAQ", "Next Action"), "medium", "decision", "Action checklist with status marks", "Turns review items into actions."),
    LayoutDefinition("LAYOUT-017", "Closing", ("Closing", "Next Action"), "low", "decision", "Next action and final message", "Clarifies the final action."),
)

SLIDE_TYPE_LAYOUTS: dict[SlideType, tuple[str, ...]] = {
    "Cover": ("LAYOUT-005", "LAYOUT-001"),
    "Agenda": ("LAYOUT-001", "LAYOUT-010"),
    "Problem": ("LAYOUT-003", "LAYOUT-013", "LAYOUT-011"),
    "Current State": ("LAYOUT-010", "LAYOUT-013", "LAYOUT-002"),
    "Analysis": ("LAYOUT-011", "LAYOUT-006", "LAYOUT-002"),
    "Comparison": ("LAYOUT-007", "LAYOUT-003", "LAYOUT-011"),
    "Proposal": ("LAYOUT-014", "LAYOUT-010", "LAYOUT-003"),
    "Feature": ("LAYOUT-004", "LAYOUT-014", "LAYOUT-002"),
    "Benefit": ("LAYOUT-006", "LAYOUT-004", "LAYOUT-015"),
    "Timeline": ("LAYOUT-008", "LAYOUT-009"),
    "Roadmap": ("LAYOUT-009", "LAYOUT-008"),
    "Estimate": ("LAYOUT-015", "LAYOUT-007", "LAYOUT-002"),
    "KPI": ("LAYOUT-006", "LAYOUT-015", "LAYOUT-011"),
    "Case Study": ("LAYOUT-013", "LAYOUT-012", "LAYOUT-004"),
    "Risk": ("LAYOUT-011", "LAYOUT-016", "LAYOUT-003"),
    "FAQ": ("LAYOUT-016", "LAYOUT-002"),
    "Summary": ("LAYOUT-012", "LAYOUT-004", "LAYOUT-001"),
    "Next Action": ("LAYOUT-016", "LAYOUT-017", "LAYOUT-010"),
    "Closing": ("LAYOUT-017", "LAYOUT-005"),
}

DESIGN_TOKENS: dict[str, DesignToken] = {
    "corporate_clean": DesignToken("corporate_clean", "Navy / Blue / White", "balanced", 34, 18, 18, 18, 12, 28),
    "modern_dark": DesignToken("modern_dark", "Navy gradient / Cyan accent", "generous", 36, 18, 20, 22, 12, 30),
    "creative_agency": DesignToken("creative_agency", "Blue / Cyan / Soft white", "generous", 36, 18, 22, 24, 14, 30),
    "executive_minimal": DesignToken("executive_minimal", "Navy / Gray / White", "generous", 32, 17, 16, 22, 12, 24),
    "data_driven": DesignToken("data_driven", "Blue / Cyan / Data green", "balanced", 34, 17, 18, 18, 12, 26),
    "warm_professional": DesignToken("warm_professional", "Navy / Warm gray / Blue", "balanced", 33, 18, 18, 18, 12, 26),
    "japanese_business": DesignToken("japanese_business", "Navy / White / Indigo", "compact", 31, 17, 14, 16, 10, 24),
    "bold_vision": DesignToken("bold_vision", "Deep navy / Bright blue / Cyan", "generous", 38, 18, 22, 24, 14, 32),
}


def analyze_layout_decisions(
    slides: list[PowerPointSlide],
    *,
    template: str = "corporate_clean",
    story_type: str = "generic",
    audience: str = "sales",
    presentation_score: int = 70,
    quality_findings: list[dict[str, object]] | None = None,
    sales_strategy_brief: SalesStrategyBrief | dict[str, object] | None = None,
) -> list[LayoutDecision]:
    token = DESIGN_TOKENS.get(template, DESIGN_TOKENS["corporate_clean"])
    findings = quality_findings or []
    sales_strategy = _parse_sales_strategy(sales_strategy_brief)
    effective_story_type = sales_strategy.recommended_story_type if sales_strategy else story_type
    effective_audience = sales_strategy.decision_maker if sales_strategy else audience
    decisions: list[LayoutDecision] = []
    for index, slide in enumerate(slides):
        slide_type = classify_slide_type(slide, index=index, total_slides=len(slides))
        candidates = _select_candidates(
            slide,
            slide_type,
            story_type=effective_story_type,
            template=template,
            findings=findings,
            sales_strategy=sales_strategy,
        )
        recommended = candidates[0]
        variation_applied = False
        previous_two = [decision.recommended_layout.id for decision in decisions[-2:]]
        if len(previous_two) == 2 and previous_two[0] == previous_two[1] == recommended.id:
            recommended = next((candidate for candidate in candidates if candidate.id != recommended.id), _layout_by_id("LAYOUT-002"))
            variation_applied = True
        score_before = _score_current_layout(slide, slide_type, presentation_score)
        delta = _estimate_score_delta(slide, slide_type, recommended, findings)
        score_after = min(100, score_before + delta)
        decisions.append(
            LayoutDecision(
                slide_no=slide.slide_no,
                slide_title=slide.title,
                slide_type=slide_type,
                current_layout=slide.layout,
                recommended_layout=recommended,
                candidates=tuple(candidates[:4]),
                selection_reason=_selection_reason(slide, slide_type, recommended, effective_audience, variation_applied, sales_strategy),
                expected_effect=recommended.expected_effect,
                design_token=token,
                score_before=score_before,
                score_after=score_after,
                variation_applied=variation_applied,
            )
        )
    return decisions


def classify_slide_type(slide: PowerPointSlide, *, index: int, total_slides: int) -> SlideType:
    text = _slide_text(slide).lower()
    if index == 0 or any(keyword in text for keyword in ("cover", "表紙", "title cover", "hero")):
        return "Cover"
    if any(keyword in text for keyword in ("agenda", "目次", "流れ")):
        return "Agenda"
    if any(keyword in text for keyword in ("faq", "質問", "q&a")):
        return "FAQ"
    if any(keyword in text for keyword in ("risk", "リスク", "懸念", "注意")):
        return "Risk"
    if any(keyword in text for keyword in ("estimate", "見積", "費用", "価格", "budget", "予算")):
        return "Estimate"
    if any(keyword in text for keyword in ("kpi", "指標", "効果", "削減", "率", "%", "score", "quality")):
        return "KPI"
    if any(keyword in text for keyword in ("timeline", "schedule", "スケジュール", "日程", "フェーズ")):
        return "Timeline"
    if any(keyword in text for keyword in ("roadmap", "ロードマップ", "将来", "展開")):
        return "Roadmap"
    if any(keyword in text for keyword in ("before", "after", "比較", "競合", "差分", "対比")):
        return "Comparison"
    if any(keyword in text for keyword in ("case", "事例", "実績")):
        return "Case Study"
    if any(keyword in text for keyword in ("problem", "課題", "痛み", "困り", "不足")):
        return "Problem"
    if any(keyword in text for keyword in ("current", "現状", "as-is", "業務")):
        return "Current State"
    if any(keyword in text for keyword in ("analysis", "分析", "要因", "洞察")):
        return "Analysis"
    if any(keyword in text for keyword in ("feature", "機能", "仕様")):
        return "Feature"
    if any(keyword in text for keyword in ("benefit", "メリット", "価値", "成果")):
        return "Benefit"
    if any(keyword in text for keyword in ("proposal", "提案", "解決", "導入")):
        return "Proposal"
    if any(keyword in text for keyword in ("closing", "まとめ", "結論")):
        return "Closing"
    if any(keyword in text for keyword in ("next", "action", "次", "承認", "確認")) or index == total_slides - 1:
        return "Next Action"
    return "Summary" if index >= total_slides - 2 else "Analysis"


def _select_candidates(
    slide: PowerPointSlide,
    slide_type: SlideType,
    *,
    story_type: str,
    template: str,
    findings: list[dict[str, object]],
    sales_strategy: SalesStrategyBrief | None = None,
) -> list[LayoutDefinition]:
    structural_slide = slide_type in {"Cover", "Agenda", "Closing"}
    ids = [
        *(SLIDE_TYPE_LAYOUTS[slide_type] if structural_slide else _signal_layouts(slide, findings)),
        *(_signal_layouts(slide, findings) if structural_slide else SLIDE_TYPE_LAYOUTS[slide_type]),
        *_sales_strategy_layouts(sales_strategy),
        *_story_layouts(story_type),
        *_template_layouts(template),
    ]
    unique_ids = list(dict.fromkeys(ids))
    return [_layout_by_id(layout_id) for layout_id in unique_ids]


def _signal_layouts(slide: PowerPointSlide, findings: list[dict[str, object]]) -> list[str]:
    text = _slide_text(slide).lower()
    ids: list[str] = []
    if any(keyword in text for keyword in ("before", "after", "比較", "競合", "差分", "対比")):
        ids.extend(["LAYOUT-007", "LAYOUT-003"])
    if any(keyword in text for keyword in ("kpi", "%", "削減", "時間", "円", "score", "quality", "精度")):
        ids.extend(["LAYOUT-006", "LAYOUT-015"])
    if any(keyword in text for keyword in ("スケジュール", "timeline", "フェーズ", "日程")):
        ids.append("LAYOUT-008")
    if any(keyword in text for keyword in ("roadmap", "ロードマップ", "段階", "展開")):
        ids.append("LAYOUT-009")
    if any(keyword in text for keyword in ("flow", "フロー", "業務", "連携", "api", "csv", "承認", "確認")):
        ids.append("LAYOUT-010")
    if any(keyword in text for keyword in ("matrix", "優先", "評価", "リスク", "難易度", "影響")):
        ids.append("LAYOUT-011")
    if any(keyword in text for keyword in ("画像", "現場", "商品", "画面", "サンプル")):
        ids.extend(["LAYOUT-013", "LAYOUT-014"])
    if len(text) > 220:
        ids.extend(["LAYOUT-003", "LAYOUT-010"])
    if any(finding.get("slide_no") == slide.slide_no and finding.get("category") == "diagram" for finding in findings):
        ids.extend(["LAYOUT-010", "LAYOUT-011"])
    return ids


def _story_layouts(story_type: str) -> list[str]:
    if any(keyword in story_type for keyword in ("ROI", "KPI", "効果", "コスト")):
        return ["LAYOUT-006", "LAYOUT-015"]
    if any(keyword in story_type for keyword in ("AI", "DX", "導入", "Automation", "自動")):
        return ["LAYOUT-010", "LAYOUT-009", "LAYOUT-014"]
    if any(keyword in story_type for keyword in ("競合", "差別")):
        return ["LAYOUT-007", "LAYOUT-011"]
    return ["LAYOUT-003", "LAYOUT-004"]


def _sales_strategy_layouts(sales_strategy: SalesStrategyBrief | None) -> list[str]:
    if sales_strategy is None:
        return []
    ids: list[str] = []
    tone = sales_strategy.recommended_presentation_tone.lower()
    position = sales_strategy.proposal_position.lower()
    if "data" in tone:
        ids.extend(["LAYOUT-006", "LAYOUT-011", "LAYOUT-015"])
    if "executive" in tone:
        ids.extend(["LAYOUT-012", "LAYOUT-015", "LAYOUT-017"])
    if "agency" in tone:
        ids.extend(["LAYOUT-013", "LAYOUT-014", "LAYOUT-004"])
    if position in {"ai_enablement", "business_improvement"}:
        ids.extend(["LAYOUT-010", "LAYOUT-009"])
    if sales_strategy.competitive_situation != "no_clear_competitor":
        ids.extend(["LAYOUT-007", "LAYOUT-011"])
    return ids


def _template_layouts(template: str) -> list[str]:
    if template == "data_driven":
        return ["LAYOUT-006", "LAYOUT-011", "LAYOUT-015"]
    if template == "executive_minimal":
        return ["LAYOUT-001", "LAYOUT-012", "LAYOUT-016"]
    if template in {"bold_vision", "modern_dark"}:
        return ["LAYOUT-005", "LAYOUT-014", "LAYOUT-015"]
    if template == "creative_agency":
        return ["LAYOUT-013", "LAYOUT-014", "LAYOUT-004"]
    return ["LAYOUT-003", "LAYOUT-010", "LAYOUT-016"]


def _selection_reason(
    slide: PowerPointSlide,
    slide_type: SlideType,
    layout: LayoutDefinition,
    audience: str,
    variation_applied: bool,
    sales_strategy: SalesStrategyBrief | None = None,
) -> str:
    reasons = [f"slide_type={slide_type}", f"layout_focus={layout.visual_focus}", f"audience={audience}"]
    if sales_strategy is not None:
        reasons.append(f"sales_strategy_tone={sales_strategy.recommended_presentation_tone}")
        reasons.append(f"proposal_position={sales_strategy.proposal_position}")
        reasons.append(f"competitive_situation={sales_strategy.competitive_situation}")
    text = _slide_text(slide).lower()
    if any(keyword in text for keyword in ("比較", "before", "after", "競合", "差分")):
        reasons.append("comparison_signal=true")
    if any(keyword in text for keyword in ("kpi", "%", "時間", "削減", "円", "精度")):
        reasons.append("metric_signal=true")
    if len(text) > 220:
        reasons.append("content_fit=needs_structure")
    if variation_applied:
        reasons.append("variation=avoid_three_repeats")
    return "; ".join(reasons)


def _score_current_layout(slide: PowerPointSlide, slide_type: SlideType, base_score: int) -> int:
    current = slide.layout.lower()
    expected = [_layout_by_id(layout_id).name.lower() for layout_id in SLIDE_TYPE_LAYOUTS[slide_type]]
    matched = any(name in current or current in name for name in expected)
    length_penalty = 8 if len(_slide_text(slide)) > 240 else 4 if len(_slide_text(slide)) > 180 else 0
    return max(45, min(92, base_score + (4 if matched else -6) - length_penalty))


def _estimate_score_delta(slide: PowerPointSlide, slide_type: SlideType, layout: LayoutDefinition, findings: list[dict[str, object]]) -> int:
    delta = 6 if layout.id in SLIDE_TYPE_LAYOUTS[slide_type] else 3
    text = _slide_text(slide).lower()
    if layout.visual_focus == "comparison" and any(keyword in text for keyword in ("比較", "before", "after", "競合", "差分")):
        delta += 3
    if layout.visual_focus == "metrics" and any(keyword in text for keyword in ("kpi", "%", "時間", "削減", "円", "精度")):
        delta += 3
    if layout.visual_focus == "flow" and any(keyword in text for keyword in ("業務", "フロー", "連携", "確認", "承認", "api", "csv")):
        delta += 3
    if len(_slide_text(slide)) > 220 and layout.density != "high":
        delta += 2
    if any(finding.get("slide_no") == slide.slide_no and finding.get("category") == "layout" for finding in findings):
        delta += 2
    return max(2, min(14, delta))


def _layout_by_id(layout_id: str) -> LayoutDefinition:
    return next((layout for layout in LAYOUT_LIBRARY if layout.id == layout_id), LAYOUT_LIBRARY[1])


def _parse_sales_strategy(value: SalesStrategyBrief | dict[str, object] | None) -> SalesStrategyBrief | None:
    if value is None:
        return None
    if isinstance(value, SalesStrategyBrief):
        return value
    return SalesStrategyBrief(**value)


def _slide_text(slide: PowerPointSlide) -> str:
    return " ".join([slide.title, slide.layout, slide.visual_suggestion or "", " ".join(slide.bullets or []), slide.speaker_notes or ""])
