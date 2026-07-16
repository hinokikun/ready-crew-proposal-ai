from __future__ import annotations

import re
from datetime import datetime
from sqlite3 import Connection
from typing import Any

from app.repositories import create_audit_log, get_project_detail, get_user_context_ids
from app.scope_policy import ScopeContext, scope_where
from app.workspace.repositories import save_workspace_bundle


MAX_RETRY_COUNT = 3

ACTION_PLAN: list[dict[str, Any]] = [
    {
        "action_type": "competitive_analysis",
        "agent": "AI営業",
        "priority": 90,
        "reason": "案件受付が完了したため、AI営業へ競合分析を依頼します。",
        "result": "比較観点、導入効果、KPI、運用設計の確認観点を整理しました。",
    },
    {
        "action_type": "proposal_story",
        "agent": "AI営業",
        "priority": 80,
        "reason": "競合分析が完了したため、提案ストーリー作成へ移行します。",
        "result": "顧客課題、提案コンセプト、勝ち筋をつなぐ提案ストーリーを整理しました。",
    },
    {
        "action_type": "proposal_document",
        "agent": "AI営業",
        "priority": 75,
        "reason": "提案ストーリーが整理できたため、提案書作成へ移行します。",
        "result": "提案書初稿の章立て、主要メッセージ、スライド骨子を作成しました。",
    },
    {
        "action_type": "director_review",
        "agent": "AIディレクター",
        "priority": 70,
        "reason": "提案書の骨子ができたため、AIディレクターへ品質レビューを依頼します。",
        "result": "提案ストーリー、課題との整合性、読みやすさをレビューしました。",
    },
    {
        "action_type": "quality_check",
        "agent": "AIディレクター",
        "priority": 65,
        "reason": "レビュー結果を踏まえ、提出前品質チェックへ移行します。",
        "result": "論理矛盾、提案漏れ、AI推測項目、確認が必要な点を整理しました。",
    },
    {
        "action_type": "ppt_generation",
        "agent": "AI PM",
        "priority": 60,
        "reason": "品質チェックが完了したため、AI PMへPPT生成準備を依頼します。",
        "result": "要約PPT、詳細PPT、提出前確認ゲートへつなぐ生成準備を整えました。",
    },
    {
        "action_type": "estimate_generation",
        "agent": "AI PM",
        "priority": 55,
        "reason": "資料構成が整ったため、AI PMへ見積生成を依頼します。",
        "result": "概算見積、必須対応、推奨対応、オプション対応の整理を完了しました。",
    },
    {
        "action_type": "notification",
        "agent": "AI秘書",
        "priority": 50,
        "reason": "成果物の準備が整ったため、AI秘書へ営業担当への通知を依頼します。",
        "result": "営業担当へ次に確認すべき内容とダウンロード導線を通知しました。",
    },
    {
        "action_type": "final_approval",
        "agent": "AI社長",
        "priority": 45,
        "reason": "全工程が完了したため、AI社長が最終レビューへ移行します。",
        "result": "AI社長が提案方針、品質、次アクションの整合性を確認しました。",
    },
]

