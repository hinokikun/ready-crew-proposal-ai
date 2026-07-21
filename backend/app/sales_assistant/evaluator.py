import json
from typing import List

from app.strategy_engine.term_guard import find_prohibited_terms

from .generator import GUARDED_SECTION_KEYS, brief_to_canonical_json, generate_sales_assistant_brief
from .models import EvaluationItem, SalesAssistantBrief, SalesAssistantEvaluationReport, SalesAssistantInput

UNSUPPORTED_CLAIMS = [
    "guaranteed roi",
    "guarantee",
    "100%",
    "certain approval",
    "no risk",
    "fixed price without confirmed scope",
    "will definitely",
]

REQUIRED_SECTIONS = [
    "summary",
    "meeting_plan",
    "discovery_questions",
    "talk_track",
    "objection_handling",
    "decision_maker_support",
    "evidence_guidance",
    "next_actions",
    "follow_up",
    "risk_and_guardrails",
    "generation_metadata",
]


def evaluate_sales_assistant_brief(value: SalesAssistantInput, brief: SalesAssistantBrief) -> SalesAssistantEvaluationReport:
    items = [
        _schema_validity(brief),
        _strategy_alignment(value, brief),
        _persona_alignment(value, brief),
        _decision_maker_alignment(value, brief),
        _question_quality(brief),
        _objection_coverage(brief),
        _evidence_safety(value, brief),
        _term_guard_compliance(value, brief),
        _follow_up_consistency(brief),
        _human_review_consistency(value, brief),
        _determinism(value, brief),
    ]
    unsupported = _unsupported_claim_count(brief)
    items.append(
        EvaluationItem(
            name="unsupported_claim_count",
            passed=unsupported == 0,
            score=10 if unsupported == 0 else 0,
            notes=[] if unsupported == 0 else [f"unsupported claims detected: {unsupported}"],
        )
    )
    overall = round(sum(item.score for item in items) / max(len(items), 1) * 10)
    red_flags: List[str] = []
    for item in items:
        if not item.passed:
            red_flags.append(item.name)
    return SalesAssistantEvaluationReport(
        overall_score=overall,
        passed=not red_flags,
        unsupported_claim_count=unsupported,
        items=items,
        red_flags=red_flags,
        metadata={
            "fixture_category": brief.summary.category,
            "strategy_confidence": brief.generation_metadata.source_strategy_confidence,
        },
    )


def _schema_validity(brief: SalesAssistantBrief) -> EvaluationItem:
    data = brief.dict()
    missing = [name for name in REQUIRED_SECTIONS if name not in data or data[name] in (None, [], {})]
    return EvaluationItem(
        name="schema_validity",
        passed=not missing,
        score=10 if not missing else 0,
        notes=[f"missing sections: {', '.join(missing)}"] if missing else [],
    )


def _strategy_alignment(value: SalesAssistantInput, brief: SalesAssistantBrief) -> EvaluationItem:
    expected = str(value.strategy_brief.primary_strategy)
    passed = brief.summary.strategy == expected and any(expected in rule for rule in brief.generation_metadata.selected_rules)
    return EvaluationItem(
        name="strategy_alignment",
        passed=passed,
        score=10 if passed else 2,
        notes=[] if passed else [f"expected strategy {expected}, got {brief.summary.strategy}"],
    )


def _persona_alignment(value: SalesAssistantInput, brief: SalesAssistantBrief) -> EvaluationItem:
    expected = str(value.strategy_brief.primary_persona)
    passed = brief.summary.persona == expected
    return EvaluationItem(
        name="persona_alignment",
        passed=passed,
        score=10 if passed else 2,
        notes=[] if passed else [f"expected persona {expected}, got {brief.summary.persona}"],
    )


def _decision_maker_alignment(value: SalesAssistantInput, brief: SalesAssistantBrief) -> EvaluationItem:
    expected = str(value.strategy_brief.decision_maker)
    passed = brief.summary.decision_maker == expected and brief.decision_maker_support.decision_maker == expected
    return EvaluationItem(
        name="decision_maker_alignment",
        passed=passed,
        score=10 if passed else 2,
        notes=[] if passed else [f"expected decision maker {expected}"],
    )


