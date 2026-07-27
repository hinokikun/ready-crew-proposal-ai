import json
from pathlib import Path

import pytest

from app.presentation_engine_v2.deck_planner import plan_deck
from app.presentation_engine_v2.deck_planner.planner_fixtures import valid_context_payloads
from app.presentation_engine_v2.evidence_planner import EvidencePlannerResult, plan_evidence, plan_evidence_from_payload
from app.presentation_engine_v2.evidence_planner.evidence_fixtures import (
    invalid_evidence_planning_payloads,
    valid_evidence_planning_payloads,
)
from app.presentation_engine_v2.evidence_planner.evidence_golden import golden_evidence_planner_results
from app.presentation_engine_v2.evidence_planner.evidence_models import (
    EvidenceConfidence,
    EvidencePlannerResult,
    EvidenceSourceType,
)
from app.presentation_engine_v2.evidence_planner.evidence_planner import EvidencePlannerInputError
from app.presentation_engine_v2.evidence_planner.evidence_prompt import evidence_planner_prompt_contract
from app.presentation_engine_v2.evidence_planner.evidence_schema import (
    evidence_planner_result_schema,
    evidence_planning_input_schema,
    example_evidence_planner_result,
)


ROOT = Path(__file__).resolve().parents[3]


def test_evidence_planner_source_type_enums_are_available() -> None:
    values = EvidenceSourceType.values()

    assert "customer_interview" in values
    assert "internal_kpi" in values
    assert "competitor_analysis" in values
    assert "financial_estimate" in values
    assert "public_information" in values


def test_evidence_planner_generates_slide_level_requirements_only() -> None:
    payload = valid_evidence_planning_payloads()[0]
    result = plan_evidence_from_payload(payload)

    assert result.slide_evidence
    assert len(result.slide_evidence) == len(payload["deck_blueprint"]["slide_plan"])
    assert all(item.required_evidence for item in result.slide_evidence)
    assert result.generated_headlines is False
    assert result.generated_main_messages is False
    assert result.generated_body_text is False
    assert result.generated_slide_blueprints is False
    assert result.connected_to_runtime is False
    assert all(not item.generated_headline for item in result.slide_evidence)
    assert all(not item.generated_slide_blueprint for item in result.slide_evidence)


def test_kpi_and_pricing_slides_require_numeric_evidence() -> None:
    result = plan_evidence_from_payload(valid_evidence_planning_payloads()[0])
    numeric_slides = [
        item
        for item in result.slide_evidence
        if item.section_type in {"kpi", "roi", "pricing", "estimate"}
    ]

    assert numeric_slides
    assert all(item.numeric_evidence_required for item in numeric_slides)
    assert all(
        any(requirement.source_type in {"internal_kpi", "financial_estimate"} for requirement in item.required_evidence)
        for item in numeric_slides
    )


def test_competitor_slide_requires_competitor_analysis() -> None:
    result = plan_evidence_from_payload(valid_evidence_planning_payloads()[0])
    competitor_slides = [item for item in result.slide_evidence if item.section_type == "competitor"]

    assert competitor_slides
    assert competitor_slides[0].evidence_priority == "critical"
    assert "competitor_analysis" in competitor_slides[0].evidence_source_types
    assert competitor_slides[0].visual_evidence_recommendation == "comparison_table"


def test_missing_numeric_context_adds_warning_without_generating_copy() -> None:
    context = next(item for item in valid_context_payloads() if item["project_id"] == "planner-fixture-knowledge-01")
    deck = plan_deck(context).deck_blueprint
    result = plan_evidence(deck, context)
    missing = [
        warning
        for slide in result.slide_evidence
        for warning in slide.missing_evidence_warnings
        if warning.warning_id == "missing-numeric"
    ]

    assert missing
    assert result.generated_body_text is False
    assert result.evaluation_result is not None
    assert result.evaluation_result.total_score >= 70


def test_evidence_plan_json_roundtrip() -> None:
    result = plan_evidence_from_payload(valid_evidence_planning_payloads()[1])
    raw = result.json(ensure_ascii=False)
    restored = EvidencePlannerResult.parse_raw(raw)

    assert restored.deck_id == result.deck_id
    assert restored.slide_evidence[0].slide_blueprint_id == result.slide_evidence[0].slide_blueprint_id
    assert restored.evaluation_result.total_score == result.evaluation_result.total_score


