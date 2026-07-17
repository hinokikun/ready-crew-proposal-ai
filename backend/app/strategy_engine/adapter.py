from .models import HumanReviewReport, PresentationContext, StrategyBrief


APPROVED_REVIEW_STATUSES = {"approved", "approved_with_changes"}


def adapt_review_report_to_presentation_context(report: HumanReviewReport) -> PresentationContext:
    if report.status not in APPROVED_REVIEW_STATUSES:
        raise ValueError("Presentation Context requires an approved Strategy Brief review.")
    return adapt_approved_strategy_brief(report.reviewed_brief, review_status=report.status)


def adapt_approved_strategy_brief(
    brief: StrategyBrief,
    *,
    review_status: str,
) -> PresentationContext:
    if review_status not in APPROVED_REVIEW_STATUSES:
        raise ValueError("review_status must be approved or approved_with_changes.")
    slide_order = _slide_order(brief)
    return PresentationContext(
        source_strategy_schema_version=brief.schema_version,
        review_status=review_status,
        source_project_category=str(brief.project_category),
        persona=str(brief.primary_persona),
        story_type=str(brief.story_type),
        hero={
            "theme": brief.hero_theme,
            "main_message": brief.main_message,
            "persona": str(brief.primary_persona),
        },
        main_message=brief.main_message,
        problem_theme=brief.problem_theme,
        architecture_type=brief.architecture_type,
        roadmap_type=brief.roadmap_type,
        kpi_pack=brief.kpi_pack,
        estimate_pack=brief.estimate_pack,
        slide_order=slide_order,
        visual_theme=_visual_theme(brief),
        presentation_pack=brief.primary_pack,
        secondary_presentation_pack=brief.secondary_pack,
        required_slides=brief.required_slide_types,
        optional_slides=brief.optional_slide_types,
        priority_messages=brief.priority_messages,
        risk_messages=brief.risk_messages,
        next_actions=brief.next_actions,
        allowed_terms=brief.allowed_terms,
        conditional_terms=brief.conditional_terms,
        prohibited_terms=brief.prohibited_terms,
    )


def _slide_order(brief: StrategyBrief) -> list[str]:
    seen = set()
    ordered = []
    for slide_type in brief.required_slide_types + brief.optional_slide_types:
        if slide_type not in seen:
            seen.add(slide_type)
            ordered.append(slide_type)
    return ordered


def _visual_theme(brief: StrategyBrief) -> str:
    return f"{brief.primary_pack}:{brief.hero_theme}:{brief.story_type}"
