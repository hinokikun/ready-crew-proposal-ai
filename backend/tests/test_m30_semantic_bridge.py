from __future__ import annotations

import pytest

from app.models import BusinessImplicationTransportItem, BusinessRelationshipTransportItem, ProblemObjectTransportItem, SolutionDirectionTransportItem
from app.services.presentation_master.integration.m30_semantic_bridge import (
    AdmittedSemanticNodeIdentity,
    ValidatedCausalEdgeIdentity,
    evaluate_m30_semantic_bridge,
    normalize_distinctness_value,
)
from app.services.presentation_master.integration.production_semantic_contract import ProductionSemanticCandidate, SemanticAuthority, SemanticItemType, SemanticReviewState


def _problem(item_id: str, role: str, value: str | None = None, *, state: str = "CONFIRMED", authority: str = "USER_EXPLICIT") -> ProblemObjectTransportItem:
    return ProblemObjectTransportItem(id=item_id, role=role, value=value or item_id, source_type="user_input", source_field="problem_structure", source_reference=f"step1:{item_id}", authority=authority, review_state=state)


def _implication(item_id: str, value: str | None = None, *, state: str = "CONFIRMED") -> BusinessImplicationTransportItem:
    return BusinessImplicationTransportItem(id=item_id, value=value or item_id, source_type="user_input", source_field="business_implication", source_reference=f"step1:{item_id}", authority="USER_EXPLICIT", review_state=state)


def _solution() -> SolutionDirectionTransportItem:
    return SolutionDirectionTransportItem(id="solution:1", value="explicit solution direction", source_type="user_input", source_field="solution_direction", source_reference="step1:solution", authority="USER_EXPLICIT", review_state="CONFIRMED")


def _edge(edge_id: str, source: str, target: str) -> BusinessRelationshipTransportItem:
    return BusinessRelationshipTransportItem(id=edge_id, from_item=source, to_item=target, relationship_type="causality", review_state="CONFIRMED", authority="USER_EXPLICIT", confirmation_authority="USER_EXPLICIT", source_reference=f"step1:{edge_id}")


def _evidence() -> ProductionSemanticCandidate:
    return ProductionSemanticCandidate("evidence:1", SemanticItemType.EVIDENCE, "bounded evidence", "user_input", "evidence", SemanticAuthority.USER_EXPLICIT, 1.0, SemanticReviewState.CONFIRMED, admissible_as_evidence=True, source_reference="step1:evidence")


def _complete():
    visible = (_problem("visible:1", "visible_issue", "visible issue"),)
    roots = tuple(_problem(f"root:{index}", "root_cause", f"root cause {index}") for index in range(1, 5))
    states = tuple(_problem(f"state:{index}", "causal_state", f"causal state {index}") for index in range(1, 6))
    implications = tuple(_implication(f"implication:{index}", f"business implication {index}") for index in range(1, 5))
    edges = (
        _edge("edge:1", "root:1", "state:1"),
        _edge("edge:2", "root:2", "visible:1"),
        _edge("edge:3", "state:3", "state:4"),
        _edge("edge:4", "state:5", "implication:1"),
    )
    return visible + roots + states, implications, _solution(), edges


def test_complete_truthful_structure_reaches_true_cardinality_without_selection():
    problems, implications, solution, edges = _complete()
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))
    assert result.m30_semantic_complete is True
    assert (result.admitted_visible_issue_count, result.distinct_root_cause_count, result.distinct_causal_state_count) == (1, 4, 5)
    assert (result.distinct_business_implication_count, result.admitted_solution_direction_count, result.valid_causality_count, result.admissible_evidence_count) == (4, 1, 4, 1)


