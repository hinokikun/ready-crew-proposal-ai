from __future__ import annotations

import json
from datetime import datetime
from sqlite3 import Connection
from typing import Any

from app.ai_watch import build_notification_analytics
from app.daily_briefing import build_daily_briefing_analytics
from app.integrations import build_integration_analytics
from app.learning.services import build_learning_analytics
from app.orchestrator import build_orchestrator_analytics
from app.project_lifecycle import build_project_lifecycle_analytics
from app.prompts.services import build_prompt_experiment_analytics


FUNNEL_STEPS = [
    ("login", "Login"),
    ("case_paste", "Case paste"),
    ("ai_analysis_start", "AI analysis start"),
    ("ai_analysis_complete", "AI analysis complete"),
    ("proposal_generated", "Proposal generated"),
    ("summary_ppt_download", "Summary PPT download"),
    ("detail_ppt_download", "Detail PPT download"),
    ("estimate_pdf_download", "Estimate PDF download"),
]

DOWNLOAD_EVENTS = {"summary_ppt_download", "detail_ppt_download", "estimate_pdf_download"}
GENERATION_EVENTS = {"proposal_generated"}
SAFE_METADATA_KEYS = {"source", "mode", "output", "reason", "category"}


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def _safe_metadata(metadata: dict[str, Any] | None) -> str:
    if not metadata:
        return ""
    safe = {
        key: value
        for key, value in metadata.items()
        if key in SAFE_METADATA_KEYS and isinstance(value, (str, int, float, bool, type(None)))
    }
    return json.dumps(safe, ensure_ascii=False)[:1000]


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace(" ", "T"))
    except ValueError:
        return None


def _error_key(category: str, message: str, source: str) -> str:
    return f"{category}|{source}|{message[:120]}".lower()


