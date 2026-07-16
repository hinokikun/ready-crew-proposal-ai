from __future__ import annotations

from datetime import datetime
from sqlite3 import Connection
from typing import Any

from app.knowledge.services import add_knowledge_entry, infer_industry, sanitize_text
from app.repositories import create_audit_log, get_or_create_customer, get_or_create_project, get_project_detail, row_to_dict
from app.scope_policy import ScopeContext, scope_where


PROJECT_STATUSES = [
    "受付",
    "ヒアリング",
    "提案中",
    "レビュー中",
    "提出済み",
    "商談中",
    "受注",
    "失注",
    "制作中",
    "納品",
    "完了",
]

LOST_REASON_LABELS = {
    "price": "価格",
    "competitor": "競合",
    "deadline": "納期",
    "proposal": "提案内容",
    "other": "その他",
    "": "",
}


def _safe(value: str, max_length: int = 800) -> str:
    return sanitize_text(value or "", max_length)


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace(" ", "T"))
    except ValueError:
        return None


def _insert_event(
    db: Connection,
    project_id: int,
    user_id: int | None,
    event_type: str,
    from_status: str = "",
    to_status: str = "",
    note: str = "",
) -> None:
    context = db.execute("SELECT organization_id, workspace_id FROM projects WHERE id = ?", (project_id,)).fetchone()
    organization_id = int(context["organization_id"] if context else 1)
    workspace_id = int(context["workspace_id"] if context else 1)
    db.execute(
        """
        INSERT INTO project_lifecycle_events (project_id, user_id, event_type, from_status, to_status, note, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (project_id, user_id, event_type[:80], from_status[:80], to_status[:80], _safe(note, 500), organization_id, workspace_id),
    )


def create_project_record(
    db: Connection,
    *,
    user_id: int | None,
    customer_name: str,
    project_name: str,
    summary: str = "",
    win_probability: int = 0,
    next_action: str = "",
) -> dict[str, Any]:
    customer_id = get_or_create_customer(db, _safe(customer_name, 160), user_id=user_id)
    project_id = get_or_create_project(
        db,
        customer_id,
        _safe(project_name, 160) or "新規提案案件",
        _safe(summary, 800),
        max(0, min(int(win_probability or 0), 100)),
        _safe(next_action, 500),
        user_id=user_id,
    )
    project = get_project_detail(db, project_id)
    if project and project.get("status") in {"", "draft"}:
        db.execute("UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", ("受付", project_id))
    _insert_event(db, project_id, user_id, "project_received", "", "受付", "案件を受付しました。")
    create_audit_log(db, user_id, "save", "project", str(project_id), "success", "project_created")
    return get_project_lifecycle(db, project_id) or {}


def list_lifecycle_events(db: Connection, project_id: int) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT e.*, COALESCE(u.email, '') AS user_email
        FROM project_lifecycle_events e
        LEFT JOIN users u ON u.id = e.user_id
        WHERE e.project_id = ?
        ORDER BY e.created_at ASC, e.id ASC
        """,
        (project_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_project_lifecycle(db: Connection, project_id: int) -> dict[str, Any] | None:
    project = get_project_detail(db, project_id)
    if not project:
        return None
    outcome = row_to_dict(db.execute("SELECT * FROM project_outcomes WHERE project_id = ?", (project_id,)).fetchone())
    handoff = row_to_dict(db.execute("SELECT * FROM project_handoffs WHERE project_id = ?", (project_id,)).fetchone())
    retrospective = row_to_dict(db.execute("SELECT * FROM project_retrospectives WHERE project_id = ?", (project_id,)).fetchone())
    return {
        "project": project,
        "statuses": PROJECT_STATUSES,
        "timeline": list_lifecycle_events(db, project_id),
        "outcome": outcome,
        "handoff": handoff,
        "retrospective": retrospective,
    }


def update_project_status(db: Connection, *, project_id: int, user_id: int | None, status: str, note: str = "") -> dict[str, Any] | None:
    if status not in PROJECT_STATUSES:
        raise ValueError("Invalid project status.")
    project = get_project_detail(db, project_id)
    if not project:
        return None
    previous_status = str(project.get("status") or "")
    db.execute("UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, project_id))
    _insert_event(db, project_id, user_id, "status_changed", previous_status, status, note or f"{status}へ変更しました。")
    create_audit_log(db, user_id, "project_status_change", "project", str(project_id), "success", f"{previous_status}->{status}")
    return get_project_lifecycle(db, project_id)


def register_project_outcome(
    db: Connection,
    *,
    project_id: int,
    user_id: int | None,
    outcome: str,
    lost_reason: str = "",
    note: str = "",
) -> dict[str, Any] | None:
    if outcome not in {"won", "lost"}:
        raise ValueError("Invalid project outcome.")
    if outcome == "won":
        lost_reason = ""
        next_status = "受注"
        event_type = "project_won"
    else:
        if lost_reason not in LOST_REASON_LABELS:
            lost_reason = "other"
        next_status = "失注"
        event_type = "project_lost"

    project = get_project_detail(db, project_id)
    if not project:
        return None

    existing = db.execute("SELECT id FROM project_outcomes WHERE project_id = ?", (project_id,)).fetchone()
    if existing:
        db.execute(
            """
            UPDATE project_outcomes
            SET outcome = ?, lost_reason = ?, note = ?, created_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE project_id = ?
            """,
            (outcome, lost_reason, _safe(note, 600), user_id, project_id),
        )
    else:
        db.execute(
            """
            INSERT INTO project_outcomes (project_id, outcome, lost_reason, note, created_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (project_id, outcome, lost_reason, _safe(note, 600), user_id),
        )

    previous_status = str(project.get("status") or "")
    db.execute("UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (next_status, project_id))
    _insert_event(db, project_id, user_id, event_type, previous_status, next_status, note or next_status)
    create_audit_log(db, user_id, event_type, "project", str(project_id), "success", f"lost_reason={lost_reason}")
    return get_project_lifecycle(db, project_id)


def build_production_handoff(
    db: Connection,
    *,
    project_id: int,
    user_id: int | None,
    payload: dict[str, str],
) -> dict[str, Any] | None:
    project = get_project_detail(db, project_id)
    if not project:
        return None
    project_summary = _safe(str(project.get("summary") or "案件概要はCRMの案件詳細を確認してください。"), 700)
    proposal_summary = _safe(payload.get("proposal_summary") or project_summary, 700)
    handoff_text = "\n".join(
        [
            "## 制作チーム向け引継ぎ",
            f"- 案件名: {_safe(str(project.get('name') or ''), 160)}",
            f"- 顧客名: {_safe(str(project.get('customer_name') or '未設定'), 160)}",
            f"- 案件概要: {project_summary}",
            f"- 提案内容: {proposal_summary}",
            f"- 注意事項: {_safe(payload.get('cautions') or '見積条件、納期、AI推測項目を制作開始前に再確認してください。', 600)}",
            f"- 納期: {_safe(payload.get('deadline') or '要確認', 120)}",
            f"- 担当: {_safe(payload.get('owner') or '要確認', 120)}",
            f"- 特殊機能: {_safe(payload.get('special_functions') or '要確認', 400)}",
            f"- 導入要件: {_safe(payload.get('cms') or payload.get('requirement') or '要確認', 120)}",
        ]
    )
    existing = db.execute("SELECT id FROM project_handoffs WHERE project_id = ?", (project_id,)).fetchone()
    if existing:
        db.execute(
            """
            UPDATE project_handoffs
            SET handoff_text = ?, created_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE project_id = ?
            """,
            (handoff_text[:3000], user_id, project_id),
        )
    else:
        db.execute(
            """
            INSERT INTO project_handoffs (project_id, handoff_text, created_by)
            VALUES (?, ?, ?)
            """,
            (project_id, handoff_text[:3000], user_id),
        )
    _insert_event(db, project_id, user_id, "handoff_created", "", str(project.get("status") or ""), "制作引継ぎを作成しました。")
    create_audit_log(db, user_id, "handoff_created", "project", str(project_id), "success", "handoff_text_saved_summary_only")
    return get_project_lifecycle(db, project_id)


def complete_project_with_retrospective(
    db: Connection,
    *,
    project_id: int,
    user_id: int | None,
    payload: dict[str, str],
) -> dict[str, Any] | None:
    project = get_project_detail(db, project_id)
    if not project:
        return None

    success_factors = _safe(payload.get("success_factors") or "課題、提案、見積、納期を早期に整理できたこと。", 700)
    improvements = _safe(payload.get("improvements") or "次回はヒアリング不足項目をより早く確認すること。", 700)
    next_learnings = _safe(payload.get("next_learnings") or "類似案件では提案前確認と制作引継ぎを早めに実施する。", 700)
    project_summary = _safe(str(project.get("summary") or project.get("next_action") or project.get("name") or ""), 500)
    industry = infer_industry(project_summary)
    knowledge = add_knowledge_entry(
        db,
        {
            "industry": industry,
            "company_size": "",
            "project_summary": project_summary or "完了案件の要約",
            "adopted_proposal": _safe(str(project.get("next_action") or "提案方針はCRM履歴を参照"), 700),
            "proposal_story": success_factors,
            "adoption_reason": success_factors,
            "lost_reason": "",
            "result": next_learnings,
            "owner_memo": improvements,
            "outcome": "success",
            "rating": 4,
            "evaluation_status": "effective",
            "tags": "project_lifecycle,retrospective",
            "approval_status": "draft",
            "source_type": "proposal_generated",
            "source_note": "Project completion retrospective candidate.",
        },
        user_id,
    )
    knowledge_id = int(knowledge.get("id") or 0) or None

    existing = db.execute("SELECT id FROM project_retrospectives WHERE project_id = ?", (project_id,)).fetchone()
    if existing:
        db.execute(
            """
            UPDATE project_retrospectives
            SET success_factors = ?, improvements = ?, next_learnings = ?, knowledge_candidate_id = ?, created_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE project_id = ?
            """,
            (success_factors, improvements, next_learnings, knowledge_id, user_id, project_id),
        )
    else:
        db.execute(
            """
            INSERT INTO project_retrospectives
            (project_id, success_factors, improvements, next_learnings, knowledge_candidate_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, success_factors, improvements, next_learnings, knowledge_id, user_id),
        )

    previous_status = str(project.get("status") or "")
    db.execute("UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", ("完了", project_id))
    _insert_event(db, project_id, user_id, "project_completed", previous_status, "完了", "振り返りを作成し、Knowledge候補に追加しました。")
    create_audit_log(db, user_id, "project_completed", "project", str(project_id), "success", f"knowledge_candidate_id={knowledge_id or ''}")
    return get_project_lifecycle(db, project_id)


def build_project_lifecycle_analytics(db: Connection, scope: ScopeContext | None = None) -> dict[str, Any]:
    project_where, project_params = scope_where(scope, "p") if scope else ("1 = 1", ())
    outcome_where, outcome_params = scope_where(scope, "o") if scope else ("1 = 1", ())
    review_where, review_params = scope_where(scope, "r") if scope else ("1 = 1", ())
    total_projects = int(db.execute(f"SELECT COUNT(*) AS count FROM projects p WHERE {project_where}", project_params).fetchone()["count"] or 0)
    won_count = int(db.execute(f"SELECT COUNT(*) AS count FROM project_outcomes o WHERE outcome = 'won' AND {outcome_where}", outcome_params).fetchone()["count"] or 0)
    lost_count = int(db.execute(f"SELECT COUNT(*) AS count FROM project_outcomes o WHERE outcome = 'lost' AND {outcome_where}", outcome_params).fetchone()["count"] or 0)
    completed_count = int(db.execute(f"SELECT COUNT(*) AS count FROM projects p WHERE status = '完了' AND {project_where}", project_params).fetchone()["count"] or 0)
    decided_count = won_count + lost_count

    lost_rows = db.execute(
        f"""
        SELECT lost_reason, COUNT(*) AS count
        FROM project_outcomes o
        WHERE outcome = 'lost' AND {outcome_where}
        GROUP BY lost_reason
        ORDER BY count DESC
        """,
        outcome_params,
    ).fetchall()
    lost_reasons = [
        {
            "reason": row["lost_reason"] or "other",
            "label": LOST_REASON_LABELS.get(row["lost_reason"] or "other", row["lost_reason"] or "その他"),
            "count": int(row["count"] or 0),
        }
        for row in lost_rows
    ]

    review_count = int(db.execute(f"SELECT COUNT(*) AS count FROM proposal_reviews r WHERE {review_where}", review_params).fetchone()["count"] or 0)
    revision_count = int(
        db.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM proposal_review_revisions rv
            INNER JOIN proposal_reviews r ON r.id = rv.review_id
            WHERE {review_where}
            """,
            review_params,
        ).fetchone()["count"]
        or 0
    )

    durations: list[float] = []
    project_rows = db.execute(f"SELECT p.id, p.created_at, p.updated_at FROM projects p WHERE {project_where}", project_params).fetchall()
    for project in project_rows:
        start_event = db.execute(
            "SELECT created_at FROM project_lifecycle_events WHERE project_id = ? ORDER BY created_at ASC, id ASC LIMIT 1",
            (project["id"],),
        ).fetchone()
        end_event = db.execute(
            """
            SELECT created_at
            FROM project_lifecycle_events
            WHERE project_id = ? AND to_status IN ('提出済み', '受注', '失注', '完了')
            ORDER BY created_at ASC, id ASC
            LIMIT 1
            """,
            (project["id"],),
        ).fetchone()
        start = _parse_time(start_event["created_at"] if start_event else project["created_at"])
        end = _parse_time(end_event["created_at"] if end_event else project["updated_at"])
        if start and end:
            durations.append(max((end - start).total_seconds() / 86400, 0))

    average_proposal_days = round(sum(durations) / len(durations), 1) if durations else 0
    return {
        "total_projects": total_projects,
        "won_count": won_count,
        "lost_count": lost_count,
        "win_rate": round((won_count / decided_count) * 100, 1) if decided_count else 0,
        "average_proposal_days": average_proposal_days,
        "review_count": review_count,
        "revision_count": revision_count,
        "lost_reasons": lost_reasons,
        "completed_count": completed_count,
        "completion_rate": round((completed_count / total_projects) * 100, 1) if total_projects else 0,
    }
