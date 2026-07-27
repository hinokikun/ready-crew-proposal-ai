import json
from pathlib import Path

import pytest

from app.presentation_engine_v2.deck_planner import plan_deck
from app.presentation_engine_v2.deck_planner.planner_fixtures import valid_context_payloads
from app.presentation_engine_v2.evidence_planner import plan_evidence
from app.presentation_engine_v2.message_designer import (
    MessageDesignerOutput,
    SlideMessageDesign,
    design_messages,
    design_messages_from_payload,
)
from app.presentation_engine_v2.message_designer.designer import MessageDesignerInputError
from app.presentation_engine_v2.message_designer.designer_enums import (
    EvidenceAlignmentLevel,
    MessageConfidence,
    MessageStyle,
    MessageTone,
)
from app.presentation_engine_v2.message_designer.designer_errors import MessageErrorCode
from app.presentation_engine_v2.message_designer.designer_normalizers import (
    normalize_slide_message_design_dict,
    stable_fingerprint,
)
from app.presentation_engine_v2.message_designer.designer_prompt import message_designer_prompt_contract
from app.presentation_engine_v2.message_designer.designer_schema import (
    example_message_designer_output,
    invalid_slide_message_examples,
    message_designer_input_schema,
    message_designer_output_schema,
    slide_message_design_schema,
)
from app.presentation_engine_v2.message_designer.designer_validators import (
    validate_message_designer_output,
    validate_slide_message_design,
)
from app.presentation_engine_v2.message_designer.fixtures import (
    invalid_message_designer_payloads,
    valid_message_designer_payloads,
)
from app.presentation_engine_v2.message_designer.golden import golden_message_designer_outputs


ROOT = Path(__file__).resolve().parents[3]


def _first_output() -> MessageDesignerOutput:
    return design_messages_from_payload(valid_message_designer_payloads()[0])


def test_message_designer_enums_are_available() -> None:
    assert "executive" in MessageStyle.values()
    assert "consulting" in MessageStyle.values()
    assert "financial" in MessageStyle.values()
    assert "concise" in MessageTone.values()
    assert "evidence_supported" in EvidenceAlignmentLevel.values()
    assert "blocked" in MessageConfidence.values()


def test_message_designer_generates_message_contracts_only() -> None:
    result = _first_output()

    assert result.slide_messages
    assert result.generated_slide_blueprints is False
    assert result.generated_visuals is False
    assert result.generated_diagrams is False
    assert result.generated_layouts is False
    assert result.generated_pptx is False
    assert result.connected_to_runtime is False
    for message in result.slide_messages:
        assert message.headline
        assert message.main_message
        assert message.key_takeaway
        assert len(message.supporting_messages) <= 3
        assert message.generation_metadata.llm_used is False
        assert message.generation_metadata.runtime_connected is False


def test_message_designer_preserves_deck_and_evidence_references() -> None:
    payload = valid_message_designer_payloads()[1]
    result = design_messages_from_payload(payload)
    deck_ids = {item["slide_blueprint_id"] for item in payload["deck_blueprint"]["slide_plan"]}
    evidence_ids = {item["slide_blueprint_id"] for item in payload["evidence_planner_output"]["slide_evidence"]}
    message_ids = {item.slide_blueprint_id for item in result.slide_messages}

    assert deck_ids == evidence_ids == message_ids
    assert all(message.source_references for message in result.slide_messages)
    assert all(message.validation_result is not None for message in result.slide_messages)
    assert all(message.evaluation_result is not None for message in result.slide_messages)


def test_message_designer_json_roundtrip() -> None:
    result = _first_output()
    raw = result.json(ensure_ascii=False)
    restored = MessageDesignerOutput.parse_raw(raw)

    assert restored.deck_id == result.deck_id
    assert restored.slide_messages[0].message_design_id == result.slide_messages[0].message_design_id
    assert restored.evaluation_result.total_score == result.evaluation_result.total_score


def test_schema_and_examples_are_contract_compatible() -> None:
    slide_schema = slide_message_design_schema()
    input_schema = message_designer_input_schema()
    output_schema = message_designer_output_schema()
    example = example_message_designer_output()

    assert slide_schema["title"] == "Presentation Engine 2.0 Slide Message Design"
    assert input_schema["title"] == "Presentation Engine 2.0 Message Designer Input"
    assert output_schema["title"] == "Presentation Engine 2.0 Message Designer Output"
    assert example["message_designer_output_version"] == "pe2_message_designer_output_v1"
    assert example["slide_messages"]


def test_fixtures_and_invalid_payloads() -> None:
    valid_payloads = valid_message_designer_payloads()
    invalid_payloads = invalid_message_designer_payloads()

    assert len(valid_payloads) >= 30
    assert len(invalid_payloads) >= 15
    assert all(design_messages_from_payload(payload).slide_messages for payload in valid_payloads)
    for payload in invalid_payloads:
        with pytest.raises(MessageDesignerInputError):
            design_messages_from_payload(payload)


def test_golden_message_designer_outputs_are_valid() -> None:
    golden = golden_message_designer_outputs()

    assert len(golden) >= 20
    for payload in golden:
        result = MessageDesignerOutput.parse_obj(payload)
        validation = validate_message_designer_output(result)
        assert validation.valid
        assert result.evaluation_result is not None
        assert result.evaluation_result.total_score >= 70


