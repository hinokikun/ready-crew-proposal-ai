from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from sqlite3 import Connection
from typing import Any

from app.config import settings
from app.repositories import create_audit_log, get_user_context_ids
from app.workspace.services import sanitize_workspace_text


OPTIMIZATION_CATEGORIES: dict[str, dict[str, Any]] = {
    "roi": {"title": "ROI improvement", "importance": 5, "effort": 3, "base_delta": 12.0, "tags": "roi,value"},
    "competition": {"title": "Competitive comparison", "importance": 4, "effort": 3, "base_delta": 9.0, "tags": "competition,differentiation"},
    "implementation": {"title": "Implementation roadmap", "importance": 4, "effort": 2, "base_delta": 7.0, "tags": "schedule,roadmap"},
    "cta": {"title": "CTA improvement", "importance": 4, "effort": 2, "base_delta": 6.0, "tags": "cta,next-action"},
    "evidence": {"title": "Numeric evidence", "importance": 4, "effort": 3, "base_delta": 8.0, "tags": "kpi,evidence"},
    "case_study": {"title": "Case study evidence", "importance": 3, "effort": 3, "base_delta": 6.0, "tags": "case-study,proof"},
    "faq": {"title": "FAQ addition", "importance": 3, "effort": 2, "base_delta": 5.0, "tags": "faq,risk"},
    "story": {"title": "Story improvement", "importance": 5, "effort": 3, "base_delta": 10.0, "tags": "story,structure"},
    "design": {"title": "Design structure", "importance": 3, "effort": 2, "base_delta": 4.0, "tags": "design,layout"},
}

