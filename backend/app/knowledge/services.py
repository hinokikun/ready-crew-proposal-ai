from __future__ import annotations

import re
from collections import Counter
from sqlite3 import Connection
from typing import Any

from app.knowledge.repositories import (
    create_knowledge_entry,
    create_template,
    get_knowledge_entry,
    list_knowledge_entries,
    list_search_candidates,
    list_templates,
    update_knowledge_evaluation,
    update_knowledge_quality,
    update_knowledge_status,
    update_template_active,
)


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,4}[-\s]?)?(?:\d{2,4}[-\s]?){2,4}\d{2,4}")
POSTAL_RE = re.compile(r"\d{3}-\d{4}")
URL_RE = re.compile(r"https?://\S+")
API_KEY_RE = re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|AIza[0-9A-Za-z_-]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[0-9A-Za-z-]{10,})")
ADDRESS_HINT_RE = re.compile(r"[\u90fd\u9053\u5e9c\u770c].{0,20}[\u5e02\u533a\u753a\u6751]|[\u4e00-\u9fff]{1,12}[\u5e02\u533a\u753a\u6751].{0,20}[\u4e01\u756a\u53f7]")
PERSON_NAME_RE = re.compile(r"(?:\u62c5\u5f53\u8005|\u6c0f\u540d|[\u4e00-\u9fff]{2,4}\s?[\u4e00-\u9fff]{1,4}(?:\u69d8|\u3055\u3093))")
AMOUNT_OR_CONTRACT_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?\s*(?:\u4e07\u5186|\u5104\u5186|\u5186)|(?:\u5951\u7d04|\u898b\u7a4d|\u6761\u4ef6|\u7a0e\u5225|\u7a0e\u8fbc)")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[\u3040-\u30ff\u3400-\u9fff]{2,}")

SAFE_TEMPLATE_CATEGORIES = {"web", "recruiting", "lp", "seo", "dx", "other"}
SAFE_OUTCOMES = {"success", "lost", "unknown"}
SAFE_EVALUATIONS = {"effective", "needs_improvement"}
SAFE_APPROVAL_STATUSES = {"draft", "pending_review", "approved", "rejected", "archived"}
SAFE_SOURCE_TYPES = {"proposal_generated", "admin_created", "imported", "feedback_based"}


def sanitize_text(value: str, max_length: int = 1200) -> str:
    text = (value or "").strip()
    text = EMAIL_RE.sub("[email_removed]", text)
    text = PHONE_RE.sub("[phone_removed]", text)
    text = POSTAL_RE.sub("[postal_removed]", text)
    text = URL_RE.sub("[url_removed]", text)
    text = API_KEY_RE.sub("[secret_removed]", text)
    text = re.sub(r"\s+", " ", text)
    return text[:max_length]


def infer_industry(text: str) -> str:
    normalized = text.lower()
    industry_rules = [
        ("manufacturing", ["manufacturing", "\u88fd\u9020", "\u5de5\u5834", "\u90e8\u54c1"]),
        ("real_estate", ["real estate", "\u4e0d\u52d5\u7523", "\u7269\u4ef6"]),
        ("recruiting", ["recruit", "\u63a1\u7528", "\u6c42\u4eba"]),
        ("medical", ["medical", "\u533b\u7642", "\u75c5\u9662", "\u30af\u30ea\u30cb\u30c3\u30af"]),
        ("education", ["education", "\u6559\u80b2", "\u5b66\u6821", "\u7814\u4fee"]),
        ("it", ["system", "saas", "dx", "\u30b7\u30b9\u30c6\u30e0", "\u30af\u30e9\u30a6\u30c9"]),
    ]
    for industry, keywords in industry_rules:
        if any(keyword in normalized for keyword in keywords):
            return industry
    return "other"


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_RE.findall(text or "") if len(token) >= 2}


