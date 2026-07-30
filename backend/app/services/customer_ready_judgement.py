from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ReleaseJudge = Literal["CUSTOMER_READY", "REVIEW_REQUIRED", "NOT_READY"]
GateStatus = Literal["READY", "REVIEW_REQUIRED", "BLOCKED"]

READY_THRESHOLD = 85
REVIEW_THRESHOLD = 70
CRITICAL_REVIEW_THRESHOLD = 78


@dataclass(frozen=True)
class CustomerReadyAssessment:
    release_judge: ReleaseJudge
    gate_status: GateStatus
    score: int
    category_scores: dict[str, int]
    reasons: list[str]
    blockers: list[str]
    required_fixes: list[str]


def gate_status_from_release_judge(judge: str) -> GateStatus:
    if judge == "CUSTOMER_READY":
        return "READY"
    if judge == "REVIEW_REQUIRED":
        return "REVIEW_REQUIRED"
    return "BLOCKED"


def release_judge_from_gate_status(status: str) -> ReleaseJudge:
    if status == "READY":
        return "CUSTOMER_READY"
    if status == "REVIEW_REQUIRED":
        return "REVIEW_REQUIRED"
    return "NOT_READY"


def assess_customer_ready_deck(
    slides: list[Any],
    context: Any | None = None,
    *,
    blockers: list[str] | None = None,
    visual_findings: list[Any] | None = None,
) -> CustomerReadyAssessment:
    """Shared release-readiness judgement for Quality Gate and Proposal Validation."""

    blocker_list = _unique([str(item) for item in blockers or [] if str(item or "").strip()], 12)
    client_name = _context_value(context, "client_name", "client", "customer", "company_name")
    category_scores = _category_scores(slides, context)
    score = _weighted_score(category_scores)
    critical_visual = _has_critical_visual_findings(visual_findings or [])
    high_visual = _has_high_visual_findings(visual_findings or [])

    if not slides:
        blocker_list.append("No proposal slides were generated.")
    if client_name and str(client_name).strip().lower() in {"client", "customer", "sample"}:
        blocker_list.append("Customer name is missing or generic.")
    if critical_visual:
        blocker_list.append("Critical visual QA findings must be fixed before customer submission.")

    release_judge = _release_judge(score, blocker_list, critical_visual=critical_visual, high_visual=high_visual)
    reasons = _decision_reasons(release_judge, score, category_scores, blocker_list)
    fixes = _required_fixes(category_scores, blocker_list, high_visual=high_visual, critical_visual=critical_visual)

    return CustomerReadyAssessment(
        release_judge=release_judge,
        gate_status=gate_status_from_release_judge(release_judge),
        score=score,
        category_scores=category_scores,
        reasons=reasons,
        blockers=blocker_list,
        required_fixes=fixes,
    )


def assessment_to_acceptance_scores(assessment: CustomerReadyAssessment) -> dict[str, int]:
    scores = assessment.category_scores
    return {
        "customer_ready_score": assessment.score,
        "executive_score": _avg(scores["executive_summary"], scores["roi_kpi"], scores["story_flow"]),
        "sales_score": _avg(scores["differentiation"], scores["next_action"], scores["customer_specificity"]),
        "technical_score": _avg(scores["risk_coverage"], scores["readability"], scores["visual_structure"]),
        "presentation_score": _avg(scores["story_flow"], scores["visual_structure"], scores["readability"]),
        "visual_score": scores["visual_structure"],
        "business_value_score": _avg(scores["roi_kpi"], scores["differentiation"], scores["executive_summary"]),
        "total_score": assessment.score,
    }


def _category_scores(slides: list[Any], context: Any | None) -> dict[str, int]:
    text = _deck_text(slides)
    slide_count = len(slides)
    client_name = _context_value(context, "client_name", "client", "customer", "company_name")
    has_client = bool(client_name and str(client_name).strip().lower() not in {"client", "customer", "sample"})
    has_context = any(
        _context_value(context, key)
        for key in (
            "proposal_category",
            "proposal_label",
            "industry",
            "decision_maker",
            "winning_strategy",
            "budget",
            "timeline",
        )
    )
    visual_score = _visual_structure_score(slides)
    readability = _readability_score(slides)
    mature_deck_bonus = 10 if slide_count >= 8 else 0
    visual_bonus = 6 if visual_score >= 85 else 0

    return {
        "customer_specificity": _clamp(62 + (18 if has_client else 0) + (8 if has_context else 0) + _keyword_bonus(text, _CUSTOMER_TERMS, 12), 0, 100),
        "executive_summary": _clamp(63 + _keyword_bonus(text, _EXECUTIVE_TERMS, 30) + mature_deck_bonus, 0, 100),
        "story_flow": _clamp(58 + _keyword_bonus(text, _STORY_TERMS, 34) + _slide_count_bonus(slide_count) + visual_bonus, 0, 100),
        "roi_kpi": _clamp(62 + _keyword_bonus(text, _ROI_KPI_TERMS, 36) + (8 if slide_count >= 8 else 0), 0, 100),
        "differentiation": _clamp(68 + _keyword_bonus(text, _DIFFERENTIATION_TERMS, 34) + (6 if has_context else 0), 0, 100),
        "risk_coverage": _clamp(68 + _keyword_bonus(text, _RISK_TERMS, 34) + (8 if slide_count >= 8 else 0), 0, 100),
        "next_action": _clamp(76 + _keyword_bonus(text, _NEXT_ACTION_TERMS, 30) + (8 if slide_count >= 8 else 0), 0, 100),
        "visual_structure": visual_score,
        "readability": readability,
    }


