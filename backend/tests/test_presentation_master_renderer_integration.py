"""Offline Composition -> Renderer Integration Contract tests."""

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services.presentation_master.integration import AdapterStatus
from app.services.presentation_master.approved_fixtures import APPROVED_SEMANTIC_FIXTURES, FixtureKind, fixtures_for
from app.services.presentation_master.composition import build_composition_for_master
from app.services.presentation_master.definitions import MASTER_REGISTRY
from app.services.presentation_master.renderer_integration import (
    IntegrationState,
    RelationshipSupport,
    build_renderer_integration_spec,
    relationship_support,
)
from app.services.presentation_master.upstream_adapter import composition_items_for_master


def _composition(master_id="M47"):
    fixture = fixtures_for(master_id, FixtureKind.NORMAL_SUFFICIENT)
    items = composition_items_for_master(fixture.envelope, master_id)
    return build_composition_for_master(master_id, items)


@pytest.mark.parametrize("master_id", [f"M{i}" for i in range(45, 55)])
def test_all_approved_normal_compositions_map_to_renderer_spec(master_id):
    outcome = _composition(master_id)
    assert outcome.composition is not None
    spec = build_renderer_integration_spec(outcome.composition, MASTER_REGISTRY.get(master_id))
    assert spec.master_id == master_id
    assert spec.integration_state in {IntegrationState.VALID, IntegrationState.DEGRADED}
    assert spec.validation_issues == ()
    assert sum(len(page.objects) for page in spec.pages) == len(outcome.composition.bound_slots)


def test_item_group_role_hierarchy_order_and_evidence_are_preserved():
    outcome = _composition("M47")
    spec = build_renderer_integration_spec(outcome.composition, MASTER_REGISTRY.get("M47"))
    composition_ids = {item.input_item_id for item in outcome.composition.bound_slots}
    renderer_ids = {item.semantic_item_id for page in spec.pages for item in page.objects}
    assert renderer_ids == composition_ids
    assert all(item.group_id and item.semantic_role and item.slot_id for page in spec.pages for item in page.objects)
    assert [page.group_id for page in spec.pages] == list(MASTER_REGISTRY.get("M47").reading_order)
    evidence_objects = [item for page in spec.pages for item in page.objects if item.content_type == "evidence"]
    assert evidence_objects
    assert all(item.primitive_type == "evidence_object" for item in evidence_objects)
    assert all(item.provenance_state and item.evidence_state for page in spec.pages for item in page.objects)


def test_relationship_types_and_direction_are_preserved_or_explicitly_degraded():
    expected = {
        "sequence": ("sequence", RelationshipSupport.SUPPORTED_WITH_EXISTING_PRIMITIVES),
        "causality": ("cause", RelationshipSupport.SUPPORTED_WITH_EXISTING_PRIMITIVES),
        "dependency": ("dependency", RelationshipSupport.SUPPORTED_WITH_EXISTING_PRIMITIVES),
        "convergence": ("convergence", RelationshipSupport.SUPPORTED_WITH_EXISTING_PRIMITIVES),
        "decision_boundary": ("boundary", RelationshipSupport.SUPPORTED_WITH_EXISTING_PRIMITIVES),
        "hierarchy": (None, RelationshipSupport.DEGRADED_BUT_SEMANTICALLY_VISIBLE),
        "feedback": (None, RelationshipSupport.DEGRADED_BUT_SEMANTICALLY_VISIBLE),
        "handoff": (None, RelationshipSupport.DEGRADED_BUT_SEMANTICALLY_VISIBLE),
    }
    for semantic_type, expected_result in expected.items():
        assert relationship_support(semantic_type) == expected_result
    outcome = _composition("M49")
    spec = build_renderer_integration_spec(outcome.composition, MASTER_REGISTRY.get("M49"))
    assert {item.semantic_type for item in spec.relationships} == {item.relationship_type for item in outcome.composition.relationships}
    assert all(item.from_ref and item.to_ref for item in spec.relationships)


