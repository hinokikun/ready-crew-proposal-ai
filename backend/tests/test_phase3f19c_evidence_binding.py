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
    rows = [
        {"criterion": "導入スピード", "own_value": "確認済み3か月", "competitor_a_value": "確認済み4か月", "competitor_b_value": "確認済み5か月", "evaluation": "条件確認済み"},
        {"criterion": "提案の具体性", "own_value": "確認済み詳細", "competitor_a_value": "確認済み概略", "competitor_b_value": "確認済み一部", "evaluation": "条件確認済み"},
        {"criterion": "AI活用実績", "own_value": "確認済み実績", "competitor_a_value": "確認済み限定", "competitor_b_value": "確認済みPoC", "evaluation": "条件確認済み"},
        {"criterion": "運用伴走", "own_value": "確認済み定例", "competitor_a_value": "確認済み限定", "competitor_b_value": "確認済み別契約", "evaluation": "条件確認済み"},
        {"criterion": "コスト透明性", "own_value": "確認済み明示", "competitor_a_value": "確認済み粗い", "competitor_b_value": "確認済み条件", "evaluation": "条件確認済み"},
    ]
    payload = adapt_role(
        "COMPETITION",
        surface="conditional",
        data=_data(_candidate("competitor_evidence", value="公開情報に基づく比較")),
        context=SimpleNamespace(
            competitor_a_name="比較対象A",
            competitor_b_name="比較対象B",
            competitor_rows=rows,
            differentiation_bullets=["確認済み支援範囲", "確認済み運用設計", "確認済み費用条件", "確認済み改善支援"],
            caution_items=["確認済み比較条件", "未確認事項は次回確認"],
            next_confirmation_items=["決裁条件を確認", "契約条件を確認", "実施時期を確認"],
            recommendation="確認済み比較根拠に基づき判断します。",
        ),
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
    evidence_rows = [
        {"item": "課題の明確性", "content": "確認済み課題", "weight": "高", "evaluation": "強い"},
        {"item": "決裁者接点", "content": "確認済み接点", "weight": "高", "evaluation": "強い"},
        {"item": "予算感", "content": "確認済み予算", "weight": "中", "evaluation": "普通"},
        {"item": "導入時期", "content": "確認済み時期", "weight": "中", "evaluation": "普通"},
        {"item": "競合比較", "content": "確認済み根拠", "weight": "中", "evaluation": "確認中"},
    ]
    payload = adapt_role(
        "WIN_PROBABILITY",
        surface="conditional",
        data=_data(_candidate("win_probability", value="68%")),
        context=SimpleNamespace(
            win_probability=SimpleNamespace(
                probability=68,
                period="2026年下期",
                confidence="中",
                confidence_summary="確認済みの中程度の確度です。",
                reason="確認済みの課題適合性を確認しています。",
                positive_factors=["確認済み課題", "確認済み接点", "確認済み予算", "確認済み時期"],
                risk_factors=["予算承認", "競合比較", "体制確認", "開始時期"],
                next_action_cards=[
                    {"title": "決裁条件の確認", "body": "決裁条件を確認します。"},
                    {"title": "予算の合意", "body": "予算条件を合意します。"},
                    {"title": "導入時期の確定", "body": "導入時期を確定します。"},
                ],
                decision_direction="次回確認で導入条件を確定します。",
                evidence_rows=evidence_rows,
            )
        ),
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

