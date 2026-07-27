import json
from pathlib import Path

import pytest

from app.presentation_engine_v2.deck_planner import plan_deck
from app.presentation_engine_v2.evidence_planner import plan_evidence
from app.presentation_engine_v2.message_designer import design_messages
from app.presentation_engine_v2.slide_intent import (
    ChartCandidate,
    DiagramCandidate,
    SlideIntentInputError,
    SlideIntentOutput,
    SlideIntentType,
    ValidationSeverity,
    VisualPattern,
    design_slide_intents,
    design_slide_intents_from_payload,
    validate_slide_intent_design,
    validate_slide_intent_output,
)
from app.presentation_engine_v2.slide_intent.intent_fixtures import (
    invalid_slide_intent_payloads,
    valid_slide_intent_payloads,
)
from app.presentation_engine_v2.slide_intent.intent_golden import golden_slide_intent_outputs
from app.presentation_engine_v2.slide_intent.intent_schema import (
    example_output,
    input_schema,
    invalid_examples,
    output_schema,
    schema_json,
    slide_intent_schema,
)


ROOT = Path(__file__).resolve().parents[3]


def test_slide_intent_pipeline_runs_from_message_designer_output() -> None:
    payload = valid_slide_intent_payloads(limit=1)[0]
    output = design_slide_intents_from_payload(payload)

    assert output.slide_intents
    assert output.validation_result.valid
    assert output.evaluation_result.total_score >= 90
    assert output.generated_slide_blueprints is False
    assert output.generated_diagrams is False
    assert output.generated_charts is False
    assert output.generated_pptx is False
    assert output.connected_to_runtime is False


def test_slide_intent_references_match_message_designer() -> None:
    payload = valid_slide_intent_payloads(limit=1)[0]
    output = design_slide_intents_from_payload(payload)
    message_ids = {
        item["slide_blueprint_id"]
        for item in payload["message_designer_output"]["slide_messages"]
    }
    intent_ids = {item.slide_blueprint_id for item in output.slide_intents}

    assert intent_ids == message_ids
    assert [item.slide_order for item in output.slide_intents] == sorted(item.slide_order for item in output.slide_intents)


def test_visual_patterns_cover_required_cases() -> None:
    output = design_slide_intents_from_payload(valid_slide_intent_payloads(limit=1)[0])
    visual_by_type = {item.slide_type: item.visual_pattern_candidate for item in output.slide_intents}
    all_visuals = {item.visual_pattern_candidate for item in output.slide_intents}

    assert visual_by_type["cover"] == VisualPattern.HERO.value
    assert visual_by_type["executive_summary"] == VisualPattern.SUMMARY_CARDS.value
    assert visual_by_type["comparison"] == VisualPattern.COMPARISON.value
    assert VisualPattern.KPI_CARDS.value in all_visuals
    assert VisualPattern.NUMBER_DOMINANT.value in all_visuals
    assert visual_by_type["roadmap"] == VisualPattern.ROADMAP.value
    assert visual_by_type["estimate"] == VisualPattern.TABLE.value


def test_intent_types_cover_decision_and_visual_roles() -> None:
    output = design_slide_intents_from_payload(valid_slide_intent_payloads(limit=1)[0])
    intents = {item.slide_intent for item in output.slide_intents}

    assert SlideIntentType.FRAME_DECISION.value in intents
    assert SlideIntentType.COMPARE_OPTIONS.value in intents
    assert SlideIntentType.PROVE_VALUE.value in intents
    assert SlideIntentType.EXPLAIN_INVESTMENT.value in intents
    assert SlideIntentType.CLOSE_NEXT_STEP.value in intents


def test_validator_detects_chart_without_numeric_evidence() -> None:
    output = design_slide_intents_from_payload(valid_slide_intent_payloads(limit=1)[0])
    design = output.slide_intents[0].copy(deep=True)
    design.chart_candidate = ChartCandidate.BAR
    design.input_metrics.numeric_claim_count = 0
    result = validate_slide_intent_design(design)

    assert any(issue.code == "PE2-INTENT-CHART-002" for issue in result.issues)


def test_validator_detects_chart_with_missing_evidence() -> None:
    output = design_slide_intents_from_payload(valid_slide_intent_payloads(limit=1)[0])
    design = output.slide_intents[0].copy(deep=True)
    design.chart_candidate = ChartCandidate.BAR
    design.input_metrics.missing_evidence_count = 1
    result = validate_slide_intent_design(design)

    assert not result.valid
    assert any(issue.code == "PE2-INTENT-CHART-001" for issue in result.issues)


