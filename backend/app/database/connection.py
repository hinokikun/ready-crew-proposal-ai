from __future__ import annotations

import re
import sqlite3
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from threading import Lock
from typing import Any, Iterable

from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.config import settings


DB_CONNECT_STAGES = frozenset({
    "dbapi_connect_start",
    "connect_event",
    "checkout_event",
    "engine_connect",
    "driver_connection",
    "adapter",
    "cursor",
    "execute",
    "commit",
    "close",
})

_connect_observation_stage: ContextVar[str] = ContextVar(
    "db_connect_observation_stage",
    default="engine_connect",
)

_HIGH_LEVEL_STAGE_ORDER = {
    "none": 0,
    "do_connect": 1,
    "first_connect": 2,
    "application_connect": 3,
}
_high_level_stage_lock = Lock()
_high_level_stage_state: dict[str, Any] = {
    "do_connect_reached": False,
    "first_connect_reached": False,
    "application_connect_reached": False,
    "last_stage": "none",
}


def _high_level_diagnostic_enabled() -> bool:
    return bool(getattr(settings, "enable_db_high_level_stage_diagnostic", False))


def _mark_high_level_stage(stage: str) -> None:
    if not _high_level_diagnostic_enabled() or stage not in _HIGH_LEVEL_STAGE_ORDER:
        return
    with _high_level_stage_lock:
        if stage == "do_connect":
            _high_level_stage_state["do_connect_reached"] = True
        elif stage == "first_connect":
            _high_level_stage_state["first_connect_reached"] = True
        elif stage == "application_connect":
            _high_level_stage_state["application_connect_reached"] = True
        if _HIGH_LEVEL_STAGE_ORDER[stage] > _HIGH_LEVEL_STAGE_ORDER[_high_level_stage_state["last_stage"]]:
            _high_level_stage_state["last_stage"] = stage


def get_high_level_stage_diagnostic() -> dict[str, Any]:
    enabled = _high_level_diagnostic_enabled()
    if not enabled:
        return {
            "enabled": False,
            "do_connect_reached": False,
            "first_connect_reached": False,
            "application_connect_reached": False,
            "last_stage": "none",
        }
    with _high_level_stage_lock:
        return {"enabled": True, **_high_level_stage_state}


def _set_connect_observation_stage(stage: str) -> None:
    if stage in DB_CONNECT_STAGES:
        _connect_observation_stage.set(stage)


def _observed_connect_stage(default: str) -> str:
    stage = _connect_observation_stage.get()
    return stage if stage in DB_CONNECT_STAGES else default


def _mark_connect_stage(error: BaseException, stage: str) -> None:
    if stage not in DB_CONNECT_STAGES:
        return
    try:
        existing = getattr(error, "_db_connect_stage", None)
        if existing in DB_CONNECT_STAGES:
            return
        setattr(error, "_db_connect_stage", stage)
    except Exception:
        return


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
    return {}


engine = create_engine(
    ENGINE_URL,
    connect_args=_connect_args(),
    pool_pre_ping=True,
)


def _observe_dbapi_connect(dialect: Any, connection_record: Any, cargs: Any, cparams: Any) -> None:
    _mark_high_level_stage("do_connect")
    _set_connect_observation_stage("dbapi_connect_start")
    return None


def _observe_first_connect(dbapi_connection: Any, connection_record: Any) -> None:
    """Formal PoolEvents.first_connect: creator returned a DBAPI connection."""
    _mark_high_level_stage("first_connect")


def _observe_connect_event(dbapi_connection: Any, connection_record: Any) -> None:
    _mark_high_level_stage("application_connect")
    _set_connect_observation_stage("connect_event")


def _observe_checkout_event(
    dbapi_connection: Any,
    connection_record: Any,
    connection_proxy: Any,
) -> None:
    _set_connect_observation_stage("checkout_event")


