from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.config import settings


def _normalise_database_url(database_url: str) -> str:
    url = (database_url or "sqlite:///app.db").strip() or "sqlite:///app.db"
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _database_path() -> str:
    if settings.database_url.startswith("sqlite:///"):
        return settings.database_url.replace("sqlite:///", "", 1)
    return "app.db"


def _engine_url() -> str:
    url = _normalise_database_url(settings.database_url)
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        if path != ":memory:":
            parent = Path(path).parent
            if parent != Path("."):
                parent.mkdir(parents=True, exist_ok=True)
    return url


ENGINE_URL = _engine_url()
ENGINE_DIALECT = make_url(ENGINE_URL).get_backend_name()


def _connect_args() -> dict[str, Any]:
    if ENGINE_DIALECT == "sqlite":
        return {"check_same_thread": False}
    if ENGINE_DIALECT == "postgresql":
        try:
            from psycopg.rows import dict_row

            return {"row_factory": dict_row}
        except Exception:
            return {}
    return {}


engine = create_engine(
    ENGINE_URL,
    connect_args=_connect_args(),
    pool_pre_ping=True,
)


class _CursorAdapter:
    def __init__(self, cursor: Any, lastrowid: int | None = None):
        self._cursor = cursor
        self.lastrowid = lastrowid

    def fetchone(self) -> Any:
        return self._cursor.fetchone()

    def fetchall(self) -> list[Any]:
        return self._cursor.fetchall()


class _PostgresConnectionAdapter:
    """Small compatibility layer for the existing SQLite-style repositories.

    The current repositories use `?` placeholders and `cursor.lastrowid`.
    This adapter keeps that surface stable while the project moves toward
    a proper SQLAlchemy/Alembic repository implementation.
    """

    def __init__(self, connection: Any):
        self._connection = connection

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> _CursorAdapter:
        cursor = self._connection.cursor()
        statement = _postgres_sql(sql)
        values = tuple(params or ())
        is_insert_with_id = statement.lstrip().upper().startswith("INSERT INTO") and " RETURNING " not in statement.upper()
        if is_insert_with_id:
            statement = statement.rstrip().rstrip(";") + " RETURNING id"
        cursor.execute(statement, values)
        lastrowid = None
        if is_insert_with_id:
            try:
                row = cursor.fetchone()
                if isinstance(row, dict):
                    lastrowid = int(row.get("id") or 0)
                elif row:
                    lastrowid = int(row[0])
            except Exception:
                lastrowid = None
        return _CursorAdapter(cursor, lastrowid)

    def executescript(self, script: str) -> None:
        for statement in _split_sql_script(script):
            self.execute(statement)


def _postgres_sql(sql: str) -> str:
    statement = sql.replace("?", "%s")
    statement = re.sub(
        r"CAST\(\(JULIANDAY\(CURRENT_TIMESTAMP\)\s*-\s*JULIANDAY\(started_at\)\)\s*\*\s*86400\s+AS\s+INTEGER\)",
        "CAST(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at::timestamp)) AS INTEGER)",
        statement,
        flags=re.IGNORECASE,
    )
    statement = re.sub(r"DATE\(created_at\)\s*=\s*DATE\('now'\)", "DATE(created_at::timestamp) = CURRENT_DATE", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DATETIME\('now',\s*'-7 days'\)", "CURRENT_TIMESTAMP - INTERVAL '7 days'", statement, flags=re.IGNORECASE)
    statement = re.sub(r"DATETIME\('now'\)", "CURRENT_TIMESTAMP", statement, flags=re.IGNORECASE)
    return statement


def _split_sql_script(script: str) -> list[str]:
    return [part.strip() for part in script.split(";") if part.strip()]


@contextmanager
def get_db():
    raw_connection = engine.raw_connection()
    connection = raw_connection.driver_connection if hasattr(raw_connection, "driver_connection") else raw_connection
    if ENGINE_DIALECT == "sqlite":
        connection.row_factory = sqlite3.Row
        db = connection
    elif ENGINE_DIALECT == "postgresql":
        db = _PostgresConnectionAdapter(connection)
    else:
        db = connection
    try:
        yield db
        raw_connection.commit()
    finally:
        raw_connection.close()


def get_db_type() -> str:
    if ENGINE_DIALECT == "sqlite":
        return "sqlite"
    if ENGINE_DIALECT == "postgresql":
        return "postgresql"
    return ENGINE_DIALECT or "unknown"


def _id_column() -> str:
    return "SERIAL PRIMARY KEY" if ENGINE_DIALECT == "postgresql" else "INTEGER PRIMARY KEY AUTOINCREMENT"
