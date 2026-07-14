from __future__ import annotations

from datetime import datetime, timedelta
from sqlite3 import Connection
from typing import Any

from app.knowledge.services import sanitize_text
from app.repositories import get_user_context_ids
from app.scope_policy import ScopeContext, scope_where


TERMINAL_STATUSES = {"受注", "失注", "完了"}
ACTIVE_REVIEW_STATUSES = {"review_requested", "changes_requested"}


def _safe(value: str, max_length: int = 220) -> str:
    return sanitize_text(value or "", max_length)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T"))
    except ValueError:
        return None


def _days_since(value: str | None, now: datetime) -> int:
    parsed = _parse_time(value)
    if not parsed:
        return 0
    return max((now - parsed).days, 0)


def _priority_rank(value: str) -> int:
    return {"高": 3, "中": 2, "低": 1}.get(value, 0)


def _project_title(project: dict[str, Any]) -> str:
    customer = _safe(str(project.get("customer_name") or ""), 80)
    name = _safe(str(project.get("name") or "案件"), 100)
    return f"{customer} / {name}" if customer else name


def _scope(db: Connection, user_id: int) -> tuple[int, int]:
    return get_user_context_ids(db, user_id)


def _load_projects(db: Connection, user_id: int) -> list[dict[str, Any]]:
    organization_id, workspace_id = _scope(db, user_id)
    rows = db.execute(
        """
        SELECT p.*, c.company_name AS customer_name
        FROM projects p
        LEFT JOIN customers c ON c.id = p.customer_id
        WHERE p.organization_id = ? AND p.workspace_id = ?
        ORDER BY p.updated_at DESC, p.id DESC
        LIMIT 200
        """,
        (organization_id, workspace_id),
    ).fetchall()
    projects: list[dict[str, Any]] = []
    for row in rows:
        project = dict(row)
        review = db.execute(
            """
            SELECT id, status, review_comment, review_requested_at, updated_at
            FROM proposal_reviews
            WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
            ORDER BY updated_at DESC, id DESC LIMIT 1
            """,
            (str(project["id"]), organization_id, workspace_id),
        ).fetchone()
        gate = db.execute(
            """
            SELECT completed, bypassed, updated_at
            FROM quality_gates
            WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
            LIMIT 1
            """,
            (str(project["id"]), organization_id, workspace_id),
        ).fetchone()
        project["review"] = dict(review) if review else None
        project["quality_gate"] = dict(gate) if gate else None
        projects.append(project)
    return projects


def _notification_payload(
    *,
    user_id: int,
    rule: str,
    agent_name: str,
    priority: str,
    title: str,
    message: str,
    recommended_action: str,
    source_type: str,
    source_id: str,
    project_id: int | None = None,
    organization_id: int = 1,
    workspace_id: int = 1,
) -> dict[str, Any]:
    key_parts = [str(user_id), rule, source_type, source_id]
    return {
        "notification_key": "|".join(key_parts),
        "user_id": user_id,
        "project_id": project_id,
        "agent_name": agent_name,
        "priority": priority,
        "title": _safe(title, 160),
        "message": _safe(message, 320),
        "recommended_action": _safe(recommended_action, 220),
        "source_type": source_type,
        "source_id": source_id,
        "organization_id": organization_id,
        "workspace_id": workspace_id,
    }