def _weighted_score(scores: dict[str, int]) -> int:
    weights = {
        "customer_specificity": 0.11,
        "executive_summary": 0.12,
        "story_flow": 0.15,
        "roi_kpi": 0.14,
        "differentiation": 0.12,
        "risk_coverage": 0.11,
        "next_action": 0.10,
        "visual_structure": 0.08,
        "readability": 0.07,
    }
    return _clamp(round(sum(scores[key] * weight for key, weight in weights.items())), 0, 100)


def _release_judge(score: int, blockers: list[str], *, critical_visual: bool, high_visual: bool) -> ReleaseJudge:
    if blockers:
        return "NOT_READY" if score < CRITICAL_REVIEW_THRESHOLD or critical_visual else "REVIEW_REQUIRED"
    if high_visual and score < READY_THRESHOLD:
        return "REVIEW_REQUIRED"
    if score >= READY_THRESHOLD:
        return "CUSTOMER_READY"
    if score >= REVIEW_THRESHOLD:
        return "REVIEW_REQUIRED"
    return "NOT_READY"


def _decision_reasons(
    judge: ReleaseJudge,
    score: int,
    scores: dict[str, int],
    blockers: list[str],
) -> list[str]:
    lines: list[str] = []
    if judge == "CUSTOMER_READY":
        lines.append(f"Total score {score}: story, value, risk coverage, and next action meet the customer-ready threshold.")
    elif judge == "REVIEW_REQUIRED":
        lines.append(f"Total score {score}: no release-blocking issue, but sales review is recommended before submission.")
    else:
        lines.append(f"Total score {score}: important fixes are required before customer submission.")

    lines.extend(blockers[:3])

    weak = sorted(((name, value) for name, value in scores.items() if value < READY_THRESHOLD), key=lambda item: item[1])
    for name, value in weak[:3]:
        lines.append(f"{_label(name)} is {value}; strengthen it before submission.")

    strong = sorted(((name, value) for name, value in scores.items() if value >= READY_THRESHOLD), key=lambda item: item[1], reverse=True)
    for name, value in strong[:2]:
        lines.append(f"{_label(name)} is {value}; it meets the release threshold.")
    return _unique(lines, 8)


def _required_fixes(
    scores: dict[str, int],
    blockers: list[str],
    *,
    high_visual: bool,
    critical_visual: bool,
) -> list[str]:
    fixes = list(blockers)
    mapping = {
        "customer_specificity": "Clarify customer name, industry, decision maker, and assumptions.",
        "executive_summary": "Make the first two pages explain background, issue, conclusion, and expected value.",
        "story_flow": "Strengthen the flow from current state to issue, cause, solution, implementation, effect, and next action.",
        "roi_kpi": "Add ROI, KPI, measurement method, measurement timing, and owner.",
        "differentiation": "Separate competitor assumptions, winning strategy, differentiation, and confirmation items.",
        "risk_coverage": "Add implementation, operation, security, and mitigation risks.",
        "next_action": "Clarify next confirmation items, agreement items, and decision points.",
        "visual_structure": "Use comparison, KPI cards, roadmap, flow, or matrix where useful.",
        "readability": "Compress long titles and bullets into one-message-per-slide content.",
    }
    for key, value in sorted(scores.items(), key=lambda item: item[1]):
        if value < READY_THRESHOLD:
            fixes.append(mapping[key])
    if critical_visual:
        fixes.insert(0, "Fix critical visual QA issues such as clipping, overlap, or blank slides.")
    elif high_visual:
        fixes.append("Review high-priority visual QA issues such as spacing, alignment, card height, and title fit.")
    return _unique(fixes, 8)


