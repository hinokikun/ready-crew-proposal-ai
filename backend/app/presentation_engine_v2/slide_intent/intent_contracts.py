"""Static contracts for Phase 2D Slide Intent."""

from __future__ import annotations

from .intent_enums import (
    ChartCandidate,
    DiagramCandidate,
    ReadingOrder,
    SlideIntentType,
    SlideType,
    VisualPattern,
)


SECTION_TO_SLIDE_TYPE: dict[str, SlideType] = {
    "cover": SlideType.COVER,
    "executive_summary": SlideType.EXECUTIVE_SUMMARY,
    "background": SlideType.ANALYSIS,
    "current_state": SlideType.CURRENT_STATE,
    "problem": SlideType.PROBLEM,
    "insight": SlideType.ANALYSIS,
    "opportunity": SlideType.BENEFIT,
    "market": SlideType.ANALYSIS,
    "competitor": SlideType.COMPARISON,
    "strategy": SlideType.PROPOSAL,
    "solution": SlideType.PROPOSAL,
    "scope": SlideType.FEATURE,
    "deliverables": SlideType.FEATURE,
    "approach": SlideType.PROPOSAL,
    "roadmap": SlideType.ROADMAP,
    "timeline": SlideType.TIMELINE,
    "team": SlideType.SUMMARY,
    "case_study": SlideType.CASE_STUDY,
    "kpi": SlideType.KPI,
    "roi": SlideType.KPI,
    "pricing": SlideType.ESTIMATE,
    "estimate": SlideType.ESTIMATE,
    "risk": SlideType.RISK,
    "faq": SlideType.FAQ,
    "next_action": SlideType.NEXT_ACTION,
    "closing": SlideType.CLOSING,
    "appendix": SlideType.APPENDIX,
}


SECTION_TO_INTENT: dict[str, SlideIntentType] = {
    "cover": SlideIntentType.FRAME_DECISION,
    "executive_summary": SlideIntentType.SUMMARIZE,
    "background": SlideIntentType.ALIGN_CONTEXT,
    "current_state": SlideIntentType.EXPLAIN_PROBLEM,
    "problem": SlideIntentType.EXPLAIN_PROBLEM,
    "insight": SlideIntentType.SHARE_INSIGHT,
    "opportunity": SlideIntentType.SHARE_INSIGHT,
    "market": SlideIntentType.SHARE_INSIGHT,
    "competitor": SlideIntentType.COMPARE_OPTIONS,
    "strategy": SlideIntentType.RECOMMEND_ACTION,
    "solution": SlideIntentType.RECOMMEND_ACTION,
    "scope": SlideIntentType.RECOMMEND_ACTION,
    "deliverables": SlideIntentType.RECOMMEND_ACTION,
    "approach": SlideIntentType.EXPLAIN_PROCESS,
    "roadmap": SlideIntentType.SHOW_PLAN,
    "timeline": SlideIntentType.SHOW_PLAN,
    "team": SlideIntentType.SHOW_HIERARCHY,
    "case_study": SlideIntentType.PROVE_VALUE,
    "kpi": SlideIntentType.PROVE_VALUE,
    "roi": SlideIntentType.EXPLAIN_INVESTMENT,
    "pricing": SlideIntentType.EXPLAIN_INVESTMENT,
    "estimate": SlideIntentType.EXPLAIN_INVESTMENT,
    "risk": SlideIntentType.REDUCE_RISK,
    "faq": SlideIntentType.REDUCE_RISK,
    "next_action": SlideIntentType.CLOSE_NEXT_STEP,
    "closing": SlideIntentType.CLOSE_NEXT_STEP,
    "appendix": SlideIntentType.ALIGN_CONTEXT,
}


