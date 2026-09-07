"""Focused offline tests for the Master Selection Contract."""

from dataclasses import replace
from pathlib import Path

import pytest

from app.services.presentation_master.definitions import MASTER_REGISTRY
from app.services.presentation_master.selection import (
    MasterSelectionInput,
    score_candidates,
    select_master,
    suitability_metadata,
)


def _clear_case(master_id: str, *, evidence=("source_backed",), relationships=None):
    definition = MASTER_REGISTRY.get(master_id)
    metadata = suitability_metadata(master_id)
    counts = {slot.slot_id: slot.cardinality.min_items for slot in definition.slots}
    return MasterSelectionInput(
        narrative_intent=definition.narrative_role,
        information_pattern=definition.information_pattern,
        relationship_types=frozenset(relationships or {item.relationship_type for item in definition.relationships}),
        decision_context=next(iter(metadata.decision_contexts)),
        evidence_states=frozenset(evidence),
        available_groups=frozenset(group.group_id for group in definition.information_groups),
        semantic_signals=frozenset(metadata.positive_signals),
        content_counts=counts,
        confidence=0.92,
    )


@pytest.mark.parametrize("master_id", [f"M{i}" for i in range(45, 55)])
def test_each_master_has_a_clear_semantic_case(master_id):
    result = select_master(_clear_case(master_id))
    assert result.state == "selected"
    assert result.selected_master_id == master_id
    assert result.human_review_required is False
    assert result.selection_reason
    assert result.matched_signals


def test_input_contract_validates_confidence_and_counts():
    with pytest.raises(ValueError, match="confidence"):
        MasterSelectionInput(confidence=1.1)
    with pytest.raises(ValueError, match="counts"):
        MasterSelectionInput(content_counts={"slot": -1})


def test_candidate_scores_are_explicit_and_deterministic():
    selection = _clear_case("M47")
    first = score_candidates(selection)
    second = score_candidates(selection)
    assert first == second
    assert first[0].master_id == "M47"
    assert set(first[0].dimension_scores) == {"semantic", "topology", "groups", "evidence", "decision", "cardinality", "density"}
    assert first[0].score > first[1].score


def test_ambiguous_pair_does_not_force_a_master():
    m45 = MASTER_REGISTRY.get("M45")
    m46 = MASTER_REGISTRY.get("M46")
    metadata = suitability_metadata("M45")
    selection = MasterSelectionInput(
        relationship_types=frozenset(item.relationship_type for item in m45.relationships + m46.relationships),
        decision_context="executive",
        evidence_states=frozenset({"source_backed"}),
        available_groups=frozenset(group.group_id for group in m45.information_groups + m46.information_groups),
        semantic_signals=suitability_metadata("M45").required_signals | suitability_metadata("M46").required_signals,
        confidence=0.8,
    )
    result = select_master(selection)
    assert result.state == "review_required"
    assert result.selected_master_id is None
    assert result.human_review_required is True
    assert result.fallback_reason == "ambiguous semantic fit"


def test_weak_case_returns_no_match():
    result = select_master(MasterSelectionInput(semantic_signals=frozenset({"generic"}), confidence=0.5))
    assert result.state == "no_match"
    assert result.selected_master_id is None
    assert result.human_review_required is True


def test_missing_evidence_requires_review_without_fabrication():
    result = select_master(_clear_case("M47", evidence=("missing",)))
    assert result.state == "review_required"
    assert result.selected_master_id == "M47"
    assert result.human_review_required is True
    assert result.fallback_reason == "required evidence missing"
    assert result.ranked_candidates[0].dimension_scores["evidence"] < 0


def test_relationship_mismatch_returns_no_match():
    result = select_master(_clear_case("M47", relationships={"handoff"}))
    assert result.state == "no_match"
    assert result.selected_master_id is None
    assert result.fallback_reason == "no eligible candidate"


def test_negative_selection_rule_blocks_metric_master_without_metric_structure():
    definition = MASTER_REGISTRY.get("M47")
    result = select_master(
        replace(
            _clear_case("M47"),
            semantic_signals=frozenset({"action", "evidence"}),
            available_groups=frozenset(group.group_id for group in definition.information_groups),
        )
    )
    assert result.state == "no_match"
    assert all(candidate.master_id != "M47" or not candidate.eligible for candidate in result.ranked_candidates)


def test_result_contains_ranked_candidates_and_explanation():
    result = select_master(_clear_case("M53"))
    assert result.ranked_candidates
    assert result.ranked_candidates[0].master_id == "M53"
    assert result.ranked_candidates[0].selection_reason
    assert isinstance(result.ranked_candidates[0].matched_signals, tuple)
    assert isinstance(result.ranked_candidates[0].missing_signals, tuple)


def test_m48_optional_escalation_absence_does_not_block_eligibility():
    selection = replace(
        _clear_case("M48"),
        available_groups=frozenset({"preparation", "decision", "approval", "execution"}),
    )
    candidate = next(item for item in score_candidates(selection) if item.master_id == "M48")
    assert candidate.eligible is True
    assert "group:escalation" not in candidate.missing_signals


def test_m48_required_preparation_absence_still_blocks_eligibility():
    selection = replace(
        _clear_case("M48"),
        available_groups=frozenset({"decision", "approval", "execution", "escalation"}),
    )
    candidate = next(item for item in score_candidates(selection) if item.master_id == "M48")
    assert candidate.eligible is False
    assert "group:preparation" in candidate.missing_signals


def test_m48_optional_escalation_presence_preserves_existing_behavior():
    candidate = next(item for item in score_candidates(_clear_case("M48")) if item.master_id == "M48")
    assert candidate.eligible is True
    assert "group:escalation" not in candidate.missing_signals


def test_selection_is_renderer_neutral():
    source = Path(__import__("app.services.presentation_master.selection", fromlist=["__file__"]).__file__).read_text(encoding="utf-8").lower()
    for forbidden in ("python-pptx", "presentationfile", "artifact tool", "powerpoint com", "source_png", "coordinates", "shape_count"):
        assert forbidden not in source
