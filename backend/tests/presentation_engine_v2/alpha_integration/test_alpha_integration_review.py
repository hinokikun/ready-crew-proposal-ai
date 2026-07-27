import json
from pathlib import Path

import pytest

from app.presentation_engine_v2.alpha_integration import (
    AlphaIntegrationOutput,
    cross_case_markdown,
    human_review_markdown,
    improvement_backlog_markdown,
    run_alpha_integration,
)
from app.presentation_engine_v2.alpha_integration.fixtures import (
    invalid_alpha_integration_cases,
    valid_alpha_integration_cases,
)
from app.presentation_engine_v2.alpha_integration.golden import golden_alpha_integration_outputs
from app.presentation_engine_v2.alpha_integration.pipeline import AlphaPipelineInputError
from app.presentation_engine_v2.alpha_integration.pipeline_models import (
    AlphaIntegrationCase,
    AlphaIssueCode,
    AlphaValidationSeverity,
    Phase2DReadinessStatus,
)
from app.presentation_engine_v2.alpha_integration.pipeline_schema import (
    cross_module_validation_schema,
    example_output,
    integration_case_input_schema,
    integration_case_output_schema,
    integration_evaluation_schema,
    invalid_examples,
    phase2d_readiness_schema,
)
from app.presentation_engine_v2.alpha_integration.pipeline_validators import validate_cross_module
from app.presentation_engine_v2.deck_planner import plan_deck
from app.presentation_engine_v2.evidence_planner import plan_evidence
from app.presentation_engine_v2.message_designer import design_messages


ROOT = Path(__file__).resolve().parents[3]


def test_alpha_pipeline_runs_from_proposal_context_to_message_designer() -> None:
    case = valid_alpha_integration_cases()[0]
    output = run_alpha_integration(case)

    assert output.deck_planner_result.deck_blueprint.slide_plan
    assert output.evidence_planner_result.slide_evidence
    assert output.message_designer_result.slide_messages
    assert len(output.deck_planner_result.deck_blueprint.slide_plan) == len(output.message_designer_result.slide_messages)
    assert output.generated_pptx is False
    assert output.connected_to_runtime is False
    assert output.generated_slide_blueprints is False
    assert output.used_external_ai is False


def test_cross_module_references_are_aligned_for_valid_case() -> None:
    output = run_alpha_integration(valid_alpha_integration_cases()[1])

    deck_ids = {item.slide_blueprint_id for item in output.deck_planner_result.deck_blueprint.slide_plan}
    evidence_ids = {item.slide_blueprint_id for item in output.evidence_planner_result.slide_evidence}
    message_ids = {item.slide_blueprint_id for item in output.message_designer_result.slide_messages}

    assert deck_ids == evidence_ids == message_ids
    assert output.cross_module_validation_result.valid
    assert not output.blocking_issues


def test_evidence_missing_is_disclosed_and_carried_to_review() -> None:
    case = next(item for item in valid_alpha_integration_cases() if item.proposal_context.project_id == "planner-fixture-knowledge-01")
    output = run_alpha_integration(case)
    markdown = human_review_markdown(output)

    assert output.warnings
    assert "Missing Evidence" in markdown
    assert any(message.missing_evidence_disclosure for message in output.message_designer_result.slide_messages)
    assert output.phase2d_readiness in {
        Phase2DReadinessStatus.READY,
        Phase2DReadinessStatus.READY_WITH_LIMITATIONS,
    }


def test_pipeline_evaluator_has_16_dimensions_and_readiness() -> None:
    output = run_alpha_integration(valid_alpha_integration_cases()[2])
    names = {item.name for item in output.pipeline_evaluation_result.dimensions}

    assert len(output.pipeline_evaluation_result.dimensions) == 16
    assert "Contract Integrity" in names
    assert "Evidence and Message Alignment" in names
    assert "Phase 2D Readiness" in names
    assert output.pipeline_evaluation_result.overall_score >= 70
    assert output.phase2d_readiness in Phase2DReadinessStatus.values()


def test_invalid_cases_fail_schema_or_pipeline_input() -> None:
    invalid = invalid_alpha_integration_cases()

    assert len(invalid) >= 15
    for payload in invalid:
        with pytest.raises((AlphaPipelineInputError, ValueError)):
            run_alpha_integration(payload)


def test_golden_alpha_outputs_are_parseable_and_human_readable() -> None:
    golden = golden_alpha_integration_outputs()

    assert len(golden) >= 10
    for payload in golden:
        output = AlphaIntegrationOutput.parse_obj(payload)
        assert output.pipeline_evaluation_result.overall_score >= 70
        assert output.human_review_summary.headline_summary
        assert "# Alpha Integration Case Review" in human_review_markdown(output)


