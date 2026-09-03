from __future__ import annotations

import pytest

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest, SemanticRelationshipTransportItem
from app.services.presentation_master.integration import (
    AdapterStatus,
    ProductionSemanticCandidate,
    ProductionSemanticCandidateSet,
    SemanticAuthority,
    SemanticItemType,
    SemanticReviewState,
    build_candidate_state_bridge,
    build_adapter_input,
    candidate_set_to_dict,
    prepare_pmv3,
)
from app.services.presentation_master.integration.semantic_input_adapter import prepare_semantics


def _candidate(candidate_id: str, semantic_type: SemanticItemType) -> ProductionSemanticCandidate:
    return ProductionSemanticCandidate(
        candidate_id,
        semantic_type,
        candidate_id,
        "analysis",
        "analysis.field",
        SemanticAuthority.AI_PROPOSED,
        0.9,
        SemanticReviewState.UNCONFIRMED,
        inferred=True,
    )


def _base() -> ProductionSemanticCandidateSet:
    return ProductionSemanticCandidateSet((
        _candidate("condition", SemanticItemType.DECISION_CONDITION),
        _candidate("owner", SemanticItemType.ACCOUNTABLE_OWNER),
        _candidate("action", SemanticItemType.EXECUTION_ACTION),
    ))


def _state(base: ProductionSemanticCandidateSet, review: str = "CONFIRMED") -> list[dict[str, str]]:
    return [{"id": item.id, "semantic_type": item.semantic_type.value, "review_state": review} for item in base.candidates]


def _relationship(*, review_state="CONFIRMED", relationship_type="causality", from_item="owner", to_item="action") -> SemanticRelationshipTransportItem:
    return SemanticRelationshipTransportItem(
        from_item=from_item,
        to_item=to_item,
        relationship_type=relationship_type,
        review_state=review_state,
        authority="USER_EXPLICIT",
        confirmation_authority="USER_EXPLICIT",
        provenance_state="supplied",
    )


def _request(base: ProductionSemanticCandidateSet, relationships=None) -> PptxDownloadRequest:
    return PptxDownloadRequest(
        powerpoint_generation_data=PowerPointData(
            deck_title="Relationship transport",
            client_name="Customer",
            slides=[PowerPointSlide(slide_no=1, layout="title", title="Relationship", bullets=[], speaker_notes="", visual_suggestion="")],
        ),
        semantic_candidates=candidate_set_to_dict(base),
        semantic_confirmation_state=_state(base),
        semantic_relationships=relationships,
    )


def test_valid_causality_round_trips_and_resolves_direction():
    base = _base()
    request = _request(base, [_relationship()])
    context = build_candidate_state_bridge(request, request_id="relationship-test")
    assert context is not None
    assert context.relationships[0].from_ref == "owner"
    assert context.relationships[0].to_ref == "action"
    assert context.relationships[0].relationship_type == "causality"
    assert context.relationships[0].provenance_state == "supplied"
    adapter_input = build_adapter_input(request, semantic_candidates=context.binding.candidates, semantic_relationships=context.relationships)
    _, resolution, _, early_status, _ = prepare_semantics(adapter_input)
    assert early_status is None
    assert resolution is not None
    assert "relationship:direction" not in resolution.unresolved_requirement_ids


def test_offline_prepare_pmv3_consumes_valid_relationship_without_semantic_fallback():
    base = _base()
    request = _request(base, [_relationship(relationship_type="dependency")])
    context = build_candidate_state_bridge(request, request_id="prepare-test")
    assert context is not None
    prepared = prepare_pmv3(request, semantic_candidates=context.binding.candidates, semantic_relationships=context.relationships)
    assert prepared.status != AdapterStatus.REVIEW_REQUIRED
    assert prepared.fallback_stage is None or prepared.fallback_stage.value != "SEMANTIC_ADAPTER"


def test_dependency_round_trips_and_preserves_ids():
    base = _base()
    context = build_candidate_state_bridge(_request(base, [_relationship(relationship_type="dependency")]), request_id="dependency-test")
    assert context is not None
    assert (context.relationships[0].from_ref, context.relationships[0].to_ref, context.relationships[0].relationship_type) == ("owner", "action", "dependency")


@pytest.mark.parametrize("review_state", ["UNCONFIRMED", "REJECTED"])
def test_unconfirmed_or_rejected_relationship_fails_closed(review_state):
    with pytest.raises(ValueError):
        build_candidate_state_bridge(_request(_base(), [_relationship(review_state=review_state)]), request_id="invalid-review")


@pytest.mark.parametrize("kwargs", [
    {"from_item": "missing"},
    {"to_item": "missing"},
    {"from_item": "owner", "to_item": "owner"},
    {"relationship_type": "sequence"},
    {"relationship_type": "unsupported"},
])
def test_invalid_relationship_fails_closed(kwargs):
    with pytest.raises(ValueError):
        build_candidate_state_bridge(_request(_base(), [_relationship(**kwargs)]), request_id="invalid-relationship")


def test_missing_relationship_preserves_existing_review_required_behavior():
    base = _base()
    request = _request(base)
    context = build_candidate_state_bridge(request, request_id="no-relationship")
    assert context is not None
    prepared = prepare_pmv3(request, semantic_candidates=context.binding.candidates, semantic_relationships=context.relationships)
    assert prepared.status == AdapterStatus.REVIEW_REQUIRED