def _build_project_notifications(projects: list[dict[str, Any]], user_id: int, now: datetime) -> list[dict[str, Any]]:
    notifications: list[dict[str, Any]] = []
    for project in projects:
        project_notification_start = len(notifications)
        project_id = int(project.get("id") or 0)
        if not project_id or str(project.get("status") or "") in TERMINAL_STATUSES:
            continue
        title = _project_title(project)
        updated_days = _days_since(str(project.get("updated_at") or ""), now)
        review = project.get("review") or {}
        review_status = str(review.get("status") or "")
        review_days = _days_since(str(review.get("review_requested_at") or review.get("updated_at") or ""), now)
        gate = project.get("quality_gate") or {}

        if review_status == "review_requested" and review_days >= 3:
            notifications.append(
                _notification_payload(
                    user_id=user_id,
                    rule="review_waiting_3_days",
                    agent_name="AIディレクター",
                    priority="高",
                    title=f"{title} のレビューが止まっています",
                    message=f"レビュー依頼から{review_days}日経過しています。",
                    recommended_action="上司レビューの状況を確認し、必要なら再依頼してください。",
                    source_type="review",
                    source_id=str(review.get("id") or project_id),
                    project_id=project_id,
                )
            )

        next_action_text = f"{project.get('next_action') or ''} {project.get('summary') or ''}"
        has_due_signal = any(keyword in next_action_text for keyword in ["期限", "締切", "提出", "今日", "本日", "明日"])
        if has_due_signal and updated_days >= 2:
            notifications.append(
                _notification_payload(
                    user_id=user_id,
                    rule="deadline_overdue",
                    agent_name="AI PM",
                    priority="高",
                    title=f"{title} の期限確認が必要です",
                    message=f"提出・期限に関係する次アクションがあり、最終更新から{updated_days}日経過しています。",
                    recommended_action="提出日、納期、担当者を確認し、案件ステータスを更新してください。",
                    source_type="project",
                    source_id=str(project_id),
                    project_id=project_id,
                )
            )

        gate_completed = bool(gate.get("completed")) or bool(gate.get("bypassed"))
        if str(project.get("status") or "") in {"レビュー中", "提出済み", "商談中"} and not gate_completed:
            notifications.append(
                _notification_payload(
                    user_id=user_id,
                    rule="quality_gate_incomplete",
                    agent_name="AI社長",
                    priority="高",
                    title=f"{title} の提出前確認が未完了です",
                    message="品質ゲートが完了していません。社外提出前の確認漏れを防ぎます。",
                    recommended_action="会社名、金額、納期、AI推測項目、上司レビュー状態を確認してください。",
                    source_type="quality_gate",
                    source_id=str(project_id),
                    project_id=project_id,
                )
            )

        if updated_days >= 3:
            notifications.append(
                _notification_payload(
                    user_id=user_id,
                    rule="stagnant_project",
                    agent_name="AI秘書",
                    priority="中",
                    title=f"{title} が停滞しています",
                    message=f"最終更新から{updated_days}日経過しています。",
                    recommended_action="顧客または社内担当へ状況確認してください。",
                    source_type="project",
                    source_id=str(project_id),
                    project_id=project_id,
                )
            )

        win_probability = int(project.get("win_probability") or 0)
        if 0 < win_probability <= 30:
            notifications.append(
                _notification_payload(
                    user_id=user_id,
                    rule="low_win_probability",
                    agent_name="AI営業",
                    priority="中",
                    title=f"{title} の受注確度が低めです",
                    message=f"現在の受注確率は{win_probability}%です。",
                    recommended_action="予算、競合、決裁者、提案方針を見直してください。",
                    source_type="project",
                    source_id=str(project_id),
                    project_id=project_id,
                )
            )

        if str(project.get("status") or "") in {"レビュー中", "提出済み", "商談中"} and review_status not in ACTIVE_REVIEW_STATUSES | {"approved"}:
            notifications.append(
                _notification_payload(
                    user_id=user_id,
                    rule="supervisor_review_missing",
                    agent_name="AI社長",
                    priority="高",
                    title=f"{title} の上司レビューが未実施です",
                    message="提案提出前に人間レビューが確認できていません。",
                    recommended_action="上司レビューを依頼してください。",
                    source_type="review",
                    source_id=str(project_id),
                    project_id=project_id,
                )
            )
        for item in notifications[project_notification_start:]:
            item["organization_id"] = int(project.get("organization_id") or 1)
            item["workspace_id"] = int(project.get("workspace_id") or 1)
    return notifications


def _build_knowledge_notifications(db: Connection, user_id: int) -> list[dict[str, Any]]:
    organization_id, workspace_id = _scope(db, user_id)
    row = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM proposal_knowledge
        WHERE approval_status IN ('draft', 'pending_review')
          AND organization_id = ? AND workspace_id = ?
        """,
        (organization_id, workspace_id),
    ).fetchone()
    count = int(row["count"] if row else 0)
    if count <= 0:
        return []
    return [
        _notification_payload(
            user_id=user_id,
            rule="knowledge_pending_approval",
            agent_name="AIディレクター",
            priority="低" if count < 5 else "中",
            title="未承認のナレッジ候補があります",
            message=f"承認待ちまたは下書きのナレッジ候補が{count}件あります。",
            recommended_action="管理者またはマネージャーが内容を確認し、承認・却下・アーカイブしてください。",
            source_type="knowledge",
            source_id="pending",
            project_id=None,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    ]


def _upsert_notification(db: Connection, item: dict[str, Any]) -> None:
    existing = db.execute(
        """
        SELECT id, status FROM ai_notifications
        WHERE notification_key = ? AND organization_id = ? AND workspace_id = ?
        """,
        (item["notification_key"], item.get("organization_id") or 1, item.get("workspace_id") or 1),
    ).fetchone()
    if existing:
        if existing["status"] == "archived":
            return
        db.execute(
            """
            UPDATE ai_notifications
            SET priority = ?, title = ?, message = ?, recommended_action = ?, agent_name = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND organization_id = ? AND workspace_id = ?
            """,
            (
                item["priority"],
                item["title"],
                item["message"],
                item["recommended_action"],
                item["agent_name"],
                existing["id"],
                item.get("organization_id") or 1,
                item.get("workspace_id") or 1,
            ),
        )
        return
    db.execute(
        """
        INSERT INTO ai_notifications
        (notification_key, user_id, project_id, agent_name, priority, title, message, recommended_action, source_type, source_id, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["notification_key"],
            item["user_id"],
            item["project_id"],
            item["agent_name"],
            item["priority"],
            item["title"],
            item["message"],
            item["recommended_action"],
            item["source_type"],
            item["source_id"],
            item.get("organization_id") or 1,
            item.get("workspace_id") or 1,
        ),
    )