def test_schema_helpers_and_examples() -> None:
    assert integration_case_input_schema()["title"] == "Presentation Engine 2.0 Alpha Integration Case Input"
    assert integration_case_output_schema()["title"] == "Presentation Engine 2.0 Alpha Integration Case Output"
    assert integration_evaluation_schema()["title"] == "Presentation Engine 2.0 Alpha Integration Evaluation"
    assert cross_module_validation_schema()["title"] == "Presentation Engine 2.0 Cross Module Validation"
    assert "READY" in phase2d_readiness_schema()["enum"]
    assert example_output()["integration_output_version"] == "pe2_alpha_integration_output_v1"
    assert len(invalid_examples()) >= 3


def test_cross_module_validator_detects_broken_message_slide_reference() -> None:
    case = valid_alpha_integration_cases()[0]
    deck = plan_deck(case.proposal_context).deck_blueprint
    evidence = plan_evidence(deck, case.proposal_context)
    message = design_messages(case.proposal_context, deck, evidence)
    broken = message.copy(deep=True)
    broken.slide_messages = broken.slide_messages[1:]
    result = validate_cross_module(
        case_id=case.integration_case_id,
        context=case.proposal_context,
        deck=deck,
        evidence=evidence,
        message=broken,
    )

    assert not result.valid
    assert any(issue.code == AlphaIssueCode.REFERENCE for issue in result.issues)
    assert any(issue.severity == AlphaValidationSeverity.ERROR.value for issue in result.issues)


def test_cross_module_validator_detects_unsupported_numeric_claim() -> None:
    case = valid_alpha_integration_cases()[0]
    deck = plan_deck(case.proposal_context).deck_blueprint
    evidence = plan_evidence(deck, case.proposal_context)
    message = design_messages(case.proposal_context, deck, evidence)
    broken = message.copy(deep=True)
    numeric_slide = next((item for item in broken.slide_messages if item.numeric_claims), None)
    if numeric_slide is None:
        pytest.skip("Fixture has no numeric claim.")
    numeric_slide.numeric_claims[0].basis_evidence_ids = []
    result = validate_cross_module(
        case_id=case.integration_case_id,
        context=case.proposal_context,
        deck=deck,
        evidence=evidence,
        message=broken,
    )

    assert any(issue.code == AlphaIssueCode.SAFETY for issue in result.issues)


def test_reporters_generate_cross_case_and_backlog_markdown() -> None:
    outputs = [run_alpha_integration(case) for case in valid_alpha_integration_cases()[:5]]

    cross = cross_case_markdown(outputs)
    backlog = improvement_backlog_markdown(outputs)

    assert "# Alpha Integration Cross-case Quality Report" in cross
    assert "Average Score" in cross
    assert "# Alpha Integration Improvement Backlog" in backlog
    assert "P0 Blocker" in backlog


def test_alpha_pipeline_is_deterministic() -> None:
    case = valid_alpha_integration_cases()[3]
    first = run_alpha_integration(case)
    second = run_alpha_integration(case)

    assert first.input_fingerprint == second.input_fingerprint
    assert first.pipeline_evaluation_result.overall_score == second.pipeline_evaluation_result.overall_score
    assert [m.message_design_id for m in first.message_designer_result.slide_messages] == [
        m.message_design_id for m in second.message_designer_result.slide_messages
    ]


def test_unicode_japanese_context_survives_alpha_pipeline() -> None:
    base = valid_alpha_integration_cases()[0].dict()
    base["integration_case_id"] = "alpha-unicode"
    base["case_name"] = "生花AI画像認識・統合レビュー"
    base["proposal_context"] = {
        "project_id": "alpha-unicode-project",
        "project_name": "生花オークション向けAI画像認識導入支援",
        "project_summary": "2027年5月導入想定。予算上限は1,000万円。花の種類・色・等級・状態をAI候補提示で確認する。",
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
    output = run_alpha_integration(AlphaIntegrationCase.parse_obj(base))
    raw = output.json(ensure_ascii=False)

    assert "生花" in raw
    assert "1,000万円以内" in raw
    assert output.message_designer_result.slide_messages


def test_json_artifacts_exist_and_are_parseable() -> None:
    module_dir = ROOT / "app" / "presentation_engine_v2" / "alpha_integration"
    docs_dir = ROOT.parent / "docs" / "presentation-engine-v2-alpha-integration"
    files = [
        module_dir / "fixtures" / "valid_alpha_integration_cases.json",
        module_dir / "fixtures" / "invalid_alpha_integration_cases.json",
        module_dir / "golden" / "golden_alpha_integration_outputs.json",
        docs_dir / "contracts" / "integration-case-input.schema.json",
        docs_dir / "contracts" / "integration-case-output.schema.json",
        docs_dir / "contracts" / "integration-evaluation.schema.json",
        docs_dir / "contracts" / "cross-module-validation.schema.json",
        docs_dir / "contracts" / "phase2d-readiness.schema.json",
        docs_dir / "contracts" / "example.json",
        docs_dir / "contracts" / "invalid-examples.json",
        docs_dir / "cross-case-summary.json",
    ]

    for path in files:
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8"))
    assert len(json.loads(files[0].read_text(encoding="utf-8"))) >= 20
    assert len(json.loads(files[2].read_text(encoding="utf-8"))) >= 10