@pytest.mark.parametrize("count,reason", [(3, "ROOT_CAUSE_INSUFFICIENT"), (4, "CAUSAL_STATE_INSUFFICIENT")])
def test_missing_cardinality_is_reported(count: int, reason: str):
    problems, implications, solution, edges = _complete()
    if count == 3:
        problems = tuple(item for item in problems if item.role != "root_cause" or item.id != "root:4")
    else:
        problems = tuple(item for item in problems if item.role != "causal_state" or item.id != "state:5")
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))
    assert result.m30_semantic_complete is False and reason in result.incompleteness_reasons


def test_semantic_duplicates_count_once_with_original_records_preserved():
    problems, implications, solution, edges = _complete()
    problems = (*problems, _problem("root:duplicate", "root_cause", " ROOT   CAUSE 1。"))
    implications = (*implications, _implication("implication:duplicate", "BUSINESS IMPLICATION 1."))
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))
    assert result.distinct_root_cause_count == 4
    assert result.distinct_business_implication_count == 4
    assert len(result.problem_objects) == len(problems)


def test_missing_solution_and_evidence_are_incomplete():
    problems, implications, _, edges = _complete()
    result = evaluate_m30_semantic_bridge(problems, implications, None, edges)
    assert {"SOLUTION_DIRECTION_MISSING", "EVIDENCE_INSUFFICIENT"} <= set(result.incompleteness_reasons)


@pytest.mark.parametrize("state,authority", [("UNCONFIRMED", "USER_EXPLICIT"), ("REJECTED", "USER_EXPLICIT"), ("CONFIRMED", "AI_PROPOSED"), ("UNRESOLVED", "USER_EXPLICIT")])
def test_non_admitted_objects_do_not_count(state: str, authority: str):
    problems, implications, solution, edges = _complete()
    problems = (*problems, _problem("not-admitted", "root_cause", state=state, authority=authority))
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))
    assert result.distinct_root_cause_count == 4


@pytest.mark.parametrize("source,target", [("root:1", "visible:1"), ("root:1", "state:1"), ("state:1", "state:2"), ("state:2", "visible:1"), ("visible:1", "implication:1"), ("state:2", "implication:1")])
def test_allowed_role_directions_are_valid(source: str, target: str):
    problems, implications, solution, _ = _complete()
    result = evaluate_m30_semantic_bridge(problems, implications, solution, (_edge("edge:valid", source, target),), evidence_candidates=(_evidence(),))
    assert result.valid_causality_count == 1


def test_reversed_direction_unknown_endpoint_and_duplicate_edges_do_not_count():
    problems, implications, solution, _ = _complete()
    edges = (_edge("edge:reverse", "visible:1", "root:1"), _edge("edge:unknown", "root:1", "missing"), _edge("edge:a", "root:1", "state:1"), _edge("edge:b", "root:1", "state:1"))
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))
    assert result.valid_causality_count == 1
    assert len(result.invalid_relationship_ids) == 3


@pytest.mark.parametrize(
    "state,authority,confirmation,expected",
    [
        ("CONFIRMED", "USER_EXPLICIT", "USER_EXPLICIT", 1),
        ("CORRECTED", "USER_EXPLICIT", "USER_EXPLICIT", 1),
        ("CORRECTED", "SYSTEM_EXTRACTED", "USER_EXPLICIT", 1),
        ("CONFIRMED", "AI_PROPOSED", "USER_EXPLICIT", 0),
        ("UNCONFIRMED", "USER_EXPLICIT", "USER_EXPLICIT", 0),
        ("REJECTED", "USER_EXPLICIT", "USER_EXPLICIT", 0),
        ("UNRESOLVED", "USER_EXPLICIT", "USER_EXPLICIT", 0),
        ("CONFIRMED", "AI_PROPOSED", None, 0),
    ],
)
def test_relationship_authority_delegates_to_existing_production_predicate(state, authority, confirmation, expected):
    problems, implications, solution, _ = _complete()
    relationship = _edge("edge:authority", "root:1", "state:1").copy(update={"review_state": state, "authority": authority, "confirmation_authority": confirmation})
    result = evaluate_m30_semantic_bridge(problems, implications, solution, (relationship,), evidence_candidates=(_evidence(),))
    assert result.valid_causality_count == expected


