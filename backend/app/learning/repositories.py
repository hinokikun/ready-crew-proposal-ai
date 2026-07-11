from __future__ import annotations

import json
from sqlite3 import Connection
from typing import Any

from app.repositories import create_audit_log


SAFE_KEYWORDS = {
    "roi": ["ROI", "費用対効果", "投資対効果"],
    "competitor": ["競合", "比較", "差別化"],
    "deadline": ["納期", "スケジュール", "期限"],
    "budget": ["予算", "見積", "金額", "費用"],
    "cms": ["CMS", "WordPress", "更新"],
    "quality": ["誤り", "矛盾", "確認", "品質"],
}


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def _keyword_counts(texts: list[str]) -> dict[str, int]:
    counts = {key: 0 for key in SAFE_KEYWORDS}
    for text in texts:
        safe_text = str(text or "")
        for key, keywords in SAFE_KEYWORDS.items():
            if any(keyword in safe_text for keyword in keywords):
                counts[key] += 1
    return counts


def collect_learning_signals(db: Connection) -> dict[str, Any]:
    review_rows = db.execute(
        """
        SELECT status, review_comment
        FROM proposal_reviews
        ORDER BY updated_at DESC
        LIMIT 500
        """
    ).fetchall()
    revision_rows = db.execute(
        """
        SELECT review_comment, ai_improvement_policy, diff_summary
        FROM proposal_review_revisions
        ORDER BY created_at DESC
        LIMIT 500
        """
    ).fetchall()
    quality_rows = db.execute(
        """
        SELECT completed, bypassed, bypass_reason
        FROM quality_gates
        ORDER BY updated_at DESC
        LIMIT 500
        """
    ).fetchall()
    outcome_rows = db.execute(
        """
        SELECT outcome, lost_reason
        FROM project_outcomes
        ORDER BY updated_at DESC
        LIMIT 500
        """
    ).fetchall()
    knowledge_rows = db.execute(
        """
        SELECT rating, evaluation_status, approval_status, quality_score, confidential_risk
        FROM proposal_knowledge
        ORDER BY updated_at DESC
        LIMIT 500
        """
    ).fetchall()
    notification_rows = db.execute(
        """
        SELECT agent_name, priority, status, source_type
        FROM ai_notifications
        ORDER BY updated_at DESC
        LIMIT 500
        """
    ).fetchall()
    workspace_rows = db.execute(
        """
        SELECT agent_name, status
        FROM workspace_work_logs
        ORDER BY updated_at DESC
        LIMIT 500
        """
    ).fetchall()
    queue_rows = db.execute(
        """
        SELECT agent, status, retry_count
        FROM action_queue
        ORDER BY created_at DESC
        LIMIT 500
        """
    ).fetchall()

    review_texts = [str(row["review_comment"] or "") for row in review_rows]
    revision_texts = [
        f"{row['review_comment'] or ''} {row['ai_improvement_policy'] or ''} {row['diff_summary'] or ''}"
        for row in revision_rows
    ]
    bypass_texts = [str(row["bypass_reason"] or "") for row in quality_rows]
    keyword_counts = _keyword_counts(review_texts + revision_texts + bypass_texts)

    won = sum(1 for row in outcome_rows if row["outcome"] == "won")
    lost = sum(1 for row in outcome_rows if row["outcome"] == "lost")
    lost_reasons: dict[str, int] = {}
    for row in outcome_rows:
        reason = str(row["lost_reason"] or "unknown")
        if str(row["outcome"]) == "lost":
            lost_reasons[reason] = lost_reasons.get(reason, 0) + 1

    knowledge_total = len(knowledge_rows)
    knowledge_effective = sum(1 for row in knowledge_rows if row["evaluation_status"] == "effective")
    knowledge_avg_rating = (
        round(sum(int(row["rating"] or 0) for row in knowledge_rows) / knowledge_total, 2)
        if knowledge_total
        else 0
    )
    knowledge_high_risk = sum(1 for row in knowledge_rows if row["confidential_risk"] == "high")

    notification_total = len(notification_rows)
    notification_unread = sum(1 for row in notification_rows if row["status"] == "unread")
    high_notifications = sum(1 for row in notification_rows if row["priority"] in {"高", "鬮・", "high"})

    queue_total = len(queue_rows)
    queue_retries = sum(1 for row in queue_rows if int(row["retry_count"] or 0) > 0)
    queue_needs_human = sum(1 for row in queue_rows if row["status"] == "needs_human")
    agent_action_counts: dict[str, int] = {}
    for row in queue_rows:
        agent = str(row["agent"] or "")
        if agent:
            agent_action_counts[agent] = agent_action_counts.get(agent, 0) + 1
    for row in workspace_rows:
        agent = str(row["agent_name"] or "")
        if agent:
            agent_action_counts[agent] = agent_action_counts.get(agent, 0) + 1

    review_changes = sum(1 for row in review_rows if row["status"] == "changes_requested")
    review_requested = sum(1 for row in review_rows if row["status"] == "review_requested")
    quality_completed = sum(1 for row in quality_rows if bool(row["completed"]) or bool(row["bypassed"]))
    quality_total = len(quality_rows)

    return {
        "review": {
            "total": len(review_rows),
            "changes_requested": review_changes,
            "review_requested": review_requested,
            "keyword_counts": keyword_counts,
        },
        "quality_gate": {
            "total": quality_total,
            "completed_or_bypassed": quality_completed,
            "bypassed": sum(1 for row in quality_rows if bool(row["bypassed"])),
            "keyword_counts": _keyword_counts(bypass_texts),
        },
        "outcome": {
            "won": won,
            "lost": lost,
            "win_rate": round((won / (won + lost)) * 100, 1) if won + lost else 0,
            "lost_reasons": lost_reasons,
        },
        "knowledge": {
            "total": knowledge_total,
            "effective": knowledge_effective,
            "average_rating": knowledge_avg_rating,
            "high_confidential_risk": knowledge_high_risk,
        },
        "notification": {
            "total": notification_total,
            "unread": notification_unread,
            "high": high_notifications,
        },
        "workspace": {
            "agent_action_counts": agent_action_counts,
        },
        "orchestrator": {
            "total": queue_total,
            "retry_count": queue_retries,
            "needs_human": queue_needs_human,
        },
        "analyzed_items_count": (
            len(review_rows)
            + len(revision_rows)
            + len(quality_rows)
            + len(outcome_rows)
            + len(knowledge_rows)
            + len(notification_rows)
            + len(workspace_rows)
            + len(queue_rows)
        ),
    }


