from __future__ import annotations

from types import SimpleNamespace

from app.services.pptx_parts.native_trace_content_adapter import FailureReason, adapt_role


def _slide() -> SimpleNamespace:
    return SimpleNamespace(title="現行案件")


def _candidate(
    semantic_type: str,
    *,
    value: str = "確認済みの値",
    source_type: str = "user_text",
    authority: str = "USER_EXPLICIT",
    review_state: str = "CONFIRMED",
    inferred: bool = False,
    admissible_as_evidence: bool = True,
    source_field: str = "hearing_result",
    source_reference: str = "hearing_result:confirmed",
    **extra: object,
) -> dict[str, object]:
    return {
        "id": f"test:{semantic_type}",
        "semantic_type": semantic_type,
        "value": value,
        "source_type": source_type,
        "source_field": source_field,
        "authority": authority,
        "review_state": review_state,
        "inferred": inferred,
        "admissible_as_evidence": admissible_as_evidence,
        "source_reference": source_reference,
        **extra,
    }


def _data(*candidates: dict[str, object], **fields: object) -> SimpleNamespace:
    return SimpleNamespace(semantic_candidates={"candidates": list(candidates)}, **fields)


def test_verified_kpi_is_accepted() -> None:
    payload = adapt_role(
        "KPI",
        surface="summary",
        data=_data(_candidate("kpi_value", value="月12件")),
        context=SimpleNamespace(verified_kpi_rows=[("問い合わせ数", "月12件")]),
        slide=_slide(),
    )
    assert payload.renderable is True
    assert payload.evidence_status["kpi.current_value"] == "VERIFIED"


def test_generated_only_kpi_is_rejected() -> None:
    payload = adapt_role(
        "KPI",
        surface="summary",
        data=_data(
            _candidate(
                "kpi_value",
                source_type="analysis",
                authority="AI_PROPOSED",
                review_state="UNCONFIRMED",
                inferred=True,
                admissible_as_evidence=False,
            )
        ),
        context=SimpleNamespace(verified_kpi_rows=[("問い合わせ数", "月20件")]),
        slide=_slide(),
    )
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_structured_estimate_with_provenance_is_accepted() -> None:
    estimate = SimpleNamespace(lines=[{"name": "設計", "quantity": 1, "unit_price": 100}], total_label="100万円")
    payload = adapt_role(
        "ESTIMATE",
        surface="summary",
        data=_data(_candidate("estimate_line", value="設計")),
        context=SimpleNamespace(estimate=estimate, verified_estimate=True),
        slide=_slide(),
    )
    assert payload.renderable is True
    assert payload.evidence_status["estimate"] == "VERIFIED"


def test_budget_range_only_is_rejected_as_detailed_estimate() -> None:
    payload = adapt_role(
        "ESTIMATE",
        surface="summary",
        data=SimpleNamespace(budget_range="500万円"),
        context=SimpleNamespace(budget_range="500万円"),
        slide=_slide(),
    )
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_verified_competition_evidence_is_accepted() -> None:
    payload = adapt_role(
        "COMPETITION",
        surface="conditional",
        data=_data(_candidate("competitor_evidence", value="公開情報に基づく比較")),
        context=SimpleNamespace(competitor_rows=[["機能", "確認済み", "確認済み", "確認済み"]]),
        slide=_slide(),
    )
    assert payload.renderable is True
    assert payload.evidence_status["competition.rows"] == "VERIFIED"


def test_unsupported_competitor_claim_is_rejected() -> None:
    payload = adapt_role(
        "COMPETITION",
        surface="conditional",
        data=_data(
            _candidate(
                "competitor_claim",
                source_type="analysis",
                authority="AI_PROPOSED",
                review_state="UNCONFIRMED",
                inferred=True,
                admissible_as_evidence=False,
            )
        ),
        context=SimpleNamespace(competitor_rows=[["機能", "競合より優位", "不明", "不明"]]),
        slide=_slide(),
    )
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_explicit_win_probability_with_provenance_is_accepted() -> None:
    payload = adapt_role(
        "WIN_PROBABILITY",
        surface="conditional",
        data=_data(_candidate("win_probability", value="68%")),
        context=SimpleNamespace(win_probability=SimpleNamespace(probability=68)),
        slide=_slide(),
    )
    assert payload.renderable is True
    assert payload.text_replacements["72%"] == "68%"


def test_rank_only_win_probability_is_rejected_without_explicit_probability() -> None:
    payload = adapt_role(
        "WIN_PROBABILITY",
        surface="conditional",
        data=_data(_candidate("win_rank", value="A", source_type="analysis", authority="AI_PROPOSED", review_state="UNCONFIRMED", inferred=True, admissible_as_evidence=False)),
        context=SimpleNamespace(win_probability=SimpleNamespace(rank="A", probability=0, label="")),
        slide=_slide(),
    )
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_case_study_without_verified_image_is_rejected() -> None:
    payload = adapt_role(
        "CASE_STUDY",
        surface="detail",
        context=SimpleNamespace(case_studies=["事例: 成果あり"]),
        slide=_slide(),
    )
    assert payload.failure_reason == FailureReason.EVIDENCE_IMAGE_REQUIRED.value


def test_case_study_with_verified_permitted_image_is_accepted() -> None:
    payload = adapt_role(
        "CASE_STUDY",
        surface="detail",
        data=_data(
            _candidate(
                "case_study_image",
                value="verified-customer-image",
                source_field="case_studies.image",
                source_reference="https://example.invalid/customer-image.png",
                permission_status="approved",
            )
        ),
        context=SimpleNamespace(case_studies=["事例: 成果あり"]),
        slide=_slide(),
    )
    assert payload.renderable is True
    assert payload.evidence_status["case_study.image"] == "VERIFIED"


def test_generated_only_roi_is_rejected() -> None:
    payload = adapt_role(
        "ROI_OR_EFFECT",
        surface="detail",
        data=_data(_candidate("roi", source_type="analysis", authority="AI_PROPOSED", review_state="UNCONFIRMED", inferred=True, admissible_as_evidence=False)),
        slide=_slide(),
    )
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_risk_without_owner_likelihood_and_impact_stays_blocked() -> None:
    payload = adapt_role(
        "RISK",
        surface="detail",
        context=SimpleNamespace(risk_items=[{"title": "情報漏えい", "mitigation": "権限管理"}]),
        slide=_slide(),
    )
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value

