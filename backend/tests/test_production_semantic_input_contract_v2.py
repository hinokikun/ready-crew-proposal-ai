from __future__ import annotations

import asyncio
from io import BytesIO
from dataclasses import replace
import inspect
from types import SimpleNamespace
from zipfile import ZipFile

import pytest

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest, ProposalRequest
from app.services.presentation_master.integration import (
    AdapterStatus, ProductionSemanticCandidate, ProductionSemanticCandidateSet,
    SemanticAuthority, SemanticItemType, SemanticReviewState, build_adapter_input,
    build_semantic_envelope_from_confirmed_candidates, confirm_candidate,
    correct_candidate, extract_explicit_candidates, prepare_pmv3,
    propose_candidates_from_analysis, reject_candidate, render_pmv3,
)
from app.services.presentation_master.integration.production_semantic_contract import candidate_set_to_dict


def _request(text: str = "案件概要") -> PptxDownloadRequest:
    return PptxDownloadRequest(
        project_brief=text, client_company_info="Synthetic customer",
        powerpoint_generation_data=PowerPointData(
            deck_title="M48 contract deck", client_name="Synthetic customer",
            slides=[PowerPointSlide(slide_no=1, layout="title", title="M48 contract", bullets=["Synthetic source"], speaker_notes="", visual_suggestion="")],
        ),
    )


def _candidate(candidate_id, semantic_type, value, *, source_field="hearing_result", authority=SemanticAuthority.USER_EXPLICIT, review=SemanticReviewState.CONFIRMED, **kwargs):
    return ProductionSemanticCandidate(candidate_id, semantic_type, value, "user_text", source_field, authority, 0.95, review, **kwargs)


def _confirmed_m48():
    return ProductionSemanticCandidateSet((
        _candidate("prep", SemanticItemType.PREPARATION_ANALYSIS, "現状業務と要件を確認する"),
        _candidate("condition", SemanticItemType.DECISION_CONDITION, "要件と予算を確認できた場合に次工程へ進む"),
        _candidate("owner", SemanticItemType.ACCOUNTABLE_OWNER, "顧客責任者"),
        _candidate("approver", SemanticItemType.APPROVER, "顧客責任者"),
        _candidate("action", SemanticItemType.EXECUTION_ACTION, "合意した実行計画を開始する"),
        _candidate("context", SemanticItemType.DECISION_CONTEXT, "導入判断", from_item="owner", to_item="approver", relationship_type="handoff"),
        _candidate("escalation", SemanticItemType.ESCALATION, "未解決事項は顧客責任者へ確認する"),
        _candidate("evidence", SemanticItemType.EVIDENCE, "顧客ヒアリング記録", source_field="hearing_result", source_reference="hearing_result:evidence", admissible_as_evidence=True),
    ))


def test_candidate_model_and_authority_validation():
    candidate = _candidate("ai-condition", SemanticItemType.DECISION_CONDITION, "AI proposal", authority=SemanticAuthority.AI_PROPOSED, review=SemanticReviewState.UNCONFIRMED, inferred=True)
    assert candidate.admissible_for_supply is False
    with pytest.raises(ValueError):
        ProductionSemanticCandidate("", SemanticItemType.EVIDENCE, "x", "x", "x", SemanticAuthority.USER_EXPLICIT, 1, SemanticReviewState.CONFIRMED)


def test_ai_confirmation_correction_and_rejection_preserve_provenance():
    ai = _candidate("ai-owner", SemanticItemType.ACCOUNTABLE_OWNER, "AI proposed owner", authority=SemanticAuthority.AI_PROPOSED, review=SemanticReviewState.UNCONFIRMED, inferred=True)
    confirmed = confirm_candidate(ai)
    assert confirmed.authority == SemanticAuthority.AI_PROPOSED and confirmed.review_state == SemanticReviewState.CONFIRMED
    assert confirmed.confirmation_authority == SemanticAuthority.USER_EXPLICIT
    corrected = correct_candidate(ai, "ユーザー指定責任者")
    assert corrected.authority == SemanticAuthority.USER_EXPLICIT and corrected.review_state == SemanticReviewState.CORRECTED
    assert corrected.original_candidate_id == "ai-owner"
    assert reject_candidate(ai).review_state == SemanticReviewState.REJECTED


