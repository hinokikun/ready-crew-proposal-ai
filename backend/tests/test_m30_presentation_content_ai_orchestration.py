from dataclasses import FrozenInstanceError, replace
import json

import pytest

from app.models import BusinessImplicationTransportItem, ProblemObjectTransportItem, SolutionDirectionTransportItem
from app.services.presentation_master.integration.m30_presentation_content_ai_orchestration import (
    M30PresentationContentAIOrchestrationResult,
    PresentationContentProposalFailure,
    orchestrate_m30_presentation_content_ai,
)
from app.services.presentation_master.integration.m30_semantic_bridge import evaluate_m30_semantic_bridge
from app.services.presentation_master.integration.presentation_content_ai_proposals import build_presentation_content_candidate
from app.services.presentation_master.integration.presentation_content_candidates import PresentationContentField, PresentationContentSourceIdentity


def _problem(item_id, role, value, state="CONFIRMED"):
    return ProblemObjectTransportItem(id=item_id, role=role, value=value, source_type="user_input", source_field=role, source_reference=f"step1:{item_id}", authority="USER_EXPLICIT", review_state=state, confirmation_authority="USER_EXPLICIT")


def _evaluation():
    objects = [_problem("issue", "visible_issue", "visible issue")]
    objects += [_problem(f"root-{i}", "root_cause", f"root {i}") for i in range(1, 5)]
    objects += [_problem(f"state-{i}", "causal_state", f"state {i}") for i in range(1, 6)]
    implications = [BusinessImplicationTransportItem(id=f"imp-{i}", value=f"implication {i}", source_type="user_input", source_field="business_implication", source_reference=f"step1:imp-{i}", authority="USER_EXPLICIT", review_state="CONFIRMED", confirmation_authority="USER_EXPLICIT") for i in range(1, 5)]
    solution = SolutionDirectionTransportItem(id="solution", value="solution", source_type="user_input", source_field="solution_direction", source_reference="step1:solution", authority="USER_EXPLICIT", review_state="CONFIRMED", confirmation_authority="USER_EXPLICIT")
    relationships = ()
    evidence = ()
    result = evaluate_m30_semantic_bridge(objects, implications, solution, relationships, evidence_candidates=())
    return replace(result, m30_semantic_complete=True, incompleteness_reasons=())


def _proposal(request):
    values = tuple(PresentationContentField(role, f"AI {role}") for role in request.requested_field_roles)
    from app.services.presentation_master.integration.presentation_content_ai_proposals import ParsedPresentationContentAIProposal
    return build_presentation_content_candidate(request, ParsedPresentationContentAIProposal(values))


def _revision(role, sources, fields):
    return f"rev:{role}:{','.join(fields)}"


def test_result_and_failure_are_immutable():
    failure = PresentationContentProposalFailure("root_cause", ("title",), "x")
    assert isinstance(failure, PresentationContentProposalFailure)
    with pytest.raises(FrozenInstanceError):
        failure.safe_error_category = "changed"
    result = M30PresentationContentAIOrchestrationResult(None, (), (), (), False, True)
    with pytest.raises(FrozenInstanceError):
        result.failures = ()


def test_complete_m30_reuses_projection_and_groups_into_nine_requests():
    calls = []
    def proposal(request):
        calls.append(request)
        return _proposal(request)
    result = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=proposal, revision_provider=_revision)
    assert result.acquisition_projection.acquisition_plan_complete is True
    assert len(calls) == 9
    assert len(result.ai_proposal_candidates) == 9
    assert result.failures == ()
    assert result.content_acquisition_complete_for_human_review is True
    assert result.presentation_framing_required is True


def test_visible_issue_fields_are_one_request_in_frozen_order():
    calls = []
    orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=lambda request: calls.append(request) or _proposal(request), revision_provider=_revision)
    visible = next(request for request in calls if request.semantic_role == "visible_issue")
    assert visible.requested_field_roles == ("title", "accent", "subtitle")


def test_direct_fields_are_not_sent_to_ai_and_sources_are_exactly_bound():
    calls = []
    orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=lambda request: calls.append(request) or _proposal(request), revision_provider=_revision)
    requested = {(request.semantic_role, role) for request in calls for role in request.requested_field_roles}
    assert ("root_cause", "body") not in requested
    assert ("causal_state", "statement") not in requested
    assert ("business_implication", "body") not in requested
    assert ("solution_direction", "statement") not in requested
    assert all(request.source_identities[0].source_item_id in {"issue", *[f"root-{i}" for i in range(1, 5)], *[f"imp-{i}" for i in range(1, 5)]} for request in calls)


