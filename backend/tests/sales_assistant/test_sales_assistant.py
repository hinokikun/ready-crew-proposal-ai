import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.sales_assistant.evaluator import evaluate_sales_assistant_brief
from app.sales_assistant.fixtures import build_sales_assistant_input, fixture_names
from app.sales_assistant.generator import GUARDED_SECTION_KEYS, brief_to_canonical_json, generate_sales_assistant_brief
from app.sales_assistant.models import SalesAssistantInput
from app.strategy_engine.term_guard import find_prohibited_terms

GOLDEN_PATH = Path(__file__).parent / "golden" / "expected_sales_assistant_briefs.json"


def _load_golden():
    return json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))


def _guarded_text(brief):
    data = brief.dict()
    return json.dumps([data[key] for key in GUARDED_SECTION_KEYS], ensure_ascii=False)


def test_fixture_count_is_at_least_twenty():
    assert len(fixture_names()) >= 20


@pytest.mark.parametrize("name", fixture_names())
def test_golden_sales_assistant_brief(name):
    value = build_sales_assistant_input(name)
    brief = generate_sales_assistant_brief(value)
    assert brief.dict() == _load_golden()[name]


@pytest.mark.parametrize("name", ["ai_adoption", "image_recognition", "web_creation", "chatbot"])
def test_contract_has_required_sections(name):
    brief = generate_sales_assistant_brief(build_sales_assistant_input(name))
    data = brief.dict()
    for key in [
        "summary",
        "meeting_plan",
        "discovery_questions",
        "talk_track",
        "objection_handling",
        "decision_maker_support",
        "evidence_guidance",
        "next_actions",
        "follow_up",
        "risk_and_guardrails",
        "generation_metadata",
    ]:
        assert data[key]
    assert {"sales_objective", "recommended_positioning", "primary_message"}.issubset(data["summary"])
    assert {"recommended_duration_minutes", "desired_outcome", "next_step_goal"}.issubset(data["meeting_plan"])
    assert {"opening_talk", "budget_talk", "schedule_talk", "closing_talk"}.issubset(data["talk_track"])
    assert {"email_subject", "meeting_summary_template", "requested_client_actions"}.issubset(data["follow_up"])
    assert {"allowed_terms", "conditional_terms", "unsupported_claims", "compliance_notes"}.issubset(
        data["risk_and_guardrails"]
    )
    assert {"strategy_brief_version", "fallback_reasons"}.issubset(data["generation_metadata"])


def test_missing_input_sets_review_and_confirmation_items():
    brief = generate_sales_assistant_brief(build_sales_assistant_input("low_confidence"))
    assert brief.summary.human_review_required is True
    assert brief.evidence_guidance.evidence_gaps
    assert "confirmation" in brief.follow_up.email_body.lower()


def test_invalid_enum_is_rejected():
    value = build_sales_assistant_input("image_recognition").dict()
    value["meeting_stage"] = "not_valid"
    with pytest.raises(ValidationError):
        SalesAssistantInput(**value)


@pytest.mark.parametrize("name", ["image_recognition", "human_review_required", "multi_persona"])
def test_strategy_brief_alignment(name):
    value = build_sales_assistant_input(name)
    brief = generate_sales_assistant_brief(value)
    assert brief.summary.category == value.strategy_brief.project_category
    assert brief.summary.strategy == value.strategy_brief.primary_strategy
    assert brief.summary.story == value.strategy_brief.story_type
    assert any(f"strategy:{value.strategy_brief.primary_strategy}" == rule for rule in brief.generation_metadata.selected_rules)


def test_persona_and_decision_maker_variants_are_reflected():
    executive = generate_sales_assistant_brief(build_sales_assistant_input("ai_adoption"))
    field = generate_sales_assistant_brief(build_sales_assistant_input("field_persona"))
    assert executive.summary.persona != field.summary.persona or executive.decision_maker_support.decision_points != field.decision_maker_support.decision_points
    assert executive.decision_maker_support.decision_points
    assert field.decision_maker_support.decision_points


def test_objections_and_questions_are_generated():
    brief = generate_sales_assistant_brief(build_sales_assistant_input("multi_persona"))
    assert len(brief.discovery_questions) >= 3
    assert {item.objection_type for item in brief.objection_handling}.issuperset({"price", "schedule", "effectiveness"})


def test_follow_up_email_is_generated_without_external_delivery():
    brief = generate_sales_assistant_brief(build_sales_assistant_input("image_recognition"))
    assert brief.follow_up.subject
    assert "Next actions" in brief.follow_up.email_body
    assert "API key" not in brief.follow_up.email_body
    assert "token" not in brief.follow_up.email_body.lower()


def test_term_guard_replaces_guarded_output_terms_and_requires_review():
    value = build_sales_assistant_input("prohibited_term_input")
    brief = generate_sales_assistant_brief(value)
    guarded_text = _guarded_text(brief)
    assert find_prohibited_terms(guarded_text, value.strategy_brief.prohibited_terms) == []
    assert brief.summary.human_review_required is True
    assert brief.risk_and_guardrails.removed_or_replaced_terms
    assert value.strategy_brief.prohibited_terms == brief.risk_and_guardrails.prohibited_terms


def test_confidence_and_evidence_shortage_prevent_assertive_claims():
    brief = generate_sales_assistant_brief(build_sales_assistant_input("evidence_shortage"))
    text = json.dumps(brief.dict(), ensure_ascii=False).lower()
    assert "guaranteed roi" not in text
    assert "100%" not in text
    assert brief.evidence_guidance.evidence_gaps
    assert brief.summary.human_review_required is True


def test_evaluator_passes_valid_fixture():
    value = build_sales_assistant_input("image_recognition")
    brief = generate_sales_assistant_brief(value)
    report = evaluate_sales_assistant_brief(value, brief)
    assert report.passed is True
    assert report.overall_score >= 90


def test_evaluator_detects_unsupported_claim():
    value = build_sales_assistant_input("image_recognition")
    brief = generate_sales_assistant_brief(value)
    mutated = brief.copy(deep=True)
    mutated.talk_track.closing_message = "This will definitely deliver guaranteed ROI with no risk."
    report = evaluate_sales_assistant_brief(value, mutated)
    assert report.passed is False
    assert report.unsupported_claim_count >= 2


@pytest.mark.parametrize("name", fixture_names())
def test_deterministic_generation(name):
    value = build_sales_assistant_input(name)
    first = generate_sales_assistant_brief(value)
    second = generate_sales_assistant_brief(value)
    assert brief_to_canonical_json(first) == brief_to_canonical_json(second)
