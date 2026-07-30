from __future__ import annotations

import asyncio

import pytest

from app.models import ProposalRequest
from app.services.openai_service import generate_proposal
from app.services.sales_consultant_engine import (
    build_sales_consultant_brief,
    build_sales_consultant_prompt_section,
)


def _request(**overrides: str) -> ProposalRequest:
    data = {
        "project_brief": (
            "製造業の検査部門で、商品画像の目視確認と品質分類に時間がかかっています。"
            "AI画像認識で候補を提示し、人が最終確認するPoCを行いたいです。"
        ),
        "client_company_info": "東都製作所\n担当: 品質管理部長",
        "competitor_company_name": "画像検査AIベンダー",
        "desired_launch_timing": "2027年5月頃",
        "budget_range": "1000万円以内",
        "special_function_required": "AI画像認識、API連携、CSV出力、判定履歴の活用",
        "hearing_result": "繁忙期の処理遅延と判定基準のばらつきが課題です。",
        "own_service_info": "PoC設計、AIモデル検証、確認UI、既存システム連携を支援できます。",
        "case_studies": "製造業向けの検査業務改善で、確認時間削減と品質標準化を支援した実績があります。",
    }
    data.update(overrides)
    return ProposalRequest(**data)


def test_sales_consultant_engine_infers_customer_and_win_strategy() -> None:
    brief = build_sales_consultant_brief(_request())

    assert brief.customer.industry.value == "製造業"
    assert brief.customer.ai_usage.value == "AI導入検討中"
    assert brief.decision_maker.primary_decision_maker == "部長"
    assert "品質" in brief.proposal_strategy or "AI" in brief.proposal_strategy
    assert brief.win_strategy
    assert brief.value_proposition
    assert len(brief.objections) >= 4
    assert len(brief.roadmap) >= 5
    assert brief.confidence >= 0.7


def test_sales_consultant_engine_marks_missing_information_as_hypothesis() -> None:
    brief = build_sales_consultant_brief(
        _request(
            client_company_info="",
            competitor_company_name="",
            desired_launch_timing="",
            budget_range="",
            case_studies="",
        )
    )

    assert "予算上限" in brief.missing_information
    assert "希望時期" in brief.missing_information
    assert "競合情報" in brief.missing_information
    assert any(item.kind == "hypothesis" for item in [brief.customer.company_size, brief.customer.budget_sense])
    assert brief.confidence < 0.8


def test_sales_consultant_prompt_is_internal_and_strategy_rich() -> None:
    section = build_sales_consultant_prompt_section(build_sales_consultant_brief(_request()))

    assert "Internal Sales Consultant Strategy Context" in section
    assert "Do not show internal engine names" in section
    assert "Winning strategy" in section
    assert "Likely objections" in section
    assert "Senior consultant review notes" in section


def test_generate_proposal_uses_sales_consultant_strategy(monkeypatch: pytest.MonkeyPatch) -> None:
    from app import config
    from app.services import openai_service

    object.__setattr__(config.settings, "use_mock_ai", True)
    object.__setattr__(openai_service.settings, "use_mock_ai", True)

    response = asyncio.run(generate_proposal(_request()))
    analysis = response.analysis
    deck_text = "\n".join(
        [analysis.project_summary, analysis.proposal_policy, analysis.proposal_story]
        + [slide.title for slide in analysis.powerpoint_generation_data.slides]
        + [bullet for slide in analysis.powerpoint_generation_data.slides for bullet in slide.bullets]
    )

    assert "提案戦略" in analysis.proposal_policy
    assert "勝ち筋" in analysis.proposal_policy
    assert "経営層向け提案サマリー" in deck_text
    assert "想定される懸念と回答" in deck_text
    assert "ROI/KPI設計" in deck_text
    assert "導入ロードマップ" in deck_text
    assert "AI Sales Consultant" not in deck_text
    assert response.powerpoint_generation_data == analysis.powerpoint_generation_data