def test_decision_boundary_review_and_degraded_states_remain_explicit():
    outcome = _composition("M49")
    reviewed = replace(outcome.composition, state="REVIEW_REQUIRED", human_review_required=True)
    spec = build_renderer_integration_spec(reviewed, MASTER_REGISTRY.get("M49"))
    assert spec.integration_state == IntegrationState.REVIEW_REQUIRED
    assert spec.review_required is True

    degraded = replace(outcome.composition, state="DEGRADED", degradation_reasons=("optional relationship omitted",))
    degraded_spec = build_renderer_integration_spec(degraded, MASTER_REGISTRY.get("M49"))
    assert degraded_spec.integration_state == IntegrationState.DEGRADED


def test_invalid_composition_and_master_mismatch_are_rejected():
    outcome = _composition("M47")
    invalid = replace(outcome.composition, state="INVALID")
    spec = build_renderer_integration_spec(invalid, MASTER_REGISTRY.get("M47"))
    assert spec.integration_state == IntegrationState.INVALID
    assert spec.validation_issues
    mismatch = build_renderer_integration_spec(outcome.composition, MASTER_REGISTRY.get("M48"))
    assert mismatch.integration_state == IntegrationState.INVALID
    assert "composition/definition master mismatch" in mismatch.validation_issues


def test_cardinality_is_not_changed_and_no_anonymous_objects_are_created():
    outcome = _composition("M52")
    spec = build_renderer_integration_spec(outcome.composition, MASTER_REGISTRY.get("M52"))
    assert sum(len(page.objects) for page in spec.pages) == len(outcome.composition.bound_slots)
    assert all(item.semantic_item_id == item.object_id for page in spec.pages for item in page.objects)


def test_generic_five_page_renderer_assumption_is_adapter_required_not_semantic_invention():
    renderer_source = Path("backend/app/services/presentation_master/renderer_mvp.py").read_text(encoding="utf-8")
    assert '"p01"' in renderer_source and '"p05"' in renderer_source
    assert "ProposalToRendererMvpAdapter" in renderer_source
    assert len(APPROVED_SEMANTIC_FIXTURES) == 30


def test_integration_adapter_is_renderer_facing_only_and_does_not_import_production():
    source = Path(__import__("app.services.presentation_master.renderer_integration", fromlist=["__file__"]).__file__).read_text(encoding="utf-8").lower()
    assert "strategybrief" not in source
    assert "pptx" not in source
    assert "production" not in source


def test_primary_pmv3_uses_shared_readiness_and_routes_only_ready_statuses(monkeypatch: pytest.MonkeyPatch):
    import app.services.presentation_engine_integration as engine
    import app.services.presentation_master.integration as integration

    candidate_binding = object()
    prepare_inputs = []
    monkeypatch.setattr(engine, "settings", SimpleNamespace(
        presentation_master_v3_renderer_mvp_enabled=True,
        presentation_master_v3_renderer_mvp_canary_enabled=False,
        presentation_master_v3_renderer_mvp_auto_fallback_enabled=True,
    ))
    monkeypatch.setattr(integration, "build_candidate_state_bridge", lambda payload, request_id: SimpleNamespace(binding=SimpleNamespace(candidates=candidate_binding)))
    monkeypatch.setattr(integration, "prepare_pmv3", lambda payload, semantic_candidates: (prepare_inputs.append(semantic_candidates) or SimpleNamespace(status=engine_status)))
    monkeypatch.setattr(integration, "render_pmv3", lambda prepared: SimpleNamespace(
        pptx_bytes=b"PK\x03\x04",
        validation_status="PASS",
        slide_count=5,
        rasterization_ratio=0.0,
        clipping_count=0,
        overflow_count=0,
        off_canvas_count=0,
    ))

    for engine_status in (AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS):
        result = engine._build_primary_pptx_bytes_for_engine(_composition_payload(), request_id="request-1")
        assert result.engine_mode == engine.ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP
        assert result.pptx_bytes[:2] == b"PK"

    assert prepare_inputs == [candidate_binding, candidate_binding]


