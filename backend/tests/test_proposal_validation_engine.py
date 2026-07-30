from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.models import PowerPointData, PowerPointSlide
from app.services.proposal_validation_engine import run_golden_validation_suite, validate_proposal


def _customer_ready_deck() -> PowerPointData:
    return PowerPointData(
        deck_title="AI-OCR導入支援 提案書",
        client_name="サンプル株式会社",
        slides=[
            _slide(1, "Executive Summary: 結論と投資価値", ["現状課題、解決策、ROI、期待効果を2分で理解できる構成です。"], "hero", "KPIカード"),
            _slide(2, "現状と課題", ["現状、課題、原因を分けて整理し、処理遅延と品質ばらつきを示します。"], "problem", "課題マップ"),
            _slide(3, "勝ち筋と競合差別化", ["想定競合、勝ち筋、差別化、確認事項を分けて説明します。"], "comparison", "比較カード"),
            _slide(4, "提案する解決策", ["AI候補提示、人の確認、API連携、運用改善で安全に導入します。"], "solution", "Before After フロー"),
            _slide(5, "KPIとROI", ["現状値、目標値、測定方法、測定タイミング、担当を定義します。"], "kpi", "KPIダッシュボード"),
            _slide(6, "導入ロードマップ", ["PoC、検証、本番導入、運用改善の判断ポイントを置きます。"], "timeline", "ロードマップ"),
            _slide(7, "リスクと対策", ["セキュリティ、運用、教育、障害時、データ連携のリスクを管理します。"], "risk", "リスクマトリクス"),
            _slide(8, "概算見積と次アクション", ["必須、推奨、オプションを分け、次回確認事項を合意します。"], "estimate", "見積カードとCTA"),
        ],
    )


def _weak_deck() -> PowerPointData:
    return PowerPointData(
        deck_title="提案",
        client_name="Client",
        slides=[
            PowerPointSlide(
                slide_no=1,
                layout="title_body",
                title="情報一覧",
                bullets=[
                    "説明が不足しています。",
                    "価格、ROI、競合、リスク、次アクションの説明がありません。",
                    "詳細情報がなく、顧客が意思決定できません。",
                    "内部確認が必要です。",
                    "文章中心です。",
                    "図解がありません。",
                    "根拠がありません。",
                    "改善が必要です。",
                ],
                speaker_notes="",
                visual_suggestion="",
            )
        ],
    )


def _slide(no: int, title: str, bullets: list[str], layout: str, visual: str) -> PowerPointSlide:
    return PowerPointSlide(
        slide_no=no,
        layout=layout,
        title=title,
        bullets=bullets,
        speaker_notes="顧客の意思決定に必要な根拠、リスク、次アクションを説明します。",
        visual_suggestion=visual,
    )


def _dump(data: PowerPointData) -> dict[str, Any]:
    if hasattr(data, "model_dump"):
        return data.model_dump()
    return data.dict()


def test_validation_engine_returns_customer_ready_acceptance() -> None:
    result = validate_proposal(_customer_ready_deck(), {"decision_maker": "経営者", "industry": "AI"})

    assert result.release_judge == "CUSTOMER_READY"
    assert result.acceptance_scores.total_score >= 85
    assert result.human_acceptance_prediction.no_revision_probability >= 85
    assert result.human_acceptance_prediction.thirty_min_revision_probability >= 90
    assert len(result.persona_reviews) == 6
    assert len(result.benchmark_reviews) == 6
    assert len(result.customer_questions) == 20
    assert len(result.slide_reviews) == 8
    assert result.regression_quality.average_improvement_rate > 0


def test_validation_engine_blocks_weak_customer_deck() -> None:
    result = validate_proposal(_weak_deck())

    assert result.release_judge in {"NOT_READY", "REVIEW_REQUIRED"}
    assert result.acceptance_scores.total_score < 85
    assert result.required_fixes
    assert any(item.issue for item in result.red_team_findings)
    assert any(item.category in {"bullet_count", "diagram_missing", "text_volume"} for item in result.visual_qa_findings)


def test_validation_engine_includes_benchmark_and_persona_reviews() -> None:
    result = validate_proposal(_customer_ready_deck(), {"decision_maker": "経営者", "industry": "AI"})

    assert {review.persona for review in result.persona_reviews} == {
        "営業部長",
        "営業マネージャー",
        "営業担当",
        "顧客経営者",
        "顧客情報システム",
        "顧客現場責任者",
    }
    assert {review.benchmark for review in result.benchmark_reviews} == {
        "BCG",
        "Accenture",
        "Deloitte",
        "PwC",
        "NRI",
        "IBM Consulting",
    }
    assert result.acceptance_scores.customer_ready_score >= 85
    assert result.acceptance_scores.business_value_score >= 80


def test_visual_qa_plus_detects_customer_facing_risks() -> None:
    result = validate_proposal(_weak_deck())
    categories = {finding.category for finding in result.visual_qa_findings}

    assert "bullet_count" in categories
    assert "diagram_missing" in categories
    assert "headline_weak" in categories
    assert result.release_judge != "CUSTOMER_READY"


def test_golden_validation_suite_contains_20_categories() -> None:
    suite = run_golden_validation_suite()

    assert suite["case_count"] == 20
    assert suite["customer_ready_count"] == 8
    assert suite["review_required_count"] == 7
    assert suite["not_ready_count"] == 5
    assert suite["average_score"] >= 70
    assert all(item["expected_release_judge"] == item["release_judge"] for item in suite["results"])
    assert {item["category"] for item in suite["results"]} >= {"Web制作", "AI", "官公庁", "大企業"}


def test_proposal_validation_api_returns_acceptance_score(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/proposal-validation/validate",
        headers=admin_headers,
        json={
            "powerpoint_generation_data": _dump(_customer_ready_deck()),
            "proposal_context": {"decision_maker": "経営者", "industry": "AI"},
        },
    )

    assert response.status_code == 200
    body = response.json()["validation"]
    assert body["release_judge"] == "CUSTOMER_READY"
    assert body["acceptance_scores"]["total_score"] >= 85
    assert len(body["customer_questions"]) == 20


def test_proposal_validation_requires_auth(client: TestClient) -> None:
    response = client.post(
        "/api/proposal-validation/validate",
        json={"powerpoint_generation_data": _dump(_customer_ready_deck()), "proposal_context": {}},
    )

    assert response.status_code in {401, 403}
