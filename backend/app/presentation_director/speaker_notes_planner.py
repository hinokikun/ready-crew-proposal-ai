"""Speaker notes planning."""

from __future__ import annotations

from .models import SlideDirectorDecision


def plan_speaker_notes(slides: tuple[SlideDirectorDecision, ...]) -> dict[str, dict[str, object]]:
    notes: dict[str, dict[str, object]] = {}
    for slide in slides:
        notes[slide.slide_id] = {
            "slide_conclusion": slide.action_title_intent,
            "talking_points": slide.must_include,
            "explanation_order": ("結論", "図解", "根拠", "確認事項"),
            "customer_question": "この前提で進めてもよいか",
            "confirmation_question": slide.speaker_note_goal,
            "objection_response": "未確認事項は断定せず、PoCで確認する条件として扱う",
            "transition_line": slide.transition_to_next,
            "caution": "仮説・確認必要・顧客事実を混同しない",
            "source_detail": slide.evidence_required,
        }
    return notes


def speaker_notes_strategy() -> dict[str, object]:
    return {
        "visible_slide_rule": "顧客向けスライドには結論と図解だけを残す",
        "notes_rule": "説明順、質問対応、根拠詳細、注意点はspeaker_notes.jsonへ分離",
        "moved_content": (
            "詳細な算定根拠",
            "セキュリティ詳細",
            "FAQ",
            "未確認ROIの前提",
            "評価条件の細目",
        ),
    }