SECTION_TO_VISUAL: dict[str, VisualPattern] = {
    "cover": VisualPattern.HERO,
    "executive_summary": VisualPattern.SUMMARY_CARDS,
    "background": VisualPattern.CALLOUT,
    "current_state": VisualPattern.PROCESS,
    "problem": VisualPattern.CALLOUT,
    "insight": VisualPattern.MATRIX,
    "opportunity": VisualPattern.CALLOUT,
    "market": VisualPattern.MATRIX,
    "competitor": VisualPattern.COMPARISON,
    "strategy": VisualPattern.SUMMARY_CARDS,
    "solution": VisualPattern.PROCESS,
    "scope": VisualPattern.TABLE,
    "deliverables": VisualPattern.CHECKLIST,
    "approach": VisualPattern.PROCESS,
    "roadmap": VisualPattern.ROADMAP,
    "timeline": VisualPattern.TIMELINE,
    "team": VisualPattern.HIERARCHY,
    "case_study": VisualPattern.CALLOUT,
    "kpi": VisualPattern.KPI_CARDS,
    "roi": VisualPattern.NUMBER_DOMINANT,
    "pricing": VisualPattern.TABLE,
    "estimate": VisualPattern.TABLE,
    "risk": VisualPattern.MATRIX,
    "faq": VisualPattern.CHECKLIST,
    "next_action": VisualPattern.CHECKLIST,
    "closing": VisualPattern.CALLOUT,
    "appendix": VisualPattern.TEXT_DOMINANT,
}


VISUAL_TO_READING_ORDER: dict[VisualPattern, ReadingOrder] = {
    VisualPattern.HERO: ReadingOrder.CENTER_OUT,
    VisualPattern.SUMMARY_CARDS: ReadingOrder.SCAN_CARDS,
    VisualPattern.CALLOUT: ReadingOrder.TITLE_FIRST,
    VisualPattern.COMPARISON: ReadingOrder.BEFORE_AFTER,
    VisualPattern.KPI_CARDS: ReadingOrder.SCAN_CARDS,
    VisualPattern.TIMELINE: ReadingOrder.TIMELINE,
    VisualPattern.ROADMAP: ReadingOrder.TIMELINE,
    VisualPattern.PROCESS: ReadingOrder.LEFT_TO_RIGHT,
    VisualPattern.HIERARCHY: ReadingOrder.HIERARCHY,
    VisualPattern.CHECKLIST: ReadingOrder.TOP_TO_BOTTOM,
    VisualPattern.IMAGE_DOMINANT: ReadingOrder.Z_PATTERN,
    VisualPattern.TEXT_DOMINANT: ReadingOrder.TOP_TO_BOTTOM,
    VisualPattern.NUMBER_DOMINANT: ReadingOrder.CENTER_OUT,
    VisualPattern.TABLE: ReadingOrder.LEFT_TO_RIGHT,
    VisualPattern.MATRIX: ReadingOrder.Z_PATTERN,
}


VISUAL_TO_DIAGRAM: dict[VisualPattern, DiagramCandidate] = {
    VisualPattern.HERO: DiagramCandidate.IMAGE_PLACEHOLDER,
    VisualPattern.SUMMARY_CARDS: DiagramCandidate.CALLOUT,
    VisualPattern.CALLOUT: DiagramCandidate.CALLOUT,
    VisualPattern.COMPARISON: DiagramCandidate.COMPARISON_TABLE,
    VisualPattern.KPI_CARDS: DiagramCandidate.NONE,
    VisualPattern.TIMELINE: DiagramCandidate.TIMELINE,
    VisualPattern.ROADMAP: DiagramCandidate.ROADMAP,
    VisualPattern.PROCESS: DiagramCandidate.PROCESS_FLOW,
    VisualPattern.HIERARCHY: DiagramCandidate.HIERARCHY_TREE,
    VisualPattern.CHECKLIST: DiagramCandidate.CHECKLIST,
    VisualPattern.IMAGE_DOMINANT: DiagramCandidate.IMAGE_PLACEHOLDER,
    VisualPattern.TEXT_DOMINANT: DiagramCandidate.NONE,
    VisualPattern.NUMBER_DOMINANT: DiagramCandidate.COST_BREAKDOWN,
    VisualPattern.TABLE: DiagramCandidate.NONE,
    VisualPattern.MATRIX: DiagramCandidate.MATRIX,
}


SECTION_TO_CHART: dict[str, ChartCandidate] = {
    "kpi": ChartCandidate.KPI_CARD,
    "roi": ChartCandidate.WATERFALL,
}