def run_ai_watch_engine(db: Connection, user_id: int) -> dict[str, Any]:
    now = datetime.now()
    projects = _load_projects(db, user_id)
    candidates = _build_project_notifications(projects, user_id, now) + _build_knowledge_notifications(db, user_id)
    candidates.sort(key=lambda item: (_priority_rank(item["priority"]), item["title"]), reverse=True)
    for item in candidates:
        _upsert_notification(db, item)
    return list_notifications(db, user_id)


def list_notifications(db: Connection, user_id: int) -> dict[str, Any]:
    organization_id, workspace_id = _scope(db, user_id)
    rows = db.execute(
        """
        SELECT n.*, p.name AS project_name, c.company_name AS customer_name
        FROM ai_notifications n
        LEFT JOIN projects p ON p.id = n.project_id
        LEFT JOIN customers c ON c.id = p.customer_id
        WHERE n.user_id = ? AND n.status != 'archived'
          AND n.organization_id = ? AND n.workspace_id = ?
        ORDER BY
            CASE n.priority WHEN '高' THEN 3 WHEN '中' THEN 2 WHEN '低' THEN 1 ELSE 0 END DESC,
            n.updated_at DESC,
            n.id DESC
        LIMIT 100
        """,
        (user_id, organization_id, workspace_id),
    ).fetchall()
    notifications = [dict(row) for row in rows]
    unread_count = sum(1 for item in notifications if item.get("status") == "unread")
    high_count = sum(1 for item in notifications if item.get("priority") == "高")
    return {
        "notifications": notifications,
        "summary": {
            "total": len(notifications),
            "unread": unread_count,
            "high": high_count,
            "medium": sum(1 for item in notifications if item.get("priority") == "中"),
            "low": sum(1 for item in notifications if item.get("priority") == "低"),
        },
    }


def mark_notification_read(db: Connection, notification_id: int, user_id: int) -> dict[str, Any] | None:
    organization_id, workspace_id = _scope(db, user_id)
    db.execute(
        """
        UPDATE ai_notifications
        SET status = CASE WHEN status = 'archived' THEN status ELSE 'read' END,
            read_at = COALESCE(read_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (notification_id, user_id, organization_id, workspace_id),
    )
    return _get_notification(db, notification_id, user_id)


def mark_notification_actioned(db: Connection, notification_id: int, user_id: int) -> dict[str, Any] | None:
    organization_id, workspace_id = _scope(db, user_id)
    db.execute(
        """
        UPDATE ai_notifications
        SET status = CASE WHEN status = 'archived' THEN status ELSE 'read' END,
            read_at = COALESCE(read_at, CURRENT_TIMESTAMP),
            actioned_at = COALESCE(actioned_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (notification_id, user_id, organization_id, workspace_id),
    )
    return _get_notification(db, notification_id, user_id)


def archive_notification(db: Connection, notification_id: int, user_id: int) -> dict[str, Any] | None:
    organization_id, workspace_id = _scope(db, user_id)
    db.execute(
        """
        UPDATE ai_notifications
        SET status = 'archived',
            read_at = COALESCE(read_at, CURRENT_TIMESTAMP),
            archived_at = COALESCE(archived_at, CURRENT_TIMESTAMP),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (notification_id, user_id, organization_id, workspace_id),
    )
    return _get_notification(db, notification_id, user_id)


def _get_notification(db: Connection, notification_id: int, user_id: int) -> dict[str, Any] | None:
    organization_id, workspace_id = _scope(db, user_id)
    row = db.execute(
        "SELECT * FROM ai_notifications WHERE id = ? AND user_id = ? AND organization_id = ? AND workspace_id = ?",
        (notification_id, user_id, organization_id, workspace_id),
    ).fetchone()
    return dict(row) if row else None


def build_notification_analytics(db: Connection, scope: ScopeContext | None = None) -> dict[str, Any]:
    where_sql, params = scope_where(scope) if scope else ("1 = 1", ())
    total = int(db.execute(f"SELECT COUNT(*) AS count FROM ai_notifications WHERE {where_sql}", params).fetchone()["count"] or 0)
    read = int(db.execute(f"SELECT COUNT(*) AS count FROM ai_notifications WHERE read_at IS NOT NULL AND {where_sql}", params).fetchone()["count"] or 0)
    actioned = int(db.execute(f"SELECT COUNT(*) AS count FROM ai_notifications WHERE actioned_at IS NOT NULL AND {where_sql}", params).fetchone()["count"] or 0)
    now = datetime.now()
    unread_rows = db.execute(f"SELECT created_at FROM ai_notifications WHERE status = 'unread' AND {where_sql}", params).fetchall()
    ignored = sum(1 for row in unread_rows if _days_since(row["created_at"], now) >= 3)
    return {
        "total": total,
        "unread": int(db.execute(f"SELECT COUNT(*) AS count FROM ai_notifications WHERE status = 'unread' AND {where_sql}", params).fetchone()["count"] or 0),
        "read_rate": round((read / total) * 100, 1) if total else 0,
        "action_rate": round((actioned / total) * 100, 1) if total else 0,
        "ignored_rate": round((ignored / total) * 100, 1) if total else 0,
    }
