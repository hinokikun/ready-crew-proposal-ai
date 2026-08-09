"""Page budget rules for meeting time and decision stage."""

from __future__ import annotations

from .models import DecisionStage, PageBudget


def plan_page_budget(stage: DecisionStage, presentation_time_minutes: int) -> PageBudget:
    ranges = {
        5: (5, 7),
        10: (8, 12),
        15: (9, 13),
        30: (12, 18),
        45: (16, 22),
        60: (18, 26),
    }
    closest = min(ranges, key=lambda value: abs(value - presentation_time_minutes))
    low, high = ranges[closest]
    stage_preference = {
        "first_meeting": low,
        "problem_hypothesis": min(high, low + 3),
        "specific_proposal": min(high, low + 5),
        "poc_proposal": min(high, low + 3),
        "final_approval": min(high, low + 4),
        "execution_plan": high,
    }[stage]
    talk_time = round(presentation_time_minutes * 0.72, 1)
    discussion = round(presentation_time_minutes * 0.18, 1)
    q_and_a = round(presentation_time_minutes - talk_time - discussion, 1)
    return PageBudget(
        recommended_page_count=stage_preference,
        presentation_time_minutes=presentation_time_minutes,
        talk_time_minutes=talk_time,
        discussion_time_minutes=discussion,
        q_and_a_minutes=q_and_a,
        rationale=f"{presentation_time_minutes}分枠では説明だけで埋めず、議論と質疑を残すため{stage_preference}枚に圧縮",
    )