ACTION_LABELS = {
    "competitive_analysis": "競合分析",
    "proposal_story": "提案ストーリー",
    "proposal_document": "提案書",
    "director_review": "レビュー",
    "quality_check": "品質チェック",
    "ppt_generation": "PPT生成",
    "estimate_generation": "見積生成",
    "notification": "通知",
    "final_approval": "最終承認",
}


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def _safe_text(value: str, max_length: int = 500) -> str:
    text = (value or "").strip()
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", text)
    text = re.sub(r"(api[_-]?key|token|password|secret)\s*[:=]\s*\S+", r"\1=[redacted]", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(sk-[A-Za-z0-9_-]{16,})\b", "[api-key]", text)
    return text[:max_length]


def _scope(db: Connection, user_id: int | None) -> tuple[int, int]:
    return get_user_context_ids(db, user_id)


def _project_in_scope(project: dict[str, Any] | None, organization_id: int, workspace_id: int) -> bool:
    if not project:
        return False
    return int(project.get("organization_id") or 1) == organization_id and int(project.get("workspace_id") or 1) == workspace_id


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T"))
    except ValueError:
        return None


def _action_plan_item(action_type: str) -> dict[str, Any]:
    return next((item for item in ACTION_PLAN if item["action_type"] == action_type), ACTION_PLAN[-1])


def _insert_workspace_update(
    db: Connection,
    *,
    user_id: int | None,
    project_id: int,
    action_id: int,
    agent: str,
    result_summary: str,
    reason: str,
    status: str,
) -> None:
    status_label = "done" if status == "success" else "active"
    save_workspace_bundle(
        db,
        user_id,
        str(project_id),
        [
            {
                "client_message_id": f"orchestrator-agent-{action_id}",
                "agent_name": agent,
                "message_type": "done" if status == "success" else "normal",
                "message_body": _safe_text(result_summary, 420),
                "status": status_label,
            },
            {
                "client_message_id": f"orchestrator-president-{action_id}",
                "agent_name": "AI社長",
                "message_type": "explanation",
                "message_body": _safe_text(reason, 420),
                "status": status_label,
            },
        ],
        [
            {
                "client_log_id": f"orchestrator-log-{action_id}",
                "agent_name": agent,
                "action_summary": _safe_text(result_summary, 300),
                "status": status_label,
            }
        ],
    )


def enqueue_project_orchestration(db: Connection, *, project_id: int, user_id: int | None) -> dict[str, Any]:
    organization_id, workspace_id = _scope(db, user_id)
    project = get_project_detail(db, project_id)
    if not _project_in_scope(project, organization_id, workspace_id):
        return {"created": 0, "project_id": project_id}

    created = 0
    for item in ACTION_PLAN:
        existing = db.execute(
            """
            SELECT id FROM action_queue
            WHERE project_id = ? AND action_type = ? AND organization_id = ? AND workspace_id = ?
            LIMIT 1
            """,
            (project_id, item["action_type"], organization_id, workspace_id),
        ).fetchone()
        if existing:
            continue
        db.execute(
            """
            INSERT INTO action_queue
            (project_id, action_type, agent, status, priority, reason, result_summary, created_by, organization_id, workspace_id)
            VALUES (?, ?, ?, 'pending', ?, ?, '', ?, ?, ?)
            """,
            (project_id, item["action_type"], item["agent"], int(item["priority"]), _safe_text(item["reason"], 500), user_id, organization_id, workspace_id),
        )
        created += 1

    if created:
        create_audit_log(db, user_id, "orchestrator_queue_created", "project", str(project_id), "success", f"actions={created}")
        save_workspace_bundle(
            db,
            int(user_id) if user_id else None,
            str(project_id),
            [
                {
                    "client_message_id": f"orchestrator-start-{project_id}",
                    "agent_name": "AI社長",
                    "message_type": "explanation",
                    "message_body": "案件受付が完了しました。AI社員へ作業を順番に割り当てます。",
                    "status": "active",
                }
            ],
            [
                {
                    "client_log_id": f"orchestrator-start-log-{project_id}",
                    "agent_name": "AI社長",
                    "action_summary": "Project Orchestratorが作業キューを作成しました。",
                    "status": "active",
                }
            ],
        )
    return {"created": created, "project_id": project_id, "queue": list_project_queue(db, project_id, user_id)}


def _needs_human_input(project: dict[str, Any], action_type: str) -> bool:
    if action_type not in {"estimate_generation", "ppt_generation"}:
        return False
    text = f"{project.get('summary') or ''} {project.get('next_action') or ''}"
    return "人間確認必須" in text or "human_required" in text


def _complete_action(db: Connection, *, action: dict[str, Any], user_id: int | None, project: dict[str, Any]) -> None:
    action_id = int(action["id"])
    action_type = str(action["action_type"])
    plan = _action_plan_item(action_type)
    if _needs_human_input(project, action_type):
        result = "予算または納期の人間確認が必要なため、自律実行を一時停止しました。"
        db.execute(
            """
            UPDATE action_queue
            SET status = 'needs_human', result_summary = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (_safe_text(result, 500), action_id),
        )
        _insert_workspace_update(
            db,
            user_id=int(user_id) if user_id else None,
            project_id=int(action["project_id"]),
            action_id=action_id,
            agent=str(action["agent"]),
            result_summary=result,
            reason="人間確認が必要なため、自律実行を停止します。",
            status="needs_human",
        )
        return

    result = str(plan["result"])
    if action_type == "notification":
        _create_orchestrator_notification(db, project_id=int(action["project_id"]), user_id=int(user_id) if user_id else None)
    db.execute(
        """
        UPDATE action_queue
        SET status = 'success', result_summary = ?, completed_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (_safe_text(result, 500), action_id),
    )
    _insert_workspace_update(
        db,
        user_id=int(user_id) if user_id else None,
        project_id=int(action["project_id"]),
        action_id=action_id,
        agent=str(action["agent"]),
        result_summary=result,
        reason=str(plan["reason"]),
        status="success",
    )


def _create_orchestrator_notification(db: Connection, *, project_id: int, user_id: int | None) -> None:
    organization_id, workspace_id = _scope(db, user_id)
    key = f"{user_id or 'system'}|orchestrator_complete|project|{project_id}"
    existing = db.execute(
        "SELECT id FROM ai_notifications WHERE notification_key = ? AND organization_id = ? AND workspace_id = ?",
        (key, organization_id, workspace_id),
    ).fetchone()
    if existing:
        db.execute(
            """
            UPDATE ai_notifications
            SET status = 'unread', updated_at = CURRENT_TIMESTAMP
            WHERE notification_key = ? AND organization_id = ? AND workspace_id = ?
            """,
            (key, organization_id, workspace_id),
        )
        return
    db.execute(
        """
        INSERT INTO ai_notifications
        (notification_key, user_id, project_id, agent_name, priority, title, message, recommended_action, source_type, source_id, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            user_id or None,
            project_id,
            "AI秘書",
            "高",
            "AI社員の自律作業が完了しました",
            "提案書、見積、品質確認の準備が整いました。",
            "提出前品質ゲートを確認し、要約PPTをダウンロードしてください。",
            "orchestrator",
            str(project_id),
            organization_id,
            workspace_id,
        ),
    )


def run_project_orchestrator(db: Connection, *, project_id: int, user_id: int | None, max_actions: int = 20) -> dict[str, Any]:
    organization_id, workspace_id = _scope(db, user_id)
    project = get_project_detail(db, project_id)
    if not _project_in_scope(project, organization_id, workspace_id):
        return {"project_id": project_id, "executed": 0, "queue": []}
    executed = 0
    for _ in range(max_actions):
        action_row = db.execute(
            """
            SELECT * FROM action_queue
            WHERE project_id = ? AND status IN ('pending', 'retry_waiting')
              AND organization_id = ? AND workspace_id = ?
            ORDER BY priority DESC, id ASC
            LIMIT 1
            """,
            (project_id, organization_id, workspace_id),
        ).fetchone()
        if not action_row:
            break
        action = dict(action_row)
        action_id = int(action["id"])
        try:
            db.execute(
                "UPDATE action_queue SET status = 'running', started_at = CURRENT_TIMESTAMP WHERE id = ? AND organization_id = ? AND workspace_id = ?",
                (action_id, organization_id, workspace_id),
            )
            _complete_action(db, action=action, user_id=user_id, project=project)
            executed += 1
            latest = db.execute(
                "SELECT status FROM action_queue WHERE id = ? AND organization_id = ? AND workspace_id = ?",
                (action_id, organization_id, workspace_id),
            ).fetchone()
            if latest and latest["status"] == "needs_human":
                break
        except Exception as exc:
            retry_count = int(action.get("retry_count") or 0) + 1
            status = "retry_waiting" if retry_count < MAX_RETRY_COUNT else "failure"
            db.execute(
                """
                UPDATE action_queue
                SET status = ?, retry_count = ?, error_type = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ? AND organization_id = ? AND workspace_id = ?
                """,
                (status, retry_count, _safe_text(type(exc).__name__, 120), action_id, organization_id, workspace_id),
            )
            create_audit_log(db, user_id, "orchestrator_action_failed", "action_queue", str(action_id), "failure", f"retry_count={retry_count}")
            if status == "failure":
                break
    create_audit_log(db, user_id, "orchestrator_run", "project", str(project_id), "success", f"executed={executed}")
    return {"project_id": project_id, "executed": executed, **get_project_orchestrator_status(db, project_id, user_id)}


def retry_queue_action(db: Connection, *, action_id: int, user_id: int | None) -> dict[str, Any] | None:
    organization_id, workspace_id = _scope(db, user_id)
    row = db.execute(
        "SELECT * FROM action_queue WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (action_id, organization_id, workspace_id),
    ).fetchone()
    if not row:
        return None
    action = dict(row)
    retry_count = min(int(action.get("retry_count") or 0) + 1, MAX_RETRY_COUNT)
    db.execute(
        """
        UPDATE action_queue
        SET status = 'pending', retry_count = ?, error_type = '', started_at = NULL, completed_at = NULL
        WHERE id = ? AND organization_id = ? AND workspace_id = ?
        """,
        (retry_count, action_id, organization_id, workspace_id),
    )
    create_audit_log(db, user_id, "orchestrator_action_retry", "action_queue", str(action_id), "success", f"retry_count={retry_count}")
    updated = db.execute(
        "SELECT * FROM action_queue WHERE id = ? AND organization_id = ? AND workspace_id = ?",
        (action_id, organization_id, workspace_id),
    ).fetchone()
    return _decorate_action(db, _row_to_dict(updated))


def _decorate_action(db: Connection, item: dict[str, Any]) -> dict[str, Any]:
    if not item:
        return {}
    project_id = int(item.get("project_id") or 0)
    project = get_project_detail(db, project_id) if project_id else None
    item["action_label"] = ACTION_LABELS.get(str(item.get("action_type") or ""), str(item.get("action_type") or ""))
    item["project_name"] = str((project or {}).get("name") or "")
    item["customer_name"] = str((project or {}).get("customer_name") or "")
    item["next_agent"] = _next_agent_for_project(db, project_id, int(item.get("id") or 0))
    return item


def _next_agent_for_project(db: Connection, project_id: int, current_action_id: int | None = None) -> str:
    params: tuple[Any, ...]
    sql = """
        SELECT agent
        FROM action_queue
        WHERE project_id = ? AND status IN ('pending', 'retry_waiting')
    """
    params = (project_id,)
    if current_action_id:
        sql += " AND id <> ?"
        params = (project_id, current_action_id)
    sql += " ORDER BY priority DESC, id ASC LIMIT 1"
    row = db.execute(sql, params).fetchone()
    return str(row["agent"]) if row else ""


def list_project_queue(db: Connection, project_id: int, user_id: int | None = None) -> list[dict[str, Any]]:
    organization_id, workspace_id = _scope(db, user_id)
    rows = db.execute(
        """
        SELECT * FROM action_queue
        WHERE project_id = ? AND organization_id = ? AND workspace_id = ?
        ORDER BY priority DESC, id ASC
        """,
        (project_id, organization_id, workspace_id),
    ).fetchall()
    return [_decorate_action(db, dict(row)) for row in rows]


def list_action_queue(db: Connection, *, status: str = "", limit: int = 100, user_id: int | None = None) -> list[dict[str, Any]]:
    organization_id, workspace_id = _scope(db, user_id)
    if status:
        rows = db.execute(
            """
            SELECT * FROM action_queue
            WHERE status = ? AND organization_id = ? AND workspace_id = ?
            ORDER BY created_at DESC, priority DESC, id DESC
            LIMIT ?
            """,
            (status, organization_id, workspace_id, max(1, min(limit, 200))),
        ).fetchall()
    else:
        rows = db.execute(
            """
            SELECT * FROM action_queue
            WHERE organization_id = ? AND workspace_id = ?
            ORDER BY
                CASE status
                    WHEN 'running' THEN 1
                    WHEN 'pending' THEN 2
                    WHEN 'retry_waiting' THEN 3
                    WHEN 'needs_human' THEN 4
                    WHEN 'failure' THEN 5
                    ELSE 6
                END,
                created_at DESC,
                priority DESC,
                id DESC
            LIMIT ?
            """,
            (organization_id, workspace_id, max(1, min(limit, 200))),
        ).fetchall()
    return [_decorate_action(db, dict(row)) for row in rows]


def get_project_orchestrator_status(db: Connection, project_id: int, user_id: int | None = None) -> dict[str, Any]:
    queue = list_project_queue(db, project_id, user_id)
    current = next((item for item in queue if item.get("status") == "running"), None)
    if not current:
        current = next((item for item in queue if item.get("status") in {"pending", "retry_waiting", "needs_human"}), None)
    next_action = None
    if current:
        current_id = int(current.get("id") or 0)
        next_action = next((item for item in queue if int(item.get("id") or 0) != current_id and item.get("status") in {"pending", "retry_waiting"}), None)
    counts: dict[str, int] = {}
    for item in queue:
        key = str(item.get("status") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return {
        "project_id": project_id,
        "current_action": current,
        "next_action": next_action,
        "counts": counts,
        "queue": queue,
    }


def build_orchestrator_analytics(db: Connection, user_id: int | None = None, scope: ScopeContext | None = None) -> dict[str, Any]:
    if scope:
        where_sql, params = scope_where(scope)
    else:
        organization_id, workspace_id = _scope(db, user_id)
        where_sql, params = "organization_id = ? AND workspace_id = ?", (organization_id, workspace_id)
    rows = [
        dict(row)
        for row in db.execute(
            f"SELECT * FROM action_queue WHERE {where_sql}",
            params,
        ).fetchall()
    ]
    total = len(rows)
    status_counts: dict[str, int] = {}
    retry_items = 0
    human_items = 0
    durations: list[float] = []
    agent_seconds: dict[str, list[float]] = {}
    for row in rows:
        status = str(row.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        retry_items += 1 if int(row.get("retry_count") or 0) > 0 else 0
        human_items += 1 if status == "needs_human" else 0
        start = _parse_time(str(row.get("started_at") or ""))
        end = _parse_time(str(row.get("completed_at") or ""))
        if start and end:
            seconds = max((end - start).total_seconds(), 0)
            durations.append(seconds)
            agent = str(row.get("agent") or "")
            agent_seconds.setdefault(agent, []).append(seconds)

    project_ids = {int(row.get("project_id") or 0) for row in rows if int(row.get("project_id") or 0)}
    completed_projects = 0
    for project_id in project_ids:
        project_queue = [row for row in rows if int(row.get("project_id") or 0) == project_id]
        if project_queue and all(str(row.get("status") or "") == "success" for row in project_queue):
            completed_projects += 1

    agent_times = [
        {
            "agent": agent,
            "total_seconds": round(sum(values), 1),
            "average_seconds": round(sum(values) / len(values), 1) if values else 0,
            "action_count": len(values),
        }
        for agent, values in sorted(agent_seconds.items())
    ]
    return {
        "total_actions": total,
        "average_processing_seconds": round(sum(durations) / len(durations), 1) if durations else 0,
        "retry_rate": round((retry_items / total) * 100, 1) if total else 0,
        "autonomous_completion_rate": round((completed_projects / len(project_ids)) * 100, 1) if project_ids else 0,
        "human_intervention_rate": round((human_items / total) * 100, 1) if total else 0,
        "status_counts": status_counts,
        "agent_times": agent_times,
    }
