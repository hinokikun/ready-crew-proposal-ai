"""Contract constants for the Phase 2C Message Designer."""

from __future__ import annotations

from .designer_enums import MessageStyle, MessageTone
from .designer_models import (
    MAX_HEADLINE_CHARS,
    MAX_KEY_TAKEAWAY_CHARS,
    MAX_MAIN_MESSAGE_CHARS,
    MAX_SPEAKER_NOTE_CHARS,
    MAX_SUPPORTING_MESSAGE_CHARS,
    MAX_SUPPORTING_MESSAGES,
    MessageStyleProfile,
)


MESSAGE_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"

MESSAGE_LENGTH_LIMITS = {
    "headline": MAX_HEADLINE_CHARS,
    "main_message": MAX_MAIN_MESSAGE_CHARS,
    "supporting_messages": MAX_SUPPORTING_MESSAGES,
    "supporting_message": MAX_SUPPORTING_MESSAGE_CHARS,
    "key_takeaway": MAX_KEY_TAKEAWAY_CHARS,
    "speaker_note_summary": MAX_SPEAKER_NOTE_CHARS,
}

PLACEHOLDER_LABELS = {
    "headline 1",
    "message 1",
    "supporting message 1",
    "key takeaway 1",
    "speaker note 1",
    "slide 1",
    "section 1",
    "action 1",
    "view 1",
    "metric 1",
    "kpi design 1",
    "tbd",
    "lorem ipsum",
    "json key",
}

INTERNAL_LABEL_PATTERNS = {
    "slide_blueprint_id",
    "slide_plan_id",
    "deck_id",
    "snake_case",
    "json",
    "internal",
    "developer",
}

WEAK_LANGUAGE = {
    "最適化します",
    "改善します",
    "強化します",
    "支援します",
    "推進します",
    "価値を提供します",
    "効果が期待できます",
    "柔軟に対応します",
    "総合的に",
    "効果的に",
    "高品質な",
    "革新的な",
    "先進的な",
    "optimize",
    "improve",
    "support",
    "enhance",
    "innovative",
    "high quality",
}

AMBIGUOUS_LANGUAGE = {
    "これ",
    "それ",
    "さまざま",
    "適切",
    "必要に応じて",
    "可能な限り",
    "一部",
    "一定",
    "大幅",
    "近々",
    "早期",
    "将来的に",
    "various",
    "appropriate",
    "some",
    "soon",
}

NOUN_ONLY_HEADLINES = {
    "概要",
    "課題",
    "提案",
    "現状",
    "kpi",
    "スケジュール",
    "比較",
    "今後について",
    "summary",
    "problem",
    "proposal",
    "current state",
    "timeline",
}

STYLE_PROFILES = {
    MessageStyle.EXECUTIVE.value: MessageStyleProfile(
        style=MessageStyle.EXECUTIVE,
        tone=MessageTone.CONCISE,
        headline_rule="Lead with the conclusion and decision implication.",
        main_message_rule="Prioritize decision criteria, impact, risk, and next action.",
        avoid=["excessive detail", "decorative phrasing", "unsupported certainty"],
    ),
    MessageStyle.CONSULTING.value: MessageStyleProfile(
        style=MessageStyle.CONSULTING,
        tone=MessageTone.ANALYTICAL,
        headline_rule="State the insight or cause-and-effect relationship.",
        main_message_rule="Connect problem, evidence, and recommendation.",
        avoid=["assertion without basis", "loose reasoning"],
    ),
    MessageStyle.SALES.value: MessageStyleProfile(
        style=MessageStyle.SALES,
        tone=MessageTone.PERSUASIVE,
        headline_rule="Make customer value and action clear.",
        main_message_rule="Show the change the customer can expect after adoption.",
        avoid=["unqualified promises", "vendor-centered wording"],
    ),
    MessageStyle.TECHNICAL.value: MessageStyleProfile(
        style=MessageStyle.TECHNICAL,
        tone=MessageTone.ANALYTICAL,
        headline_rule="Clarify mechanism, condition, or feasibility.",
        main_message_rule="State constraints and implementation basis without over-selling.",
        avoid=["vague business slogans", "unsupported technical certainty"],
    ),
    MessageStyle.FINANCIAL.value: MessageStyleProfile(
        style=MessageStyle.FINANCIAL,
        tone=MessageTone.CAUTIOUS,
        headline_rule="Separate assumption, estimate, and confirmed value.",
        main_message_rule="Explain amount, ratio, period, and condition when evidence exists.",
        avoid=["unsupported ROI", "currency without basis", "mixed actual and trial values"],
    ),
    MessageStyle.OPERATIONAL.value: MessageStyleProfile(
        style=MessageStyle.OPERATIONAL,
        tone=MessageTone.SUPPORTIVE,
        headline_rule="Show operational change and review point.",
        main_message_rule="Connect current workflow, constraint, and next practical step.",
        avoid=["abstract transformation claims", "executive-only wording"],
    ),
    MessageStyle.MARKETING.value: MessageStyleProfile(
        style=MessageStyle.MARKETING,
        tone=MessageTone.PERSUASIVE,
        headline_rule="Explain audience change or customer response.",
        main_message_rule="Tie message, conversion, and evidence requirement together.",
        avoid=["generic branding claims", "unsupported market certainty"],
    ),
    MessageStyle.STRATEGIC.value: MessageStyleProfile(
        style=MessageStyle.STRATEGIC,
        tone=MessageTone.CONFIDENT,
        headline_rule="State the strategic choice and why now.",
        main_message_rule="Connect direction, trade-off, and expected value.",
        avoid=["tactical detail overload", "unbounded claims"],
    ),
    MessageStyle.NEUTRAL.value: MessageStyleProfile(
        style=MessageStyle.NEUTRAL,
        tone=MessageTone.FORMAL,
        headline_rule="State the slide purpose clearly.",
        main_message_rule="Keep the message factual and reviewable.",
        avoid=["decorative wording", "unsupported claims"],
    ),
}