def create_learning_run(db: Connection, *, user_id: int | None, metrics: dict[str, Any], release_candidate: dict[str, str]) -> int:
    cursor = db.execute(
        """
        INSERT INTO learning_runs
        (triggered_by, status, analyzed_items_count, metrics_summary, release_candidate_version, release_candidate_summary)
        VALUES (?, 'success', ?, ?, ?, ?)
        """,
        (
            user_id,
            int(metrics.get("analyzed_items_count") or 0),
            json.dumps(_safe_metrics_summary(metrics), ensure_ascii=False)[:3000],
            release_candidate.get("version", "13.6候補")[:40],
            release_candidate.get("summary", "")[:2000],
        ),
    )
    create_audit_log(db, user_id, "learning_run", "learning", str(cursor.lastrowid), "success", "sanitized=true")
    return int(cursor.lastrowid)


def save_learning_improvements(db: Connection, *, run_id: int, improvements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    saved: list[dict[str, Any]] = []
    for item in improvements[:30]:
        cursor = db.execute(
            """
            INSERT INTO learning_improvements
            (run_id, improvement_type, agent, category, current_version, suggested_prompt,
             recommendation, expected_effect, confidence, priority, simulation, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate')
            """,
            (
                run_id,
                str(item.get("improvement_type") or "prompt")[:40],
                str(item.get("agent") or "")[:80],
                str(item.get("category") or "")[:80],
                str(item.get("current_version") or "13.5")[:40],
                str(item.get("suggested_prompt") or "")[:1200],
                str(item.get("recommendation") or "")[:1200],
                str(item.get("expected_effect") or "")[:800],
                max(0, min(int(item.get("confidence") or 50), 100)),
                max(0, min(int(item.get("priority") or 50), 100)),
                json.dumps(item.get("simulation") or {}, ensure_ascii=False)[:1200],
            ),
        )
        row = db.execute("SELECT * FROM learning_improvements WHERE id = ?", (cursor.lastrowid,)).fetchone()
        if row:
            saved.append(_learning_row_to_dict(row))
    return saved


def _safe_metrics_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "review": metrics.get("review", {}),
        "quality_gate": metrics.get("quality_gate", {}),
        "outcome": metrics.get("outcome", {}),
        "knowledge": metrics.get("knowledge", {}),
        "notification": metrics.get("notification", {}),
        "orchestrator": metrics.get("orchestrator", {}),
    }


