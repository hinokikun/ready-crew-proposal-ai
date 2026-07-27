import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.presentation_engine_v2.deck_planner import DeckPlannerResult, ProposalContext, plan_deck
from app.presentation_engine_v2.deck_planner.planner_fixtures import invalid_context_payloads, valid_context_payloads
from app.presentation_engine_v2.deck_planner.planner_golden import golden_planner_results
from app.presentation_engine_v2.deck_planner.planner_prompt import planner_prompt_contract
from app.presentation_engine_v2.deck_planner.planner_schema import (
    deck_planner_result_schema,
    example_planner_result,
    proposal_context_schema,
)
from app.presentation_engine_v2.deck_validators import validate_deck_blueprint


ROOT = Path(__file__).resolve().parents[3]


def _section_types(result: DeckPlannerResult) -> list[str]:
    return [section.section_type for section in result.deck_blueprint.sections]


def test_planner_context_schema_and_example_contract() -> None:
    context_schema = proposal_context_schema()
    result_schema = deck_planner_result_schema()
    example = example_planner_result()

    assert context_schema["title"] == "Presentation Engine 2.0 Proposal Context"
    assert result_schema["title"] == "Presentation Engine 2.0 Deck Planner Result"
    assert example["planner_version"] == "pe2_deck_planner_v1"
    assert example["deck_blueprint"]["deck_blueprint_version"] == "pe2_deck_blueprint_v1"


def test_planner_generates_valid_deck_blueprint_only() -> None:
    result = plan_deck(valid_context_payloads()[0])
    deck = result.deck_blueprint

    assert deck.validation_result is not None
    assert deck.validation_result.valid
    assert validate_deck_blueprint(deck).valid
    assert result.generated_slide_blueprints is False
    assert result.connected_to_runtime is False
    assert all(ref.embedded_slide_blueprint is None for ref in deck.slide_blueprint_refs)
    assert all(slide.working_title.endswith("planning slide") for slide in deck.slide_plan)


def test_ai_ocr_case_uses_diagnosis_execution_and_approach() -> None:
    payload = next(item for item in valid_context_payloads() if item["project_id"] == "planner-fixture-ocr-01")
    result = plan_deck(payload)
    sections = _section_types(result)

    assert result.deck_blueprint.story_arc == "diagnosis_strategy_execution"
    assert "current_state" in sections
    assert "approach" in sections
    assert "kpi" in sections
    assert "pricing" in sections
    assert sections[-1] == "next_action"


def test_web_competitive_case_adds_competitor_and_uses_web_deck_type() -> None:
    result = plan_deck(valid_context_payloads()[0])
    sections = _section_types(result)

    assert result.deck_blueprint.deck_type == "web_production_proposal"
    assert "competitor" in sections
    competitor_recommendations = [
        item for item in result.slide_recommendations if item.section_id.endswith("competitor")
    ]
    assert competitor_recommendations
    assert competitor_recommendations[0].recommended_visual == "comparison_table"


def test_executive_audience_uses_summary_and_executive_length() -> None:
    payload = next(item for item in valid_context_payloads() if item["project_id"] == "planner-fixture-investor-01")
    result = plan_deck(payload)
    sections = _section_types(result)

    assert result.deck_blueprint.audience_seniority == "executive"
    assert result.deck_blueprint.deck_length_type == "executive"
    assert sections[0] == "cover"
    assert "executive_summary" in sections
    assert result.deck_blueprint.target_slide_count <= 10


def test_no_budget_context_omits_pricing_but_keeps_next_action() -> None:
    payload = next(item for item in valid_context_payloads() if item["project_id"] == "planner-fixture-knowledge-01")
    result = plan_deck(payload)
    sections = _section_types(result)

    assert "pricing" not in sections
    assert "next_action" in sections
    assert result.deck_blueprint.cta_plan.next_action


def test_planner_fixture_counts_and_validity() -> None:
    valid_payloads = valid_context_payloads()
    invalid_payloads = invalid_context_payloads()

    assert len(valid_payloads) >= 30
    assert len(invalid_payloads) >= 12
    assert all(plan_deck(payload).deck_blueprint.validation_result.valid for payload in valid_payloads)
    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            plan_deck(payload)


def test_golden_planner_results_are_valid_and_high_quality() -> None:
    golden = golden_planner_results()

    assert len(golden) >= 20
    for payload in golden:
        result = DeckPlannerResult.parse_obj(payload)
        assert result.deck_blueprint.validation_result.valid
        assert result.evaluation_result is not None
        assert result.evaluation_result.total_score >= 80


def test_planner_json_serialization_roundtrip() -> None:
    result = plan_deck(valid_context_payloads()[1])
    raw = result.json(ensure_ascii=False)
    restored = DeckPlannerResult.parse_raw(raw)

    assert restored.context.project_id == result.context.project_id
    assert restored.deck_blueprint.deck_id == result.deck_blueprint.deck_id
    assert restored.deck_blueprint.slide_blueprint_refs[0].embedded_slide_blueprint is None


def test_unicode_numeric_and_date_signals_are_preserved() -> None:
    payload = {
        "project_id": "unicode-001",
        "project_name": "生花オークション向けAI画像認識導入支援",
        "project_summary": "2027年5月導入想定。予算上限は1,000万円。画像認識で花の種類・色・等級・状態を確認する。",
        "industry": "生花卸売",
        "proposal_category": "AI画像認識",
        "budget_range": "1,000万円以内",
        "decision_maker": "Operations executive",
        "persona": "品質管理責任者",
        "implementation_purpose": "人の最終確認を残しながら確認時間を短縮する。",
        "problems": ["繁忙時の処理遅延", "判定基準の属人化"],
        "expected_outcomes": ["確認時間短縮", "誤分類低減", "PoC合格基準の明確化"],
        "timeline": "2027年5月頃",
    }
    result = plan_deck(payload)
    raw = result.json(ensure_ascii=False)

    assert "生花オークション" in raw
    assert "1,000万円" in raw
    assert "2027年5月" in raw
    assert result.deck_blueprint.validation_result.valid


def test_planner_decisions_cover_required_rule_families() -> None:
    result = plan_deck(valid_context_payloads()[2])
    names = {decision.rule_name for decision in result.decisions}

    assert {
        "proposal_category",
        "audience",
        "decision_stage",
        "deck_type",
        "story_arc",
        "persuasion_strategy",
        "deck_length",
        "deck_goal",
        "section_sequence",
    }.issubset(names)


def test_planner_prompt_contract_is_offline_and_bounded() -> None:
    contract = planner_prompt_contract()

    assert contract["llm_enabled"] is False
    assert "Headlines" in contract["system_prompt"] or "headlines" in contract["system_prompt"]
    assert "deck_goal" in contract["output_keys"]


def test_planner_json_artifacts_exist_and_are_parseable() -> None:
    module_dir = ROOT / "app" / "presentation_engine_v2" / "deck_planner"
    docs_dir = ROOT.parent / "docs" / "presentation-engine-v2-phase2a"
    files = [
        module_dir / "planner_fixtures" / "valid_proposal_contexts.json",
        module_dir / "planner_fixtures" / "invalid_proposal_contexts.json",
        module_dir / "planner_golden" / "golden_planner_results.json",
        docs_dir / "proposal-context.schema.json",
        docs_dir / "deck-planner-result.schema.json",
        docs_dir / "deck-planner-example.json",
    ]

    for path in files:
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8"))
    assert len(json.loads(files[0].read_text(encoding="utf-8"))) >= 30
    assert len(json.loads(files[2].read_text(encoding="utf-8"))) >= 20

