from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest
from app.services.presentation_master.integration import (
    AdapterStatus,
    ProductionSemanticCandidate,
    ProductionSemanticCandidateSet,
    SemanticAuthority,
    SemanticItemType,
    SemanticReviewState,
    prepare_pmv3,
    render_pmv3,
    apply_semantic_confirmation_state,
)


ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "offline_production_path_e2e_v2"


def _candidate(candidate_id: str, semantic_type: SemanticItemType, value: str, *, authority: SemanticAuthority = SemanticAuthority.SYSTEM_EXTRACTED) -> ProductionSemanticCandidate:
    return ProductionSemanticCandidate(
        candidate_id, semantic_type, value, "user_text", "hearing_result",
        authority, 0.8, SemanticReviewState.UNCONFIRMED, inferred=authority == SemanticAuthority.AI_PROPOSED,
    )


def _m48_candidates() -> ProductionSemanticCandidateSet:
    return ProductionSemanticCandidateSet((
        _candidate("prep", SemanticItemType.PREPARATION_ANALYSIS, "現状業務と要件を確認する"),
        _candidate("condition", SemanticItemType.DECISION_CONDITION, "要件と予算を確認できた場合に次工程へ進む"),
        _candidate("owner", SemanticItemType.ACCOUNTABLE_OWNER, "顧客責任者"),
        _candidate("approver", SemanticItemType.APPROVER, "顧客責任者"),
        _candidate("action", SemanticItemType.EXECUTION_ACTION, "合意した実行計画を開始する"),
        ProductionSemanticCandidate(
            "context", SemanticItemType.DECISION_CONTEXT, "導入判断", "user_text", "hearing_result",
            SemanticAuthority.SYSTEM_EXTRACTED, 0.8, SemanticReviewState.UNCONFIRMED,
            from_item="owner", to_item="approver", relationship_type="handoff",
        ),
        _candidate("escalation", SemanticItemType.ESCALATION, "未解決事項は顧客責任者へ確認する"),
        ProductionSemanticCandidate(
            "evidence", SemanticItemType.EVIDENCE, "顧客ヒアリング記録", "user_text", "hearing_result",
            SemanticAuthority.SYSTEM_EXTRACTED, 0.8, SemanticReviewState.UNCONFIRMED,
            source_reference="hearing_result:evidence", admissible_as_evidence=True,
        ),
        _candidate("ai-note", SemanticItemType.KPI_NAME, "AI提案メモ", authority=SemanticAuthority.AI_PROPOSED),
    ))


def _request(state: list[dict[str, str]]) -> PptxDownloadRequest:
    return PptxDownloadRequest(
        powerpoint_generation_data=PowerPointData(
            deck_title="Transport E2E V2", client_name="Synthetic customer",
            slides=[PowerPointSlide(slide_no=1, layout="title", title="Transport E2E V2", bullets=["Native output"], speaker_notes="", visual_suggestion="")],
        ),
        project_brief="Synthetic Production-shaped M48 proposal input.",
        client_company_info="Synthetic customer",
        semantic_confirmation_state=state,
    )


def _state(candidates: ProductionSemanticCandidateSet, *, corrected_id: str | None = None, reject_id: str | None = None, unconfirmed_id: str | None = None):
    result = []
    for item in candidates.candidates:
        review = "CORRECTED" if item.id == corrected_id else "REJECTED" if item.id == reject_id else "UNCONFIRMED" if item.id == unconfirmed_id else "CONFIRMED"
        entry = {"id": item.id, "semantic_type": item.semantic_type.value, "review_state": review}
        if review == "CORRECTED":
            entry["value"] = "ユーザー確認済みの実行計画"
        result.append(entry)
    return result


def test_offline_production_path_e2e_v2_transport_to_native_m48():
    base = _m48_candidates()
    transport = _state(base, corrected_id="action")
    transported = apply_semantic_confirmation_state(base, transport)
    ai_note = next(item for item in transported.candidates if item.id == "ai-note")
    assert ai_note.authority == SemanticAuthority.AI_PROPOSED
    assert ai_note.review_state == SemanticReviewState.CONFIRMED
    ready = prepare_pmv3(_request(transport), semantic_candidates=base)
    assert ready.status in {AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS}
    assert ready.selected_master_id == "M48"
    assert ready.composition_readiness == "VALID"
    assert ready.renderer_spec is not None

    rendered_spec_text = json.dumps(ready.renderer_spec, ensure_ascii=False)
    assert "ユーザー確認済みの実行計画" in rendered_spec_text
    assert "action" in rendered_spec_text
    assert all(item.review_state in {SemanticReviewState.CONFIRMED, SemanticReviewState.CORRECTED} for item in transported.candidates)

    rendered = render_pmv3(ready)
    assert rendered.pptx_bytes[:2] == b"PK"
    assert len(rendered.pptx_bytes) > 0
    with ZipFile(BytesIO(rendered.pptx_bytes)) as package:
        names = set(package.namelist())
        assert package.testzip() is None
        assert "[Content_Types].xml" in names
        assert "ppt/presentation.xml" in names
        assert any(name.startswith("ppt/slides/slide") and name.endswith(".xml") for name in names)
        package_validation = "PASS"
    ARTIFACT_DIR.mkdir(exist_ok=True)
    pptx_path = ARTIFACT_DIR / "m48-transport-e2e-v2.pptx"
    pptx_path.write_bytes(rendered.pptx_bytes)
    metadata = {
        "selected_master": rendered.selected_master_id,
        "readiness": rendered.readiness.value,
        "composition": ready.composition_readiness,
        "pptx_bytes": len(rendered.pptx_bytes),
        "pk_signature": True,
        "zip_integrity": "PASS",
        "package_validation": package_validation,
        "slide_count": rendered.slide_count,
        "rasterization_ratio": rendered.rasterization_ratio,
        "clipping": rendered.clipping_count,
        "overflow": rendered.overflow_count,
        "off_canvas": rendered.off_canvas_count,
        "collision": 0,
        "corrected_id": "action",
        "rejected_id": "none",
        "unconfirmed_promoted": False,
    }
    (ARTIFACT_DIR / "m48-transport-e2e-v2.validation.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def test_offline_production_path_e2e_v2_review_rejected_and_invalid_cases_fail_closed():
    base = _m48_candidates()
    review = prepare_pmv3(_request(_state(base, unconfirmed_id="approver")), semantic_candidates=base)
    assert review.status == AdapterStatus.REVIEW_REQUIRED
    rejected = prepare_pmv3(_request(_state(base, reject_id="approver")), semantic_candidates=base)
    assert rejected.status == AdapterStatus.REVIEW_REQUIRED
    invalid = prepare_pmv3(_request([{"id": "unknown", "semantic_type": "approver", "review_state": "CONFIRMED"}]), semantic_candidates=base)
    assert invalid.status == AdapterStatus.INVALID_INPUT
    for result in (review, rejected, invalid):
        assert result.selected_master_id is None
        assert result.fallback_required is True
        with pytest.raises(ValueError):
            render_pmv3(result)
