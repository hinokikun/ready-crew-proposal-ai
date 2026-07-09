from sqlite3 import Connection, Row
from typing import Any

from app.config import settings
from app.security import hash_password, verify_password


def row_to_dict(row: Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def ensure_initial_admin(db: Connection) -> None:
    if not settings.initial_admin_email or not settings.initial_admin_password:
        return
    existing = db.execute("SELECT id FROM users WHERE email = ?", (settings.initial_admin_email,)).fetchone()
    if existing:
        return
    db.execute(
        "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, 'admin', 1)",
        (settings.initial_admin_email, hash_password(settings.initial_admin_password)),
    )


def authenticate_user(db: Connection, email: str, password: str) -> dict[str, Any] | None:
    user = db.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email.strip().lower(),)).fetchone()
    if not user or not verify_password(password, user["password_hash"]):
        return None
    return row_to_dict(user)


def get_user_by_id(db: Connection, user_id: int) -> dict[str, Any] | None:
    return row_to_dict(db.execute("SELECT id, email, role, is_active, created_at, updated_at FROM users WHERE id = ?", (user_id,)).fetchone())


def list_users(db: Connection) -> list[dict[str, Any]]:
    rows = db.execute("SELECT id, email, role, is_active, created_at, updated_at FROM users ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def create_user(db: Connection, email: str, password: str, role: str) -> dict[str, Any]:
    db.execute(
        "INSERT INTO users (email, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
        (email.strip().lower(), hash_password(password), role),
    )
    user = db.execute("SELECT id, email, role, is_active, created_at, updated_at FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return dict(user)


def set_user_active(db: Connection, user_id: int, is_active: bool) -> dict[str, Any] | None:
    db.execute("UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (1 if is_active else 0, user_id))
    return get_user_by_id(db, user_id)


def get_or_create_customer(db: Connection, company_name: str, industry: str = "", contact_person: str = "") -> int | None:
    name = company_name.strip()
    if not name:
        return None
    existing = db.execute("SELECT id FROM customers WHERE company_name = ?", (name,)).fetchone()
    if existing:
        db.execute(
            "UPDATE customers SET industry = COALESCE(NULLIF(?, ''), industry), contact_person = COALESCE(NULLIF(?, ''), contact_person), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (industry.strip(), contact_person.strip(), existing["id"]),
        )
        return int(existing["id"])
    cursor = db.execute(
        "INSERT INTO customers (company_name, industry, contact_person) VALUES (?, ?, ?)",
        (name, industry.strip(), contact_person.strip()),
    )
    return int(cursor.lastrowid)


def get_or_create_project(db: Connection, customer_id: int | None, name: str, summary: str = "", win_probability: int = 0, next_action: str = "") -> int:
    project_name = name.strip() or "提案準備案件"
    existing = db.execute(
        "SELECT id FROM projects WHERE name = ? AND (customer_id IS ? OR customer_id = ?)",
        (project_name, customer_id, customer_id),
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE projects SET summary = ?, win_probability = ?, next_action = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (summary[:500], win_probability, next_action[:300], existing["id"]),
        )
        return int(existing["id"])
    cursor = db.execute(
        "INSERT INTO projects (customer_id, name, summary, win_probability, next_action) VALUES (?, ?, ?, ?, ?)",
        (customer_id, project_name, summary[:500], win_probability, next_action[:300]),
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
    db.execute(
        """
        INSERT INTO proposal_histories
        (user_id, customer_id, project_id, feature_name, input_length, output_type, status, error_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, customer_id, project_id, feature_name, input_length, output_type, status, error_type),
    )
    db.execute(
        """
        INSERT INTO usage_logs (user_id, feature_name, input_length, output_type, status, error_type)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, feature_name, input_length, output_type, status, error_type),
    )
    if feature_name in {"提案書生成", "PowerPoint", "要約PowerPoint", "見積書PDF"}:
        create_audit_log(db, user_id, "generate", feature_name, "", status, f"output_type={output_type};error_type={error_type}")


def list_crm(db: Connection) -> dict[str, list[dict[str, Any]]]:
    customers = [dict(row) for row in db.execute("SELECT * FROM customers ORDER BY updated_at DESC LIMIT 100").fetchall()]
    projects = [
        dict(row)
        for row in db.execute(
            """
            SELECT p.*, c.company_name AS customer_name
            FROM projects p
            LEFT JOIN customers c ON c.id = p.customer_id
            ORDER BY p.updated_at DESC
            LIMIT 100
            """
        ).fetchall()
    ]
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
    return project


def list_usage_logs(db: Connection, limit: int = 50) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in db.execute(
            """
            SELECT l.*, u.email AS user_email
            FROM usage_logs l
            LEFT JOIN users u ON u.id = l.user_id
            ORDER BY l.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    ]


def create_audit_log(
    db: Connection,
    user_id: int | None,
    event_type: str,
    target_type: str = "",
    target_id: str = "",
    status: str = "success",
    metadata: str = "",
) -> None:
    db.execute(
        """
        INSERT INTO audit_logs (user_id, event_type, target_type, target_id, status, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, event_type, target_type, target_id, status, metadata[:300]),
    )


def list_audit_logs(db: Connection, limit: int = 100) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in db.execute(
            """
            SELECT a.*, u.email AS user_email
            FROM audit_logs a
            LEFT JOIN users u ON u.id = a.user_id
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    ]