def test_valid_relationship_authority_still_fails_for_invalid_direction_or_missing_provenance():
    problems, implications, solution, _ = _complete()
    invalid_direction = _edge("edge:direction", "visible:1", "root:1")
    missing_provenance = _edge("edge:provenance", "root:1", "state:1").copy(update={"source_reference": ""})
    result = evaluate_m30_semantic_bridge(problems, implications, solution, (invalid_direction, missing_provenance), evidence_candidates=(_evidence(),))
    assert result.valid_causality_count == 0


def test_source_reference_is_not_evidence_and_project_brief_is_not_converted():
    problems = (_problem("problem:1", "visible_issue", "project brief"),)
    result = evaluate_m30_semantic_bridge(problems)
    assert result.admissible_evidence_count == 0
    assert result.problem_objects == problems


def test_production_admission_is_type_independent_for_phase1a_authority_combinations():
    for semantic_type in SemanticItemType:
        candidate = ProductionSemanticCandidate("candidate:1", semantic_type, "value", "user_input", "field", SemanticAuthority.USER_EXPLICIT, 1.0, SemanticReviewState.CONFIRMED, source_reference="source:1")
        assert candidate.admissible_for_supply is True


def test_normalization_is_bounded_and_does_not_infer_synonyms():
    assert normalize_distinctness_value("  Root　Cause 1。 ") == "root cause 1"
    assert normalize_distinctness_value("root cause") != normalize_distinctness_value("underlying issue")


def test_empty_phase1a_fields_are_incomplete_and_do_not_activate_selection():
    result = evaluate_m30_semantic_bridge()
    assert result.m30_semantic_complete is False
    assert result.problem_objects == () and result.business_relationships == ()


def test_admitted_node_and_solution_identities_are_exposed_without_raw_text():
    problems, implications, solution, edges = _complete()
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))

    assert result.admitted_node_identities[0] == AdmittedSemanticNodeIdentity("visible:1", "visible_issue")
    assert {item.role for item in result.admitted_node_identities} == {"visible_issue", "root_cause", "causal_state", "business_implication"}
    assert result.admitted_solution_direction_id == "solution:1"
    assert all(not hasattr(item, "value") for item in result.admitted_node_identities)


@pytest.mark.parametrize("state,authority", [("UNCONFIRMED", "USER_EXPLICIT"), ("REJECTED", "USER_EXPLICIT"), ("UNRESOLVED", "USER_EXPLICIT"), ("CONFIRMED", "AI_PROPOSED")])
def test_non_admitted_nodes_are_excluded_from_identity(state, authority):
    problems, implications, solution, edges = _complete()
    problems = (*problems, _problem("excluded", "root_cause", state=state, authority=authority))
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))

    assert "excluded" not in {item.id for item in result.admitted_node_identities}


def test_corrected_system_extracted_node_identity_follows_existing_admission():
    problems, implications, solution, edges = _complete()
    corrected = _problem("corrected", "root_cause", state="CORRECTED", authority="SYSTEM_EXTRACTED").copy(update={"confirmation_authority": "USER_EXPLICIT"})
    result = evaluate_m30_semantic_bridge((*problems, corrected), implications, solution, edges, evidence_candidates=(_evidence(),))

    assert "corrected" in {item.id for item in result.admitted_node_identities}


def test_valid_causal_edge_identity_is_exposed_from_validated_result():
    problems, implications, solution, edges = _complete()
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))

    assert result.validated_causal_edges[0] == ValidatedCausalEdgeIdentity("edge:1", "root:1", "state:1", "causality")
    assert len(result.validated_causal_edges) == result.valid_causality_count
    assert result.validated_graph_available is True