BACKLOG_STATUSES = {"suggested", "selected", "approved", "in_revision", "applied", "measured", "rejected", "archived"}
LEGACY_STATUS_MAP = {"open": "suggested", "adopted": "selected", "done": "applied", "deferred": "archived"}
STATUS_TRANSITIONS = {
    "suggested": {"selected", "approved", "rejected", "archived"},
    "selected": {"approved", "in_revision", "rejected", "archived"},
    "approved": {"in_revision", "rejected", "archived"},
    "in_revision": {"applied", "rejected", "archived"},
    "applied": {"measured", "archived"},
    "measured": {"archived"},
    "rejected": {"archived"},
    "archived": set(),
}
BEST_PRACTICE_STATUSES = {"draft", "pending_review", "approved", "rejected", "archived"}
EVIDENCE_TYPES = {
    "workspace_history",
    "organization_history",
    "approved_knowledge",
    "presentation_review",
    "project_outcome",
    "quality_gate",
    "review_feedback",
    "rule_based",
    "ai_estimate",
    "insufficient_data",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_text(value: Any, limit: int = 400) -> str:
    return sanitize_workspace_text(str(value or ""), limit)


def _safe_json(value: Any, limit: int = 5000) -> str:
    text = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if len(text) <= limit:
        return text
    return json.dumps({"summary": "truncated", "count": len(text)}, ensure_ascii=True, sort_keys=True)


def _parse_json(value: Any, fallback: Any) -> Any:
    try:
        return json.loads(str(value or ""))
    except (TypeError, json.JSONDecodeError):
        return fallback


def _scope(db: Connection, user_id: int) -> tuple[int, int]:
    return get_user_context_ids(db, user_id)


def _normalize_status(status: str) -> str:
    return LEGACY_STATUS_MAP.get(str(status or ""), str(status or "suggested"))


def _normalized_title(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:120] or "untitled"


def _category_from_action(action: dict[str, Any]) -> str:
    raw = " ".join(
        str(action.get(key) or "")
        for key in ("action_id", "action_type", "type", "title", "summary", "instruction", "target")
    ).lower()
    if "roi" in raw or "cost" in raw or "return" in raw:
        return "roi"
    if "compet" in raw or "compare" in raw:
        return "competition"
    if "roadmap" in raw or "schedule" in raw or "timeline" in raw or "implementation" in raw:
        return "implementation"
    if "cta" in raw or "next action" in raw or "contact" in raw:
        return "cta"
    if "case" in raw or "result" in raw or "record" in raw:
        return "case_study"
    if "faq" in raw or "qa" in raw or "q&a" in raw:
        return "faq"
    if "design" in raw or "visual" in raw or "layout" in raw:
        return "design"
    if "evidence" in raw or "number" in raw or "kpi" in raw or "metric" in raw:
        return "evidence"
    return "story"


def _priority(score: float) -> str:
    if score >= 80:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"


def _weights() -> dict[str, float]:
    values = {
        "impact": settings.optimization_weight_impact,
        "confidence": settings.optimization_weight_confidence,
        "urgency": settings.optimization_weight_urgency,
        "adoption": settings.optimization_weight_adoption,
        "effort": settings.optimization_weight_effort,
    }
    total = sum(values.values())
    if total <= 0:
        return {"impact": 0.30, "confidence": 0.25, "urgency": 0.20, "adoption": 0.15, "effort": 0.10}
    return {key: value / total for key, value in values.items()}


def _evidence_meta(*, sample_size: int, adopted_count: int, generated_count: int, source_type: str = "presentation_review") -> dict[str, Any]:
    min_sample = max(1, int(settings.optimization_min_sample_size))
    if sample_size <= 0:
        evidence_type = "insufficient_data"
    elif sample_size < min_sample:
        evidence_type = "ai_estimate"
    elif generated_count or adopted_count:
        evidence_type = "workspace_history"
    else:
        evidence_type = source_type if source_type in EVIDENCE_TYPES else "presentation_review"
    requires_review = evidence_type in {"insufficient_data", "ai_estimate", "rule_based"} or sample_size < min_sample
    confidence_adjustment = 0.72 if requires_review else 1.0
    return {
        "evidence_type": evidence_type,
        "sample_size": sample_size,
        "min_sample_size": min_sample,
        "is_estimate": True,
        "calculation_method": "weighted_score_v20_1",
        "generated_at": _now(),
        "requires_human_review": requires_review,
        "confidence_adjustment": confidence_adjustment,
        "evidence_period": "latest_safe_workspace_metadata",
        "evidence_summary": (
            f"Uses {sample_size} safe metadata signal(s): presentation review actions, selected revision actions, "
            f"approval flags, and generated revision status. Customer body text is not used."
        ),
        "sample_warning": "" if sample_size >= min_sample else "Limited sample size. Treat this as a low-confidence reference estimate.",
    }


def _simulation(expected_improvement: float, effort: int, confidence: float, meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "win_rate_delta": round(expected_improvement, 1),
        "review_count_delta": round(-1 * min(25.0, expected_improvement * 1.2), 1),
        "proposal_time_delta": round(-1 * max(3.0, 16.0 - effort * 2.2), 1),
        "quality_gate_delta": round(min(15.0, expected_improvement * 0.65), 1),
        "is_estimated": True,
        "is_estimate": True,
        "note": "AI reference estimate, not a guaranteed result.",
        "confidence": round(confidence, 2),
        "sample_size": int(meta["sample_size"]),
        "evidence_type": str(meta["evidence_type"]),
        "calculation_method": str(meta["calculation_method"]),
        "generated_at": str(meta["generated_at"]),
        "requires_human_review": bool(meta["requires_human_review"]),
    }


def _score_item(*, category: str, issue_count: int, adopted_count: int, generated_count: int, source_type: str = "presentation_review") -> dict[str, Any]:
    config = OPTIMIZATION_CATEGORIES.get(category, OPTIMIZATION_CATEGORIES["story"])
    sample_size = max(0, issue_count + adopted_count + generated_count)
    meta = _evidence_meta(sample_size=sample_size, adopted_count=adopted_count, generated_count=generated_count, source_type=source_type)
    adoption_rate = round((adopted_count / max(1, issue_count)) * 100, 1) if issue_count else 0.0
    raw_confidence = min(0.95, 0.40 + issue_count * 0.06 + adopted_count * 0.05 + generated_count * 0.04)
    confidence = max(0.18, raw_confidence * float(meta["confidence_adjustment"]))
    expected = float(config["base_delta"]) + min(6.0, issue_count * 1.0) + min(4.0, adoption_rate / 25)
    if meta["requires_human_review"]:
        expected *= 0.55
    impact = min(100.0, expected * 6 + float(config["importance"]) * 5)
    effort = int(config["effort"])
    importance = int(config["importance"])
    urgency = min(100.0, issue_count * 12 + importance * 8)
    weights = _weights()
    composite = round(
        impact * weights["impact"]
        + (confidence * 100) * weights["confidence"]
        + urgency * weights["urgency"]
        + adoption_rate * weights["adoption"]
        - (effort * 20) * weights["effort"],
        1,
    )
    explanation = (
        f"{config['title']} is recommended because safe {meta['evidence_type']} metadata shows a related tendency "
        f"across {sample_size} signal(s). This is correlation/heuristic evidence, not proof of causation."
    )
    if meta["sample_warning"]:
        explanation += f" {meta['sample_warning']}"
    simulation = _simulation(expected, effort, confidence, meta)
    return {
        "category": category,
        "title": str(config["title"]),
        "priority": _priority(composite),
        "impact": round(impact, 1),
        "confidence": round(confidence, 2),
        "expected_improvement": round(expected, 1),
        "effort": effort,
        "importance": importance,
        "adoption_rate": adoption_rate,
        "predicted_win_rate_delta": round(expected, 1),
        "composite_score": composite,
        "simulation": simulation,
        "predicted_effect": simulation,
        "measured_effect": {},
        "measurement_status": "insufficient_data" if meta["requires_human_review"] else "pending",
        "evidence_type": meta["evidence_type"],
        "sample_size": meta["sample_size"],
        "is_estimate": True,
        "calculation_method": meta["calculation_method"],
        "requires_human_review": meta["requires_human_review"],
        "evidence_summary": meta["evidence_summary"],
        "evidence_period": meta["evidence_period"],
        "explanation": explanation,
    }


def _collect_signal_counts(db: Connection, organization_id: int, workspace_id: int, project_id: str = "") -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    where_project = "AND project_id = ?" if project_id else ""
    params: tuple[Any, ...] = (organization_id, workspace_id, project_id) if project_id else (organization_id, workspace_id)
    rows = db.execute(
        f"""
        SELECT actions_json, improvements_json
        FROM presentation_reviews
        WHERE organization_id = ? AND workspace_id = ? {where_project}
        ORDER BY updated_at DESC
        LIMIT 40
        """,
        params,
    ).fetchall()
    for row in rows:
        actions = _parse_json(row["actions_json"], []) or _parse_json(row["improvements_json"], [])
        for action in actions[:20] if isinstance(actions, list) else []:
            if not isinstance(action, dict):
                continue
            category = _category_from_action(action)
            bucket = counts.setdefault(category, {"issues": 0, "adopted": 0, "generated": 0})
            bucket["issues"] += 1

    revision_rows = db.execute(
        f"""
        SELECT selected_actions_json, status, approved
        FROM presentation_revisions
        WHERE organization_id = ? AND workspace_id = ? {where_project}
        ORDER BY updated_at DESC
        LIMIT 60
        """,
        params,
    ).fetchall()
    for row in revision_rows:
        actions = _parse_json(row["selected_actions_json"], [])
        for action in actions if isinstance(actions, list) else []:
            if not isinstance(action, dict):
                continue
            category = _category_from_action(action)
            bucket = counts.setdefault(category, {"issues": 0, "adopted": 0, "generated": 0})
            bucket["adopted"] += 1 if int(row["approved"] or 0) else 0
            bucket["generated"] += 1 if str(row["status"] or "") == "generated" else 0
    return counts


def _decorate_backlog(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["status"] = _normalize_status(str(item.get("status") or "suggested"))
    item["simulation"] = _parse_json(item.get("simulation_json"), {}) or _parse_json(item.get("predicted_effect_json"), {})
    item["predicted_effect"] = _parse_json(item.get("predicted_effect_json"), {}) or item["simulation"]
    item["measured_effect"] = _parse_json(item.get("measured_effect_json"), {})
    item["is_estimate"] = bool(item.get("is_estimate", 1))
    item["requires_human_review"] = bool(item.get("requires_human_review", 1))
    return item


def _upsert_backlog_item(
    db: Connection,
    *,
    organization_id: int,
    workspace_id: int,
    project_id: str,
    category: str,
    scored: dict[str, Any],
    user_id: int,
    source_type: str = "review_signal",
) -> None:
    existing = db.execute(
        """
        SELECT id
        FROM proposal_improvement_backlog
        WHERE organization_id = ? AND workspace_id = ? AND project_id = ? AND category = ? AND status IN ('open', 'suggested', 'adopted', 'selected', 'approved', 'in_revision')
        ORDER BY id DESC
        LIMIT 1
        """,
        (organization_id, workspace_id, project_id, category),
    ).fetchone()
    values = (
        scored["title"],
        f"Improve {scored['title']} before sending the next Beautiful.ai revision.",
        scored["priority"],
        scored["impact"],
        scored["confidence"],
        scored["expected_improvement"],
        scored["effort"],
        scored["importance"],
        scored["adoption_rate"],
        scored["predicted_win_rate_delta"],
        scored["composite_score"],
        scored["explanation"],
        _safe_json(scored["simulation"]),
        scored["evidence_type"],
        scored["sample_size"],
        1 if scored["is_estimate"] else 0,
        scored["calculation_method"],
        _safe_json(scored["predicted_effect"]),
        scored["measurement_status"],
        1 if scored["requires_human_review"] else 0,
        scored["evidence_summary"],
        scored["evidence_period"],
    )
    if existing:
        db.execute(
            """
            UPDATE proposal_improvement_backlog
            SET title = ?, summary = ?, priority = ?, impact = ?, confidence = ?, expected_improvement = ?,
                effort = ?, importance = ?, adoption_rate = ?, predicted_win_rate_delta = ?, composite_score = ?,
                explanation = ?, simulation_json = ?, evidence_type = ?, sample_size = ?, is_estimate = ?,
                calculation_method = ?, predicted_effect_json = ?, measurement_status = ?,
                requires_human_review = ?, evidence_summary = ?, evidence_period = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (*values, int(existing["id"])),
        )
        return
    db.execute(
        """
        INSERT INTO proposal_improvement_backlog
        (project_id, category, title, summary, priority, impact, confidence, expected_improvement, effort, importance,
         adoption_rate, predicted_win_rate_delta, composite_score, explanation, simulation_json, evidence_type, sample_size,
         is_estimate, calculation_method, predicted_effect_json, measurement_status, requires_human_review, evidence_summary,
         evidence_period, source_type, created_by, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, category, *values, source_type, user_id, organization_id, workspace_id),
    )


def run_optimization(db: Connection, *, user_id: int, project_id: str = "") -> dict[str, Any]:
    organization_id, workspace_id = _scope(db, user_id)
    safe_project_id = _safe_text(project_id, 120)
    signals = _collect_signal_counts(db, organization_id, workspace_id, safe_project_id)
    created_or_updated = 0

    for category, count in signals.items():
        if count["issues"] <= 0:
            continue
        scored = _score_item(
            category=category,
            issue_count=count["issues"],
            adopted_count=count["adopted"],
            generated_count=count["generated"],
        )
        _upsert_backlog_item(
            db,
            organization_id=organization_id,
            workspace_id=workspace_id,
            project_id=safe_project_id,
            category=category,
            scored=scored,
            user_id=user_id,
        )
        created_or_updated += 1

    if not signals:
        for category in ("roi", "competition", "cta"):
            scored = _score_item(category=category, issue_count=1, adopted_count=0, generated_count=0, source_type="ai_estimate")
            scored["explanation"] += " Baseline recommendation created because no review signal exists yet."
            _upsert_backlog_item(
                db,
                organization_id=organization_id,
                workspace_id=workspace_id,
                project_id=safe_project_id,
                category=category,
                scored=scored,
                user_id=user_id,
                source_type="ai_estimate",
            )
            created_or_updated += 1

    create_audit_log(db, user_id, "proposal_optimization_run", "proposal_optimization", safe_project_id, "success", f"items={created_or_updated};sanitized=true")
    return build_recommendations(db, user_id=user_id, project_id=safe_project_id)


def list_backlog(db: Connection, *, user_id: int, project_id: str = "", status: str = "") -> list[dict[str, Any]]:
    organization_id, workspace_id = _scope(db, user_id)
    clauses = ["organization_id = ?", "workspace_id = ?"]
    params: list[Any] = [organization_id, workspace_id]
    if project_id:
        clauses.append("project_id = ?")
        params.append(_safe_text(project_id, 120))
    if status:
        clauses.append("status = ?")
        params.append(_normalize_status(_safe_text(status, 40)))
    rows = db.execute(
        f"""
        SELECT *
        FROM proposal_improvement_backlog
        WHERE {' AND '.join(clauses)}
        ORDER BY composite_score DESC, updated_at DESC, id DESC
        LIMIT 100
        """,
        tuple(params),
    ).fetchall()
    return [_decorate_backlog(row) for row in rows]


def build_recommendations(db: Connection, *, user_id: int, project_id: str = "") -> dict[str, Any]:
    items = list_backlog(db, user_id=user_id, project_id=project_id, status="")
    active = [item for item in items if item["status"] in {"suggested", "selected", "approved", "in_revision"}]
    return {
        "recommendations": active[:5],
        "backlog": items,
        "dashboard": build_optimization_dashboard(db, user_id=user_id),
        "note": "Effects are AI reference estimates from safe metadata. They are not guaranteed results.",
    }


def update_backlog_status(db: Connection, *, backlog_id: int, user_id: int, status: str) -> dict[str, Any] | None:
    requested = _normalize_status(status)
    if requested not in BACKLOG_STATUSES:
        raise ValueError("invalid_status")
    organization_id, workspace_id = _scope(db, user_id)
    row = db.execute(
        "SELECT * FROM proposal_improvement_backlog WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (backlog_id, organization_id, workspace_id),
    ).fetchone()
    if not row:
        return None
    current = _normalize_status(str(row["status"] or "suggested"))
    if requested != current and requested not in STATUS_TRANSITIONS.get(current, set()):
        raise RuntimeError("invalid_transition")
    owner_sql = ", owner = ?" if requested == "selected" else ""
    owner_params: tuple[Any, ...] = (user_id,) if requested == "selected" else ()
    db.execute(
        f"""
        UPDATE proposal_improvement_backlog
        SET status = ?, updated_at = CURRENT_TIMESTAMP {owner_sql}
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (requested, *owner_params, backlog_id, organization_id, workspace_id),
    )
    updated = db.execute(
        "SELECT * FROM proposal_improvement_backlog WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (backlog_id, organization_id, workspace_id),
    ).fetchone()
    if updated:
        create_audit_log(db, user_id, f"proposal_optimization_{requested}", "proposal_improvement_backlog", str(backlog_id), "success", "sanitized=true")
    return _decorate_backlog(updated) if updated else None


def approve_backlog_item(db: Connection, *, backlog_id: int, user_id: int) -> dict[str, Any] | None:
    item = update_backlog_status(db, backlog_id=backlog_id, user_id=user_id, status="approved")
    if not item:
        return None
    organization_id, workspace_id = _scope(db, user_id)
    db.execute(
        """
        UPDATE proposal_improvement_backlog
        SET approved_by = ?, approved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (user_id, backlog_id, organization_id, workspace_id),
    )
    row = db.execute(
        "SELECT * FROM proposal_improvement_backlog WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (backlog_id, organization_id, workspace_id),
    ).fetchone()
    if row:
        create_audit_log(db, user_id, "proposal_optimization_approve", "proposal_improvement_backlog", str(backlog_id), "success", "sanitized=true")
    return _decorate_backlog(row) if row else None


def mark_backlog_in_revision(db: Connection, *, backlog_ids: list[int], user_id: int) -> list[dict[str, Any]]:
    results = []
    for backlog_id in backlog_ids[:20]:
        try:
            item = update_backlog_status(db, backlog_id=backlog_id, user_id=user_id, status="in_revision")
        except RuntimeError:
            continue
        if item:
            results.append(item)
    return results


def record_backlog_measurement(
    db: Connection,
    *,
    backlog_id: int,
    user_id: int,
    measured_effect: dict[str, Any],
    measurement_status: str,
    measurement_period: str = "",
    outcome_type: str = "",
) -> dict[str, Any] | None:
    if measurement_status not in {"pending", "insufficient_data", "measured", "inconclusive"}:
        raise ValueError("invalid_measurement_status")
    organization_id, workspace_id = _scope(db, user_id)
    row = db.execute(
        "SELECT * FROM proposal_improvement_backlog WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (backlog_id, organization_id, workspace_id),
    ).fetchone()
    if not row:
        return None
    measured_safe = {
        key: measured_effect.get(key)
        for key in ("win_rate_delta", "review_count_delta", "proposal_time_delta", "quality_gate_delta", "sample_size", "note")
        if key in measured_effect
    }
    db.execute(
        """
        UPDATE proposal_improvement_backlog
        SET measured_effect_json = ?, measurement_status = ?, measured_at = CURRENT_TIMESTAMP,
            measurement_period = ?, outcome_type = ?, status = CASE WHEN ? = 'measured' THEN 'measured' ELSE status END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (_safe_json(measured_safe), measurement_status, _safe_text(measurement_period, 120), _safe_text(outcome_type, 80), measurement_status, backlog_id, organization_id, workspace_id),
    )
    updated = db.execute(
        "SELECT * FROM proposal_improvement_backlog WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (backlog_id, organization_id, workspace_id),
    ).fetchone()
    if updated:
        create_audit_log(db, user_id, "proposal_optimization_measure", "proposal_improvement_backlog", str(backlog_id), "success", "sanitized=true")
    return _decorate_backlog(updated) if updated else None


def _decorate_best_practice(row: Any) -> dict[str, Any]:
    item = dict(row)
    item["has_prediction"] = bool(item.get("has_prediction", 0))
    return item


def extract_best_practices(db: Connection, *, user_id: int) -> list[dict[str, Any]]:
    organization_id, workspace_id = _scope(db, user_id)
    revisions = db.execute(
        """
        SELECT selected_actions_json
        FROM presentation_revisions
        WHERE organization_id = ? AND workspace_id = ? AND status = 'generated'
        ORDER BY generated_at DESC, updated_at DESC
        LIMIT 50
        """,
        (organization_id, workspace_id),
    ).fetchall()
    inserted_or_updated = 0
    for row in revisions:
        actions = _parse_json(row["selected_actions_json"], [])
        for action in actions if isinstance(actions, list) else []:
            if not isinstance(action, dict):
                continue
            category = _category_from_action(action)
            config = OPTIMIZATION_CATEGORIES.get(category, OPTIMIZATION_CATEGORIES["story"])
            title = str(config["title"])
            normalized = _normalized_title(title)
            existing = db.execute(
                """
                SELECT id FROM proposal_best_practices
                WHERE organization_id = ? AND workspace_id = ? AND category = ? AND normalized_title = ?
                """,
                (organization_id, workspace_id, category, normalized),
            ).fetchone()
            if existing:
                db.execute(
                    """
                    UPDATE proposal_best_practices
                    SET adoption_count = adoption_count + 1, evidence_count = evidence_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (int(existing["id"]),),
                )
                inserted_or_updated += 1
                continue
            db.execute(
                """
                INSERT INTO proposal_best_practices
                (category, title, normalized_title, pattern_summary, source_type, success_metric, confidence, adoption_count,
                 status, tags, structure_summary, cta_type, slide_order_pattern, evidence_count, evidence_period,
                 confidential_risk, quality_score, has_prediction, organization_id, workspace_id)
                VALUES (?, ?, ?, ?, 'presentation_revision', ?, ?, 1, 'pending_review', ?, ?, ?, ?, 1, ?,
                        'low', ?, 0, ?, ?)
                """,
                (
                    category,
                    title,
                    normalized,
                    f"Reusable pattern: {title}. Summary only; no proposal body text is stored.",
                    "generated_revision",
                    0.72,
                    str(config.get("tags", "")),
                    f"Apply {title} as a safe proposal structure improvement.",
                    "contextual",
                    category,
                    "latest_generated_revisions",
                    72,
                    organization_id,
                    workspace_id,
                ),
            )
            inserted_or_updated += 1
    if inserted_or_updated:
        create_audit_log(db, user_id, "best_practice_extract", "proposal_best_practices", "", "success", f"count={inserted_or_updated};sanitized=true")
    return list_best_practices(db, user_id=user_id, approved_only=False)


def list_best_practices(db: Connection, *, user_id: int, approved_only: bool = True) -> list[dict[str, Any]]:
    organization_id, workspace_id = _scope(db, user_id)
    where_status = "AND status = 'approved'" if approved_only else ""
    rows = db.execute(
        f"""
        SELECT *
        FROM proposal_best_practices
        WHERE organization_id = ? AND workspace_id = ? {where_status}
        ORDER BY quality_score DESC, confidence DESC, adoption_count DESC, updated_at DESC
        LIMIT 100
        """,
        (organization_id, workspace_id),
    ).fetchall()
    return [_decorate_best_practice(row) for row in rows]


def update_best_practice_status(
    db: Connection,
    *,
    best_practice_id: int,
    user_id: int,
    status: str,
    reason: str = "",
) -> dict[str, Any] | None:
    if status not in BEST_PRACTICE_STATUSES:
        raise ValueError("invalid_status")
    organization_id, workspace_id = _scope(db, user_id)
    if status == "approved":
        sql = """
            UPDATE proposal_best_practices
            SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP,
                approval_reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """
        params = (user_id, _safe_text(reason, 300), best_practice_id, organization_id, workspace_id)
    elif status == "rejected":
        sql = """
            UPDATE proposal_best_practices
            SET status = 'rejected', rejection_reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """
        params = (_safe_text(reason, 300), best_practice_id, organization_id, workspace_id)
    elif status == "archived":
        sql = """
            UPDATE proposal_best_practices
            SET status = 'archived', archived_reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """
        params = (_safe_text(reason, 300), best_practice_id, organization_id, workspace_id)
    else:
        sql = """
            UPDATE proposal_best_practices
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """
        params = (status, best_practice_id, organization_id, workspace_id)
    db.execute(sql, params)
    row = db.execute(
        "SELECT * FROM proposal_best_practices WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (best_practice_id, organization_id, workspace_id),
    ).fetchone()
    if row:
        create_audit_log(db, user_id, f"best_practice_{status}", "proposal_best_practices", str(best_practice_id), "success", "sanitized=true")
    return _decorate_best_practice(row) if row else None


def build_revision_actions(db: Connection, *, user_id: int, project_id: str = "") -> list[dict[str, Any]]:
    items = [
        item
        for item in list_backlog(db, user_id=user_id, project_id=project_id)
        if item["status"] in {"selected", "approved"}
    ][:10]
    return [
        {
            "action_id": f"optimization-{item['id']}",
            "action_type": item["category"],
            "title": item["title"],
            "summary": item["summary"],
            "instruction": f"{item['title']}: {item['explanation']}",
            "human_action": "Reflect selected optimization in the next Presentation Revision.",
        }
        for item in items
    ]


def build_optimization_dashboard(db: Connection, *, user_id: int | None = None, scope: Any | None = None) -> dict[str, Any]:
    if scope:
        from app.scope_policy import scope_where

        where, params = scope_where(scope, "b")
    elif user_id is not None:
        organization_id, workspace_id = _scope(db, user_id)
        where, params = "b.organization_id = ? AND b.workspace_id = ?", (organization_id, workspace_id)
    else:
        where, params = "1 = 1", ()
    row = db.execute(
        f"""
        SELECT
          COUNT(*) AS backlog_count,
          COALESCE(SUM(CASE WHEN status IN ('selected', 'adopted') THEN 1 ELSE 0 END), 0) AS selected_count,
          COALESCE(SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END), 0) AS approved_count,
          COALESCE(SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END), 0) AS rejected_count,
          COALESCE(SUM(CASE WHEN is_estimate = 1 THEN 1 ELSE 0 END), 0) AS estimated_count,
          COALESCE(SUM(CASE WHEN measurement_status = 'measured' THEN 1 ELSE 0 END), 0) AS measured_count,
          COALESCE(SUM(CASE WHEN sample_size < ? THEN 1 ELSE 0 END), 0) AS insufficient_sample_count,
          COALESCE(SUM(CASE WHEN requires_human_review = 1 THEN 1 ELSE 0 END), 0) AS human_review_count,
          COALESCE(AVG(expected_improvement), 0) AS avg_expected,
          COALESCE(AVG(predicted_win_rate_delta), 0) AS avg_win_delta,
          COALESCE(AVG(confidence), 0) AS avg_confidence
        FROM proposal_improvement_backlog b
        WHERE {where}
        """,
        (settings.optimization_min_sample_size, *params),
    ).fetchone()
    revision_row = db.execute(
        f"""
        SELECT
          COUNT(*) AS revision_count,
          COALESCE(SUM(CASE WHEN status = 'generated' THEN 1 ELSE 0 END), 0) AS generated_count
        FROM presentation_revisions b
        WHERE {where}
        """,
        params,
    ).fetchone()
    bp_row = db.execute(
        f"""
        SELECT
          COUNT(*) AS total_count,
          COALESCE(SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END), 0) AS approved_count
        FROM proposal_best_practices b
        WHERE {where}
        """,
        params,
    ).fetchone()
    backlog_count = int(row["backlog_count"] or 0) if row else 0
    selected_count = int(row["selected_count"] or 0) if row else 0
    approved_count = int(row["approved_count"] or 0) if row else 0
    rejected_count = int(row["rejected_count"] or 0) if row else 0
    estimated_count = int(row["estimated_count"] or 0) if row else 0
    measured_count = int(row["measured_count"] or 0) if row else 0
    insufficient_count = int(row["insufficient_sample_count"] or 0) if row else 0
    human_review_count = int(row["human_review_count"] or 0) if row else 0
    revision_count = int(revision_row["revision_count"] or 0) if revision_row else 0
    generated_count = int(revision_row["generated_count"] or 0) if revision_row else 0
    bp_total = int(bp_row["total_count"] or 0) if bp_row else 0
    bp_approved = int(bp_row["approved_count"] or 0) if bp_row else 0
    return {
        "backlog_count": backlog_count,
        "improvement_adoption_rate": round((selected_count / backlog_count) * 100, 1) if backlog_count else 0,
        "improvement_success_rate": round((approved_count / backlog_count) * 100, 1) if backlog_count else 0,
        "improvement_rejection_rate": round((rejected_count / backlog_count) * 100, 1) if backlog_count else 0,
        "average_improvements": round(float(row["avg_expected"] or 0), 1) if row else 0,
        "average_revisions": round(revision_count / max(1, backlog_count), 1) if backlog_count else 0,
        "revision_success_rate": round((generated_count / revision_count) * 100, 1) if revision_count else 0,
        "predicted_win_rate_improvement": round(float(row["avg_win_delta"] or 0), 1) if row else 0,
        "estimated_improvement_count": estimated_count,
        "measured_improvement_count": measured_count,
        "insufficient_sample_count": insufficient_count,
        "human_review_required_count": human_review_count,
        "best_practice_approval_rate": round((bp_approved / bp_total) * 100, 1) if bp_total else 0,
        "revision_link_rate": round((revision_count / backlog_count) * 100, 1) if backlog_count else 0,
        "prediction_measurement_gap": None,
        "measurement_uncertainty_rate": round((insufficient_count / backlog_count) * 100, 1) if backlog_count else 0,
        "average_prediction_error": None,
        "confidence_success_rate": round(float(row["avg_confidence"] or 0) * 100, 1) if row else 0,
    }