def _learning_row_to_dict(row: Any) -> dict[str, Any]:
    item = _row_to_dict(row)
    try:
        item["simulation"] = json.loads(item.get("simulation") or "{}")
    except (TypeError, json.JSONDecodeError):
        item["simulation"] = {}
    return item


def list_latest_learning_improvements(db: Connection, limit: int = 30) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT i.*, r.release_candidate_version
        FROM learning_improvements i
        LEFT JOIN learning_runs r ON r.id = i.run_id
        ORDER BY i.priority DESC, i.confidence DESC, i.created_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_learning_row_to_dict(row) for row in rows]


def get_latest_learning_run(db: Connection) -> dict[str, Any] | None:
    row = db.execute(
        """
        SELECT *
        FROM learning_runs
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    item = _row_to_dict(row)
    try:
        item["metrics_summary"] = json.loads(item.get("metrics_summary") or "{}")
    except (TypeError, json.JSONDecodeError):
        item["metrics_summary"] = {}
    return item


def update_improvement_status(db: Connection, *, improvement_id: int, status: str, user_id: int | None) -> dict[str, Any] | None:
    row = db.execute("SELECT id FROM learning_improvements WHERE id = ?", (improvement_id,)).fetchone()
    if not row:
        return None
    safe_status = status if status in {"candidate", "adopted", "rejected"} else "candidate"
    db.execute(
        """
        UPDATE learning_improvements
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (safe_status, improvement_id),
    )
    create_audit_log(db, user_id, "learning_improvement_status", "learning_improvement", str(improvement_id), "success", f"status={safe_status}")
    updated = db.execute("SELECT * FROM learning_improvements WHERE id = ?", (improvement_id,)).fetchone()
    return _learning_row_to_dict(updated)


def build_learning_analytics_from_db(db: Connection) -> dict[str, Any]:
    runs = int(db.execute("SELECT COUNT(*) AS count FROM learning_runs").fetchone()["count"] or 0)
    total = int(db.execute("SELECT COUNT(*) AS count FROM learning_improvements").fetchone()["count"] or 0)
    adopted = int(db.execute("SELECT COUNT(*) AS count FROM learning_improvements WHERE status = 'adopted'").fetchone()["count"] or 0)
    prompt_count = int(db.execute("SELECT COUNT(*) AS count FROM learning_improvements WHERE improvement_type = 'prompt'").fetchone()["count"] or 0)
    workflow_count = int(db.execute("SELECT COUNT(*) AS count FROM learning_improvements WHERE improvement_type = 'workflow'").fetchone()["count"] or 0)
    avg_effect_rows = db.execute("SELECT simulation FROM learning_improvements").fetchall()
    effect_values: list[float] = []
    for row in avg_effect_rows:
        try:
            simulation = json.loads(row["simulation"] or "{}")
            effect_values.append(float(simulation.get("win_rate_delta", 0) or 0))
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
    return {
        "learning_runs": runs,
        "improvement_adoption_rate": round((adopted / total) * 100, 1) if total else 0,
        "average_expected_win_rate_delta": round(sum(effect_values) / len(effect_values), 1) if effect_values else 0,
        "prompt_improvements": prompt_count,
        "workflow_improvements": workflow_count,
        "total_improvements": total,
    }
