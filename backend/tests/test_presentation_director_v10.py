from __future__ import annotations

from dataclasses import replace
from io import BytesIO

from pptx import Presentation

from app.presentation_composer import CaseContext, render_director_plan_to_pptx
from app.presentation_director import build_directed_presentation_plan, direct_case, validate_director_plan


def _case() -> CaseContext:
    return CaseContext(
        case_id="case_01",
        case_name="画像認識AI導入提案",
        client_name="株式会社フラワーオークションジャパン",
        industry="花卉流通",
        category="AI / DX",
        project_summary="花卉検品に画像認識AIを導入し、判断ばらつきと検品負荷を減らす。",
        pain_points=("等級判断のばらつき", "繁忙期の確認待ち", "品質記録の分散"),
        expected_outcomes=("検品時間30%削減", "判定一致率90%以上", "再確認件数20%削減"),
        budget="PoC 800万円前後",
        timeline="8週間PoC",
        decision_maker="経営層、現場責任者、情報システム",
        competitor="OCR/画像AIベンダー",
    )


def test_director_identifies_poc_audience_and_objective() -> None:
    plan = direct_case(_case(), presentation_time_minutes=30)

    assert plan.decision_stage == "poc_proposal"
    assert plan.primary_audience == "部門責任者 / 役員"
    assert plan.secondary_audience == "現場責任者 / 情報システム"
    assert plan.deck_objective.objective == "PoC条件と次回合意事項を確定する"
    assert plan.recommended_page_count == 15
    assert plan.presentation_time == 30
    assert plan.story_strategy.selected_story_strategy == "PoC Hypothesis → Test → Evaluation → Scale"


def test_director_has_priority_appendix_notes_and_no_peak_streak() -> None:
    plan = direct_case(_case(), presentation_time_minutes=30)

    assert validate_director_plan(plan) == []
    assert 3 <= len(plan.priority_slides) <= 5
    assert plan.appendix_slides == ("slide-14", "slide-15")
    assert "詳細な算定根拠" in plan.speaker_notes_strategy["moved_content"]

    peak_streak = 0
    for slide in plan.slide_sequence:
        peak_streak = peak_streak + 1 if slide.emphasis_level == "peak" else 0
        assert peak_streak <= 1


def test_director_sequence_connects_executive_summary_to_next_action() -> None:
    plan = direct_case(_case(), presentation_time_minutes=30)
    titles = [slide.action_title_intent for slide in plan.slide_sequence]

    assert titles[1] == "AIで検品品質と処理速度を同時に高めます"
    assert "判定基準" in titles[2]
    assert titles[-3] == "次回はPoC範囲・評価指標・開始条件を合意します"
    assert all(slide.transition_to_next for slide in plan.slide_sequence)


def test_director_page_count_adapts_to_stage_audience_and_time() -> None:
    case = _case()
    first = direct_case(
        replace(case, decision_maker="経営者"),
        presentation_time_minutes=10,
        current_sales_stage="初回相談",
        meeting_purpose="経営者向け初回相談",
        expected_outcome="方向性確認",
    )
    poc = direct_case(
        replace(case, decision_maker="部門責任者"),
        presentation_time_minutes=30,
        current_sales_stage="PoC具体提案",
        meeting_purpose="部門責任者向けPoC具体提案",
        expected_outcome="PoC条件合意",
    )
    final = direct_case(
        replace(case, decision_maker="役員＋情報システム"),
        presentation_time_minutes=45,
        current_sales_stage="最終提案",
        meeting_purpose="役員＋情報システム向け最終提案",
        expected_outcome="承認判断",
    )

    assert first.recommended_page_count < poc.recommended_page_count < final.recommended_page_count
    assert len(first.slide_sequence) == first.recommended_page_count
    assert len(poc.slide_sequence) == poc.recommended_page_count
    assert len(final.slide_sequence) == final.recommended_page_count
    assert validate_director_plan(first) == []
    assert validate_director_plan(poc) == []
    assert validate_director_plan(final) == []


def test_directed_presentation_plan_and_renderer_are_openable() -> None:
    case = _case()
    director_plan = direct_case(case, presentation_time_minutes=30)
    presentation_plan = build_directed_presentation_plan(case, director_plan)
    pptx_bytes, render_report = render_director_plan_to_pptx(presentation_plan, director_plan)

    prs = Presentation(BytesIO(pptx_bytes))
    assert len(prs.slides) == 15
    assert render_report["provider"] == "presentation_director_v10"
    assert render_report["pages"][0]["slide_role"] == "cover"
    assert render_report["pages"][1]["slide_role"] == "executive_summary"
    assert render_report["pages"][2]["slide_role"] == "problem"
