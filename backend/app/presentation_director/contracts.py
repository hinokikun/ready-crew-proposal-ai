"""Input contract builders for the Presentation Director."""

from __future__ import annotations

from typing import Any

from app.presentation_composer import CaseContext

from .models import PresentationDirectorInput


def build_director_input(
    case: CaseContext,
    *,
    presentation_time_minutes: int = 30,
    current_sales_stage: str | None = None,
    meeting_purpose: str | None = None,
    expected_outcome: str | None = None,
    version9_design_contract: dict[str, Any] | None = None,
    sales_consultant_output: dict[str, Any] | None = None,
    customer_ready_validation_output: dict[str, Any] | None = None,
) -> PresentationDirectorInput:
    """Build a safe offline input without requiring API, DB, or frontend changes."""

    lower = " ".join([case.budget, case.timeline, case.project_summary, case.category]).lower()
    is_poc = "poc" in lower or "検証" in lower
    stage = current_sales_stage or ("PoC具体提案" if is_poc else "具体提案")
    purpose = meeting_purpose or ("PoC条件と次回合意事項を確定する" if is_poc else "提案内容と次の意思決定を合意する")
    outcome = expected_outcome or ("PoC範囲・評価指標・開始条件への合意" if is_poc else "次フェーズ実施への合意")

    return PresentationDirectorInput(
        case_id=case.case_id,
        case_name=case.case_name,
        client_name=case.client_name,
        industry=case.industry,
        company_size="unknown",
        proposal_category=case.category,
        decision_maker=case.decision_maker,
        secondary_audience="現場責任者 / 情報システム" if "現場" in case.decision_maker or "情報" in case.decision_maker else "unknown",
        current_sales_stage=stage,
        meeting_purpose=purpose,
        presentation_time_minutes=presentation_time_minutes,
        expected_outcome=outcome,
        customer_concerns=case.pain_points,
        customer_maturity="hypothesis",
        budget_status="known" if case.budget else "unknown",
        evidence_availability="hypothesis",
        kpi_availability="known" if case.expected_outcomes else "requires_confirmation",
        roi_availability="requires_confirmation",
        competitive_situation=case.competitor or "unknown",
        implementation_complexity="hypothesis",
        risk_level="hypothesis",
        proposal_context=case.to_dict(),
        sales_consultant_output=sales_consultant_output or {},
        version9_design_contract=version9_design_contract or {},
        customer_ready_validation_output=customer_ready_validation_output or {},
    )