def detect_confidential_flags(value: str) -> list[str]:
    text = value or ""
    checks = [
        ("email", EMAIL_RE),
        ("phone", PHONE_RE),
        ("postal_code", POSTAL_RE),
        ("url", URL_RE),
        ("api_key", API_KEY_RE),
        ("address", ADDRESS_HINT_RE),
        ("personal_name", PERSON_NAME_RE),
        ("amount_or_contract", AMOUNT_OR_CONTRACT_RE),
    ]
    flags = [name for name, pattern in checks if pattern.search(text)]
    return sorted(set(flags))


def calculate_confidential_risk(flags: list[str]) -> str:
    high_risk_flags = {"email", "phone", "api_key", "address", "personal_name"}
    if any(flag in high_risk_flags for flag in flags):
        return "high"
    if flags:
        return "medium"
    return "low"


def calculate_quality_score(data: dict[str, Any], flags: list[str]) -> int:
    summary = str(data.get("project_summary") or "")
    proposal = str(data.get("adopted_proposal") or "")
    story = str(data.get("proposal_story") or "")
    result = str(data.get("result") or "")
    tags = str(data.get("tags") or "")

    specificity = min(20, len(summary) // 25 + len(_tokens(summary)))
    reusability = (8 if proposal else 0) + (8 if story else 0) + (4 if tags else 0)
    success_record = (12 if data.get("outcome") == "success" else 4 if data.get("outcome") == "unknown" else 0) + (8 if result else 0)
    freshness = 15
    rating_bonus = min(max(int(data.get("rating") or 3), 1), 5) * 4
    confidentiality_penalty = 0
    confidentiality_penalty += 35 if "api_key" in flags else 0
    confidentiality_penalty += 18 * len([flag for flag in flags if flag in {"email", "phone", "address", "personal_name"}])
    confidentiality_penalty += 8 * len([flag for flag in flags if flag in {"url", "amount_or_contract", "postal_code"}])

    score = specificity + reusability + success_record + freshness + rating_bonus - min(confidentiality_penalty, 55)
    return min(100, max(0, int(score)))


def _normalise_entry_payload(payload: dict[str, Any]) -> dict[str, Any]:
    combined = " ".join(
        str(payload.get(key, ""))
        for key in ["industry", "project_summary", "adopted_proposal", "proposal_story", "result", "tags"]
    )
    industry = sanitize_text(str(payload.get("industry") or infer_industry(combined)), 80)
    outcome = str(payload.get("outcome") or "unknown")
    evaluation_status = str(payload.get("evaluation_status") or "effective")
    source_type = str(payload.get("source_type") or "admin_created")
    if source_type not in SAFE_SOURCE_TYPES:
        source_type = "admin_created"

    requested_status = str(payload.get("approval_status") or ("draft" if source_type == "proposal_generated" else "pending_review"))
    if requested_status not in SAFE_APPROVAL_STATUSES or requested_status == "approved":
        requested_status = "draft" if source_type == "proposal_generated" else "pending_review"

    raw_text = " ".join(str(payload.get(key, "")) for key in payload)
    flags = detect_confidential_flags(raw_text)
    approval_status = "pending_review" if flags else requested_status

    normalized = {
        "industry": industry or "other",
        "company_size": sanitize_text(str(payload.get("company_size", "")), 80),
        "project_summary": sanitize_text(str(payload.get("project_summary", "")), 500),
        "adopted_proposal": sanitize_text(str(payload.get("adopted_proposal", "")), 800),
        "proposal_story": sanitize_text(str(payload.get("proposal_story", "")), 800),
        "adoption_reason": sanitize_text(str(payload.get("adoption_reason", "")), 500),
        "lost_reason": sanitize_text(str(payload.get("lost_reason", "")), 500),
        "result": sanitize_text(str(payload.get("result", "")), 500),
        "owner_memo": sanitize_text(str(payload.get("owner_memo", "")), 800),
        "outcome": outcome if outcome in SAFE_OUTCOMES else "unknown",
        "rating": min(max(int(payload.get("rating") or 3), 1), 5),
        "evaluation_status": evaluation_status if evaluation_status in SAFE_EVALUATIONS else "effective",
        "tags": sanitize_text(str(payload.get("tags", "")), 300),
        "approval_status": approval_status,
        "source_type": source_type,
        "source_note": sanitize_text(str(payload.get("source_note", "")), 500),
    }
    normalized["quality_score"] = calculate_quality_score(normalized, flags)
    normalized["confidential_risk"] = calculate_confidential_risk(flags)
    normalized["confidential_flags"] = ",".join(flags)
    return normalized


def add_knowledge_entry(db: Connection, payload: dict[str, Any], user_id: int | None) -> dict[str, Any]:
    return create_knowledge_entry(db, _normalise_entry_payload(payload), user_id)


def get_knowledge_entries(db: Connection, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    return [_format_knowledge_entry(entry) for entry in list_knowledge_entries(db, limit, offset)]


def set_knowledge_evaluation(db: Connection, entry_id: int, rating: int, evaluation_status: str) -> dict[str, Any]:
    status = evaluation_status if evaluation_status in SAFE_EVALUATIONS else "effective"
    entry = update_knowledge_evaluation(db, entry_id, min(max(rating, 1), 5), status)
    return _format_knowledge_entry(entry)


def set_knowledge_status(db: Connection, entry_id: int, approval_status: str) -> dict[str, Any]:
    if approval_status not in SAFE_APPROVAL_STATUSES:
        raise ValueError("Invalid knowledge approval status.")
    return _format_knowledge_entry(update_knowledge_status(db, entry_id, approval_status))


def recalculate_knowledge_quality(db: Connection, entry_id: int) -> dict[str, Any]:
    entry = get_knowledge_entry(db, entry_id)
    if not entry:
        return {}
    combined = " ".join(
        str(entry.get(key, ""))
        for key in [
            "industry",
            "company_size",
            "project_summary",
            "adopted_proposal",
            "proposal_story",
            "adoption_reason",
            "lost_reason",
            "result",
            "owner_memo",
            "tags",
            "source_note",
        ]
    )
    persisted_flags = [flag for flag in str(entry.get("confidential_flags") or "").split(",") if flag]
    flags = sorted(set(detect_confidential_flags(combined) + persisted_flags))
    score = calculate_quality_score(entry, flags)
    risk = calculate_confidential_risk(flags)
    updated = update_knowledge_quality(db, entry_id, score, risk, ",".join(flags))
    if flags and updated.get("approval_status") == "approved":
        updated = update_knowledge_status(db, entry_id, "pending_review")
    return _format_knowledge_entry(updated)


def _score_candidate(query_tokens: set[str], industry: str, candidate: dict[str, Any]) -> float:
    candidate_text = " ".join(
        str(candidate.get(key, ""))
        for key in ["industry", "project_summary", "adopted_proposal", "proposal_story", "result", "tags"]
    )
    candidate_tokens = _tokens(candidate_text)
    overlap = len(query_tokens & candidate_tokens)
    score = overlap * 5
    if industry and candidate.get("industry") == industry:
        score += 25
    score += int(candidate.get("rating") or 3) * 4
    score += int(candidate.get("quality_score") or 0) / 5
    if candidate.get("outcome") == "success":
        score += 12
    if candidate.get("evaluation_status") == "effective":
        score += 8
    return float(score)


def search_similar_knowledge(db: Connection, project_summary: str, industry: str = "", limit: int = 5) -> dict[str, Any]:
    safe_summary = sanitize_text(project_summary, 700)
    inferred_industry = industry or infer_industry(safe_summary)
    query_tokens = _tokens(f"{inferred_industry} {safe_summary}")
    candidates = list_search_candidates(db, 200, approved_only=True)
    scored = []
    for candidate in candidates:
        score = _score_candidate(query_tokens, inferred_industry, candidate)
        if score > 0:
            item = _format_knowledge_entry(candidate)
            item["similarity_score"] = round(score, 1)
            scored.append(item)
    scored.sort(key=lambda item: item["similarity_score"], reverse=True)
    matches = scored[:limit]
    return {
        "industry": inferred_industry,
        "matches": matches,
        "success_patterns": _extract_patterns(matches, "success"),
        "lost_patterns": _extract_patterns(matches, "lost"),
        "recommendation": build_knowledge_recommendation(matches),
    }


def _extract_patterns(entries: list[dict[str, Any]], outcome: str) -> list[str]:
    patterns: list[str] = []
    for entry in entries:
        if entry.get("outcome") != outcome:
            continue
        value = entry.get("adopted_proposal") if outcome == "success" else entry.get("lost_reason")
        if value:
            patterns.append(str(value)[:140])
    return patterns[:3]


def build_knowledge_recommendation(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "承認済みナレッジが少ないため、今回の提案結果をレビュー後にナレッジ登録することを推奨します。"
    success_count = sum(1 for item in matches if item.get("outcome") == "success")
    lost_count = sum(1 for item in matches if item.get("outcome") == "lost")
    top = matches[0]
    if success_count >= lost_count:
        return f"{top.get('industry', 'similar')}案件では、評価の高い構成を優先し、{top.get('adopted_proposal', '提案価値')}を中心に組み立てることを推奨します。"
    return "類似の失注理由を先に確認し、差別化・予算整合・決裁者確認を提案前に補強することを推奨します。"


def build_best_practices(db: Connection) -> dict[str, Any]:
    entries = [_format_knowledge_entry(entry) for entry in list_search_candidates(db, 300, approved_only=True)]
    successful = [entry for entry in entries if entry.get("outcome") == "success" and int(entry.get("rating") or 0) >= 4]
    industry_counter = Counter(entry.get("industry") or "other" for entry in successful)
    proposal_counter = Counter()
    for entry in successful:
        for token in _tokens(f"{entry.get('adopted_proposal', '')} {entry.get('tags', '')}"):
            proposal_counter[token] += 1
    return {
        "winning_structures": _top_texts(successful, "proposal_story", 5),
        "frequent_proposals": [key for key, _ in proposal_counter.most_common(8)],
        "industry_success_examples": [
            {"industry": industry, "count": count}
            for industry, count in industry_counter.most_common(8)
        ],
    }


def _top_texts(entries: list[dict[str, Any]], key: str, limit: int) -> list[str]:
    values = []
    for entry in entries:
        value = str(entry.get(key) or "").strip()
        if value and value not in values:
            values.append(value[:160])
    return values[:limit]


def _format_knowledge_entry(entry: dict[str, Any]) -> dict[str, Any]:
    if not entry:
        return {}
    item = dict(entry)
    item["rating"] = int(item.get("rating") or 3)
    item["quality_score"] = int(item.get("quality_score") or 0)
    item["confidential_flags_list"] = [flag for flag in str(item.get("confidential_flags") or "").split(",") if flag]
    item["is_high_quality"] = (
        item["rating"] >= 4
        and item["quality_score"] >= 70
        and item.get("evaluation_status") == "effective"
        and item.get("approval_status") == "approved"
    )
    return item


def _normalise_template_payload(payload: dict[str, Any]) -> dict[str, Any]:
    category = str(payload.get("category") or "other")
    return {
        "category": category if category in SAFE_TEMPLATE_CATEGORIES else "other",
        "title": sanitize_text(str(payload.get("title", "")), 120) or "Proposal Template",
        "template_summary": sanitize_text(str(payload.get("template_summary", "")), 500),
        "structure": sanitize_text(str(payload.get("structure", "")), 1200),
        "recommended_for": sanitize_text(str(payload.get("recommended_for", "")), 500),
        "is_active": bool(payload.get("is_active", True)),
    }


def add_template(db: Connection, payload: dict[str, Any], user_id: int | None) -> dict[str, Any]:
    return _format_template(create_template(db, _normalise_template_payload(payload), user_id))


def get_templates(db: Connection, category: str = "", include_inactive: bool = False, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    return [_format_template(template) for template in list_templates(db, category, include_inactive, limit, offset)]


def set_template_active(db: Connection, template_id: int, is_active: bool) -> dict[str, Any]:
    return _format_template(update_template_active(db, template_id, is_active))


def _format_template(template: dict[str, Any]) -> dict[str, Any]:
    item = dict(template)
    if item:
        item["is_active"] = bool(item.get("is_active"))
    return item
