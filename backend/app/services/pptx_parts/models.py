from __future__ import annotations

from dataclasses import dataclass

from app.models import WinProbability


@dataclass(frozen=True)
class EstimateSummary:
    page_count: int
    scope_label: str
    total_min: int
    total_max: int
    total_label: str
    budget_label: str
    budget_fit: str
    lines: list[dict[str, object]]
    required: list[str]
    recommended: list[str]
    optional: list[str]
    premise_items: list[str]
    notes: list[str]


@dataclass(frozen=True)
class PptxContext:
    client_name: str
    proposal_category: str
    proposal_label: str
    concept: str
    current_understanding: dict[str, str]
    journey_points: list[tuple[str, str]]
    sitemap_items: list[str]
    kpi_rows: list[tuple[str, str]]
    kpi_targets: dict[str, float]
    competitor_rows: list[list[str]]
    competitor_site_url: str
    competitor_company_name: str
    winning_strategy: str
    target_user_rows: list[tuple[str, str]]
    content_items: list[str]
    web_strategy_items: list[str]
    case_studies: list[str]
    case_triplets: list[dict[str, str]]
    project_points: list[str]
    solution_points: list[str]
    service_points: list[str]
    schedule_points: list[str]
    team_points: list[str]
    cost_points: list[str]
    estimate: EstimateSummary
    confirmation_items: list[str]
    win_probability: WinProbability | None