def test_missing_numeric_evidence_is_disclosed_without_inventing_roi() -> None:
    context = next(item for item in valid_context_payloads() if item["project_id"] == "planner-fixture-knowledge-01")
    deck = plan_deck(context).deck_blueprint
    evidence = plan_evidence(deck, context)
    result = design_messages(context, deck, evidence)
    disclosed = [
        message
        for message in result.slide_messages
        if message.evidence_alignment_level == "evidence_missing"
    ]

    assert disclosed
    assert any(message.missing_evidence_disclosure for message in disclosed)
    assert all(not message.numeric_claims for message in disclosed)
    assert "120%" not in result.json(ensure_ascii=False)


def test_validators_detect_headline_support_placeholder_and_numeric_errors() -> None:
    base = _first_output().slide_messages[0]
    long_headline = base.copy(update={"headline": "x" * 61})
    duplicate_support = base.copy(update={"supporting_messages": [base.supporting_messages[0], base.supporting_messages[0]]})
    noun_only = base.copy(update={"headline": "summary"})

    assert MessageErrorCode.HEADLINE_LENGTH in {item.code for item in validate_slide_message_design(long_headline).issues}
    assert MessageErrorCode.SUPPORT_DUPLICATE in {
        item.code for item in validate_slide_message_design(duplicate_support).issues
    }
    assert MessageErrorCode.HEADLINE_NOUN_ONLY in {item.code for item in validate_slide_message_design(noun_only).issues}
    assert validate_slide_message_design({}).valid is False

    invalid_examples = invalid_slide_message_examples()
    assert any(MessageErrorCode.PLACEHOLDER in {item.code for item in validate_slide_message_design(example).issues} for example in invalid_examples)
    assert any(
        MessageErrorCode.NUMERIC_UNSUPPORTED in {item.code for item in validate_slide_message_design(example).issues}
        for example in invalid_examples
    )


def test_normalizer_dedupes_support_messages_and_keeps_fingerprint_stable() -> None:
    base = _first_output().slide_messages[0].dict()
    base["supporting_messages"] = [base["supporting_messages"][0], base["supporting_messages"][0]]
    base["message_style"] = "Executive"
    normalized, changed = normalize_slide_message_design_dict(base)

    assert len(normalized["supporting_messages"]) == 1
    assert normalized["message_style"] == "executive"
    assert "supporting_messages" in changed
    assert stable_fingerprint(normalized) == stable_fingerprint(json.loads(json.dumps(normalized, ensure_ascii=False)))


def test_deterministic_id_and_fingerprint_are_stable() -> None:
    payload = valid_message_designer_payloads()[2]
    first = design_messages_from_payload(payload)
    second = design_messages_from_payload(payload)

    assert [item.message_design_id for item in first.slide_messages] == [
        item.message_design_id for item in second.slide_messages
    ]
    assert [item.input_fingerprint for item in first.slide_messages] == [
        item.input_fingerprint for item in second.slide_messages
    ]


def test_unicode_numeric_and_date_values_survive_message_design() -> None:
    context = {
        "project_id": "phase2c-unicode",
        "project_name": "生花オークション向けAI画像認識導入支援",
        "project_summary": "2027年5月導入想定。予算上限は1,000万円。画像認識で花の種類・色・等級を確認する。",
        "industry": "生花卸売",
        "proposal_category": "AI画像認識",
        "competitive_information": "現行の人手確認が代替案。",
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
    result = design_messages(context, deck, evidence)
    raw = result.json(ensure_ascii=False)

    assert "生花" in raw
    assert "1,000万円以内" in raw
    assert result.slide_messages


def test_prompt_contract_is_offline_and_bounded() -> None:
    contract = message_designer_prompt_contract()

    assert contract["llm_enabled"] is False
    assert contract["temperature"] == 0
    assert "headline" in contract["output_keys"]
    assert "slide_blueprint" in contract["forbidden_output_keys"]


def test_json_artifacts_exist_and_are_parseable() -> None:
    module_dir = ROOT / "app" / "presentation_engine_v2" / "message_designer"
    docs_dir = ROOT.parent / "docs" / "presentation-engine-v2-message-contracts"
    files = [
        module_dir / "fixtures" / "valid_message_designer_payloads.json",
        module_dir / "fixtures" / "invalid_message_designer_payloads.json",
        module_dir / "golden" / "golden_message_designer_outputs.json",
        docs_dir / "slide-message-design.schema.json",
        docs_dir / "message-designer-input.schema.json",
        docs_dir / "message-designer-output.schema.json",
        docs_dir / "slide-message-design.example.json",
        docs_dir / "message-designer-output.example.json",
        docs_dir / "slide-message-design-invalid-examples.json",
    ]

    for path in files:
        assert path.exists()
        assert json.loads(path.read_text(encoding="utf-8"))
    assert len(json.loads(files[0].read_text(encoding="utf-8"))) >= 30
    assert len(json.loads(files[2].read_text(encoding="utf-8"))) >= 20


def test_phase2a_phase2b_phase2c_integration_stays_deck_blueprint_only_until_message_design() -> None:
    context = valid_context_payloads()[3]
    deck = plan_deck(context).deck_blueprint
    evidence = plan_evidence(deck, context)
    result = design_messages(context, deck, evidence)

    assert len(result.slide_messages) == len(deck.slide_plan)
    assert evidence.generated_slide_blueprints is False
    assert result.generated_slide_blueprints is False
    assert result.generated_pptx is False
    assert all(isinstance(message, SlideMessageDesign) for message in result.slide_messages)
