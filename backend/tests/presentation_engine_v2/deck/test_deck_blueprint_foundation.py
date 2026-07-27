import json
import re
from pathlib import Path

from pydantic import ValidationError

from app.presentation_engine_v2.deck_enums import (
    AudienceSeniority,
    DeckGoal,
    DeckStatus,
    DeckType,
    SectionType,
    StoryArcType,
)
from app.presentation_engine_v2.deck_evaluator import DECK_EVALUATOR_NOTE, evaluate_deck_blueprint
from app.presentation_engine_v2.deck_fixtures import (
    golden_deck_payloads,
    invalid_deck_payloads,
    valid_deck_payloads,
)
from app.presentation_engine_v2.deck_models import DeckBlueprint
from app.presentation_engine_v2.deck_normalizers import normalize_deck_blueprint_dict, normalize_deck_blueprint_payload
from app.presentation_engine_v2.deck_schema import deck_blueprint_schema, deck_slide_reference_contract
from app.presentation_engine_v2.deck_validators import validate_deck_blueprint


ROOT = Path(__file__).resolve().parents[3]


def test_deck_enums_are_lowercase_snake_case() -> None:
    enum_classes = [DeckGoal, DeckType, AudienceSeniority, StoryArcType, SectionType, DeckStatus]
    pattern = re.compile(r"^[a-z0-9_]+$")

    for enum_cls in enum_classes:
        assert enum_cls.values()
        assert all(pattern.match(value) for value in enum_cls.values())


def test_deck_blueprint_serializes_and_deserializes() -> None:
    deck = DeckBlueprint.parse_obj(valid_deck_payloads()[0])
    raw = deck.json(ensure_ascii=False)
    restored = DeckBlueprint.parse_raw(raw)

    assert restored.deck_blueprint_version == "pe2_deck_blueprint_v1"
    assert restored.deck_title == "Web制作会社向け新規サイト提案"
    assert restored.sections[0].section_type == "cover"


def test_deck_schema_contains_contract_metadata() -> None:
    schema = deck_blueprint_schema()
    ref_contract = deck_slide_reference_contract()

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "Presentation Engine 2.0 Deck Blueprint"
    assert "DeckBlueprint" in json.dumps(schema, ensure_ascii=False)
    assert ref_contract["title"] == "Deck to Slide Blueprint Reference Contract"


def test_missing_required_fields_are_rejected() -> None:
    payload = valid_deck_payloads()[0]
    payload.pop("deck_title")

    result = validate_deck_blueprint(payload)

    assert not result.valid
    assert any(issue.code == "PE2-DECK-SCHEMA-001" for issue in result.issues)


def test_invalid_enum_and_additional_property_are_rejected() -> None:
    enum_payload = {**valid_deck_payloads()[0], "deck_type": "unknown_deck"}
    extra_payload = {**valid_deck_payloads()[0], "unexpected": "not allowed"}

    assert not validate_deck_blueprint(enum_payload).valid
    with pytest_raises_validation_error():
        DeckBlueprint.parse_obj(extra_payload)


class pytest_raises_validation_error:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, _tb):
        assert exc_type is ValidationError
        return True


def test_deck_structure_rules() -> None:
    no_cover = invalid_deck_payloads()[0]
    no_next = invalid_deck_payloads()[1]
    broken_ref = invalid_deck_payloads()[5]

    assert any(issue.code == "PE2-DECK-STRUCTURE-001" for issue in validate_deck_blueprint(no_cover).issues)
    assert any(issue.code == "PE2-DECK-STRUCTURE-001" for issue in validate_deck_blueprint(no_next).issues)
    assert any(issue.code == "PE2-DECK-STRUCTURE-004" for issue in validate_deck_blueprint(broken_ref).issues)


def test_story_arc_and_audience_rules() -> None:
    price_first = invalid_deck_payloads()[2]
    executive_missing_summary = invalid_deck_payloads()[6]

    assert any(issue.code == "PE2-DECK-NARRATIVE-001" for issue in validate_deck_blueprint(price_first).issues)
    assert any(issue.code == "PE2-DECK-AUDIENCE-001" for issue in validate_deck_blueprint(executive_missing_summary).issues)


def test_placeholder_and_slide_reference_rules() -> None:
    placeholder = invalid_deck_payloads()[7]
    missing_refs = invalid_deck_payloads()[8]
    ref_mismatch = invalid_deck_payloads()[9]

    assert any(issue.code == "PE2-DECK-SAFETY-001" for issue in validate_deck_blueprint(placeholder).issues)
    assert any(issue.code == "PE2-DECK-SAFETY-002" for issue in validate_deck_blueprint(missing_refs).issues)
    assert any(issue.code == "PE2-DECK-SAFETY-002" for issue in validate_deck_blueprint(ref_mismatch).issues)