def record_analytics_event(
    db: Connection,
    *,
    user_id: int | None,
    session_key: str,
    event_name: str,
    feature_name: str = "",
    status: str = "success",
    duration_ms: int = 0,
    error_type: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    db.execute(
        """
        INSERT INTO analytics_sessions (session_key, user_id)
        VALUES (?, ?)
        ON CONFLICT(session_key) DO NOTHING
        """,
        (session_key, user_id),
    )
    db.execute(
        """
        INSERT INTO analytics_events (session_key, user_id, event_name, feature_name, status, duration_ms, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (session_key, user_id, event_name, feature_name, status, max(duration_ms, 0), _safe_metadata(metadata)),
    )

    generation_increment = 1 if event_name in GENERATION_EVENTS and status == "success" else 0
    download_increment = 1 if event_name in DOWNLOAD_EVENTS and status == "success" else 0
    error_increment = 1 if status == "failure" else 0
    db.execute(
        """
        UPDATE analytics_sessions
        SET
            user_id = COALESCE(user_id, ?),
            ended_at = CURRENT_TIMESTAMP,
            duration_seconds = CAST((JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(started_at)) * 86400 AS INTEGER),
            generation_count = generation_count + ?,
            download_count = download_count + ?,
            error_count = error_count + ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE session_key = ?
        """,
        (user_id, generation_increment, download_increment, error_increment, session_key),
    )

    if status == "failure":
        category = error_type or "unknown"
        source = feature_name or event_name
        key = _error_key(category, event_name, source)
        db.execute(
            """
            INSERT INTO analytics_errors (error_key, category, message, source)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(error_key) DO UPDATE SET
                count = count + 1,
                last_seen_at = CURRENT_TIMESTAMP
            """,
            (key, category, event_name, source),
        )

    return {"ok": True}


def list_analytics_sessions(db: Connection, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT
            s.id,
            s.session_key,
            s.user_id,
            COALESCE(u.email, 'anonymous') AS user_name,
            COALESCE(u.role, 'unknown') AS user_role,
            s.started_at,
            s.ended_at,
            s.duration_seconds,
            s.generation_count,
            s.download_count,
            s.error_count
        FROM analytics_sessions s
        LEFT JOIN users u ON u.id = s.user_id
        ORDER BY s.started_at DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def list_error_ranking(db: Connection, limit: int = 10) -> list[dict[str, Any]]:
    total = db.execute("SELECT COALESCE(SUM(count), 0) AS total FROM analytics_errors").fetchone()["total"]
    rows = db.execute(
        """
        SELECT id, category, message, source, count, first_seen_at, last_seen_at, resolved
        FROM analytics_errors
        ORDER BY count DESC, last_seen_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        item = _row_to_dict(row)
        item["percentage"] = round((int(item["count"]) / total) * 100, 1) if total else 0
        item["resolved"] = bool(item["resolved"])
        result.append(item)
    return result


def update_error_resolved(db: Connection, error_id: int, resolved: bool) -> dict[str, Any] | None:
    db.execute("UPDATE analytics_errors SET resolved = ? WHERE id = ?", (1 if resolved else 0, error_id))
    row = db.execute(
        "SELECT id, category, message, source, count, first_seen_at, last_seen_at, resolved FROM analytics_errors WHERE id = ?",
        (error_id,),
    ).fetchone()
    if not row:
        return None
    item = _row_to_dict(row)
    item["resolved"] = bool(item["resolved"])
    return item


def build_funnel_analytics(db: Connection) -> list[dict[str, Any]]:
    sessions = db.execute("SELECT session_key, started_at FROM analytics_sessions").fetchall()
    total_sessions = len(sessions)
    session_start = {row["session_key"]: _parse_time(row["started_at"]) for row in sessions}
    event_rows = db.execute(
        """
        SELECT session_key, event_name, MIN(created_at) AS first_seen
        FROM analytics_events
        GROUP BY session_key, event_name
        """
    ).fetchall()

    first_seen: dict[tuple[str, str], datetime] = {}
    for row in event_rows:
        parsed = _parse_time(row["first_seen"])
        if parsed:
            first_seen[(row["session_key"], row["event_name"])] = parsed

    previous_reached = total_sessions
    previous_step = ""
    output: list[dict[str, Any]] = []
    for index, (event_name, label) in enumerate(FUNNEL_STEPS):
        reached_sessions = [session_key for session_key, _ in session_start.items() if (session_key, event_name) in first_seen]
        reached = len(reached_sessions)
        reach_rate = round((reached / total_sessions) * 100, 1) if total_sessions else 0
        dropout_rate = round(((previous_reached - reached) / previous_reached) * 100, 1) if previous_reached else 0

        durations: list[float] = []
        for session_key in reached_sessions:
            current_time = first_seen.get((session_key, event_name))
            if not current_time:
                continue
            previous_time = session_start.get(session_key) if index == 0 else first_seen.get((session_key, previous_step))
            if previous_time:
                durations.append(max((current_time - previous_time).total_seconds(), 0))

        average_time_seconds = round(sum(durations) / len(durations), 1) if durations else 0
        output.append(
            {
                "step": event_name,
                "label": label,
                "sessions": reached,
                "reach_rate": reach_rate,
                "dropoff_rate": dropout_rate,
                "average_time_seconds": average_time_seconds,
            }
        )
        previous_reached = reached
        previous_step = event_name
    return output


def build_feature_usage(db: Connection) -> list[dict[str, Any]]:
    total_sessions = db.execute("SELECT COUNT(*) AS count FROM analytics_sessions").fetchone()["count"]
    rows = db.execute(
        """
        SELECT
            COALESCE(NULLIF(feature_name, ''), event_name) AS feature_key,
            COUNT(*) AS event_count,
            COUNT(DISTINCT session_key) AS session_count
        FROM analytics_events
        GROUP BY COALESCE(NULLIF(feature_name, ''), event_name)
        ORDER BY event_count DESC
        """
    ).fetchall()
    return [
        {
            "feature_key": row["feature_key"],
            "feature_name": row["feature_key"],
            "event_count": row["event_count"],
            "session_count": row["session_count"],
            "usage_rate": round((row["session_count"] / total_sessions) * 100, 1) if total_sessions else 0,
        }
        for row in rows
    ]


def build_improvement_candidates(funnel: list[dict[str, Any]], errors: list[dict[str, Any]], feature_usage: list[dict[str, Any]]) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    proposal_step = next((item for item in funnel if item["step"] == "proposal_generated"), None)
    if proposal_step and proposal_step["reach_rate"] < 60:
        candidates.append(
            {
                "priority": "High",
                "title": "Improve proposal generation conversion",
                "reason": f"Proposal generation reach rate is {proposal_step['reach_rate']}%.",
                "hypothesis": "Input friction, long analysis time, or unclear next action may be causing drop-off.",
                "next_action": "Review the paste-to-generation flow and reduce decision points before generation.",
            }
        )
    summary_step = next((item for item in funnel if item["step"] == "summary_ppt_download"), None)
    if summary_step and summary_step["reach_rate"] < 70:
        candidates.append(
            {
                "priority": "Medium",
                "title": "Improve summary PPT download rate",
                "reason": f"Summary PPT reach rate is {summary_step['reach_rate']}%.",
                "hypothesis": "Users may not notice the recommended download action after generation.",
                "next_action": "Keep the summary PPT download action visually dominant after generation.",
            }
        )
    if errors:
        top_error = errors[0]
        candidates.append(
            {
                "priority": "High" if int(top_error["count"]) >= 3 else "Medium",
                "title": "Reduce recurring errors",
                "reason": f"Top error is {top_error['category']} with {top_error['count']} occurrences.",
                "hypothesis": "Repeated failure patterns are blocking task completion.",
                "next_action": "Check Render logs and add targeted recovery guidance for the top error category.",
            }
        )
    if not feature_usage:
        candidates.append(
            {
                "priority": "Low",
                "title": "Collect more usage data",
                "reason": "Feature usage data is still limited.",
                "hypothesis": "More sessions are needed before prioritizing product improvements.",
                "next_action": "Run a pilot with several members and review this dashboard again.",
            }
        )
    return candidates[:6]


def build_product_analytics_dashboard(db: Connection, limit: int = 20, offset: int = 0) -> dict[str, Any]:
    total_sessions = db.execute("SELECT COUNT(*) AS count FROM analytics_sessions").fetchone()["count"]
    total_events = db.execute("SELECT COUNT(*) AS count FROM analytics_events").fetchone()["count"]
    total_errors = db.execute("SELECT COALESCE(SUM(count), 0) AS count FROM analytics_errors").fetchone()["count"]
    avg_duration = db.execute("SELECT COALESCE(AVG(duration_seconds), 0) AS value FROM analytics_sessions").fetchone()["value"]

    funnel = build_funnel_analytics(db)
    errors = list_error_ranking(db, 10)
    feature_usage = build_feature_usage(db)
    return {
        "summary": {
            "total_sessions": total_sessions,
            "total_events": total_events,
            "total_errors": total_errors,
            "average_session_seconds": round(float(avg_duration or 0), 1),
        },
        "funnel": funnel,
        "sessions": list_analytics_sessions(db, limit, offset),
        "errors": errors,
        "feature_usage": feature_usage,
        "improvement_candidates": build_improvement_candidates(funnel, errors, feature_usage),
        "project_lifecycle": build_project_lifecycle_analytics(db),
        "daily_briefing": build_daily_briefing_analytics(db),
        "notification_center": build_notification_analytics(db),
        "integrations": build_integration_analytics(db),
        "orchestrator": build_orchestrator_analytics(db),
        "learning": build_learning_analytics(db),
        "prompt_experiments": build_prompt_experiment_analytics(db),
    }


def list_release_notes(db: Connection, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT r.id, r.version, r.release_date, r.title, r.improvements, r.created_by, COALESCE(u.email, '') AS created_by_email, r.created_at
        FROM release_notes r
        LEFT JOIN users u ON u.id = r.created_by
        ORDER BY r.release_date DESC, r.id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def create_release_note(db: Connection, *, user_id: int, version: str, release_date: str, title: str, improvements: str) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO release_notes (version, release_date, title, improvements, created_by)
        VALUES (?, ?, ?, ?, ?)
        """,
        (version[:40], release_date[:20], title[:120], improvements[:2000], user_id),
    )
    row = db.execute(
        """
        SELECT r.id, r.version, r.release_date, r.title, r.improvements, r.created_by, COALESCE(u.email, '') AS created_by_email, r.created_at
        FROM release_notes r
        LEFT JOIN users u ON u.id = r.created_by
        WHERE r.id = ?
        """,
        (cursor.lastrowid,),
    ).fetchone()
    return _row_to_dict(row)
