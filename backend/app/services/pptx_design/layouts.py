from __future__ import annotations

from app.services.pptx_design.theme import PREMIUM_LAYOUTS


def layout_catalog() -> list[str]:
    return sorted(PREMIUM_LAYOUTS)


def layout_family_for_kind(kind: str) -> str:
    mapping = {
        "cover": "hero_cover",
        "proposal_summary": "three_point_cards",
        "current_understanding": "problem_solution",
        "issues": "problem_solution",
        "proposal_concept": "three_point_cards",
        "solution": "comparison",
        "customer_journey": "process_flow",
        "sitemap": "architecture",
        "kpi": "kpi_dashboard",
        "process": "process_flow",
        "schedule": "timeline",
        "team": "architecture",
        "cost": "estimate",
        "estimate": "estimate",
        "budget_fit": "estimate",
        "estimate_priority": "estimate",
        "win_probability": "risk_matrix",
        "next_steps": "next_steps",
    }
    return mapping.get(kind, "three_point_cards")