def test_validator_detects_comparison_without_basis() -> None:
    output = design_slide_intents_from_payload(valid_slide_intent_payloads(limit=1)[0])
    design = output.slide_intents[0].copy(deep=True)
    design.visual_pattern_candidate = VisualPattern.COMPARISON
    design.diagram_candidate = DiagramCandidate.COMPARISON_TABLE
    design.input_metrics.comparison_basis_present = False
    result = validate_slide_intent_design(design)

    assert not result.valid
    assert any(issue.code == "PE2-INTENT-COMPARISON-001" for issue in result.issues)


def test_validator_detects_offline_boundary_violation() -> None:
    output = design_slide_intents_from_payload(valid_slide_intent_payloads(limit=1)[0])
    mutated = output.copy(deep=True)
    mutated.generated_slide_blueprints = True
    result = validate_slide_intent_output(mutated)

    assert not result.valid
    assert any(issue.severity == ValidationSeverity.ERROR.value for issue in result.issues)


def test_invalid_payloads_are_rejected() -> None:
    invalid = invalid_slide_intent_payloads()

    assert len(invalid) >= 15
    for payload in invalid:
        with pytest.raises((SlideIntentInputError, ValueError)):
            design_slide_intents_from_payload(payload)


def test_fixture_and_golden_counts() -> None:
    assert len(valid_slide_intent_payloads()) >= 30
    assert len(golden_slide_intent_outputs()) >= 20
    for payload in golden_slide_intent_outputs()[:5]:
        output = SlideIntentOutput.parse_obj(payload)
        assert output.evaluation_result.total_score >= 90
        assert output.validation_result.valid


def test_schema_helpers_and_examples() -> None:
    assert input_schema()["title"] == "Presentation Engine 2.0 Slide Intent Input"
    assert output_schema()["title"] == "Presentation Engine 2.0 Slide Intent Output"
    assert slide_intent_schema()["title"] == "Presentation Engine 2.0 Slide Intent"
    assert example_output()["slide_intent_output_version"] == "pe2_slide_intent_output_v1"
    assert len(invalid_examples()) >= 3
    assert "slide_intent" in schema_json()


def test_deterministic_output() -> None:
    payload = valid_slide_intent_payloads(limit=4)[3]
    first = design_slide_intents_from_payload(payload)
    second = design_slide_intents_from_payload(payload)

    assert [item.intent_id for item in first.slide_intents] == [item.intent_id for item in second.slide_intents]
    assert first.evaluation_result.total_score == second.evaluation_result.total_score


def test_unicode_context_survives_slide_intent() -> None:
    context = {
        "project_id": "slide-intent-unicode",
        "project_name": "生花オークション向けAI画像認識導入支援",
        "project_summary": "花の種類、色、等級、状態をAI候補提示で確認する。",
        "industry": "生花卸売",
        "proposal_category": "AI画像認識",
        "competitive_information": "現行の人手確認が主な代替案。",
        "budget_range": "1,000万円以内",
        "decision_maker": "Operations executive",
        "persona": "品質管理責任者",
        "implementation_purpose": "人の最終確認を残しながら確認時間を短縮する。",
        "problems": ["繁忙時の処理遅延", "判定基準の属人化"],
        "expected_outcomes": ["確認時間短縮", "PoC合格基準の明確化"],
        "timeline": "2027年5月頃",
        "language": "ja",
    }
    deck = plan_deck(context).deck_blueprint
    evidence = plan_evidence(deck, context)
    message = design_messages(context, deck, evidence)
    output = design_slide_intents(context, deck, evidence, message)
    raw = output.json(ensure_ascii=False)

    assert "生花" in raw
    assert output.slide_intents
    assert output.validation_result.valid


def test_json_artifact_paths_are_supported_when_present() -> None:
    module_dir = ROOT / "app" / "presentation_engine_v2" / "slide_intent"
    files = [
        module_dir / "intent_fixtures" / "valid_slide_intent_payloads.json",
        module_dir / "intent_fixtures" / "invalid_slide_intent_payloads.json",
        module_dir / "intent_golden" / "golden_slide_intent_outputs.json",
    ]
    existing = [path for path in files if path.exists()]
    for path in existing:
        assert json.loads(path.read_text(encoding="utf-8"))
