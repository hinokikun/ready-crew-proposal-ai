import importlib.util
import os
import re
import uuid
from sqlite3 import Connection, Row
from datetime import date
from typing import Any

from app.config import settings
from app.role_permissions import add_role_display_fields, normalize_role_for_storage
from app.security import hash_password, verify_password

from app.repository_parts.users import row_to_dict, get_user_context_ids, record_pilot_event
from app.repository_parts.shared import _scope_filter, _scope_label

def get_or_create_customer(
    db: Connection,
    company_name: str,
    industry: str = "",
    contact_person: str = "",
    *,
    user_id: int | None = None,
    organization_id: int | None = None,
    workspace_id: int | None = None,
) -> int | None:
    name = company_name.strip()
    if not name:
        return None
    context_org_id, context_workspace_id = (organization_id, workspace_id) if organization_id and workspace_id else get_user_context_ids(db, user_id)
    existing = db.execute(
        "SELECT id FROM customers WHERE company_name = ? AND organization_id = ? AND workspace_id = ?",
        (name, context_org_id, context_workspace_id),
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE customers SET industry = COALESCE(NULLIF(?, ''), industry), contact_person = COALESCE(NULLIF(?, ''), contact_person), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (industry.strip(), contact_person.strip(), existing["id"]),
        )
        return int(existing["id"])
    cursor = db.execute(
        "INSERT INTO customers (company_name, industry, contact_person, organization_id, workspace_id) VALUES (?, ?, ?, ?, ?)",
        (name, industry.strip(), contact_person.strip(), context_org_id, context_workspace_id),
    )
    return int(cursor.lastrowid)


def get_or_create_project(
    db: Connection,
    customer_id: int | None,
    name: str,
    summary: str = "",
    win_probability: int = 0,
    next_action: str = "",
    *,
    user_id: int | None = None,
    organization_id: int | None = None,
    workspace_id: int | None = None,
) -> int:
    project_name = name.strip() or "提案準備案件"
    if organization_id and workspace_id:
        context_org_id, context_workspace_id = organization_id, workspace_id
    elif user_id:
        context_org_id, context_workspace_id = get_user_context_ids(db, user_id)
    elif customer_id:
        customer_context = db.execute(
            "SELECT organization_id, workspace_id FROM customers WHERE id = ?",
            (customer_id,),
        ).fetchone()
        context_org_id = int(customer_context["organization_id"] if customer_context else 1)
        context_workspace_id = int(customer_context["workspace_id"] if customer_context else 1)
    else:
        context_org_id, context_workspace_id = 1, 1
    existing = db.execute(
        "SELECT id FROM projects WHERE name = ? AND (customer_id IS ? OR customer_id = ?) AND organization_id = ? AND workspace_id = ?",
        (project_name, customer_id, customer_id, context_org_id, context_workspace_id),
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE projects SET summary = ?, win_probability = ?, next_action = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (summary[:500], win_probability, next_action[:300], existing["id"]),
        )
        return int(existing["id"])
    cursor = db.execute(
        "INSERT INTO projects (customer_id, name, summary, win_probability, next_action, organization_id, workspace_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (customer_id, project_name, summary[:500], win_probability, next_action[:300], context_org_id, context_workspace_id),
    )
    return int(cursor.lastrowid)


