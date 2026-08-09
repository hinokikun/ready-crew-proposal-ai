from __future__ import annotations

from io import BytesIO

from pptx import Presentation

from app.presentation_composer import CaseContext
from app.presentation_design_ai import design_presentation_deck
from app.presentation_design_ai.contracts import FEATURE_FLAG_NAME, is_presentation_design_ai_enabled
from app.presentation_design_ai.evaluator import (
    content_density_report,
    diagram_selection_report,
    narrative_flow_report,
    visual_hierarchy_report,
)
from app.presentation_design_ai.refinement_loop import refine_design_deck
from app.presentation_design_ai.renderer_adapter import render_design_deck_to_pptx
from app.presentation_design_ai.validators import has_repeated_composition, validate_design_deck


def _case() -> CaseContext:
    return CaseContext(
        case_id="v9-test",
        case_name="AI image recognition proposal",
        client_name="Flower Auction Japan",
        industry="flower auction",
        category="AI / DX",
        project_summary="Introduce AI image recognition to reduce inspection variance and speed up confirmation work.",
        pain_points=("manual inspection varies by operator", "confirmation takes time", "quality records are fragmented"),
        expected_outcomes=("inspection time down 30%", "agreement rate above 90%", "recheck cases down 20%"),
        budget="PoC 8,000,000 JPY",
        timeline="12 weeks",
        decision_maker="CEO, operations manager, information systems",
        competitor="image AI vendors and OCR vendors",
    )


def test_feature_flag_defaults_false_and_can_be_enabled(monkeypatch) -> None:
    monkeypatch.delenv(FEATURE_FLAG_NAME, raising=False)
    assert is_presentation_design_ai_enabled() is False
    monkeypatch.setenv(FEATURE_FLAG_NAME, "true")
    assert is_presentation_design_ai_enabled() is True


def test_information_architecture_classifies_required_business_items() -> None:
    deck = design_presentation_deck(_case(), force_enabled=True)
    item_ids = {item.item_id for item in deck.information_architecture.items}
    assert {"background", "problem", "root_cause", "kpi", "roi", "risk", "next_action"} <= item_ids
    assert "root_cause" in deck.information_architecture.hypothesis_items


def test_action_titles_are_conclusion_style_and_short() -> None:
    deck = design_presentation_deck(_case(), force_enabled=True)
    forbidden = {"現状の課題", "提案概要", "KPI", "ロードマップ", "リスク", "費用"}
    assert all(contract.action_title not in forbidden for contract in deck.slide_contracts)
    assert all(len(contract.action_title) <= 40 for contract in deck.slide_contracts)


def test_diagram_selection_records_rejections_and_reasons() -> None:
    deck = design_presentation_deck(_case(), force_enabled=True)
    report = diagram_selection_report(deck)
    assert all(item["selected_diagram"] for item in report["slides"])
    assert all(item["rejected_candidates"] for item in report["slides"])
    assert any(item["selected_diagram"] == "waterfall" for item in report["slides"])


def test_visual_hierarchy_narrative_and_density_reports_are_complete() -> None:
    deck = design_presentation_deck(_case(), force_enabled=True)
    hierarchy = visual_hierarchy_report(deck)
    narrative = narrative_flow_report(deck)
    density = content_density_report(deck)
    assert len(hierarchy["slides"]) == deck.slide_count
    assert len(narrative["title_only_story"]) == deck.slide_count
    assert density["diagram_ratio_average"] >= 0.60
    assert density["max_visible_characters"] <= 170
    assert has_repeated_composition(deck) is False


def test_design_contract_validates_without_internal_label_leakage() -> None:
    deck = design_presentation_deck(_case(), force_enabled=True)
    assert validate_design_deck(deck) == []
    assert all("COMP-" not in contract.action_title for contract in deck.slide_contracts)


def test_refinement_loop_keeps_clean_deck_renderable() -> None:
    deck = design_presentation_deck(_case(), force_enabled=True)
    refined, report = refine_design_deck(deck)
    assert report.final_status == "clean"
    assert refined.slide_count == deck.slide_count


def test_renderer_adapter_creates_openable_pptx() -> None:
    deck = design_presentation_deck(_case(), force_enabled=True)
    refined, _ = refine_design_deck(deck)
    pptx_bytes, render_report = render_design_deck_to_pptx(refined)
    prs = Presentation(BytesIO(pptx_bytes))
    assert len(prs.slides) == refined.slide_count
    assert render_report["design_version"] == "presentation_design_ai_v9"
    assert render_report["design_plan_fingerprint"]