def _visual_structure_score(slides: list[Any]) -> int:
    if not slides:
        return 0
    visual_hits = 0
    layout_ids: list[str] = []
    repeated = 0
    for slide in slides:
        visual = f"{_field(slide, 'layout')} {_field(slide, 'visual_suggestion')}".lower()
        layout_ids.append(str(_field(slide, "layout")))
        if any(term in visual for term in _VISUAL_TERMS):
            visual_hits += 1
    for index in range(2, len(layout_ids)):
        if layout_ids[index] and layout_ids[index] == layout_ids[index - 1] == layout_ids[index - 2]:
            repeated += 1
    ratio = visual_hits / max(1, len(slides))
    return _clamp(round(66 + ratio * 30 - repeated * 8), 0, 100)


def _readability_score(slides: list[Any]) -> int:
    if not slides:
        return 0
    penalty = 0
    for slide in slides:
        title = str(_field(slide, "title"))
        bullets = _bullets(slide)
        total_chars = sum(len(item) for item in bullets)
        if len(title) > 54:
            penalty += 5
        if len(bullets) > 7:
            penalty += 8
        if total_chars > 560:
            penalty += 10
    return _clamp(94 - penalty, 0, 100)


def _slide_count_bonus(slide_count: int) -> int:
    if 8 <= slide_count <= 26:
        return 8
    if 6 <= slide_count <= 30:
        return 4
    return 0


def _keyword_bonus(text: str, terms: tuple[str, ...], max_bonus: int) -> int:
    hits = sum(1 for term in terms if term.lower() in text)
    return min(max_bonus, hits * max(3, max_bonus // 7))


def _has_critical_visual_findings(findings: list[Any]) -> bool:
    return any(_severity(item) in {"critical", "p0"} for item in findings)


def _has_high_visual_findings(findings: list[Any]) -> bool:
    return any(_severity(item) in {"high", "p1"} for item in findings)


def _severity(item: Any) -> str:
    if isinstance(item, dict):
        value = item.get("severity", "")
    else:
        value = getattr(item, "severity", "")
    return str(value or "").strip().lower()


def _deck_text(slides: list[Any]) -> str:
    parts: list[str] = []
    for slide in slides:
        parts.append(str(_field(slide, "layout")))
        parts.append(str(_field(slide, "title")))
        parts.append(str(_field(slide, "speaker_notes")))
        parts.append(str(_field(slide, "visual_suggestion")))
        parts.extend(_bullets(slide))
    return "\n".join(part for part in parts if part).lower()


def _bullets(slide: Any) -> list[str]:
    items = _field(slide, "bullets")
    if isinstance(items, list):
        return [str(item) for item in items if str(item or "").strip()]
    return []


def _field(item: Any, name: str) -> Any:
    if isinstance(item, dict):
        return item.get(name, "")
    return getattr(item, name, "")


def _context_value(context: Any | None, *names: str) -> Any:
    if context is None:
        return ""
    for name in names:
        if isinstance(context, dict) and context.get(name):
            return context.get(name)
        value = getattr(context, name, "")
        if value:
            return value
    return ""


def _avg(*values: int) -> int:
    return _clamp(round(sum(values) / max(1, len(values))), 0, 100)


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def _unique(values: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = " ".join(str(value or "").split())
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(clean)
        if len(result) >= limit:
            break
    return result


def _label(key: str) -> str:
    labels = {
        "customer_specificity": "customer context",
        "executive_summary": "executive summary",
        "story_flow": "proposal story",
        "roi_kpi": "ROI/KPI",
        "differentiation": "differentiation",
        "risk_coverage": "risk coverage",
        "next_action": "next action",
        "visual_structure": "visual structure",
        "readability": "readability",
    }
    return labels.get(key, key)


_CUSTOMER_TERMS = ("client", "customer", "decision", "industry", "persona", "stakeholder", "company")
_EXECUTIVE_TERMS = ("executive", "summary", "conclusion", "background", "impact", "roi", "value", "benefit", "outcome")
_STORY_TERMS = ("current", "problem", "cause", "solution", "roadmap", "timeline", "process", "next", "before", "after", "implementation", "effect", "future")
_ROI_KPI_TERMS = ("roi", "kpi", "target", "measure", "%", "budget", "cost", "estimate", "effect", "baseline", "goal", "owner")
_DIFFERENTIATION_TERMS = ("competitor", "differentiation", "winning", "comparison", "advantage", "positioning", "strength")
_RISK_TERMS = ("risk", "security", "operation", "mitigation", "training", "support", "governance", "fallback")
_NEXT_ACTION_TERMS = ("next", "action", "confirm", "decision", "agree", "meeting", "approve", "review")
_VISUAL_TERMS = ("card", "cards", "flow", "timeline", "roadmap", "matrix", "comparison", "kpi", "icon", "before", "after", "dashboard", "table", "chart", "diagram")
