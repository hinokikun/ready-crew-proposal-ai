import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.presentation_engine_v2.contracts import LIMITS
from app.presentation_engine_v2.enums import (
    AudienceType,
    BlueprintStatus,
    DiagramType,
    SlideGoal,
    SlideType,
    ThemeType,
    ValidationSeverity,
    VisualType,
)
from app.presentation_engine_v2.evaluator import EVALUATOR_NOTE, evaluate_blueprint
from app.presentation_engine_v2.fixtures import (
    golden_payloads,
    invalid_fixture_payloads,
    valid_fixture_payloads,
)
from app.presentation_engine_v2.models import SlideBlueprint
from app.presentation_engine_v2.normalizers import normalize_blueprint_dict, normalize_blueprint_payload
from app.presentation_engine_v2.schema import example_blueprint_payload, invalid_blueprint_payloads, slide_blueprint_schema
from app.presentation_engine_v2.validators import validate_blueprint


ROOT = Path(__file__).resolve().parents[2]


def test_required_enums_are_lowercase_snake_case() -> None:
    enum_classes = [
        SlideGoal,
        AudienceType,
        SlideType,
        VisualType,
        DiagramType,
        ThemeType,
        BlueprintStatus,
        ValidationSeverity,
    ]
    pattern = re.compile(r"^[a-z0-9_]+$")

    for enum_cls in enum_classes:
        assert enum_cls.values()
        assert all(pattern.match(value) for value in enum_cls.values())


def test_model_serializes_and_deserializes_json() -> None:
    blueprint = SlideBlueprint.parse_obj(example_blueprint_payload())
    raw = blueprint.json(ensure_ascii=False)
    restored = SlideBlueprint.parse_raw(raw)

    assert restored.blueprint_version == "pe2_slide_blueprint_v1"
    assert restored.headline.startswith("AI候補提示")
    assert restored.visual_type == "two_column"


def test_json_schema_contains_required_contract_metadata() -> None:
    schema = slide_blueprint_schema()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "Presentation Engine 2.0 Slide Blueprint"
    assert "definitions" in schema
    assert "SlideGoal" in json.dumps(schema, ensure_ascii=False)


def test_required_fields_are_rejected() -> None:
    payload = example_blueprint_payload()
    payload.pop("headline")

    result = validate_blueprint(payload)

    assert not result.valid
    assert any(issue.code == "PE2-SCHEMA-001" for issue in result.issues)


def test_invalid_enum_is_rejected() -> None:
    payload = {**example_blueprint_payload(), "visual_type": "unknown_visual"}

    result = validate_blueprint(payload)

    assert not result.valid
    assert any(issue.code == "PE2-SCHEMA-002" for issue in result.issues)


def test_string_length_and_array_limits_are_enforced() -> None:
    payload = example_blueprint_payload()
    payload["headline"] = "長" * (LIMITS["headline_chars"] + 1)

    result = validate_blueprint(payload)

    assert not result.valid
    assert any(issue.code == "PE2-SCHEMA-003" for issue in result.issues)

    too_many_blocks = example_blueprint_payload()
    too_many_blocks["content_blocks"] = [
        {"block_id": f"b{i}", "role": "body", "text": "説明"} for i in range(20)
    ]
    with pytest.raises(ValidationError):
        SlideBlueprint.parse_obj(too_many_blocks)


def test_visual_consistency_rules() -> None:
    mismatch = {**example_blueprint_payload(), "visual_type": "timeline", "diagram_type": "risk_matrix"}
    comparison_missing = {**example_blueprint_payload(), "slide_goal": "comparison", "comparison_items": []}
    matrix_missing_axes = {
        **example_blueprint_payload(),
        "visual_type": "matrix_2x2",
        "diagram_type": "matrix_2x2",
        "diagram_definition": {
            **example_blueprint_payload()["diagram_definition"],
            "diagram_type": "matrix_2x2",
            "axes": [],
        },
    }

    assert not validate_blueprint(mismatch).valid
    assert not validate_blueprint(comparison_missing).valid
    assert not validate_blueprint(matrix_missing_axes).valid


def test_placeholder_duplicate_and_cta_rules() -> None:
    placeholder = {**example_blueprint_payload(), "headline": "Metric 1"}
    duplicate = example_blueprint_payload()
    duplicate["content_blocks"] = [
        {"block_id": "dup", "role": "body", "text": "説明1"},
        {"block_id": "dup", "role": "body", "text": "説明2"},
    ]
    cta_missing = {
        **example_blueprint_payload(),
        "slide_goal": "next_action",
        "slide_type": "next_action",
        "visual_type": "closing",
        "diagram_type": "none",
        "cta": {"cta_type": "none"},
    }

    assert any(issue.code == "PE2-MESSAGE-002" for issue in validate_blueprint(placeholder).issues)
    assert any(issue.code == "PE2-SCHEMA-004" for issue in validate_blueprint(duplicate).issues)
    assert any(issue.code == "PE2-QUALITY-002" for issue in validate_blueprint(cta_missing).issues)


