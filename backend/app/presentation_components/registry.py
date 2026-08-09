"""Version 7.0 Consulting Presentation Component Registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


VisualType = Literal[
    "hero",
    "issue_tree",
    "current_future",
    "before_after",
    "comparison",
    "swot",
    "pest",
    "three_c",
    "journey",
    "flow",
    "sitemap",
    "architecture",
    "timeline",
    "roadmap",
    "phase_gate",
    "milestone",
    "process",
    "cycle",
    "matrix",
    "priority_matrix",
    "kpi_dashboard",
    "kpi_cards",
    "waterfall",
    "breakdown",
    "investment",
    "risk_matrix",
    "decision_tree",
    "landscape",
    "feature_comparison",
    "business_model",
    "value_chain",
    "service_blueprint",
    "organization",
    "team",
    "stakeholder",
    "governance",
    "security",
    "schedule",
    "gantt",
    "implementation",
    "support",
    "operation",
    "faq",
    "next_action",
    "closing",
    "contact",
    "appendix",
    "pyramid",
    "fishbone",
    "radar",
    "funnel",
    "heatmap",
    "capability_map",
]


@dataclass(frozen=True)
class ComponentSpec:
    component_id: str
    name: str
    category: str
    visual_type: VisualType
    layout_family: str
    purpose_keywords: tuple[str, ...]
    diagram_ratio: float
    text_ratio: float
    max_title_chars: int = 42
    max_body_chars: int = 90
    max_items: int = 5
    recommended_chart: str = ""
    recommended_icon: str = ""
    design_rule: str = ""


_SEEDS: list[tuple[str, str, VisualType, str, tuple[str, ...], str, str]] = [
    ("Executive Hero", "executive", "hero", "hero_split", ("executive", "cover", "decision"), "", "compass"),
    ("Executive Summary Map", "executive", "pyramid", "executive_pyramid", ("summary", "decision", "roi"), "", "spark"),
    ("Problem Statement", "problem", "issue_tree", "issue_tree", ("problem", "pain", "課題"), "", "alert"),
    ("Issue Tree", "problem", "issue_tree", "issue_tree_left", ("cause", "root", "why"), "", "branch"),
    ("Current / Future", "transformation", "current_future", "split_future", ("future", "change", "after"), "", "arrow"),
    ("Before After", "transformation", "before_after", "before_after_arc", ("before", "after", "改善"), "", "switch"),
    ("Comparison", "analysis", "comparison", "comparison_columns", ("compare", "alternative", "比較"), "", "scale"),
    ("SWOT", "analysis", "swot", "quadrant_swot", ("swot", "strength", "weakness"), "", "quadrant"),
    ("PEST", "analysis", "pest", "pest_ring", ("market", "regulation", "industry"), "", "globe"),
    ("3C", "analysis", "three_c", "three_circle", ("customer", "competitor", "company"), "", "venn"),
    ("Customer Journey", "customer", "journey", "journey_wave", ("customer", "journey", "experience"), "", "person"),
    ("User Flow", "process", "flow", "flow_ladder", ("flow", "user", "operation"), "", "route"),
    ("Site Map", "architecture", "sitemap", "sitemap_tree", ("site", "information", "structure"), "", "map"),
    ("Architecture", "architecture", "architecture", "architecture_layers", ("system", "platform", "architecture"), "", "server"),
    ("Timeline", "roadmap", "timeline", "timeline_horizontal", ("timeline", "history", "sequence"), "", "clock"),
    ("Roadmap", "roadmap", "roadmap", "roadmap_stream", ("roadmap", "plan", "phase"), "", "flag"),
    ("Phase Gate", "roadmap", "phase_gate", "phase_gate_steps", ("phase", "gate", "approval"), "", "gate"),
    ("Milestone", "roadmap", "milestone", "milestone_flags", ("milestone", "deadline", "target"), "", "pin"),
    ("Process", "process", "process", "process_chevrons", ("process", "steps", "導入"), "", "gear"),
    ("Cycle", "process", "cycle", "cycle_orbit", ("cycle", "continuous", "運用"), "", "refresh"),
    ("Matrix", "analysis", "matrix", "matrix_2x2", ("matrix", "position", "priority"), "", "grid"),
    ("Priority Matrix", "analysis", "priority_matrix", "priority_2x2", ("priority", "impact", "effort"), "", "target"),
    ("KPI Dashboard", "kpi", "kpi_dashboard", "dashboard_gauges", ("kpi", "metric", "測定"), "gauge", "speedometer"),
    ("KPI Cards", "kpi", "kpi_cards", "metric_row", ("kpi", "smart", "target"), "cards", "bar"),
    ("ROI Waterfall", "roi", "waterfall", "waterfall_bridge", ("roi", "return", "investment"), "waterfall", "yen"),
    ("Cost Breakdown", "estimate", "breakdown", "breakdown_stack", ("cost", "estimate", "費用"), "stacked", "wallet"),
    ("Benefit Breakdown", "benefit", "breakdown", "benefit_stack", ("benefit", "effect", "value"), "stacked", "spark"),
    ("Investment", "roi", "investment", "investment_loop", ("investment", "budget", "回収"), "timeline", "coin"),
    ("Risk Matrix", "risk", "risk_matrix", "risk_heatmap", ("risk", "mitigation", "懸念"), "heatmap", "shield"),
    ("Decision Tree", "decision", "decision_tree", "decision_branch", ("decision", "option", "判断"), "", "branch"),
    ("Competitive Landscape", "competition", "landscape", "landscape_map", ("competitor", "differentiation", "勝ち筋"), "", "map"),
    ("Feature Comparison", "competition", "feature_comparison", "feature_lanes", ("feature", "compare", "差別化"), "", "check"),
    ("Business Model", "business", "business_model", "business_model_canvas", ("business", "model", "revenue"), "", "canvas"),
    ("Value Chain", "business", "value_chain", "value_chain_flow", ("value", "chain", "process"), "", "chain"),
    ("Service Blueprint", "operation", "service_blueprint", "swimlane_blueprint", ("service", "operation", "touchpoint"), "", "layers"),
    ("Organization", "team", "organization", "org_tree", ("organization", "role", "体制"), "", "users"),
    ("Team", "team", "team", "team_constellation", ("team", "member", "owner"), "", "users"),
    ("Stakeholder", "decision", "stakeholder", "stakeholder_map", ("stakeholder", "decision", "関係者"), "", "people"),
    ("Governance", "operation", "governance", "governance_rings", ("governance", "approval", "control"), "", "shield"),
    ("Security", "risk", "security", "security_layers", ("security", "privacy", "risk"), "", "lock"),
    ("Schedule", "roadmap", "schedule", "schedule_blocks", ("schedule", "date", "納期"), "", "calendar"),
    ("Gantt", "roadmap", "gantt", "gantt_swimlane", ("gantt", "timeline", "task"), "gantt", "calendar"),
    ("Implementation", "process", "implementation", "implementation_wave", ("implementation", "導入", "rollout"), "", "rocket"),
    ("Support", "operation", "support", "support_model", ("support", "help", "保守"), "", "lifebuoy"),
    ("Operation", "operation", "operation", "operation_loop", ("operation", "run", "運用"), "", "refresh"),
    ("FAQ", "closing", "faq", "faq_stack", ("question", "objection", "faq"), "", "question"),
    ("Next Action", "closing", "next_action", "next_action_path", ("next", "action", "合意"), "", "arrow"),
    ("Closing", "closing", "closing", "closing_focus", ("closing", "meeting", "打ち合わせ"), "", "calendar"),
    ("Contact", "closing", "contact", "contact_card", ("contact", "owner", "担当"), "", "mail"),
    ("Appendix", "appendix", "appendix", "appendix_index", ("appendix", "reference", "補足"), "", "paperclip"),
    ("Pyramid Principle", "strategy", "pyramid", "pyramid_argument", ("logic", "argument", "conclusion"), "", "triangle"),
    ("Fishbone Cause Map", "problem", "fishbone", "fishbone_cause", ("cause", "fishbone", "原因"), "", "bone"),
    ("Radar Capability", "capability", "radar", "radar_capability", ("capability", "maturity", "診断"), "radar", "radar"),
    ("Funnel Conversion", "sales", "funnel", "funnel_steps", ("conversion", "funnel", "営業"), "funnel", "filter"),
    ("Heatmap Prioritization", "analysis", "heatmap", "heatmap_grid", ("heat", "risk", "priority"), "heatmap", "grid"),
    ("Capability Map", "capability", "capability_map", "capability_grid", ("capability", "function", "map"), "", "grid"),
]

_EXTRA_NAMES = [
    "Executive Decision Brief", "Board-Level ROI Snapshot", "Urgency Framing", "Market Pressure Map",
    "Customer Pain Ladder", "Root Cause Ladder", "Hypothesis Stack", "Evidence Chain",
    "Value Proposition Canvas", "Outcome Tree", "Impact Bridge", "Transformation Thesis",
    "Operating Model Shift", "Target Operating Model", "Data Flow Map", "AI Workflow Map",
    "Automation Opportunity Map", "Manual-to-AI Handoff", "Human-in-the-Loop Model", "Quality Control Loop",
    "Exception Handling Map", "Integration Map", "Platform Layering", "Data Governance Map",
    "Risk Control Model", "Compliance Trace", "Security Posture Map", "Adoption Curve",
    "Training Plan", "Change Management Map", "Stakeholder Alignment Plan", "Decision Meeting Plan",
    "Procurement Logic", "Pricing Rationale", "Must-Should-Could Scope", "Option Architecture",
    "Scenario Comparison", "Sensitivity Snapshot", "ROI Payback Path", "Benefit Realization Map",
    "KPI Measurement Plan", "SMART KPI Board", "Baseline-to-Target Chart", "Management Dashboard",
    "Operating Cadence", "Review Rhythm", "Implementation Swimlane", "Pilot Design",
    "PoC Success Criteria", "Scale-Up Plan", "Post-Launch Support", "Continuous Improvement Loop",
    "Competitive Win Themes", "Differentiation Map", "Alternative Evaluation", "Vendor Selection Matrix",
    "Client Fit Matrix", "Case Study Snapshot", "Proof Point Map", "Reference Architecture",
    "Data Readiness Check", "Migration Path", "Dependency Map", "Assumption Register",
    "Open Questions Board", "Decision Checklist", "Executive Ask", "Meeting Agenda",
]


def _make_component(seed: tuple[str, str, VisualType, str, tuple[str, ...], str, str], index: int) -> ComponentSpec:
    name, category, visual_type, layout_family, keywords, chart, icon = seed
    diagram_ratio = 0.76 if visual_type not in {"faq", "appendix", "contact"} else 0.62
    return ComponentSpec(
        component_id=f"COMP-{index:03d}",
        name=name,
        category=category,
        visual_type=visual_type,
        layout_family=layout_family,
        purpose_keywords=keywords,
        diagram_ratio=diagram_ratio,
        text_ratio=round(1 - diagram_ratio, 2),
        recommended_chart=chart,
        recommended_icon=icon,
        design_rule="one action title, one conclusion, diagram-first canvas, notes for explanation",
    )


def _build_registry() -> list[ComponentSpec]:
    components = [_make_component(seed, idx + 1) for idx, seed in enumerate(_SEEDS)]
    visual_cycle: list[VisualType] = [
        "matrix",
        "flow",
        "roadmap",
        "kpi_dashboard",
        "risk_matrix",
        "architecture",
        "pyramid",
        "journey",
        "waterfall",
        "stakeholder",
        "timeline",
        "decision_tree",
        "capability_map",
    ]
    for offset, name in enumerate(_EXTRA_NAMES, start=len(components) + 1):
        visual_type = visual_cycle[(offset - 1) % len(visual_cycle)]
        components.append(
            ComponentSpec(
                component_id=f"COMP-{offset:03d}",
                name=name,
                category="consulting",
                visual_type=visual_type,
                layout_family=f"{visual_type}_{offset:03d}",
                purpose_keywords=tuple(name.lower().replace("-", " ").split()[:4]),
                diagram_ratio=0.74,
                text_ratio=0.26,
                recommended_chart="diagram",
                recommended_icon="insight",
                design_rule="diagram-first consulting component with compact evidence and explicit next action",
            )
        )
    return components


COMPONENT_REGISTRY: list[ComponentSpec] = _build_registry()


def select_component_sequence(category: str, slide_count: int = 25) -> list[ComponentSpec]:
    """Return a visually diverse component sequence for a proposal deck."""

    preferred_keywords = tuple((category or "").lower().split())
    story_ids = [
        "COMP-001",
        "COMP-002",
        "COMP-003",
        "COMP-052",
        "COMP-005",
        "COMP-006",
        "COMP-012",
        "COMP-014",
        "COMP-021",
        "COMP-023",
        "COMP-025",
        "COMP-028",
        "COMP-029",
        "COMP-030",
        "COMP-032",
        "COMP-034",
        "COMP-036",
        "COMP-038",
        "COMP-039",
        "COMP-041",
        "COMP-042",
        "COMP-043",
        "COMP-047",
        "COMP-048",
        "COMP-049",
    ]
    by_id = {item.component_id: item for item in COMPONENT_REGISTRY}
    sequence = [by_id[item] for item in story_ids if item in by_id]

    if any(key in category.lower() for key in ("ai", "dx", "ocr", "it", "saas")):
        replacements = {
            7: by_id["COMP-075"],  # AI Workflow Map
            8: by_id["COMP-076"],  # Automation Opportunity Map
            12: by_id["COMP-082"],  # Security Posture Map
        }
        for index, component in replacements.items():
            if index < len(sequence):
                sequence[index] = component
    elif preferred_keywords:
        matching = [
            item
            for item in COMPONENT_REGISTRY
            if any(keyword in " ".join(item.purpose_keywords) for keyword in preferred_keywords)
        ]
        for idx, component in enumerate(matching[:3]):
            if 5 + idx < len(sequence):
                sequence[5 + idx] = component

    used_layouts: set[str] = set()
    final: list[ComponentSpec] = []
    for component in sequence:
        if len(final) >= slide_count:
            break
        if len(final) >= 2 and final[-1].layout_family == component.layout_family == final[-2].layout_family:
            alternative = next(item for item in COMPONENT_REGISTRY if item.layout_family not in used_layouts)
            final.append(alternative)
            used_layouts.add(alternative.layout_family)
            continue
        final.append(component)
        used_layouts.add(component.layout_family)

    for component in COMPONENT_REGISTRY:
        if len(final) >= slide_count:
            break
        if component.layout_family not in used_layouts:
            final.append(component)
            used_layouts.add(component.layout_family)
    return final[:slide_count]