@pytest.mark.parametrize("status", [
    AdapterStatus.REVIEW_REQUIRED,
    AdapterStatus.NOT_READY,
    AdapterStatus.NO_MATCH,
    AdapterStatus.INVALID_INPUT,
])
def test_primary_pmv3_non_ready_statuses_fail_closed_to_legacy(monkeypatch: pytest.MonkeyPatch, status: AdapterStatus):
    import app.services.presentation_engine_integration as engine
    import app.services.presentation_master.integration as integration

    monkeypatch.setattr(engine, "settings", SimpleNamespace(
        presentation_master_v3_renderer_mvp_enabled=True,
        presentation_master_v3_renderer_mvp_canary_enabled=False,
        presentation_master_v3_renderer_mvp_auto_fallback_enabled=True,
    ))
    monkeypatch.setattr(integration, "build_candidate_state_bridge", lambda payload, request_id: SimpleNamespace(binding=SimpleNamespace(candidates=object())))
    monkeypatch.setattr(integration, "prepare_pmv3", lambda payload, semantic_candidates: SimpleNamespace(status=status))
    monkeypatch.setattr(engine, "_log_renderer_mvp_block_event", lambda **kwargs: None)
    monkeypatch.setattr(engine, "_build_legacy_pptx_result", lambda *args, **kwargs: SimpleNamespace(
        pptx_bytes=b"legacy",
        quality_report=SimpleNamespace(to_dict=lambda: {"engine": "legacy"}),
    ))

    result = engine._build_primary_pptx_bytes_for_engine(_composition_payload(), request_id="request-1")
    assert result.engine_mode == engine.ENGINE_MODE_LEGACY
    assert result.pptx_bytes == b"legacy"


def test_primary_pmv3_flag_off_and_summary_remain_legacy(monkeypatch: pytest.MonkeyPatch):
    import app.services.presentation_engine_integration as engine

    monkeypatch.setattr(engine, "settings", SimpleNamespace(
        presentation_master_v3_renderer_mvp_enabled=False,
        presentation_master_v3_renderer_mvp_canary_enabled=False,
        presentation_design_ai_master_enabled=False,
        presentation_design_ai_master_shadow_enabled=False,
        presentation_design_ai_v10_enabled=False,
        presentation_engine_mode="legacy",
    ))
    monkeypatch.setattr(engine, "_build_legacy_pptx_result", lambda *args, **kwargs: SimpleNamespace(
        pptx_bytes=b"legacy",
        quality_report=SimpleNamespace(to_dict=lambda: {"engine": "legacy"}),
    ))

    normal = engine._build_primary_pptx_bytes_for_engine(_composition_payload(), request_id="request-1")
    summary = engine._build_primary_pptx_bytes_for_engine(_composition_payload(summary=True), request_id="request-1")
    assert normal.engine_mode == engine.ENGINE_MODE_LEGACY
    assert summary.engine_mode == engine.ENGINE_MODE_LEGACY


def _composition_payload(*, summary: bool = False):
    from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest

    return PptxDownloadRequest(
        project_brief="Production-shaped PMV3 bridge request with confirmed semantics.",
        client_company_info="Synthetic customer",
        summary=summary,
        powerpoint_generation_data=PowerPointData(
            deck_title="Bridge test",
            client_name="Synthetic customer",
            slides=[PowerPointSlide(slide_no=1, layout="title", title="Bridge", bullets=["test"], speaker_notes="", visual_suggestion="")],
        ),
    )