def test_normalizer_is_safe_and_deterministic() -> None:
    payload = example_blueprint_payload()
    payload.pop("blueprint_id")
    payload.pop("slide_id")
    payload["visual_type"] = "Two Column"
    payload["theme"] = "Consulting"
    payload["color_palette"]["primary"] = "2563eb"
    payload["supporting_messages"].append(payload["supporting_messages"][0])
    payload["headline"] = "  AI候補提示で確認作業を改善する  "

    first, first_changed = normalize_blueprint_dict(payload)
    second, second_changed = normalize_blueprint_dict(payload)

    assert first["blueprint_id"] == second["blueprint_id"]
    assert first["slide_id"] == second["slide_id"]
    assert first["visual_type"] == "two_column"
    assert first["theme"] == "consulting"
    assert first["color_palette"]["primary"] == "#2563EB"
    assert first["headline"] == "AI候補提示で確認作業を改善する"
    assert len(first["supporting_messages"]) == len(set(first["supporting_messages"]))
    assert first_changed == second_changed


def test_normalizer_result_contains_original_and_blueprint() -> None:
    result = normalize_blueprint_payload(example_blueprint_payload())

    assert result.original["headline"] == example_blueprint_payload()["headline"]
    assert result.blueprint.slide_id == "slide-before-after"


def test_offline_evaluator_scores_blueprint_readiness() -> None:
    report = evaluate_blueprint(example_blueprint_payload())

    assert report.total_score >= 80
    assert report.grade in {"A", "B"}
    assert len(report.items) == 10
    assert report.note == EVALUATOR_NOTE
    assert "PowerPoint" in report.note


def test_all_valid_fixtures_pass_and_invalid_fixtures_fail() -> None:
    valid = valid_fixture_payloads()
    invalid = invalid_fixture_payloads()

    assert len(valid) >= 20
    assert len(golden_payloads()) >= 10
    assert len(invalid) >= 7
    assert all(validate_blueprint(payload).valid for payload in valid)
    assert all(not validate_blueprint(payload).valid for payload in invalid)


def test_golden_json_payloads_are_high_quality() -> None:
    reports = [evaluate_blueprint(payload) for payload in golden_payloads()]

    assert len(reports) >= 10
    assert all(report.total_score >= 75 for report in reports)


def test_contract_json_artifacts_exist_and_are_parseable() -> None:
    contract_dir = ROOT.parent / "docs" / "presentation-engine-v2-contracts"
    schema_path = contract_dir / "slide-blueprint.schema.json"
    example_path = contract_dir / "slide-blueprint.example.json"
    invalid_path = contract_dir / "slide-blueprint-invalid-examples.json"

    assert schema_path.exists()
    assert example_path.exists()
    assert invalid_path.exists()
    assert json.loads(schema_path.read_text(encoding="utf-8"))["title"]
    assert validate_blueprint(json.loads(example_path.read_text(encoding="utf-8"))).valid
    assert all(
        not validate_blueprint(payload).valid
        for payload in json.loads(invalid_path.read_text(encoding="utf-8"))
    )


def test_fixture_and_golden_json_artifacts_exist() -> None:
    module_dir = ROOT / "app" / "presentation_engine_v2"
    valid_path = module_dir / "fixtures" / "valid_slide_blueprints.json"
    invalid_path = module_dir / "fixtures" / "invalid_slide_blueprints.json"
    golden_path = module_dir / "golden" / "golden_slide_blueprints.json"

    assert valid_path.exists()
    assert invalid_path.exists()
    assert golden_path.exists()
    assert len(json.loads(valid_path.read_text(encoding="utf-8"))) >= 20
    assert len(json.loads(golden_path.read_text(encoding="utf-8"))) >= 10


def test_japanese_unicode_dates_and_numeric_values_are_preserved() -> None:
    payload = example_blueprint_payload()
    payload["headline"] = "2027年5月導入に向けて1,000万円以内でPoCを設計する"
    payload["metrics"] = [
        {"metric_id": "m-budget", "label": "予算上限", "value": "1,000万円", "confidence": "high"}
    ]

    result = normalize_blueprint_payload(payload)
    raw = result.blueprint.json(ensure_ascii=False)

    assert "2027年5月" in raw
    assert "1,000万円" in raw
    assert validate_blueprint(result.blueprint).valid


def test_additional_properties_are_rejected() -> None:
    payload = {**example_blueprint_payload(), "unexpected": "not allowed"}

    assert not validate_blueprint(payload).valid