def test_upstream_order_and_revision_provider_are_preserved():
    calls = []
    def revision(role, sources, fields):
        calls.append((role, tuple(source.source_item_id for source in sources), fields))
        return "system-revision"
    result = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=lambda request: _proposal(request), revision_provider=revision)
    assert [role for role, _, _ in calls] == ["visible_issue", *(["root_cause"] * 4), *(["business_implication"] * 4)]
    assert all(request.candidate_id.startswith("presentation-ai:") for request in result.ai_proposal_candidates)


def test_all_ai_candidates_remain_unconfirmed_and_inadmissible():
    result = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=lambda request: _proposal(request), revision_provider=_revision)
    assert all(candidate.derivation_type.value == "SEMANTIC_DERIVATION" for candidate in result.ai_proposal_candidates)
    assert all(candidate.authority.value == "AI_PROPOSED" for candidate in result.ai_proposal_candidates)
    assert all(candidate.review_state.value == "UNCONFIRMED" for candidate in result.ai_proposal_candidates)
    assert all(candidate.confirmation_authority is None for candidate in result.ai_proposal_candidates)


def test_revision_change_changes_identity_through_frozen_builder():
    first = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=lambda request: _proposal(request), revision_provider=lambda *_: "r1")
    second = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=lambda request: _proposal(request), revision_provider=lambda *_: "r2")
    assert first.ai_proposal_candidates[0].candidate_id != second.ai_proposal_candidates[0].candidate_id


@pytest.mark.parametrize("bad", ["wrong-role", "wrong-fields", "wrong-source", "wrong-fingerprint", "confirmed", "malformed"])
def test_invalid_injected_candidate_is_rejected(bad):
    def proposal(request):
        candidate = _proposal(request)
        if bad == "wrong-role":
            return replace(candidate, semantic_role="other")
        if bad == "wrong-fields":
            return replace(candidate, fields=(PresentationContentField("other", "x"),))
        if bad == "wrong-source":
            return replace(candidate, source_identities=(PresentationContentSourceIdentity("other", request.semantic_role, "x"),))
        if bad == "wrong-fingerprint":
            return replace(candidate, source_fingerprint="0" * 64)
        if bad == "confirmed":
            return replace(candidate, review_state="CONFIRMED", authority="USER_EXPLICIT", confirmation_authority="USER_EXPLICIT")
        return object()
    result = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=proposal, revision_provider=_revision)
    assert len(result.ai_proposal_candidates) == 0
    assert len(result.failures) == 9
    assert result.content_acquisition_complete_for_human_review is False


def test_one_failure_isolated_and_successful_groups_retained_without_fallback():
    seen = []
    def proposal(request):
        seen.append(request.semantic_role + ":" + request.source_identities[0].source_item_id)
        if request.semantic_role == "root_cause" and request.source_identities[0].source_item_id == "root-2":
            raise RuntimeError("private raw model output must not be recorded")
        return _proposal(request)
    result = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=proposal, revision_provider=_revision)
    assert len(seen) == 9
    assert len(result.ai_proposal_candidates) == 8
    assert len(result.failures) == 1
    assert result.failures[0].safe_error_category == "proposal_failure"
    assert "root-2" not in result.failures[0].safe_error_category
    assert result.content_acquisition_complete_for_human_review is False


def test_incomplete_upstream_evaluation_makes_no_ai_calls():
    calls = []
    evaluation = replace(_evaluation(), m30_semantic_complete=False, incompleteness_reasons=("ROOT_CAUSE_INSUFFICIENT",))
    result = orchestrate_m30_presentation_content_ai(evaluation, proposal_callable=lambda request: calls.append(request) or _proposal(request), revision_provider=_revision)
    assert calls == []
    assert result.ai_proposal_candidates == ()
    assert result.content_acquisition_complete_for_human_review is False


def test_no_human_transition_or_final_slot_ready_contract_is_used():
    result = orchestrate_m30_presentation_content_ai(_evaluation(), proposal_callable=lambda request: _proposal(request), revision_provider=_revision)
    assert not any(name in str(type(item)) for item in result.ai_proposal_candidates for name in ("SlotReadyContentPack", "PresentationFraming"))
    assert not any("confirm" in name or "correct" in name or "reject" in name for name in dir(result))
