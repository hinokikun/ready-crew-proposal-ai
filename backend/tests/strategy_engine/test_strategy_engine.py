import json
from pathlib import Path

import pytest

from app.strategy_engine.evaluator import evaluate_strategy
from app.strategy_engine.fixtures import FIXTURES
from app.strategy_engine.models import ProposalStrategyInput


GOLDEN_PATH = Path(__file__).parent / "golden" / "expected_strategy_briefs.json"
GOLDEN = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("fixture_name", sorted(FIXTURES.keys()))
def test_fixture_matches_golden_summary(fixture_name):
    brief = evaluate_strategy(FIXTURES[fixture_name])
    expected = GOLDEN[fixture_name]

    for key in [
        "project_category",
        "secondary_category",
        "primary_persona",
        "primary_strategy",
        "story_type",
        "primary_pack",
        "secondary_pack",
        "human_review_required",
        "required_slide_types",
    ]:
        assert getattr(brief, key) == expected[key]
    assert expected["confidence_min"] <= brief.confidence <= expected["confidence_max"]


def test_strategy_brief_schema_has_required_contract_fields():
    brief = evaluate_strategy(FIXTURES["ai_ocr"])
    payload = brief.dict()
    required_fields = {
        "schema_version",
        "project_category",
        "secondary_category",
        "primary_persona",
        "secondary_personas",
        "decision_maker",
        "primary_strategy",
        "secondary_strategies",
        "story_type",
        "primary_pack",
        "secondary_pack",
        "confidence",
        "selection_reasons",
        "assumptions",
        "missing_information",
        "evidence_summary",
        "hero_theme",
        "main_message",
        "problem_theme",
        "before_after_type",
        "architecture_type",
        "roadmap_type",
        "kpi_pack",
        "estimate_pack",
        "priority_messages",
        "risk_messages",
        "next_actions",
        "required_slide_types",
        "optional_slide_types",
        "allowed_terms",
        "conditional_terms",
        "prohibited_terms",
        "human_review_required",
        "human_review_reasons",
    }
    assert required_fields.issubset(payload.keys())


def test_empty_input_is_safe_generic_fallback():
    brief = evaluate_strategy(ProposalStrategyInput())
    assert brief.project_category == "generic_consulting"
    assert brief.primary_pack == "generic_consulting"
    assert brief.primary_persona == "unknown"
    assert brief.human_review_required is True
    assert "input information is sparse" in brief.human_review_reasons


def test_compound_ai_ocr_rpa_selects_secondary_pack():
    brief = evaluate_strategy(FIXTURES["ai_ocr_rpa"])
    assert brief.project_category == "vision_ocr"
    assert brief.secondary_category == "automation"
    assert brief.primary_pack == "vision_ocr"
    assert brief.secondary_pack == "automation"


def test_compound_web_chatbot_keeps_digital_primary():
    brief = evaluate_strategy(FIXTURES["web_chatbot"])
    assert brief.primary_pack == "digital_experience"
    assert brief.secondary_pack == "conversational_ai"
    assert brief.story_type == "customer_experience"


def test_persona_hint_changes_story_for_same_project():
    field_brief = evaluate_strategy(FIXTURES["ai_ocr"])
    executive_brief = evaluate_strategy(FIXTURES["same_project_executive"])
    assert field_brief.primary_pack == executive_brief.primary_pack
    assert field_brief.primary_persona == "field_leader"
    assert executive_brief.primary_persona == "executive"
    assert field_brief.story_type == "quality"
    assert executive_brief.story_type == "roi"


def test_budget_upper_limit_is_not_treated_as_formal_estimate():
    brief = evaluate_strategy(FIXTURES["image_recognition"])
    assert "budget is treated as planning guidance, not a formal estimate" in brief.assumptions
    assert brief.evidence_summary["budget"] == "provided"


def test_budget_without_budget_type_requires_human_review():
    brief = evaluate_strategy(FIXTURES["budget_only"])
    assert brief.human_review_required is True
    assert "budget exists but budget_type is unclear" in brief.human_review_reasons


def test_term_guard_blocks_web_terms_for_ai_ocr():
    brief = evaluate_strategy(FIXTURES["ai_ocr"])
    assert "OCR" in brief.allowed_terms
    assert "CMS" in brief.prohibited_terms
    assert "SEO" in brief.prohibited_terms
    assert "Webサイト" not in brief.main_message


def test_generic_fallback_does_not_allow_category_terms():
    brief = evaluate_strategy(FIXTURES["generic_consulting"])
    assert brief.primary_pack == "generic_consulting"
    assert "OCR" in brief.prohibited_terms
    assert "CMS" in brief.prohibited_terms
    assert "CRM" in brief.prohibited_terms


def test_same_input_returns_same_output():
    first = evaluate_strategy(FIXTURES["crm_generative_ai"]).dict()
    second = evaluate_strategy(FIXTURES["crm_generative_ai"]).dict()
    assert first == second


def test_strategy_engine_imports_are_limited_to_feature_flag_boundary():
    root = Path(__file__).resolve().parents[2]
    production_files = [
        root / "app" / "main.py",
        root / "app" / "router_registry.py",
        root / "app" / "services" / "pptx_service.py",
    ]
    for path in production_files:
        if path.exists():
            assert "strategy_engine" not in path.read_text(encoding="utf-8", errors="ignore")
    boundary = root / "app" / "services" / "presentation_engine_integration.py"
    assert "app.strategy_engine" in boundary.read_text(encoding="utf-8", errors="ignore")


def test_strategy_engine_does_not_call_external_services():
    root = Path(__file__).resolve().parents[2] / "app" / "strategy_engine"
    source = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.py"))
    forbidden = ["openai", "httpx", "requests", "Beautiful"]
    for token in forbidden:
        assert token not in source