def test_schema_and_example_contract() -> None:
    input_schema = evidence_planning_input_schema()
    result_schema = evidence_planner_result_schema()
    example = example_evidence_planner_result()

    assert input_schema["title"] == "Presentation Engine 2.0 Evidence Planning Input"
    assert result_schema["title"] == "Presentation Engine 2.0 Evidence Planner Result"
    assert example["evidence_planner_version"] == "pe2_evidence_planner_v1"
    assert example["slide_evidence"]


def test_fixtures_and_invalid_payloads() -> None:
    valid_payloads = valid_evidence_planning_payloads()
    invalid_payloads = invalid_evidence_planning_payloads()

    assert len(valid_payloads) >= 30
    assert len(invalid_payloads) >= 15
    assert all(plan_evidence_from_payload(payload).slide_evidence for payload in valid_payloads)
    for payload in invalid_payloads:
        with pytest.raises(EvidencePlannerInputError):
            plan_evidence_from_payload(payload)


def test_golden_evidence_results_are_valid() -> None:
    golden = golden_evidence_planner_results()

    assert len(golden) >= 20
    for payload in golden:
        result = EvidencePlannerResult.parse_obj(payload)
        assert result.slide_evidence
        assert result.evaluation_result is not None
        assert result.evaluation_result.total_score >= 70


def test_unicode_numeric_and_date_values_survive_planning() -> None:
    context = {
        "project_id": "phase2b-unicode",
        "project_name": "生花オークション向けAI画像認識導入支援",
        "project_summary": "2027年5月導入想定。予算上限は1,000万円。画像認識で花の種類・色・等級・状態を確認する。",
        "industry": "生花卸売",
        "proposal_category": "AI画像認識",
        "competitive_information": "現行の人手確認が代替案。",
        "budget_range": "1,000万円以内",
        "decision_maker": "Operations executive",
        "persona": "品質管理責任者",
        "implementation_purpose": "人の最終確認を残しながら確認時間を短縮する。",
        "problems": ["繁忙時の処理遅延", "判定基準の属人化"],
        "expected_outcomes": ["確認時間短縮", "誤分類低減", "PoC合格基準の明確化"],
        "timeline": "2027年5月頃",
    }
    deck = plan_deck(context).deck_blueprint
    result = plan_evidence(deck, context)
    raw = result.json(ensure_ascii=False)

    assert "1,000万円" in json.dumps(context, ensure_ascii=False)
    assert "2027年5月" in json.dumps(context, ensure_ascii=False)
    assert result.slide_evidence
    assert "financial_estimate" in raw


def test_evaluator_dimensions_match_phase2b_requirements() -> None:
    result = plan_evidence_from_payload(valid_evidence_planning_payloads()[2])
    dimension_names = {item.name for item in result.evaluation_result.dimensions}

    assert {
        "Evidence Completeness",
        "Evidence Quality",
        "Evidence Traceability",
        "Numeric Integrity Readiness",
        "Sales Persuasiveness",
        "Customer-facing Readiness",
    } == dimension_names


def test_prompt_contract_is_offline_and_bounded() -> None:
    contract = evidence_planner_prompt_contract()

    assert contract["llm_enabled"] is False
    assert "headline" in contract["system_prompt"].lower()
    assert "required_evidence" in contract["output_keys"]


def test_json_artifacts_exist_and_are_parseable() -> None:
    module_dir = ROOT / "app" / "presentation_engine_v2" / "evidence_planner"
    docs_dir = ROOT.parent / "docs" / "presentation-engine-v2-phase2b"
    files = [
        module_dir / "evidence_fixtures" / "valid_evidence_planning_payloads.json",
        module_dir / "evidence_fixtures" / "invalid_evidence_planning_payloads.json",
        module_dir / "evidence_golden" / "golden_evidence_planner_results.json",
        docs_dir / "evidence-planning-input.schema.json",
        docs_dir / "evidence-planner-result.schema.json",
        docs_dir / "evidence-planner-example.json",
    ]

    for path in files:
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8"))
    assert len(json.loads(files[0].read_text(encoding="utf-8"))) >= 30
    assert len(json.loads(files[2].read_text(encoding="utf-8"))) >= 20

