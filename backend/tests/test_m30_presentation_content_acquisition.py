from dataclasses import FrozenInstanceError, replace

import pytest

from app.models import BusinessImplicationTransportItem, ProblemObjectTransportItem, SolutionDirectionTransportItem
from app.services.presentation_master.integration.m30_presentation_content_acquisition import (
    M30PresentationContentAcquisitionItem,
    M30PresentationContentAcquisitionProjection,
    PresentationAcquisitionMode,
    PresentationFieldAcquisitionRequirement,
    project_m30_presentation_content_acquisition,
)
from app.services.presentation_master.integration.m30_semantic_bridge import evaluate_m30_semantic_bridge
from app.services.presentation_master.integration.presentation_content_candidates import PresentationContentCandidate


def _problem(item_id, role, value):
    return ProblemObjectTransportItem(id=item_id, role=role, value=value, source_type="user_input", source_field=role, source_reference=f"step1:{item_id}", authority="USER_EXPLICIT", review_state="CONFIRMED", confirmation_authority="USER_EXPLICIT")


def _evaluation(complete=True):
    objects = [_problem("issue", "visible_issue", "visible canonical issue")]
    objects += [_problem(f"root-{i}", "root_cause", f"canonical root {i}") for i in range(1, 5)]
    objects += [_problem(f"state-{i}", "causal_state", f"canonical state {i}") for i in range(1, 6)]
    implications = [BusinessImplicationTransportItem(id=f"imp-{i}", value=f"canonical implication {i}", source_type="user_input", source_field="business_implication", source_reference=f"step1:imp-{i}", authority="USER_EXPLICIT", review_state="CONFIRMED", confirmation_authority="USER_EXPLICIT") for i in range(1, 5)]
    solution = SolutionDirectionTransportItem(id="solution", value="canonical solution", source_type="user_input", source_field="solution_direction", source_reference="step1:solution", authority="USER_EXPLICIT", review_state="CONFIRMED", confirmation_authority="USER_EXPLICIT")
    result = evaluate_m30_semantic_bridge(objects, implications, solution, evidence_candidates=())
    return replace(result, m30_semantic_complete=complete, incompleteness_reasons=() if complete else ("ROOT_CAUSE_INSUFFICIENT",))


def test_contracts_are_immutable():
    requirement = PresentationFieldAcquisitionRequirement("root_cause", "title", PresentationAcquisitionMode.AI_PROPOSAL_REQUIRED, ("root-1",), "reason")
    item = M30PresentationContentAcquisitionItem("root_cause", "root-1", None, (requirement,))
    projection = M30PresentationContentAcquisitionProjection((item,), True, True, ())
    with pytest.raises(FrozenInstanceError):
        requirement.reason = "changed"
    with pytest.raises(FrozenInstanceError):
        item.source_item_id = "changed"
    with pytest.raises(FrozenInstanceError):
        projection.acquisition_plan_complete = False


def test_complete_admitted_set_is_classified_without_text_generation():
    result = project_m30_presentation_content_acquisition(_evaluation())
    assert result.acquisition_plan_complete is True
    assert result.presentation_framing_required is True
    assert [item.semantic_role for item in result.items] == ["visible_issue", *(["root_cause"] * 4), *(["causal_state"] * 5), *(["business_implication"] * 4), "solution_direction"]
    assert sum(item.direct_candidate is not None for item in result.items) == 14
    assert all(item.direct_candidate is None for item in result.items if item.semantic_role == "visible_issue")


def test_incomplete_upstream_evaluation_fails_closed():
    result = project_m30_presentation_content_acquisition(_evaluation(False))
    assert result.acquisition_plan_complete is False
    assert "ROOT_CAUSE_INSUFFICIENT" in result.issues


def test_required_fields_are_classified_by_frozen_m30_contract():
    result = project_m30_presentation_content_acquisition(_evaluation())
    visible = result.items[0]
    assert [r.field_role for r in visible.required_derivations] == ["title", "accent", "subtitle"]
    roots = result.items[1:5]
    assert all([r.field_role for r in root.required_derivations] == ["title"] for root in roots)
    assert all(root.direct_candidate.fields[0].field_role == "body" for root in roots)
    implications = result.items[10:14]
    assert all([r.field_role for r in item.required_derivations] == ["title"] for item in implications)
    assert result.items[-1].direct_candidate.fields[0].field_role == "statement"


def test_direct_values_and_source_provenance_are_exact():
    result = project_m30_presentation_content_acquisition(_evaluation())
    for item in result.items:
        candidate = item.direct_candidate
        if candidate is None:
            continue
        source = candidate.source_identities[0]
        assert candidate.fields[0].value == source.value
        assert candidate.source_identities[0].source_item_id == item.source_item_id
        assert candidate.derivation_type == "DIRECT"


def test_no_fabricated_titles_accent_subtitle_or_fallback_text():
    result = project_m30_presentation_content_acquisition(_evaluation())
    for item in result.items:
        for requirement in item.required_derivations:
            assert requirement.acquisition_mode == PresentationAcquisitionMode.AI_PROPOSAL_REQUIRED
            assert requirement.source_item_ids == (item.source_item_id,)
            assert requirement.reason.startswith("canonical semantic value")
    assert not any(isinstance(item.direct_candidate, PresentationContentCandidate) and item.semantic_role == "visible_issue" for item in result.items)


def test_only_current_admitted_distinct_representatives_are_used():
    evaluation = _evaluation()
    rejected = _problem("rejected", "root_cause", "rejected root")
    rejected = rejected.copy(update={"review_state": "REJECTED"})
    evaluation = replace(evaluation, problem_objects=(*evaluation.problem_objects, rejected))
    result = project_m30_presentation_content_acquisition(evaluation)
    assert all(item.source_item_id != "rejected" for item in result.items)


def test_no_slot_ready_pack_or_integration_is_created():
    result = project_m30_presentation_content_acquisition(_evaluation())
    assert not any(type(item).__name__ == "SlotReadyContentPack" for item in result.items)
    assert not any(name in str(type(item.direct_candidate)) for item in result.items for name in ("Composition", "MasterDefinition"))


def test_no_m30_physical_or_golden_identifiers():
    annotations = str(M30PresentationContentAcquisitionProjection.__annotations__)
    assert not any(token in annotations.lower() for token in ("coordinate", "shape_id", "golden", "pptx"))