def test_readiness_event_emits_bounded_review_metadata_without_free_text(caplog):
    import logging
    import app.services.presentation_engine_integration as engine

    caplog.set_level(logging.INFO)
    prepared = SimpleNamespace(
        fallback_stage=SimpleNamespace(value="SEMANTIC_RESOLUTION"),
        selection=None,
        composition_readiness="NOT_READY",
        provenance_summary={"DIRECT": 2, "UNRESOLVED": 1},
        diagnostics={"human_review_reason": "do not log this", "diagnostic_count": 99},
    )
    metadata = engine._bounded_readiness_metadata(prepared, candidate_count=3)
    engine._log_shadow_eligibility_decision(
        "request-1",
        "INELIGIBLE",
        "READINESS_NOT_ELIGIBLE",
        readiness_class="REVIEW_REQUIRED",
        readiness_metadata=metadata,
    )

    record = next(record for record in caplog.records if record.getMessage().startswith("presentation_shadow_eligibility_decision"))
    message = record.getMessage()
    assert "readiness_class=REVIEW_REQUIRED" in message
    assert "candidate_count=3" in message
    assert "fallback_stage=SEMANTIC_RESOLUTION" in message
    assert "provenance_counts=DIRECT:2,UNRESOLVED:1" in message
    assert "diagnostic_count=2" in message
    assert message.index("fallback_stage=SEMANTIC_RESOLUTION") < message.index("candidate_count=3")
    assert record.readiness_class == "REVIEW_REQUIRED"
    assert record.fallback_stage == "SEMANTIC_RESOLUTION"
    assert record.candidate_count == 3
    assert record.provenance_counts == {"DIRECT": 2, "UNRESOLVED": 1}
    assert not hasattr(record, "fallback_reason")
    assert "do not log this" not in str(record.__dict__)


@pytest.mark.parametrize(
    ("status", "stage", "selection_state", "composition_status"),
    [
        ("READY", None, "selected", "VALID"),
        ("READY_WITH_VALID_BINDINGS", None, "selected", "VALID"),
        ("REVIEW_REQUIRED", "MASTER_SELECTION", "review_required", "NOT_READY"),
        ("REVIEW_REQUIRED", "COMPOSITION", "selected", "REVIEW_REQUIRED"),
    ],
)
def test_readiness_metadata_preserves_authoritative_stage_states(status, stage, selection_state, composition_status):
    import app.services.presentation_engine_integration as engine

    prepared = SimpleNamespace(
        status=SimpleNamespace(value=status),
        fallback_stage=SimpleNamespace(value=stage) if stage else None,
        selection=SimpleNamespace(state=selection_state),
        composition_readiness=composition_status,
        provenance_summary={},
        diagnostics={},
    )
    metadata = engine._bounded_readiness_metadata(prepared, candidate_count=2)
    assert metadata["candidate_count"] == 2
    assert metadata["selection_state"] == selection_state
    assert metadata["composition_status"] == composition_status
    if stage:
        assert metadata["fallback_stage"] == stage


def test_readiness_metadata_only_emits_allowlisted_diagnostic_codes():
    import app.services.presentation_engine_integration as engine

    prepared = SimpleNamespace(
        fallback_stage=None,
        selection=None,
        composition_readiness="NOT_READY",
        provenance_summary={},
        diagnostics={
            "invalid_input_reason": "SEMANTIC_SUPPLY_INVALID",
            "semantic_supply_invalid_reason": "NO_CANDIDATES",
            "free_text": "secret proposal text",
        },
    )
    metadata = engine._bounded_readiness_metadata(prepared, candidate_count=0)
    assert metadata["allowlisted_diagnostic_codes"] == ("SEMANTIC_SUPPLY_INVALID", "NO_CANDIDATES")
    assert metadata["semantic_supply_status"] == "INVALID"
    assert "secret proposal text" not in str(metadata)


def test_readiness_message_serialization_is_deterministic_and_omits_unavailable_fields():
    import app.services.presentation_engine_integration as engine

    metadata = {
        "candidate_count": 1,
        "fallback_stage": None,
        "selection_state": "selected",
        "composition_status": "VALID",
        "provenance_counts": {"UNRESOLVED": 0, "DIRECT": 1},
        "allowlisted_diagnostic_codes": ("NO_CANDIDATES", "SEMANTIC_SUPPLY_INVALID"),
        "diagnostic_count": 2,
    }
    first = engine._serialize_bounded_readiness_metadata(metadata)
    second = engine._serialize_bounded_readiness_metadata(dict(reversed(tuple(metadata.items()))))
    assert first == second
    assert "fallback_stage=" not in first
    assert first == (
        "selection_state=selected composition_status=VALID candidate_count=1 "
        "provenance_counts=DIRECT:1,UNRESOLVED:0 "
        "diagnostic_codes=NO_CANDIDATES,SEMANTIC_SUPPLY_INVALID diagnostic_count=2"
    )


