"""Version 10.0 Presentation Director orchestration."""

from __future__ import annotations

from app.presentation_composer import CaseContext, PageSpec, PresentationPlan

from .appendix_planner import omitted_from_main_deck, plan_appendix
from .audience_analyzer import analyze_audience
from .contracts import build_director_input
from .decision_stage_analyzer import analyze_decision_stage
from .deck_objective import decide_deck_objective
from .emphasis_planner import build_emphasis_curve, build_emotion_curve
from .evidence_placement import plan_evidence_distribution
from .models import PresentationDirectorInput, PresentationDirectorPlan
from .page_budget import plan_page_budget
from .section_planner import plan_sections
from .sequence_optimizer import optimize_sequence
from .slide_role_planner import plan_slide_roles
from .speaker_notes_planner import plan_speaker_notes, speaker_notes_strategy
from .story_strategy import select_story_strategy
from .transition_planner import plan_transitions


def direct_presentation(input_data: PresentationDirectorInput) -> PresentationDirectorPlan:
    audience = analyze_audience(input_data)
    stage, meeting_type = analyze_decision_stage(input_data)
    objective = decide_deck_objective(input_data, stage)
    story = select_story_strategy(input_data, audience, stage)
    budget = plan_page_budget(stage, input_data.presentation_time_minutes)
    slides = optimize_sequence(plan_slide_roles(budget.recommended_page_count))
    sections = plan_sections(stage)
    evidence = plan_evidence_distribution(slides)
    appendix = plan_appendix(slides)
    notes = plan_speaker_notes(slides)
    transitions = plan_transitions(slides)
    priority = tuple(slide.slide_id for slide in slides if slide.priority_level in {"hero", "key"} and slide.slide_no in {2, 3, 6, 8, 13})
    supporting = tuple(slide.slide_id for slide in slides if slide.priority_level == "support")
    optional = tuple(slide.slide_id for slide in slides if slide.removal_reason_if_optional)
    appendix_ids = tuple(item["slide_id"] for item in appendix)
    confidence = 0.84 if input_data.roi_availability == "requires_confirmation" else 0.9
    human_review = tuple(
        dict.fromkeys(
            audience.human_review_reasons
            + (
                "PoC評価条件とROI前提は顧客確認が必要",
                "顧客企業規模が未確認のためページ量は人間確認が必要",
            )
        )
    )
    return PresentationDirectorPlan(
        version="10.0",
        deck_objective=objective,
        audience_analysis=audience,
        primary_audience=audience.primary_audience,
        secondary_audience=audience.secondary_audience,
        decision_stage=stage,
        meeting_type=meeting_type,
        recommended_page_count=budget.recommended_page_count,
        presentation_time=input_data.presentation_time_minutes,
        story_strategy=story,
        narrative_arc=story.narrative_arc,
        section_plan=sections,
        slide_sequence=slides,
        priority_slides=priority,
        supporting_slides=supporting,
        optional_slides=optional,
        appendix_slides=appendix_ids,
        omitted_slides=omitted_from_main_deck(),
        emphasis_curve=build_emphasis_curve(slides),
        emotion_curve=build_emotion_curve(slides),
        evidence_distribution=evidence,
        decision_points=("PoC対象範囲", "評価指標", "開始条件", "次回日程"),
        questions_to_answer=("どの範囲で検証するか", "何を成功指標にするか", "誰が現場確認を担うか", "本番判断の条件は何か"),
        objections_to_resolve=("AI精度は十分か", "現場負荷は増えないか", "既存業務に組み込めるか", "投資対効果をどう確認するか"),
        final_call_to_action="PoC範囲・評価指標・開始条件を次回合意する",
        speaker_notes_strategy=speaker_notes_strategy(),
        fallback_strategy={
            "if_roi_missing": "ROIを断定せず、PoC評価条件として扱う",
            "if_evidence_missing": "仮説と確認事項を分け、Appendixに確認リストを置く",
            "if_time_shortened": "Priority Slide 2,3,8,13だけで説明する",
        },
        confidence=confidence,
        human_review_reasons=human_review,
    )


def direct_case(case: CaseContext, **kwargs) -> PresentationDirectorPlan:
    return direct_presentation(build_director_input(case, **kwargs))


def build_directed_presentation_plan(case: CaseContext, director_plan: PresentationDirectorPlan) -> PresentationPlan:
    pages: list[PageSpec] = []
    visual_by_role = {
        "cover": "hero",
        "executive_summary": "current_future",
        "problem": "issue_tree",
        "root_cause": "fishbone",
        "poc_scope": "matrix",
        "solution": "current_future",
        "process": "flow",
        "kpi": "kpi_dashboard",
        "roadmap": "timeline",
        "roi": "waterfall",
        "risk": "risk_matrix",
        "governance": "governance",
        "decision": "next_action",
        "appendix_evidence": "appendix",
        "appendix_faq": "faq",
    }
    for slide in director_plan.slide_sequence:
        labels = tuple(slide.must_include[:4]) or (slide.slide_role,)
        pages.append(
            PageSpec(
                slide_no=slide.slide_no,
                component_id=f"V10-{slide.slide_role.upper()}",
                component_name=slide.slide_role.replace("_", " ").title(),
                visual_type=visual_by_role.get(slide.slide_role, "flow"),
                layout_family=visual_by_role.get(slide.slide_role, "flow"),
                action_title=slide.action_title_intent,
                conclusion=slide.slide_purpose,
                diagram_labels=labels,
                evidence=" / ".join(slide.evidence_required),
                next_action=slide.transition_to_next,
                diagram_ratio=0.78 if slide.priority_level in {"hero", "key"} else 0.68,
                text_ratio=0.22 if slide.priority_level in {"hero", "key"} else 0.32,
                speaker_notes={
                    "slide_conclusion": slide.action_title_intent,
                    "talking_points": " / ".join(slide.must_include),
                    "confirmation_question": slide.speaker_note_goal,
                    "transition": slide.transition_to_next,
                    "caution": "仮説と確認事項を混同しない",
                },
            )
        )
    return PresentationPlan(
        case=case,
        pages=tuple(pages),
        palette_id="executive_consulting_navy",
        design_system_version="10.0",
        provider="presentation_director_v10",
    )
