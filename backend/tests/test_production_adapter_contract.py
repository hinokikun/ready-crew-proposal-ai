from dataclasses import replace

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest
from app.services.presentation_master.approved_fixtures import FixtureKind, fixtures_for
from app.services.presentation_master.integration import (
    AdapterStatus,
    FallbackStage,
    PRODUCTION_REQUEST_MAPPING,
    build_adapter_input,
    prepare_pmv3,
    SemanticAvailability,
    inspect_production_semantic_supply,
)
from app.services.presentation_master.source_binding import SourceBindingInput, SourceIdentity, SourceOrigin
from app.services.presentation_master.upstream_adapter import DerivationLevel, SemanticGap, SemanticRelationship
from app.strategy_engine.evaluator import evaluate_strategy
from app.strategy_engine.fixtures import FIXTURES


def _payload(summary=False):
    return PptxDownloadRequest(
        powerpoint_generation_data=PowerPointData(
            deck_title="Contract test deck",
            client_name="Contract test customer",
            slides=[PowerPointSlide(slide_no=1, layout="title", title="Contract test", bullets=["Input"], speaker_notes="", visual_suggestion="")],
        ),
        project_brief="A compact contract test project summary.",
        client_company_info="Contract test customer",
        summary=summary,
    )


def _prepared(master_id, kind=FixtureKind.NORMAL_SUFFICIENT, **kwargs):
    fixture = fixtures_for(master_id, kind)
    kwargs.setdefault("semantic_envelope", fixture.envelope)
    return prepare_pmv3(build_adapter_input(_payload(), **kwargs))


def test_production_request_mapping_is_explicit_and_conservative():
    assert PRODUCTION_REQUEST_MAPPING["project_summary"].value == "DIRECT"
    assert PRODUCTION_REQUEST_MAPPING["audience"].value == "SAFE_DERIVED"
    assert PRODUCTION_REQUEST_MAPPING["kpi"] is None
    assert PRODUCTION_REQUEST_MAPPING["evidence"] is None


def test_production_semantic_supply_classifies_actual_fields_without_invention():
    supply = inspect_production_semantic_supply(_payload())
    assert supply.classification("budget") == SemanticAvailability.UNAVAILABLE
    assert supply.classification("timeline") == SemanticAvailability.UNAVAILABLE
    assert supply.classification("kpi_value") == SemanticAvailability.UNAVAILABLE
    assert supply.classification("kpi_threshold") == SemanticAvailability.UNAVAILABLE
    assert supply.classification("evidence_source_bindings") == SemanticAvailability.UNAVAILABLE

    payload = _payload()
    payload.budget_range = "10M JPY"
    payload.desired_launch_timing = "2027 Q1"
    payload.case_studies = "Synthetic case study source text"
    supply = inspect_production_semantic_supply(payload)
    assert supply.classification("budget") == SemanticAvailability.EXPLICIT_SOURCE
    assert supply.classification("timeline") == SemanticAvailability.EXPLICIT_SOURCE
    assert supply.classification("evidence_items") == SemanticAvailability.EXPLICIT_SOURCE
    assert supply.classification("evidence_source_bindings") == SemanticAvailability.UNAVAILABLE


def test_ready_preparation_representative_masters():
    for master_id in ("M47", "M49", "M52"):
        result = _prepared(master_id)
        assert result.status == AdapterStatus.READY
        assert result.selected_master_id == master_id
        assert result.renderer_spec is not None
        assert result.fallback_required is False


def test_ready_with_valid_bindings_uses_explicit_binding_without_inference():
    binding = SourceBindingInput(
        "decision-owner",
        SourceOrigin.HUMAN_INPUT,
        SourceIdentity("test", "decision-owner"),
        "decision-context",
        "decision_maker",
        raw_value="営業責任者",
        human_supplied=True,
        confidence=0.9,
    )
    result = _prepared("M47", source_bindings=(binding,))
    assert result.status == AdapterStatus.READY_WITH_VALID_BINDINGS
    assert result.fallback_required is False


