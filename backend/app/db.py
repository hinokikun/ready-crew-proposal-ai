import sqlite3
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine

from app.config import settings


def _database_path() -> str:
    if settings.database_url.startswith("sqlite:///"):
        return settings.database_url.replace("sqlite:///", "", 1)
    return "app.db"


def _engine_url() -> str:
    if settings.database_url.startswith("sqlite:///"):
        path = _database_path()
        if path != ":memory:":
            parent = Path(path).parent
            if parent != Path("."):
                parent.mkdir(parents=True, exist_ok=True)
        return settings.database_url
    return settings.database_url


ENGINE_URL = _engine_url()

engine = create_engine(
    ENGINE_URL,
    connect_args={"check_same_thread": False} if ENGINE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)


@contextmanager
def get_db():
    raw_connection = engine.raw_connection()
    connection = raw_connection.driver_connection if hasattr(raw_connection, "driver_connection") else raw_connection
    if ENGINE_URL.startswith("sqlite"):
        connection.row_factory = sqlite3.Row
    try:
        yield connection
        raw_connection.commit()
    finally:
        raw_connection.close()


def init_db() -> None:
    with get_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'member', 'viewer')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                industry TEXT NOT NULL DEFAULT '',
                contact_person TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                win_probability INTEGER NOT NULL DEFAULT 0,
                summary TEXT NOT NULL DEFAULT '',
                next_action TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(customer_id) REFERENCES customers(id)
            );

            CREATE TABLE IF NOT EXISTS proposal_histories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                customer_id INTEGER,
                project_id INTEGER,
                feature_name TEXT NOT NULL,
                input_length INTEGER NOT NULL DEFAULT 0,
                output_type TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'success',
                error_type TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(customer_id) REFERENCES customers(id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS meeting_memos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                project_id INTEGER,
                summary TEXT NOT NULL DEFAULT '',
                next_action TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(project_id) REFERENCES projects(id)
            );

            CREATE TABLE IF NOT EXISTS usage_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feature_name TEXT NOT NULL,
                input_length INTEGER NOT NULL DEFAULT 0,
                output_type TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'success',
                error_type TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                target_type TEXT NOT NULL DEFAULT '',
                target_id TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'success',
                metadata TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS feedback_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_role TEXT NOT NULL DEFAULT '',
                rating TEXT NOT NULL CHECK(rating IN ('usable', 'needs_revision', 'hard_to_use')),
                comment TEXT NOT NULL DEFAULT '',
                feature_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            );
            """
        )


def check_db() -> bool:
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        return True
    except Exception:
        return False
