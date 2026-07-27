from app.models import PowerPointSlide
from app.services.presentation_designer_ai import analyze_layout_decisions
from app.strategy_engine.evaluator import evaluate_strategy
from app.strategy_engine.models import ProposalStrategyWorkspace, StrategyWorkspaceChange, StrategyWorkspaceScore, StrategyScoreItem
from app.strategy_engine.sales_strategy import generate_sales_strategy_brief
from app.strategy_engine.sales_strategy_fixtures import SALES_STRATEGY_FIXTURES


def test_sales_strategy_fixtures_cover_required_categories() -> None:
    assert {"web_creation", "ec", "recruiting", "ai_adoption", "dx", "branding"}.issubset(
        SALES_STRATEGY_FIXTURES
    )


def test_decision_maker_analysis_changes_focus_and_order() -> None:
    executive = generate_sales_strategy_brief(SALES_STRATEGY_FIXTURES["ai_adoption"])
    web = generate_sales_strategy_brief(SALES_STRATEGY_FIXTURES["web_creation"])

    assert executive.decision_maker == "executive"
    assert "ROI" in executive.decision_maker_profile.focus_points
    assert executive.recommended_presentation_tone == "Executive"
    assert web.decision_maker in {"sales", "department_head"}
    assert web.decision_maker_profile.proposal_order


def test_competitive_position_and_proposal_position_are_classified() -> None:
    branding = generate_sales_strategy_brief(SALES_STRATEGY_FIXTURES["branding"])
    ec = generate_sales_strategy_brief(SALES_STRATEGY_FIXTURES["ec"])

    assert branding.competitive_situation in {"brand_competition", "quality_competition", "no_clear_competitor"}
    assert branding.proposal_position == "branding"
    assert ec.proposal_position == "ec_improvement"
    assert ec.recommended_presentation_tone in {"Agency", "Data Driven", "Friendly"}


def test_expected_objections_include_recommended_slide_and_evidence() -> None:
    brief = generate_sales_strategy_brief(SALES_STRATEGY_FIXTURES["dx"])

    assert brief.expected_objections
    assert all(item.recommended_slide for item in brief.expected_objections)
    assert all(item.recommended_evidence for item in brief.expected_objections)
    assert {"missing", "hypothesis", "needs_confirmation", "ai_inferred"}.issubset(
        brief.evidence_classification.dict()
    )


def test_strategy_brief_contains_sales_strategy_without_overwriting_legacy_story() -> None:
    brief = evaluate_strategy(SALES_STRATEGY_FIXTURES["ai_adoption"])

    assert brief.sales_strategy_brief is not None
    assert brief.story_type
    assert brief.sales_strategy_brief.recommended_story_type
    assert brief.sales_strategy_brief.recommended_slide_types
    assert brief.sales_strategy_brief.winning_strategy


def test_presentation_designer_uses_sales_strategy_tone_and_position() -> None:
    sales_strategy = generate_sales_strategy_brief(SALES_STRATEGY_FIXTURES["ai_adoption"])
    slides = [
        PowerPointSlide(
            slide_no=1,
            title="AI adoption proposal",
            layout="Title + Body",
            bullets=["Show governance, KPI, risk, and approval decision."],
            speaker_notes="",
            visual_suggestion="",
        )
    ]

    decision = analyze_layout_decisions(
        slides,
        story_type="generic",
        audience="sales",
        sales_strategy_brief=sales_strategy,
    )[0]

    assert f"sales_strategy_tone={sales_strategy.recommended_presentation_tone}" in decision.selection_reason
    assert f"proposal_position={sales_strategy.proposal_position}" in decision.selection_reason
    assert decision.candidates


def test_proposal_strategy_workspace_model_keeps_draft_review_and_approved_states() -> None:
    sales_strategy = generate_sales_strategy_brief(SALES_STRATEGY_FIXTURES["ec"])
    edited = sales_strategy.copy(deep=True)
    edited.winning_strategy = "Prioritize ROI improvement before creative renewal."
    workspace = ProposalStrategyWorkspace(
        status="review",
        ai_brief=sales_strategy,
        edited_brief=edited,
        selected_story_id="story-roi",
        selected_tone="Data Driven",
        confirmed_information=["budget"],
        changes=[
            StrategyWorkspaceChange(
                field="winning_strategy",
                ai_value=sales_strategy.winning_strategy,
                edited_value=edited.winning_strategy,
                changed=True,
            )
        ],
        score=StrategyWorkspaceScore(
            total=88,
            items=[StrategyScoreItem(key="roi_appeal", label="ROI", score=91, reason="ROI-first strategy.")],
            changed_field_count=1,
            confirmed_information_count=1,
        ),
    )

    assert workspace.schema_version == "proposal_strategy_workspace_v1"
    assert workspace.status == "review"
    assert workspace.edited_brief.winning_strategy != workspace.ai_brief.winning_strategy
    assert workspace.score is not None
    assert workspace.score.total == 88

    approved = workspace.copy(update={"status": "approved"})
    assert approved.status == "approved"