def _question_quality(brief: SalesAssistantBrief) -> EvaluationItem:
    questions = brief.discovery_questions
    high_count = sum(1 for item in questions if item.priority == "high")
    passed = len(questions) >= 3 and high_count >= 2 and all(item.purpose for item in questions)
    return EvaluationItem(
        name="question_quality",
        passed=passed,
        score=10 if passed else 4,
        notes=[] if passed else ["expected at least three questions, two high-priority, each with purpose"],
    )


def _objection_coverage(brief: SalesAssistantBrief) -> EvaluationItem:
    types = {item.objection_type for item in brief.objection_handling}
    required = {"price", "schedule", "effectiveness"}
    passed = required.issubset(types)
    return EvaluationItem(
        name="objection_coverage",
        passed=passed,
        score=10 if passed else 5,
        notes=[] if passed else ["price, schedule, and effectiveness objections are required"],
    )


def _evidence_safety(value: SalesAssistantInput, brief: SalesAssistantBrief) -> EvaluationItem:
    has_gap = bool(brief.evidence_guidance.evidence_gaps)
    mentions_confirmation = "confirmation" in json.dumps(brief.evidence_guidance.dict(), ensure_ascii=False).lower()
    if value.evidence_items:
        passed = bool(brief.evidence_guidance.available_evidence)
    else:
        passed = has_gap and mentions_confirmation
    return EvaluationItem(
        name="evidence_safety",
        passed=passed,
        score=10 if passed else 2,
        notes=[] if passed else ["missing evidence must create explicit confirmation guidance"],
    )


def _term_guard_compliance(value: SalesAssistantInput, brief: SalesAssistantBrief) -> EvaluationItem:
    prohibited = value.strategy_brief.prohibited_terms
    hits = find_prohibited_terms(_guarded_text(brief), prohibited)
    review_marked = not hits or brief.summary.human_review_required
    passed = not hits and review_marked
    return EvaluationItem(
        name="term_guard_compliance",
        passed=passed,
        score=10 if passed else 0,
        notes=[] if passed else [f"guarded sections include prohibited terms: {', '.join(hits)}"],
    )


def _follow_up_consistency(brief: SalesAssistantBrief) -> EvaluationItem:
    body = brief.follow_up.email_body.lower()
    passed = "next actions" in body and "confirmation" in body
    return EvaluationItem(
        name="follow_up_consistency",
        passed=passed,
        score=10 if passed else 4,
        notes=[] if passed else ["follow-up must include next actions and confirmation items"],
    )


def _human_review_consistency(value: SalesAssistantInput, brief: SalesAssistantBrief) -> EvaluationItem:
    expected = value.strategy_brief.human_review_required or bool(brief.evidence_guidance.evidence_gaps)
    passed = (not expected) or brief.summary.human_review_required
    return EvaluationItem(
        name="human_review_consistency",
        passed=passed,
        score=10 if passed else 3,
        notes=[] if passed else ["human review required by strategy or evidence gaps must be propagated"],
    )


def _determinism(value: SalesAssistantInput, brief: SalesAssistantBrief) -> EvaluationItem:
    regenerated = generate_sales_assistant_brief(value)
    passed = brief_to_canonical_json(brief) == brief_to_canonical_json(regenerated)
    return EvaluationItem(
        name="determinism",
        passed=passed,
        score=10 if passed else 0,
        notes=[] if passed else ["same input generated different output"],
    )


def _unsupported_claim_count(brief: SalesAssistantBrief) -> int:
    text = json.dumps(brief.dict(), ensure_ascii=False).lower()
    return sum(1 for token in UNSUPPORTED_CLAIMS if token in text)


def _guarded_text(brief: SalesAssistantBrief) -> str:
    data = brief.dict()
    sections = [data[key] for key in GUARDED_SECTION_KEYS]
    return json.dumps(sections, ensure_ascii=False).lower()
