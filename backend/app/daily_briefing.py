from __future__ import annotations

from datetime import datetime, timedelta
from sqlite3 import Connection
from typing import Any

from app.knowledge.services import sanitize_text


ACTIVE_STATUSES = {"受付", "ヒアリング", "提案中", "レビュー中", "提出済み", "商談中", "制作中", "納品", "draft", ""}
TERMINAL_STATUSES = {"受注", "失注", "完了"}


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T"))
    except ValueError:
        return None


def _safe(value: str, max_length: int = 180) -> str:
    return sanitize_text(value or "", max_length)


def _project_title(project: dict[str, Any]) -> str:
    customer = _safe(str(project.get("customer_name") or ""), 80)
    name = _safe(str(project.get("name") or "案件"), 100)
    return f"{customer} / {name}" if customer else name


def _priority(score: int) -> str:
    if score >= 80:
        return "高"
    if score >= 50:
        return "中"
    return "低"


def _load_projects(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT
            p.id,
            p.name,
            p.status,
            p.win_probability,
            p.summary,
            p.next_action,
            p.updated_at,
            c.company_name AS customer_name
        FROM projects p
        LEFT JOIN customers c ON c.id = p.customer_id
        ORDER BY p.updated_at DESC, p.id DESC
        LIMIT 100
        """
    ).fetchall()
    projects: list[dict[str, Any]] = []
    for row in rows:
        project = dict(row)
        review = db.execute(
            "SELECT status, review_comment, updated_at FROM proposal_reviews WHERE project_id = ? ORDER BY updated_at DESC, id DESC LIMIT 1",
            (str(project["id"]),),
        ).fetchone()
        latest_event = db.execute(
            "SELECT event_type, note, created_at FROM project_lifecycle_events WHERE project_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
            (project["id"],),
        ).fetchone()
        project["review_status"] = review["status"] if review else ""
        project["review_comment"] = review["review_comment"] if review else ""
        project["review_updated_at"] = review["updated_at"] if review else ""
        project["latest_event_type"] = latest_event["event_type"] if latest_event else ""
        project["latest_event_note"] = latest_event["note"] if latest_event else ""
        project["latest_event_at"] = latest_event["created_at"] if latest_event else ""
        projects.append(project)
    return projects


def _is_active(project: dict[str, Any]) -> bool:
    return str(project.get("status") or "") not in TERMINAL_STATUSES


def _is_due_soon(project: dict[str, Any]) -> bool:
    text = f"{project.get('next_action') or ''} {project.get('summary') or ''} {project.get('latest_event_note') or ''}"
    due_keywords = ["今日", "本日", "明日", "提出", "期限", "締切", "レビュー", "修正"]
    return any(keyword in text for keyword in due_keywords) or str(project.get("status") or "") in {"提案中", "レビュー中", "提出済み"}


def _is_stagnant(project: dict[str, Any], now: datetime) -> bool:
    if not _is_active(project):
        return False
    updated_at = _parse_time(str(project.get("updated_at") or ""))
    if not updated_at:
        return False
    return now - updated_at >= timedelta(days=2)


def _build_suggestion(project: dict[str, Any], *, reason: str, score: int, action: str) -> dict[str, Any]:
    return {
        "key": f"project-{project.get('id')}-{score}",
        "project_id": int(project.get("id") or 0),
        "title": _project_title(project),
        "priority": _priority(score),
        "reason": _safe(reason, 240),
        "recommended_action": _safe(action, 180),
        "deadline": _safe(str(project.get("next_action") or "今日中に状況を確認"), 160),
        "review_status": str(project.get("review_status") or ""),
        "win_probability": int(project.get("win_probability") or 0),
    }


def build_daily_briefing(db: Connection, user_id: int | None = None) -> dict[str, Any]:
    now = datetime.now()
    projects = _load_projects(db)
    active_projects = [project for project in projects if _is_active(project)]
    review_waiting = [project for project in active_projects if project.get("review_status") == "review_requested"]
    changes_requested = [project for project in active_projects if project.get("review_status") == "changes_requested"]
    due_soon = [project for project in active_projects if _is_due_soon(project)]
    expected_wins = [project for project in active_projects if int(project.get("win_probability") or 0) >= 70]
    stagnant = [project for project in active_projects if _is_stagnant(project, now)]

    suggestions: list[dict[str, Any]] = []
    for project in changes_requested[:2]:
        suggestions.append(_build_suggestion(project, reason="修正依頼が出ているため、提案内容の手戻りを早めに解消します。", score=92, action="修正コメントを確認して再作成します。"))
    for project in review_waiting[:2]:
        suggestions.append(_build_suggestion(project, reason="レビュー依頼中です。承認待ちのまま提出準備が止まる可能性があります。", score=84, action="上司レビューの状況を確認します。"))
    for project in stagnant[:3]:
        suggestions.append(_build_suggestion(project, reason="最終更新から2日以上経過しています。返信・確認漏れを防ぎます。", score=73, action="顧客または社内担当へ状況確認します。"))
    for project in due_soon[:3]:
        suggestions.append(_build_suggestion(project, reason="提出やレビューに関係する次アクションがあります。", score=72, action="今日中に提出準備を進めます。"))
    for project in stagnant[:3]:
        suggestions.append(_build_suggestion(project, reason="最終更新から2日以上経過しています。返信・確認漏れを防ぎます。", score=69, action="顧客または社内担当へ状況確認します。"))
    for project in stagnant[:3]:
        suggestions.append(_build_suggestion(project, reason="最終更新から2日以上経過しています。返信・確認漏れを防ぎます。", score=68, action="顧客または社内担当へ状況確認します。"))
    for project in expected_wins[:2]:
        suggestions.append(_build_suggestion(project, reason="受注確率が高いため、クロージング準備を優先します。", score=62, action="残課題と次回アクションを整理します。"))

    seen: set[int] = set()
    unique_suggestions: list[dict[str, Any]] = []
    for suggestion in suggestions:
        project_id = int(suggestion["project_id"])
        if project_id in seen:
            continue
        seen.add(project_id)
        unique_suggestions.append(suggestion)
        if len(unique_suggestions) >= 3:
            break

    timeline = _build_today_timeline(review_waiting, changes_requested, due_soon, expected_wins)
    recommended = unique_suggestions[0] if unique_suggestions else None
    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "summary": {
            "action_required_count": len({int(project["id"]) for project in active_projects if project in review_waiting + changes_requested + due_soon + expected_wins + stagnant}),
            "review_waiting": len(review_waiting),
            "changes_requested": len(changes_requested),
            "due_soon": len(due_soon),
            "expected_wins": len(expected_wins),
            "stagnant": len(stagnant),
        },
        "suggestions": unique_suggestions,
        "timeline": timeline,
        "recommended_project": recommended,
        "agent_comments": _build_agent_comments(review_waiting, changes_requested, due_soon, expected_wins, stagnant),
    }


def _build_today_timeline(
    review_waiting: list[dict[str, Any]],
    changes_requested: list[dict[str, Any]],
    due_soon: list[dict[str, Any]],
    expected_wins: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    if review_waiting:
        timeline.append({"time": "09:00", "label": "レビュー確認", "description": f"{_project_title(review_waiting[0])} のレビュー状況を確認"})
    if due_soon:
        timeline.append({"time": "10:30", "label": "提案提出準備", "description": f"{_project_title(due_soon[0])} の提出準備"})
    if expected_wins:
        timeline.append({"time": "13:00", "label": "商談・クロージング", "description": f"{_project_title(expected_wins[0])} の受注前確認"})
    if changes_requested:
        timeline.append({"time": "16:00", "label": "修正対応", "description": f"{_project_title(changes_requested[0])} の修正依頼対応"})
    if not timeline:
        timeline.append({"time": "09:00", "label": "案件確認", "description": "CRMの未完了案件を確認し、今日の優先順位を決めます。"})
    return timeline[:4]


def _build_agent_comments(
    review_waiting: list[dict[str, Any]],
    changes_requested: list[dict[str, Any]],
    due_soon: list[dict[str, Any]],
    expected_wins: list[dict[str, Any]],
    stagnant: list[dict[str, Any]],
) -> list[dict[str, str]]:
    return [
        {"agent": "AI秘書", "comment": f"今日対応が必要そうな案件を整理しました。停滞案件は{len(stagnant)}件です。"},
        {"agent": "AI営業", "comment": f"受注確率が高い案件は{len(expected_wins)}件あります。クロージング準備を優先します。"},
        {"agent": "AIディレクター", "comment": f"レビュー待ちは{len(review_waiting)}件、修正依頼は{len(changes_requested)}件です。"},
        {"agent": "AI PM", "comment": f"提出・期限に近い案件は{len(due_soon)}件です。スケジュールを確認します。"},
        {"agent": "AI社長", "comment": "今日は重要度の高い案件から順番に進めましょう。判断が必要なものを先に片付けます。"},
    ]


def record_briefing_event(
    db: Connection,
    *,
    user_id: int | None,
    session_key: str,
    event_type: str,
    project_id: int | None = None,
    item_key: str = "",
) -> dict[str, Any]:
    safe_events = {
        "viewed": "daily_briefing_viewed",
        "priority_clicked": "daily_briefing_priority_clicked",
        "item_completed": "daily_briefing_item_completed",
    }
    event_name = safe_events.get(event_type, "daily_briefing_viewed")
    metadata: dict[str, Any] = {"source": "daily_briefing", "category": event_type}
    if project_id:
        metadata["reason"] = f"project_id:{project_id}"
    if item_key:
        metadata["mode"] = item_key[:80]
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
        VALUES (?, ?, ?, 'daily_briefing', 'success', 0, ?)
        """,
        (session_key, user_id, event_name, _safe_metadata(metadata)),
    )
    db.execute(
        """
        UPDATE analytics_sessions
        SET user_id = COALESCE(user_id, ?), ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE session_key = ?
        """,
        (user_id, session_key),
    )
    return {"ok": True}


def _safe_metadata(metadata: dict[str, Any]) -> str:
    safe = {
        key: value
        for key, value in metadata.items()
        if key in {"source", "mode", "reason", "category"} and isinstance(value, (str, int, float, bool, type(None)))
    }
    import json

    return json.dumps(safe, ensure_ascii=False)[:1000]


def build_daily_briefing_analytics(db: Connection) -> dict[str, Any]:
    views = int(db.execute("SELECT COUNT(*) AS count FROM analytics_events WHERE event_name = 'daily_briefing_viewed'").fetchone()["count"] or 0)
    clicks = int(db.execute("SELECT COUNT(*) AS count FROM analytics_events WHERE event_name = 'daily_briefing_priority_clicked'").fetchone()["count"] or 0)
    completed = int(db.execute("SELECT COUNT(*) AS count FROM analytics_events WHERE event_name = 'daily_briefing_item_completed'").fetchone()["count"] or 0)
    return {
        "views": views,
        "priority_clicks": clicks,
        "completed": completed,
        "completion_rate": round((completed / clicks) * 100, 1) if clicks else 0,
    }