def create_history_log(
    db: Connection,
    user_id: int | None,
    customer_id: int | None,
    project_id: int | None,
    feature_name: str,
    input_length: int,
    output_type: str,
    status: str,
    error_type: str = "",
) -> None:
    from app.repository_parts.operations import create_audit_log

    organization_id, workspace_id = get_user_context_ids(db, user_id)
    db.execute(
        """
        INSERT INTO proposal_histories
        (user_id, customer_id, project_id, feature_name, input_length, output_type, status, error_type, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, customer_id, project_id, feature_name, input_length, output_type, status, error_type, organization_id, workspace_id),
    )
    db.execute(
        """
        INSERT INTO usage_logs (user_id, feature_name, input_length, output_type, status, error_type, organization_id, workspace_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, feature_name, input_length, output_type, status, error_type, organization_id, workspace_id),
    )
    if output_type in {"markdown", "markdown+pptx-data"}:
        record_pilot_event(db, user_id, "proposal_generation", status, metadata=f"output_type={output_type};error_type={error_type}")
    elif output_type in {"pptx", "summary-pptx", "estimate-pdf"}:
        record_pilot_event(db, user_id, "download", status, metadata=f"output_type={output_type};error_type={error_type}")
    if feature_name in {"提案書生成", "PowerPoint", "要約PowerPoint", "見積書PDF"}:
        create_audit_log(db, user_id, "generate", feature_name, "", status, f"output_type={output_type};error_type={error_type}")


def list_creation_history(
    db: Connection,
    user: dict[str, Any],
    limit: int = 100,
    query: str = "",
    status: str = "",
    date_from: str = "",
    date_to: str = "",
) -> list[dict[str, Any]]:
    organization_id, workspace_id = get_user_context_ids(db, int(user.get("id") or 0))
    role = str(user.get("role") or "")
    clauses = ["h.organization_id = ?", "h.workspace_id = ?"]
    params: list[Any] = [organization_id, workspace_id]
    if role not in {"admin", "manager"}:
        clauses.append("h.user_id = ?")
        params.append(int(user.get("id") or 0))
    if status:
        clauses.append("h.status = ?")
        params.append(status[:40])
    if date_from:
        clauses.append("h.created_at >= ?")
        params.append(date_from[:30])
    if date_to:
        clauses.append("h.created_at <= ?")
        params.append(date_to[:30])
    if query:
        like_query = f"%{query[:120]}%"
        clauses.append(
            "(COALESCE(p.name, '') LIKE ? OR COALESCE(c.company_name, '') LIKE ? OR COALESCE(u.email, '') LIKE ?)"
        )
        params.extend([like_query, like_query, like_query])
    rows = db.execute(
        f"""
        SELECT
            h.id,
            h.user_id,
            COALESCE(u.email, '') AS created_by_email,
            COALESCE(u.display_name, '') AS created_by_name,
            h.customer_id,
            COALESCE(c.company_name, '') AS customer_name,
            h.project_id,
            COALESCE(p.name, '') AS project_name,
            h.feature_name,
            h.output_type,
            h.status,
            h.error_type,
            h.organization_id,
            h.workspace_id,
            COALESCE(o.name, '') AS organization_name,
            COALESCE(w.name, '') AS workspace_name,
            h.created_at,
            h.created_at AS updated_at,
            h.output_type AS output_formats,
            (
                SELECT editor_url
                FROM beautiful_ai_presentations b
                WHERE b.organization_id = h.organization_id
                  AND b.workspace_id = h.workspace_id
                  AND COALESCE(b.project_id, '') = COALESCE(CAST(h.project_id AS TEXT), '')
                ORDER BY b.created_at DESC
                LIMIT 1
            ) AS beautiful_ai_url
        FROM proposal_histories h
        LEFT JOIN users u ON u.id = h.user_id
        LEFT JOIN customers c ON c.id = h.customer_id
        LEFT JOIN projects p ON p.id = h.project_id
        LEFT JOIN organizations o ON o.id = h.organization_id
        LEFT JOIN workspaces w ON w.id = h.workspace_id
        WHERE {" AND ".join(clauses)}
        ORDER BY h.created_at DESC, h.id DESC
        LIMIT ?
        """,
        (*params, max(1, min(int(limit), 200))),
    ).fetchall()
    return [dict(row) for row in rows]