def test_deterministic_extraction_is_traceable_and_ai_proposals_stay_unconfirmed():
    extracted = extract_explicit_candidates(_request("案件概要\n責任者: 業務責任者\n承認者: 顧客承認者\n判断条件: 要件確認"))
    assert {item.semantic_type for item in extracted.candidates} == {SemanticItemType.ACCOUNTABLE_OWNER, SemanticItemType.APPROVER, SemanticItemType.DECISION_CONDITION}
    assert all(item.authority == SemanticAuthority.SYSTEM_EXTRACTED and item.review_state == SemanticReviewState.CONFIRMED for item in extracted.candidates)
    proposed = propose_candidates_from_analysis(SimpleNamespace(proposal_policy="実行計画を提案", quality_check=SimpleNamespace(human_review_notes="承認条件を確認")))
    assert proposed.candidates
    assert all(item.authority == SemanticAuthority.AI_PROPOSED and item.review_state == SemanticReviewState.UNCONFIRMED for item in proposed.candidates)


def test_unconfirmed_rejected_and_missing_evidence_never_reach_ready():
    confirmed = _confirmed_m48()
    unconfirmed = ProductionSemanticCandidateSet(confirmed.candidates[:-1] + (_candidate("ai-action", SemanticItemType.EXECUTION_ACTION, "AI action", authority=SemanticAuthority.AI_PROPOSED, review=SemanticReviewState.UNCONFIRMED, inferred=True),))
    assert prepare_pmv3(_request(), semantic_candidates=unconfirmed).status == AdapterStatus.REVIEW_REQUIRED
    rejected = ProductionSemanticCandidateSet(tuple(reject_candidate(item) if item.id == "approver" else item for item in confirmed.candidates))
    assert prepare_pmv3(_request(), semantic_candidates=rejected).status == AdapterStatus.REVIEW_REQUIRED
    no_evidence = ProductionSemanticCandidateSet(tuple(item for item in confirmed.candidates if item.id != "evidence"))
    assert prepare_pmv3(_request(), semantic_candidates=no_evidence).status in {AdapterStatus.REVIEW_REQUIRED, AdapterStatus.NO_MATCH, AdapterStatus.NOT_READY}


def test_confirmed_production_supply_reaches_m48_and_renders_native_pptx():
    candidates = _confirmed_m48()
    envelope = build_semantic_envelope_from_confirmed_candidates(candidates)
    assert envelope.decision_context == "department_head"
    prepared = prepare_pmv3(build_adapter_input(_request(), semantic_candidates=candidates))
    assert prepared.status in {AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS}
    assert prepared.selected_master_id == "M48" and prepared.composition_readiness == "VALID"
    rendered = render_pmv3(prepared)
    assert rendered.pptx_bytes[:2] == b"PK" and len(rendered.pptx_bytes) > 0
    assert rendered.rasterization_ratio == 0
    assert rendered.clipping_count == 0
    assert rendered.overflow_count == 0
    assert rendered.off_canvas_count == 0
    with ZipFile(BytesIO(rendered.pptx_bytes)) as package:
        names = set(package.namelist())
        assert "[Content_Types].xml" in names and "ppt/presentation.xml" in names
        assert package.testzip() is None
        assert any(name.startswith("ppt/slides/slide") and name.endswith(".xml") for name in names)


def test_analysis_response_optional_field_remains_backward_compatible():
    from app.models import AnalysisResponse
    field = AnalysisResponse.__fields__["semantic_candidates"]
    assert field.allow_none is True and field.required is False


