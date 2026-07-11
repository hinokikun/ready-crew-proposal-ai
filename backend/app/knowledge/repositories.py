from __future__ import annotations

from sqlite3 import Connection
from typing import Any


def _row_to_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row is not None else {}


def create_knowledge_entry(db: Connection, data: dict[str, Any], user_id: int | None) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO proposal_knowledge (
            industry,
            company_size,
            project_summary,
            adopted_proposal,
            proposal_story,
            adoption_reason,
            lost_reason,
            result,
            owner_memo,
            outcome,
            rating,
            evaluation_status,
            tags,
            approval_status,
            quality_score,
            confidential_risk,
            confidential_flags,
            source_type,
            source_note,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["industry"],
            data["company_size"],
            data["project_summary"],
            data["adopted_proposal"],
            data["proposal_story"],
            data["adoption_reason"],
            data["lost_reason"],
            data["result"],
            data["owner_memo"],
            data["outcome"],
            data["rating"],
            data["evaluation_status"],
            data["tags"],
            data["approval_status"],
            data["quality_score"],
            data["confidential_risk"],
            data["confidential_flags"],
            data["source_type"],
            data["source_note"],
            user_id,
        ),
    )
    return get_knowledge_entry(db, int(cursor.lastrowid))


def get_knowledge_entry(db: Connection, entry_id: int) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT
            k.*,
            COALESCE(u.email, '') AS created_by_email
        FROM proposal_knowledge k
        LEFT JOIN users u ON u.id = k.created_by
        WHERE k.id = ?
        """,
        (entry_id,),
    ).fetchone()
    return _row_to_dict(row)


def list_knowledge_entries(db: Connection, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT
            k.*,
            COALESCE(u.email, '') AS created_by_email
        FROM proposal_knowledge k
        LEFT JOIN users u ON u.id = k.created_by
        ORDER BY k.rating DESC, k.updated_at DESC, k.id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def update_knowledge_evaluation(db: Connection, entry_id: int, rating: int, evaluation_status: str) -> dict[str, Any]:
    db.execute(
        """
        UPDATE proposal_knowledge
        SET rating = ?, evaluation_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (rating, evaluation_status, entry_id),
    )
    return get_knowledge_entry(db, entry_id)


def update_knowledge_status(db: Connection, entry_id: int, approval_status: str) -> dict[str, Any]:
    db.execute(
        """
        UPDATE proposal_knowledge
        SET approval_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (approval_status, entry_id),
    )
    return get_knowledge_entry(db, entry_id)


def update_knowledge_quality(
    db: Connection,
    entry_id: int,
    quality_score: int,
    confidential_risk: str,
    confidential_flags: str,
) -> dict[str, Any]:
    db.execute(
        """
        UPDATE proposal_knowledge
        SET quality_score = ?,
            confidential_risk = ?,
            confidential_flags = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (quality_score, confidential_risk, confidential_flags, entry_id),
    )
    return get_knowledge_entry(db, entry_id)


def list_search_candidates(db: Connection, limit: int = 100, approved_only: bool = True) -> list[dict[str, Any]]:
    where_sql = "WHERE approval_status = 'approved'" if approved_only else ""
    rows = db.execute(
        f"""
        SELECT *
        FROM proposal_knowledge
        {where_sql}
        ORDER BY quality_score DESC, rating DESC, updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def create_template(db: Connection, data: dict[str, Any], user_id: int | None) -> dict[str, Any]:
    cursor = db.execute(
        """
        INSERT INTO proposal_templates (
            category,
            title,
            template_summary,
            structure,
            recommended_for,
            is_active,
            created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["category"],
            data["title"],
            data["template_summary"],
            data["structure"],
            data["recommended_for"],
            1 if data["is_active"] else 0,
            user_id,
        ),
    )
    return get_template(db, int(cursor.lastrowid))


def get_template(db: Connection, template_id: int) -> dict[str, Any]:
    row = db.execute(
        """
        SELECT
            t.*,
            COALESCE(u.email, '') AS created_by_email
        FROM proposal_templates t
        LEFT JOIN users u ON u.id = t.created_by
        WHERE t.id = ?
        """,
        (template_id,),
    ).fetchone()
    return _row_to_dict(row)


def list_templates(db: Connection, category: str = "", include_inactive: bool = False, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    conditions = []
    params: list[Any] = []
    if category:
        conditions.append("category = ?")
        params.append(category)
    if not include_inactive:
        conditions.append("t.is_active = 1")
    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = db.execute(
        f"""
        SELECT
            t.*,
            COALESCE(u.email, '') AS created_by_email
        FROM proposal_templates t
        LEFT JOIN users u ON u.id = t.created_by
        {where_sql}
        ORDER BY t.updated_at DESC, t.id DESC
        LIMIT ? OFFSET ?
        """,
        (*params, limit, offset),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def update_template_active(db: Connection, template_id: int, is_active: bool) -> dict[str, Any]:
    db.execute(
        """
        UPDATE proposal_templates
        SET is_active = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (1 if is_active else 0, template_id),
    )
    return get_template(db, template_id)