def list_crm(
    db: Connection,
    user_id: int | None = None,
    organization_id: int | None = None,
    workspace_id: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    context_org_id, context_workspace_id = (organization_id, workspace_id) if organization_id and workspace_id else get_user_context_ids(db, user_id)
    if user_id is None:
        customers = [
            dict(row)
            for row in db.execute(
                "SELECT * FROM customers WHERE organization_id = ? AND workspace_id = ? ORDER BY updated_at DESC LIMIT 100",
                (context_org_id, context_workspace_id),
            ).fetchall()
        ]
        project_rows = db.execute(
                """
                SELECT p.*, c.company_name AS customer_name
                FROM projects p
                LEFT JOIN customers c ON c.id = p.customer_id
                WHERE p.organization_id = ? AND p.workspace_id = ?
                ORDER BY p.updated_at DESC
                LIMIT 100
                """
                ,
                (context_org_id, context_workspace_id),
            ).fetchall()
    else:
        customers = [
            dict(row)
            for row in db.execute(
                """
                SELECT DISTINCT c.*
                FROM customers c
                INNER JOIN projects p ON p.customer_id = c.id
                INNER JOIN project_lifecycle_events e ON e.project_id = p.id
                WHERE e.user_id = ? AND p.organization_id = ? AND p.workspace_id = ?
                ORDER BY c.updated_at DESC
                LIMIT 100
                """,
                (user_id, context_org_id, context_workspace_id),
            ).fetchall()
        ]
        project_rows = db.execute(
                """
                SELECT p.*, c.company_name AS customer_name
                FROM projects p
                LEFT JOIN customers c ON c.id = p.customer_id
                WHERE EXISTS (
                    SELECT 1 FROM project_lifecycle_events e
                    WHERE e.project_id = p.id AND e.user_id = ?
                )
                AND p.organization_id = ? AND p.workspace_id = ?
                ORDER BY p.updated_at DESC
                LIMIT 100
                """,
                (user_id, context_org_id, context_workspace_id),
            ).fetchall()
    projects: list[dict[str, Any]] = []
    for row in project_rows:
        project = dict(row)
        review = db.execute("SELECT status FROM proposal_reviews WHERE project_id = ? ORDER BY updated_at DESC, id DESC LIMIT 1", (str(project["id"]),)).fetchone()
        outcome = db.execute("SELECT outcome, lost_reason FROM project_outcomes WHERE project_id = ? LIMIT 1", (project["id"],)).fetchone()
        project["review_status"] = review["status"] if review else ""
        project["outcome"] = outcome["outcome"] if outcome else ""
        project["lost_reason"] = outcome["lost_reason"] if outcome else ""
        projects.append(project)
    return {"customers": customers, "projects": projects}


def get_project_detail(db: Connection, project_id: int) -> dict[str, Any] | None:
    project = row_to_dict(
        db.execute(
            """
            SELECT p.*, c.company_name AS customer_name
            FROM projects p
            LEFT JOIN customers c ON c.id = p.customer_id
            WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()
    )
    if not project:
        return None
    project["proposal_histories"] = [
        dict(row) for row in db.execute("SELECT * FROM proposal_histories WHERE project_id = ? ORDER BY created_at DESC LIMIT 50", (project_id,)).fetchall()
    ]
    project["meeting_memos"] = [
        dict(row) for row in db.execute("SELECT * FROM meeting_memos WHERE project_id = ? ORDER BY created_at DESC LIMIT 50", (project_id,)).fetchall()
    ]
    project["workspace_conversations"] = [
        dict(row)
        for row in db.execute(
            "SELECT * FROM workspace_conversations WHERE project_id = ? ORDER BY created_at ASC, id ASC LIMIT 100",
            (str(project_id),),
        ).fetchall()
    ]
    project["workspace_work_logs"] = [
        dict(row)
        for row in db.execute(
            "SELECT * FROM workspace_work_logs WHERE project_id = ? ORDER BY created_at ASC, id ASC LIMIT 100",
            (str(project_id),),
        ).fetchall()
    ]
    project["proposal_reviews"] = [
        dict(row)
        for row in db.execute(
            "SELECT * FROM proposal_reviews WHERE project_id = ? ORDER BY updated_at DESC, id DESC LIMIT 20",
            (str(project_id),),
        ).fetchall()
    ]
    return project