def test_readiness_message_serialization_failure_returns_minimal_safe_message(monkeypatch):
    import app.services.presentation_engine_integration as engine

    monkeypatch.setattr(engine, "_serialize_bounded_readiness_metadata", lambda metadata: (_ for _ in ()).throw(RuntimeError("serialization failed")))
    engine._log_shadow_eligibility_decision(
        "request-1",
        "INELIGIBLE",
        "READINESS_NOT_ELIGIBLE",
        readiness_class="REVIEW_REQUIRED",
        readiness_metadata={"candidate_count": 1},
    )


def test_candidate_state_counts_reuse_existing_unresolved_critical_authority():
    import app.services.presentation_engine_integration as engine
    from app.services.presentation_master.integration.production_semantic_contract import (
        ProductionSemanticCandidate,
        ProductionSemanticCandidateSet,
        SemanticAuthority,
        SemanticItemType,
        SemanticReviewState,
    )

    def candidate(candidate_id, state):
        return ProductionSemanticCandidate(
            candidate_id,
            SemanticItemType.DECISION_CONDITION,
            "bounded value",
            "analysis",
            "source_field",
            SemanticAuthority.AI_PROPOSED,
            0.6,
            state,
            inferred=True,
            confirmation_authority=(
                SemanticAuthority.USER_EXPLICIT
                if state in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED}
                else None
            ),
        )

    candidates = ProductionSemanticCandidateSet(
        (
            candidate("candidate-id-alpha", SemanticReviewState.UNCONFIRMED),
            candidate("candidate-id-bravo", SemanticReviewState.CONFIRMED),
            candidate("candidate-id-charlie", SemanticReviewState.CORRECTED),
            candidate("candidate-id-delta", SemanticReviewState.REJECTED),
            candidate("candidate-id-echo", SemanticReviewState.UNRESOLVED),
        )
    )
    metadata = engine._bounded_readiness_metadata(
        SimpleNamespace(fallback_stage=None, selection=None, composition_readiness="NOT_READY", provenance_summary={}, diagnostics={}),
        candidate_count=5,
        candidate_set=candidates,
    )
    assert metadata["candidate_count"] == 5
    assert metadata["confirmed_candidate_count"] == 1
    assert metadata["corrected_candidate_count"] == 1
    assert metadata["unconfirmed_candidate_count"] == 1
    assert metadata["rejected_candidate_count"] == 1
    assert metadata["unresolved_candidate_count"] == 1
    assert metadata["unresolved_critical_count"] == len(candidates.unresolved_critical())
    message = engine._serialize_bounded_readiness_metadata(metadata)
    assert "candidate_count=5" in message
    assert "unresolved_critical_count=3" in message
    assert all(identifier not in message for identifier in ("candidate-id-alpha", "candidate-id-bravo", "candidate-id-charlie", "candidate-id-delta", "candidate-id-echo"))