if ENGINE_DIALECT == "postgresql":
    event.listen(engine, "do_connect", _observe_dbapi_connect)
    event.listen(engine.pool, "first_connect", _observe_first_connect)
    event.listen(engine, "connect", _observe_connect_event)
    event.listen(engine, "checkout", _observe_checkout_event)


class _CursorAdapter:
    def __init__(self, cursor: Any, lastrowid: int | None = None):
        self._cursor = cursor
        self.lastrowid = lastrowid

    def fetchone(self) -> Any:
        return _application_row(self._cursor.fetchone(), getattr(self._cursor, "description", None))

    def fetchall(self) -> list[Any]:
        rows = self._cursor.fetchall()
        return [_application_row(row, getattr(self._cursor, "description", None)) for row in rows]


def _description_column_names(description: Any) -> list[str] | None:
    if not description:
        return None
    names: list[str] = []
    for item in description:
        name = getattr(item, "name", None)
        if name is None:
            try:
                name = item[0]
            except (IndexError, KeyError, TypeError):
                return None
        if not isinstance(name, str):
            return None
        names.append(name)
    return names or None


def _application_row(row: Any, description: Any) -> Any:
    if row is None or isinstance(row, Mapping):
        return row
    if isinstance(row, (str, bytes, bytearray)):
        return row
    names = _description_column_names(description)
    if names is None:
        return row
    try:
        if len(row) != len(names):
            return row
        return dict(zip(names, row))
    except (TypeError, ValueError):
        return row


class _PostgresConnectionAdapter:
    """Small compatibility layer for the existing SQLite-style repositories.

    The current repositories use `?` placeholders and `cursor.lastrowid`.
    This adapter keeps that surface stable while the project moves toward
    a proper SQLAlchemy/Alembic repository implementation.
    """

    def __init__(self, connection: Any):
        self._connection = connection

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> _CursorAdapter:
        try:
            cursor = self._connection.cursor()
        except BaseException as exc:
            _mark_connect_stage(exc, "cursor")
            raise
        statement = _postgres_sql(sql)
        values = tuple(params or ())
        is_insert_with_id = statement.lstrip().upper().startswith("INSERT INTO") and " RETURNING " not in statement.upper()
        if is_insert_with_id:
            statement = statement.rstrip().rstrip(";") + " RETURNING id"
        try:
            cursor.execute(statement, values)
        except BaseException as exc:
            _mark_connect_stage(exc, "execute")
            raise
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
    raw_connection = None
    stage = "engine_connect"
    observation_token = _connect_observation_stage.set(stage)
    try:
        raw_connection = engine.raw_connection()
        stage = "driver_connection"
        connection = raw_connection.driver_connection if hasattr(raw_connection, "driver_connection") else raw_connection
        if ENGINE_DIALECT == "sqlite":
            connection.row_factory = sqlite3.Row
            db = connection
        elif ENGINE_DIALECT == "postgresql":
            stage = "adapter"
            db = _PostgresConnectionAdapter(connection)
        else:
            db = connection
        stage = "execute"
        yield db
        stage = "commit"
        raw_connection.commit()
    except BaseException as exc:
        failure_stage = (
            _observed_connect_stage(stage)
            if stage == "engine_connect"
            else stage
        )
        _mark_connect_stage(exc, failure_stage)
        raise
    finally:
        try:
            if raw_connection is not None:
                try:
                    raw_connection.close()
                except BaseException as exc:
                    _mark_connect_stage(exc, "close")
                    raise
        finally:
            _connect_observation_stage.reset(observation_token)


def get_db_type() -> str:
    if ENGINE_DIALECT == "sqlite":
        return "sqlite"
    if ENGINE_DIALECT == "postgresql":
        return "postgresql"
    return ENGINE_DIALECT or "unknown"


def _id_column() -> str:
    return "SERIAL PRIMARY KEY" if ENGINE_DIALECT == "postgresql" else "INTEGER PRIMARY KEY AUTOINCREMENT"