def test_review_required_and_not_ready_never_force_a_master():
    fixture = fixtures_for("M48", FixtureKind.NORMAL_SUFFICIENT)
    review_envelope = replace(fixture.envelope, relationships=())
    review = _prepared("M48", semantic_envelope=review_envelope)
    assert review.status in {AdapterStatus.REVIEW_REQUIRED, AdapterStatus.NOT_READY}
    assert review.fallback_required is True
    assert review.fallback_stage in {
        FallbackStage.SEMANTIC_ADAPTER,
        FallbackStage.MASTER_SELECTION,
        FallbackStage.COMPOSITION,
    }

    absent_strategy = prepare_pmv3(_payload())
    assert absent_strategy.status == AdapterStatus.NOT_READY
    assert absent_strategy.fallback_stage == FallbackStage.SEMANTIC_ADAPTER
    assert absent_strategy.selected_master_id is None


def test_no_match_invalid_input_and_invalid_composition_are_safe():
    fixture = fixtures_for("M47", FixtureKind.NORMAL_SUFFICIENT)
    no_match_envelope = replace(fixture.envelope, semantic_signals=frozenset({"unrelated"}), items=(), groups=(), relationships=())
    no_match = prepare_pmv3(build_adapter_input(_payload(), semantic_envelope=no_match_envelope))
    assert no_match.status == AdapterStatus.NO_MATCH
    assert no_match.fallback_stage == FallbackStage.MASTER_SELECTION
    assert no_match.selected_master_id is None

    invalid = prepare_pmv3("not a production request")
    assert invalid.status == AdapterStatus.INVALID_INPUT
    assert invalid.fallback_stage == FallbackStage.INPUT_ADAPTER


def test_strategy_brief_uses_frozen_upstream_adapter_and_remains_conservative():
    brief = evaluate_strategy(FIXTURES["ai_ocr"])
    result = prepare_pmv3(_payload(), strategy_brief=brief)
    assert result.status in {AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS, AdapterStatus.REVIEW_REQUIRED, AdapterStatus.NOT_READY, AdapterStatus.NO_MATCH}
    assert result.fallback_required or result.renderer_spec is not None


def test_missing_kpi_threshold_and_evidence_binding_are_not_fabricated():
    fixture = fixtures_for("M47", FixtureKind.NORMAL_SUFFICIENT)
    result = _prepared("M47", semantic_envelope=replace(fixture.envelope, unresolved_gaps=fixture.envelope.unresolved_gaps + (
        SemanticGap("kpi_threshold_missing", "KPI threshold is not available.", ("metric", "threshold")),
        SemanticGap("evidence_binding_missing", "Evidence source binding is not available.", ("evidence", "source_binding")),
    )))
    assert result.status == AdapterStatus.REVIEW_REQUIRED
    assert result.fallback_required is True
    assert result.provenance_summary["UNRESOLVED"] >= 2


def test_resolved_relationship_clears_only_stale_review_flag():
    fixture = fixtures_for("M48", FixtureKind.NORMAL_SUFFICIENT)
    envelope = replace(fixture.envelope, relationships=())
    relationship = SemanticRelationship(
        "decision_boundary", "condition", "action", 1.0, "supplied",
        DerivationLevel.DIRECT, "explicit confirmed relationship", False,
    )
    result = prepare_pmv3(build_adapter_input(_payload(), semantic_envelope=envelope, semantic_relationships=(relationship,)))
    assert result.status in {AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS}
    assert result.selection is not None
    assert result.selection.human_review_required is False


def test_unresolved_relationship_keeps_review_required_fail_closed():
    fixture = fixtures_for("M48", FixtureKind.NORMAL_SUFFICIENT)
    envelope = replace(fixture.envelope, relationships=())
    result = prepare_pmv3(build_adapter_input(_payload(), semantic_envelope=envelope))
    assert result.status == AdapterStatus.REVIEW_REQUIRED
    assert result.fallback_stage == FallbackStage.SEMANTIC_ADAPTER
    assert result.diagnostics["unresolved_requirements"] == ("relationship:direction",)