def test_analysis_generation_assigns_present_semantic_candidates_for_mock_path():
    from app import config
    from app.services import openai_service

    original_use_mock_ai = config.settings.use_mock_ai
    object.__setattr__(config.settings, "use_mock_ai", True)
    try:
        response = asyncio.run(openai_service.generate_proposal(ProposalRequest(project_brief="既存業務の改善とAI導入を検討する案件です。")))
    finally:
        object.__setattr__(config.settings, "use_mock_ai", original_use_mock_ai)

    assert isinstance(response.semantic_candidates, dict)
    assert isinstance(response.semantic_candidates.get("candidates"), list)


def test_candidate_set_serialization_preserves_empty_nonempty_and_metadata():
    empty = candidate_set_to_dict(ProductionSemanticCandidateSet())
    assert empty == {"candidates": []}

    candidate = _candidate(
        "evidence-1",
        SemanticItemType.EVIDENCE,
        "顧客ヒアリング記録",
        source_field="hearing_result",
        source_reference="hearing_result:evidence",
        admissible_as_evidence=True,
    )
    serialized = candidate_set_to_dict(ProductionSemanticCandidateSet((candidate,)))
    assert serialized["candidates"] == [{
        "id": "evidence-1",
        "semantic_type": "evidence",
        "value": "顧客ヒアリング記録",
        "source_type": "user_text",
        "source_field": "hearing_result",
        "authority": "USER_EXPLICIT",
        "confidence": 0.95,
        "review_state": "CONFIRMED",
        "inferred": False,
        "admissible_as_evidence": True,
        "source_reference": "hearing_result:evidence",
        "from_item": "",
        "to_item": "",
        "relationship_type": "",
        "original_candidate_id": "",
        "confirmation_authority": None,
    }]


def test_candidate_assignment_is_after_both_analysis_branches_and_preserves_fail_closed_contract():
    from app.services.openai_service import generate_proposal

    source = inspect.getsource(generate_proposal)
    assert "if settings.use_mock_ai:" in source
    assert "else:" in source
    assert "semantic_candidates = ProductionSemanticCandidateSet" in source
    assert "semantic_candidates=candidate_set_to_dict(semantic_candidates)" in source


def test_transported_frontend_state_reaches_m48_supply_without_envelope_shortcut():
    base = _confirmed_m48()
    transport = [
        {"id": item.id, "semantic_type": item.semantic_type.value, "review_state": "CONFIRMED"}
        for item in base.candidates
    ]
    payload = _request()
    payload.semantic_confirmation_state = transport
    prepared = prepare_pmv3(payload, semantic_candidates=base)
    assert prepared.status in {AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS}
    assert prepared.selected_master_id == "M48"
    assert prepared.composition_readiness == "VALID"


def test_transported_unconfirmed_and_rejected_critical_states_remain_blocked():
    base = _confirmed_m48()
    ai_base = ProductionSemanticCandidateSet(tuple(replace(item, authority=SemanticAuthority.AI_PROPOSED, review_state=SemanticReviewState.UNCONFIRMED, inferred=True, confirmation_authority=None) for item in base.candidates))
    unconfirmed = [{"id": item.id, "semantic_type": item.semantic_type.value, "review_state": "UNCONFIRMED"} for item in ai_base.candidates]
    unconfirmed_payload = _request()
    unconfirmed_payload.semantic_confirmation_state = unconfirmed
    assert prepare_pmv3(unconfirmed_payload, semantic_candidates=ai_base).status == AdapterStatus.REVIEW_REQUIRED
    rejected = [{"id": item.id, "semantic_type": item.semantic_type.value, "review_state": "REJECTED" if item.id == "approver" else "CONFIRMED"} for item in base.candidates]
    rejected_payload = _request()
    rejected_payload.semantic_confirmation_state = rejected
    assert prepare_pmv3(rejected_payload, semantic_candidates=base).status == AdapterStatus.REVIEW_REQUIRED