def test_readiness_metadata_includes_only_bounded_relationship_and_admission_data():
    import app.services.presentation_engine_integration as engine
    from app.services.presentation_master.integration.production_semantic_contract import (
        ProductionSemanticCandidate,
        ProductionSemanticCandidateSet,
        SemanticAuthority,
        SemanticItemType,
        SemanticReviewState,
    )

    def candidate(candidate_id, state, authority):
        return ProductionSemanticCandidate(
            candidate_id,
            SemanticItemType.DECISION_CONDITION,
            "bounded value",
            "analysis",
            "source_field",
            authority,
            0.8,
            state,
            confirmation_authority=(SemanticAuthority.USER_EXPLICIT if state == SemanticReviewState.CONFIRMED else None),
        )

    candidates = ProductionSemanticCandidateSet(
        (
            candidate("confirmed", SemanticReviewState.CONFIRMED, SemanticAuthority.USER_EXPLICIT),
            candidate("rejected", SemanticReviewState.REJECTED, SemanticAuthority.AI_PROPOSED),
        )
    )
    prepared = SimpleNamespace(
        status=SimpleNamespace(value="REVIEW_REQUIRED"),
        fallback_stage=SimpleNamespace(value="SEMANTIC_ADAPTER"),
        selection=None,
        composition_readiness="NOT_READY",
        provenance_summary={},
        diagnostics={"invalid_input_reason": "raw text must not be logged"},
    )
    metadata = engine._bounded_readiness_metadata(
        prepared,
        candidate_count=2,
        candidate_set=candidates,
        relationships=(SimpleNamespace(relationship_type="decision_boundary"),),
    )
    message = engine._serialize_bounded_readiness_metadata(metadata)

    assert metadata["diagnostic_status"] == "AVAILABLE"
    assert metadata["readiness_class"] == "REVIEW_REQUIRED"
    assert metadata["admitted_candidate_count"] == 1
    assert metadata["relationship_count"] == 1
    assert metadata["relationship_types"] == ("decision_boundary",)
    assert "admitted_candidate_count=1" in message
    assert "relationship_count=1" in message
    assert "relationship_types=decision_boundary" in message
    assert "raw text must not be logged" not in message


def test_readiness_observability_failure_is_non_blocking(monkeypatch):
    import app.services.presentation_engine_integration as engine

    monkeypatch.setattr(engine, "_log_shadow_metadata", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("logging failed")))
    engine._log_shadow_eligibility_decision(
        "request-1",
        "ELIGIBLE",
        "ELIGIBLE",
        readiness_class="READY",
        readiness_metadata={"candidate_count": 1},
    )


def test_resolution_diagnostics_decompose_existing_result_without_free_text():
    import app.services.presentation_master.integration.engine_adapter as adapter

    resolution = SimpleNamespace(
        status=SimpleNamespace(value="PARTIALLY_RESOLVED"),
        unresolved_requirement_ids=("relationship:direction", "user-provided-secret"),
        conflicts=(SimpleNamespace(semantic_role="metric", reason="raw Product text"), SimpleNamespace(semantic_role="raw-owner")),
    )

    diagnostics = adapter._resolution_diagnostics(resolution)

    assert diagnostics["resolution_diagnostic_status"] == "AVAILABLE"
    assert diagnostics["resolution_status"] == "PARTIALLY_RESOLVED"
    assert diagnostics["resolution_has_unresolved_requirements"] is True
    assert diagnostics["resolution_has_conflicts"] is True
    assert diagnostics["resolution_status_requires_review"] is True
    assert diagnostics["unresolved_requirement_count"] == 2
    assert diagnostics["unresolved_requirements"] == ("relationship:direction",)
    assert diagnostics["conflict_count"] == 2
    assert diagnostics["conflict_types"] == ("metric",)
    assert "raw Product text" not in str(diagnostics)
    assert "user-provided-secret" not in str(diagnostics)


def test_resolution_diagnostics_fail_safe_when_existing_result_is_unreadable():
    import app.services.presentation_master.integration.engine_adapter as adapter

    class BrokenResolution:
        @property
        def status(self):
            raise RuntimeError("must not escape")

    diagnostics = adapter._resolution_diagnostics(BrokenResolution())

    assert diagnostics == {"resolution_diagnostic_status": "UNAVAILABLE"}


def test_resolution_diagnostics_all_false_for_resolved_result():
    import app.services.presentation_master.integration.engine_adapter as adapter

    diagnostics = adapter._resolution_diagnostics(
        SimpleNamespace(
            status=SimpleNamespace(value="RESOLVED"),
            unresolved_requirement_ids=(),
            conflicts=(),
        )
    )

    assert diagnostics["resolution_status"] == "RESOLVED"
    assert diagnostics["resolution_has_unresolved_requirements"] is False
    assert diagnostics["resolution_has_conflicts"] is False
    assert diagnostics["resolution_status_requires_review"] is False