def test_non_admitted_source_and_target_edges_are_excluded():
    problems, implications, solution, edges = _complete()
    source = _problem("unconfirmed-source", "root_cause", state="UNCONFIRMED")
    target = _problem("unconfirmed-target", "causal_state", state="UNCONFIRMED")
    source_edge = _edge("edge:source", "unconfirmed-source", "state:1")
    target_edge = _edge("edge:target", "root:1", "unconfirmed-target")
    result = evaluate_m30_semantic_bridge((*problems, source, target), implications, solution, (*edges, source_edge, target_edge), evidence_candidates=(_evidence(),))

    assert {edge.relationship_id for edge in result.validated_causal_edges} == {f"edge:{index}" for index in range(1, 5)}


def test_semantic_duplicates_collapse_to_first_representative_and_map_edges():
    problems, implications, solution, edges = _complete()
    duplicate = _problem("root:duplicate", "root_cause", " ROOT   CAUSE 1。")
    duplicate_edge = _edge("edge:duplicate", "root:duplicate", "state:2")
    result = evaluate_m30_semantic_bridge((*problems, duplicate), implications, solution, (*edges, duplicate_edge), evidence_candidates=(_evidence(),))

    ids = [item.id for item in result.distinct_admitted_node_identities if item.role == "root_cause"]
    assert ids == ["root:1", "root:2", "root:3", "root:4"]
    mapped = next(edge for edge in result.validated_causal_edges if edge.relationship_id == "edge:duplicate")
    assert mapped.from_item == "root:1"


def test_duplicate_edges_do_not_inflate_validated_edge_identity():
    problems, implications, solution, edges = _complete()
    duplicate_edges = (*edges, _edge("edge:duplicate-a", "root:1", "state:1"), _edge("edge:duplicate-b", "root:1", "state:1"))
    result = evaluate_m30_semantic_bridge(problems, implications, solution, duplicate_edges, evidence_candidates=(_evidence(),))

    assert result.valid_causality_count == 4
    assert len(result.validated_causal_edges) == 4


def test_duplicate_relationship_ids_are_not_resolved_by_id_difference():
    problems, implications, solution, edges = _complete()
    duplicate_ids = (*edges, _edge("edge:1", "root:4", "state:5"))
    result = evaluate_m30_semantic_bridge(problems, implications, solution, duplicate_ids, evidence_candidates=(_evidence(),))

    assert result.valid_causality_count == 5
    assert len(result.validated_causal_edges) == 5
    assert {edge.from_item for edge in result.validated_causal_edges if edge.relationship_id == "edge:1"} == {"root:1", "root:4"}


def test_duplicate_item_ids_make_graph_unavailable_without_silent_selection():
    problems, implications, solution, edges = _complete()
    duplicate = _problem("root:1", "root_cause", "another root")
    result = evaluate_m30_semantic_bridge((*problems, duplicate), implications, solution, edges, evidence_candidates=(_evidence(),))

    assert "DUPLICATE_ITEM_ID" in result.incompleteness_reasons
    assert result.validated_graph_available is False
    assert result.validated_causal_edges == ()


def test_solution_direction_is_not_a_causal_graph_node_or_inferred_edge():
    problems, implications, solution, edges = _complete()
    result = evaluate_m30_semantic_bridge(problems, implications, solution, edges, evidence_candidates=(_evidence(),))

    assert "solution:1" not in {item.id for item in result.admitted_node_identities}
    assert all("solution:1" not in {edge.from_item, edge.to_item} for edge in result.validated_causal_edges)


def test_endpoint_admission_correction_changes_only_affected_causality_result():
    problems, implications, solution, edges = _complete()
    unconfirmed = _problem("unconfirmed", "root_cause", state="UNCONFIRMED")
    result = evaluate_m30_semantic_bridge((*problems, unconfirmed), implications, solution, (*edges, _edge("edge:invalid", "unconfirmed", "state:1")), evidence_candidates=(_evidence(),))

    assert result.valid_causality_count == 4
    assert "edge:invalid" in result.invalid_relationship_ids
