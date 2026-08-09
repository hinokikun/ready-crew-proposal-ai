"""Appendix planning."""

from __future__ import annotations

from .models import SlideDirectorDecision


def plan_appendix(slides: tuple[SlideDirectorDecision, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "slide_id": slide.slide_id,
            "slide_role": slide.slide_role,
            "reason": slide.appendix_reason_if_moved,
            "contains": slide.must_include,
        }
        for slide in slides
        if slide.priority_level == "appendix"
    )


def omitted_from_main_deck() -> tuple[dict[str, str], ...]:
    return (
        {"topic": "詳細な技術仕様", "reason": "PoC合意の本編では意思決定を遅くするためAppendixへ移動"},
        {"topic": "詳細なセキュリティ項目", "reason": "情報システム確認時に参照する補足情報として扱う"},
        {"topic": "詳細なFAQ", "reason": "営業担当の質疑対応用としてSpeaker Notes / Appendixへ移動"},
        {"topic": "詳細な算定根拠", "reason": "未確認ROIを本編で断定しないため、評価条件の詳細へ分離"},
    )
