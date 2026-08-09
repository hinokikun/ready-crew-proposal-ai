"""Sales-stage detection for deck-level planning."""

from __future__ import annotations

from .models import DecisionStage, PresentationDirectorInput


def analyze_decision_stage(input_data: PresentationDirectorInput) -> tuple[DecisionStage, str]:
    text = " ".join(
        [
            input_data.current_sales_stage,
            input_data.meeting_purpose,
            input_data.expected_outcome,
            str(input_data.proposal_context.get("budget", "")),
            str(input_data.proposal_context.get("timeline", "")),
        ]
    ).lower()
    if any(word in text for word in ("first_meeting", "initial", "初回", "初回相談", "相談")):
        return "first_meeting", "初回相談"
    if any(word in text for word in ("稟議", "最終", "承認", "final", "役員")):
        return "final_approval", "最終提案・稟議"
    if "poc" in text or "検証" in text:
        return "poc_proposal", "PoC条件合意ミーティング"
    if "課題" in text and "仮説" in text:
        return "problem_hypothesis", "課題整理・仮説提案"
    if "実行" in text or "運用" in text:
        return "execution_plan", "実行計画"
    return "specific_proposal", "具体提案"