def test_normalizer_is_safe_and_deterministic() -> None:
    payload = valid_deck_payloads()[0]
    payload.pop("deck_id")
    payload.pop("target_slide_count")
    payload["deck_type"] = "Sales Proposal"
    payload["story_arc"] = "Problem Solution"
    payload["deck_title"] = "  Web制作会社向け新規サイト提案  "
    payload["key_takeaways"].append(payload["key_takeaways"][0])

    first, first_changed = normalize_deck_blueprint_dict(payload)
    second, second_changed = normalize_deck_blueprint_dict(payload)

    assert first["deck_id"] == second["deck_id"]
    assert first["deck_type"] == "sales_proposal"
    assert first["story_arc"] == "problem_solution"
    assert first["deck_title"] == "Web制作会社向け新規サイト提案"
    assert first["target_slide_count"] == len(first["slide_plan"])
    assert len(first["key_takeaways"]) == len(set(first["key_takeaways"]))
    assert first_changed == second_changed


def test_normalizer_result_contains_original_and_deck() -> None:
    payload = valid_deck_payloads()[0]
    result = normalize_deck_blueprint_payload(payload)

    assert result.original["deck_title"] == payload["deck_title"]
    assert result.deck.deck_id == payload["deck_id"]


def test_deck_evaluator_scores_readiness_on_100_point_scale() -> None:
    report = evaluate_deck_blueprint(valid_deck_payloads()[0])

    assert 0 <= report.total_score <= 100
    assert report.total_score >= 80
    assert report.grade in {"A", "B"}
    assert len(report.dimensions) == 12
    assert report.note == DECK_EVALUATOR_NOTE


def test_all_valid_and_invalid_deck_fixtures() -> None:
    valid = valid_deck_payloads()
    invalid = invalid_deck_payloads()

    assert len(valid) >= 24
    assert len(golden_deck_payloads()) >= 12
    assert len(invalid) >= 12
    assert all(validate_deck_blueprint(payload).valid for payload in valid)
    assert all(not validate_deck_blueprint(payload).valid for payload in invalid)


def test_golden_deck_json_quality() -> None:
    reports = [evaluate_deck_blueprint(payload) for payload in golden_deck_payloads()]

    assert len(reports) >= 12
    assert all(report.total_score >= 75 for report in reports)


def test_deck_contract_json_artifacts_exist_and_are_parseable() -> None:
    contract_dir = ROOT.parent / "docs" / "presentation-engine-v2-deck-contracts"
    schema_path = contract_dir / "deck-blueprint.schema.json"
    example_path = contract_dir / "deck-blueprint.example.json"
    invalid_path = contract_dir / "deck-blueprint-invalid-examples.json"
    reference_path = contract_dir / "deck-slide-reference-contract.json"

    assert schema_path.exists()
    assert example_path.exists()
    assert invalid_path.exists()
    assert reference_path.exists()
    assert json.loads(schema_path.read_text(encoding="utf-8"))["title"]
    assert validate_deck_blueprint(json.loads(example_path.read_text(encoding="utf-8"))).valid
    assert all(
        not validate_deck_blueprint(payload).valid
        for payload in json.loads(invalid_path.read_text(encoding="utf-8"))
    )


def test_deck_fixture_and_golden_json_artifacts_exist() -> None:
    module_dir = ROOT / "app" / "presentation_engine_v2"
    valid_path = module_dir / "deck_fixtures" / "valid_deck_blueprints.json"
    invalid_path = module_dir / "deck_fixtures" / "invalid_deck_blueprints.json"
    golden_path = module_dir / "deck_golden" / "golden_deck_blueprints.json"

    assert valid_path.exists()
    assert invalid_path.exists()
    assert golden_path.exists()
    assert len(json.loads(valid_path.read_text(encoding="utf-8"))) >= 24
    assert len(json.loads(golden_path.read_text(encoding="utf-8"))) >= 12


def test_japanese_unicode_dates_and_numeric_values_are_preserved() -> None:
    payload = valid_deck_payloads()[0]
    payload["deck_title"] = "2027年5月導入に向けた1,000万円以内のPoC提案"
    payload["value_proposition"] = "1,000万円以内でPoC範囲を確定し、2027年5月導入判断へ進める。"

    result = normalize_deck_blueprint_payload(payload)
    raw = result.deck.json(ensure_ascii=False)

    assert "2027年5月" in raw
    assert "1,000万円" in raw
    assert validate_deck_blueprint(result.deck).valid


def test_slide_blueprint_reference_boundary() -> None:
    deck = DeckBlueprint.parse_obj(valid_deck_payloads()[0])
    planned_ids = {slide.slide_blueprint_id for slide in deck.slide_plan}
    ref_ids = {ref.slide_blueprint_id for ref in deck.slide_blueprint_refs}

    assert planned_ids == ref_ids
    assert all(ref.embedded_slide_blueprint is None for ref in deck.slide_blueprint_refs)
