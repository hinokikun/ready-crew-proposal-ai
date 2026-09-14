from fastapi.testclient import TestClient
from contextlib import contextmanager
import logging
import sys
import types
from pathlib import Path

import pytest

from app.database import health as database_health
from app.database import connection as database_connection


@contextmanager
def _failing_db(error: BaseException):
    raise error
    yield


def test_check_db_logs_only_bounded_safe_fields_without_exception_text(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    class SecretConnectionError(Exception):
        sqlstate = "28P01"

        def __str__(self) -> str:
            return "postgresql://secret-user:secret-pass@secret-host:5432/secret-db"

    monkeypatch.setattr(database_health, "get_db", lambda: _failing_db(SecretConnectionError("secret")))
    caplog.set_level(logging.WARNING, logger=database_health.logger.name)

    assert database_health.check_db() is False

    message = next(record.getMessage() for record in caplog.records if record.getMessage().startswith("database_connectivity_failed"))
    assert "db_dialect=" + database_health.ENGINE_DIALECT in message
    assert "exception_class=SecretConnectionError" in message
    assert "failure_category=authentication" in message
    assert "sqlstate=28P01" in message
    assert "secret-user" not in caplog.text
    assert "secret-pass" not in caplog.text
    assert "secret-host" not in caplog.text
    assert "secret-db" not in caplog.text
    assert "postgresql://" not in caplog.text
    assert "secret" not in caplog.text


def test_migration_head_uses_authoritative_backend_alembic_config(monkeypatch: pytest.MonkeyPatch) -> None:
    config_path = database_health._authoritative_alembic_config_path()

    assert config_path == Path(database_health.__file__).resolve().parents[2] / "alembic.ini"
    assert config_path.exists()
    assert config_path != Path(database_health.__file__).resolve().parents[1] / "alembic.ini"

    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "sqlite")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(allow_startup_schema_migration=False),
    )
    monkeypatch.setattr(database_health, "check_db", lambda: True)
    monkeypatch.setattr(database_health, "get_schema_readiness", lambda: {
        "schema_ready": False,
        "schema_missing": [],
        "quality_gate_unique_scoped": False,
        "quality_gate_legacy_project_unique": False,
    })
    monkeypatch.setattr(database_health, "_table_exists", lambda *_: False)

    @contextmanager
    def empty_db():
        yield object()

    monkeypatch.setattr(database_health, "get_db", empty_db)

    assert database_health.get_migration_state()["migration_head"] == "20260903_8000"


def test_migration_head_resolution_fails_safely_for_missing_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        database_health,
        "_authoritative_alembic_config_path",
        lambda: Path(database_health.__file__).with_name("missing-alembic.ini"),
    )
    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "sqlite")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(allow_startup_schema_migration=False),
    )
    monkeypatch.setattr(database_health, "check_db", lambda: True)
    monkeypatch.setattr(database_health, "get_schema_readiness", lambda: {
        "schema_ready": False,
        "schema_missing": [],
        "quality_gate_unique_scoped": False,
        "quality_gate_legacy_project_unique": False,
    })
    monkeypatch.setattr(database_health, "_table_exists", lambda *_: False)

    @contextmanager
    def empty_db():
        yield object()

    monkeypatch.setattr(database_health, "get_db", empty_db)

    result = database_health.get_migration_state()

    assert result["migration_head"] == ""
    assert result["migration_current"] == ""


def test_check_db_without_sqlstate_logs_fixed_category_and_returns_false(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    class UnclassifiedConnectionError(Exception):
        pass

    monkeypatch.setattr(database_health, "get_db", lambda: _failing_db(UnclassifiedConnectionError()))
    caplog.set_level(logging.WARNING, logger=database_health.logger.name)

    assert database_health.check_db() is False

    message = next(record.getMessage() for record in caplog.records if record.getMessage().startswith("database_connectivity_failed"))
    assert "exception_class=UnclassifiedConnectionError" in message
    assert "failure_category=unknown" in message
    assert " sqlstate=" not in message


def test_check_db_success_remains_true(monkeypatch: pytest.MonkeyPatch) -> None:
    @contextmanager
    def successful_db():
        class Cursor:
            def execute(self, query: str) -> None:
                assert query == "SELECT 1"

        yield Cursor()

    monkeypatch.setattr(database_health, "get_db", successful_db)
    assert database_health.check_db() is True


def test_database_diagnostic_is_secret_free_and_reports_allowed_url_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "postgresql")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(database_url="postgresql://secret-user:secret-pass@secret-host:5432/secret-db?sslmode=require&connect_timeout=5&private=secret"),
    )
    fake_pq = types.SimpleNamespace(__impl__="binary", version=lambda: 180005)
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(pq=fake_pq))

    diagnostic = database_health.get_database_diagnostic()

    assert diagnostic["psycopg_implementation"] == "binary"
    assert diagnostic["libpq_version"] == 180005
    assert diagnostic["database_url_scheme"] == "postgresql"
    assert diagnostic["database_url_host_present"] is True
    assert diagnostic["database_url_port_present"] is True
    assert diagnostic["database_url_username_present"] is True
    assert diagnostic["database_url_password_present"] is True
    assert diagnostic["sslmode_present"] is True
    assert diagnostic["connect_timeout_present"] is True
    assert diagnostic["sslrootcert_present"] is False
    assert diagnostic["target_session_attrs_present"] is False
    serialized = repr(diagnostic)
    for secret in ("secret-user", "secret-pass", "secret-host", "secret-db", "postgresql://"):
        assert secret not in serialized


def test_database_diagnostic_handles_unknown_implementation_and_version_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "postgresql")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(database_url="postgresql+psycopg://user@host/db"),
    )
    fake_pq = types.SimpleNamespace(
        __impl__="unexpected",
        version=lambda: (_ for _ in ()).throw(AssertionError("secret")),
    )
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(pq=fake_pq))

    diagnostic = database_health.get_database_diagnostic()

    assert diagnostic["psycopg_implementation"] == "unknown"
    assert diagnostic["libpq_version"] == "unknown"
    assert diagnostic["database_url_scheme"] == "postgresql_psycopg"


class _AdapterDescription:
    def __init__(self, name: str) -> None:
        self.name = name


class _AdapterCursor:
    def __init__(self, rows: list[object], description: object = None) -> None:
        self.rows = list(rows)
        self.description = description
        self.rowcount = 1
        self.executed: tuple[str, tuple[object, ...]] | None = None

    def execute(self, sql: str, params: tuple[object, ...]) -> None:
        self.executed = (sql, params)

    def fetchone(self) -> object:
        return self.rows.pop(0) if self.rows else None

    def fetchall(self) -> list[object]:
        rows = list(self.rows)
        self.rows.clear()
        return rows


class _AdapterConnection:
    def __init__(self, cursor: _AdapterCursor) -> None:
        self.cursor_value = cursor

    def cursor(self) -> _AdapterCursor:
        return self.cursor_value


def test_postgres_engine_connect_args_no_longer_set_global_dict_row(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_connection, "ENGINE_DIALECT", "postgresql")

    assert database_connection._connect_args() == {}


def test_postgres_cursor_adapter_converts_tuple_fetchone_to_dict_like_row() -> None:
    cursor = _AdapterCursor(
        [("abc", 123)],
        [_AdapterDescription("id"), _AdapterDescription("value")],
    )

    row = database_connection._CursorAdapter(cursor).fetchone()

    assert row["id"] == "abc"
    assert row.get("value") == 123
    assert dict(row) == {"id": "abc", "value": 123}


def test_postgres_cursor_adapter_fetchall_preserves_order_and_empty_result() -> None:
    cursor = _AdapterCursor(
        [("a", 1), ("b", 2)],
        [("id",), ("value",)],
    )
    adapter = database_connection._CursorAdapter(cursor)

    assert adapter.fetchall() == [{"id": "a", "value": 1}, {"id": "b", "value": 2}]
    assert adapter.fetchall() == []


def test_postgres_cursor_adapter_preserves_mapping_none_and_descriptionless_rows() -> None:
    mapping = {"id": "existing"}
    mapping_cursor = _AdapterCursor([mapping], [_AdapterDescription("id")])
    none_cursor = _AdapterCursor([None], [_AdapterDescription("id")])
    raw_cursor = _AdapterCursor([("abc",)], None)

    assert database_connection._CursorAdapter(mapping_cursor).fetchone() is mapping
    assert database_connection._CursorAdapter(none_cursor).fetchone() is None
    assert database_connection._CursorAdapter(raw_cursor).fetchone() == ("abc",)


@pytest.mark.parametrize("raw", ["abc", b"abc", bytearray(b"abc")])
def test_postgres_cursor_adapter_does_not_convert_scalar_text_or_bytes_rows(raw: object) -> None:
    description = [
        _AdapterDescription("one"),
        _AdapterDescription("two"),
        _AdapterDescription("three"),
    ]

    result = database_connection._application_row(raw, description)

    assert result is raw


def test_postgres_cursor_adapter_still_converts_valid_tuple_rows() -> None:
    description = [_AdapterDescription("id"), _AdapterDescription("value")]

    result = database_connection._application_row(("abc", 123), description)

    assert result == {"id": "abc", "value": 123}


def test_postgres_cursor_adapter_preserves_returning_id_extraction() -> None:
    cursor = _AdapterCursor(
        [(42,)],
        [_AdapterDescription("id")],
    )
    adapter = database_connection._PostgresConnectionAdapter(_AdapterConnection(cursor))

    result = adapter.execute("INSERT INTO example (name) VALUES (?)", ("sample",))

    assert result.lastrowid == 42
    assert cursor.executed is not None
    assert "RETURNING id" in cursor.executed[0]


@pytest.mark.parametrize(
    ("url", "expected_scheme"),
    [
        ("postgresql+psycopg://user@host/db", "postgresql_psycopg"),
        ("postgresql://user@host/db", "postgresql"),
        ("postgres://user@host/db", "postgres"),
        ("sqlite:///app.db", "other"),
        ("not a url", "unknown"),
    ],
)
def test_database_url_scheme_classification(url: str, expected_scheme: str) -> None:
    assert database_health._database_url_scheme(url) == expected_scheme


def test_high_level_stage_diagnostic_disabled_is_read_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        database_connection,
        "settings",
        types.SimpleNamespace(enable_db_high_level_stage_diagnostic=False),
    )
    database_connection._high_level_stage_state.update({
        "do_connect_reached": False,
        "first_connect_reached": False,
        "application_connect_reached": False,
        "last_stage": "none",
    })

    database_connection._observe_dbapi_connect(None, None, [], {})
    database_connection._observe_first_connect(object(), object())
    database_connection._observe_connect_event(object(), object())

    assert database_connection.get_high_level_stage_diagnostic() == {
        "enabled": False,
        "do_connect_reached": False,
        "first_connect_reached": False,
        "application_connect_reached": False,
        "last_stage": "none",
    }


def test_high_level_stage_diagnostic_is_monotonic_and_observers_do_not_replace_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        database_connection,
        "settings",
        types.SimpleNamespace(enable_db_high_level_stage_diagnostic=True),
    )
    database_connection._high_level_stage_state.update({
        "do_connect_reached": False,
        "first_connect_reached": False,
        "application_connect_reached": False,
        "last_stage": "none",
    })

    assert database_connection._observe_dbapi_connect(None, None, [], {}) is None
    database_connection._observe_first_connect(object(), object())
    database_connection._observe_connect_event(object(), object())
    database_connection._observe_dbapi_connect(None, None, [], {})

    assert database_connection.get_high_level_stage_diagnostic() == {
        "enabled": True,
        "do_connect_reached": True,
        "first_connect_reached": True,
        "application_connect_reached": True,
        "last_stage": "application_connect",
    }


def test_formal_first_connect_observer_has_no_connection_side_effect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        database_connection,
        "settings",
        types.SimpleNamespace(enable_db_high_level_stage_diagnostic=True),
    )
    database_connection._high_level_stage_state.update({
        "do_connect_reached": False,
        "first_connect_reached": False,
        "application_connect_reached": False,
        "last_stage": "none",
    })
    marker = object()

    assert database_connection._observe_first_connect(marker, marker) is None
    assert database_connection.get_high_level_stage_diagnostic()["first_connect_reached"] is True


def _reset_safe_exception_location_state() -> None:
    database_health._safe_exception_location_state.clear()
    database_health._safe_exception_location_state.update({
        "captured": False,
        "exception_class": "unknown",
        "module_id": "unknown",
        "function_id": "unknown",
        "line_number": None,
        "failure_category": "unclassified",
    })


def test_safe_exception_location_disabled_does_not_scan_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_safe_exception_location_state()
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_safe_exception_location_diagnostic=False),
    )
    database_health._capture_safe_exception_location(AssertionError("secret-url"))
    assert database_health.get_safe_exception_location_diagnostic() == {
        "enabled": False,
        "captured": False,
        "exception_class": "unknown",
        "module_id": "unknown",
        "function_id": "unknown",
        "line_number": None,
        "failure_category": "unclassified",
    }


def test_safe_exception_location_maps_known_sqlalchemy_frames(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_safe_exception_location_state()
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_safe_exception_location_diagnostic=True),
    )
    namespace: dict[str, object] = {}
    exec(compile(
        "def _get_server_version_info():\n    raise AssertionError('postgresql://secret-user:secret-pass@secret-host/secret-db')\n",
        "C:/venv/Lib/site-packages/sqlalchemy/dialects/postgresql/base.py",
        "exec",
    ), namespace)
    try:
        namespace["_get_server_version_info"]()  # type: ignore[operator]
    except AssertionError as exc:
        database_health._capture_safe_exception_location(exc)
    diagnostic = database_health.get_safe_exception_location_diagnostic()
    assert diagnostic["captured"] is True
    assert diagnostic["exception_class"] == "AssertionError"
    assert diagnostic["module_id"] == "postgresql_base"
    assert diagnostic["function_id"] == "get_server_version_info"
    assert diagnostic["failure_category"] == "server_version_parse"
    assert isinstance(diagnostic["line_number"], int)
    assert "secret" not in repr(diagnostic)


def test_safe_exception_location_unknown_frame_and_args_are_not_exposed(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_safe_exception_location_state()
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_safe_exception_location_diagnostic=True),
    )
    error = ValueError("postgresql://secret-user:secret-pass@secret-host/secret-db")
    error.args = ("secret-user", "secret-pass", "secret-host", "secret-db")
    database_health._capture_safe_exception_location(error)
    diagnostic = database_health.get_safe_exception_location_diagnostic()
    assert diagnostic["module_id"] == "unknown"
    assert diagnostic["function_id"] == "unknown"
    assert diagnostic["line_number"] is None
    assert diagnostic["failure_category"] == "unclassified"
    assert "secret" not in repr(diagnostic)


def test_safe_exception_location_selects_innermost_allowed_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_safe_exception_location_state()
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_safe_exception_location_diagnostic=True),
    )
    outer: dict[str, object] = {}
    inner: dict[str, object] = {}
    exec(compile(
        "def first_connect():\n    raise AssertionError('secret')\n",
        "C:/venv/Lib/site-packages/sqlalchemy/engine/create.py",
        "exec",
    ), outer)
    exec(compile(
        "def _get_server_version_info():\n    first_connect()\n",
        "C:/venv/Lib/site-packages/sqlalchemy/dialects/postgresql/base.py",
        "exec",
    ), inner)
    inner["first_connect"] = outer["first_connect"]
    try:
        inner["_get_server_version_info"]()  # type: ignore[operator]
    except AssertionError as exc:
        database_health._capture_safe_exception_location(exc)
    diagnostic = database_health.get_safe_exception_location_diagnostic()
    assert diagnostic["module_id"] == "engine_create"
    assert diagnostic["function_id"] == "engine_first_connect"
    assert diagnostic["failure_category"] == "engine_first_connect"


def test_check_db_captures_safe_location_without_changing_failure_result(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_safe_exception_location_state()
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_safe_exception_location_diagnostic=True),
    )
    monkeypatch.setattr(database_health, "get_db", lambda: _failing_db(AssertionError("postgresql://secret")))
    assert database_health.check_db() is False
    diagnostic = database_health.get_safe_exception_location_diagnostic()
    assert diagnostic["captured"] is True
    assert diagnostic["exception_class"] == "AssertionError"
    assert "secret" not in repr(diagnostic)


class _StageCursor:
    def __init__(self, error: BaseException | None = None) -> None:
        self.error = error

    def execute(self, query: str, params: tuple[object, ...]) -> None:
        if self.error is not None:
            raise self.error


class _StageConnection:
    def __init__(self, cursor_error: BaseException | None = None, execute_error: BaseException | None = None) -> None:
        self.cursor_error = cursor_error
        self.cursor_value = _StageCursor(execute_error)

    def cursor(self) -> _StageCursor:
        if self.cursor_error is not None:
            raise self.cursor_error
        return self.cursor_value


class _StageRawConnection:
    def __init__(
        self,
        connection: object,
        close_error: BaseException | None = None,
        commit_error: BaseException | None = None,
    ) -> None:
        self.connection = connection
        self.close_error = close_error
        self.commit_error = commit_error
        self.close_called = False

    @property
    def driver_connection(self) -> object:
        return self.connection

    def commit(self) -> None:
        if self.commit_error is not None:
            raise self.commit_error
        return None

    def close(self) -> None:
        self.close_called = True
        if self.close_error is not None:
            raise self.close_error


class _StageEngine:
    def __init__(self, raw_connection: object) -> None:
        self.raw_connection_value = raw_connection

    def raw_connection(self) -> object:
        if isinstance(self.raw_connection_value, BaseException):
            raise self.raw_connection_value
        return self.raw_connection_value


def test_get_db_marks_engine_connect_and_driver_connection_without_changing_exception_type(monkeypatch: pytest.MonkeyPatch) -> None:
    engine_error = AssertionError("postgresql://secret-user:secret-pass@secret-host/secret-db")
    monkeypatch.setattr(database_connection, "engine", _StageEngine(engine_error))
    with pytest.raises(AssertionError) as raised:
        with database_connection.get_db():
            pass
    assert getattr(raised.value, "_db_connect_stage") == "engine_connect"

    class DriverFailureRaw(_StageRawConnection):
        @property
        def driver_connection(self) -> object:
            raise AssertionError("secret driver detail")

    driver_error_raw = DriverFailureRaw(object())
    monkeypatch.setattr(database_connection, "engine", _StageEngine(driver_error_raw))
    with pytest.raises(AssertionError) as raised:
        with database_connection.get_db():
            pass
    assert getattr(raised.value, "_db_connect_stage") == "driver_connection"


@pytest.mark.parametrize("observed_stage", ["engine_connect", "dbapi_connect_start"])
def test_get_db_uses_observed_stage_only_for_raw_connection_failure(
    monkeypatch: pytest.MonkeyPatch,
    observed_stage: str,
) -> None:
    class ObservedFailureEngine:
        def raw_connection(self) -> object:
            if observed_stage != "engine_connect":
                database_connection._set_connect_observation_stage(observed_stage)
            raise AssertionError("secret")

    token = database_connection._connect_observation_stage.set("outer_context")
    try:
        monkeypatch.setattr(database_connection, "engine", ObservedFailureEngine())
        with pytest.raises(AssertionError) as raised:
            with database_connection.get_db():
                pass
        assert getattr(raised.value, "_db_connect_stage") == observed_stage
    finally:
        database_connection._connect_observation_stage.reset(token)


@pytest.mark.parametrize(
    ("connection", "expected_stage"),
    [
        (_StageConnection(cursor_error=AssertionError("secret cursor")), "cursor"),
        (_StageConnection(execute_error=AssertionError("secret execute")), "execute"),
    ],
)
def test_get_db_marks_cursor_and_execute_stages(monkeypatch: pytest.MonkeyPatch, connection: _StageConnection, expected_stage: str) -> None:
    monkeypatch.setattr(database_connection, "ENGINE_DIALECT", "postgresql")
    monkeypatch.setattr(database_connection, "engine", _StageEngine(_StageRawConnection(connection)))
    with pytest.raises(AssertionError) as raised:
        with database_connection.get_db() as db:
            db.execute("SELECT 1")
    assert getattr(raised.value, "_db_connect_stage") == expected_stage


def test_get_db_marks_close_stage_without_replacing_exception_type(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_connection, "ENGINE_DIALECT", "postgresql")
    raw = _StageRawConnection(_StageConnection(), close_error=AssertionError("secret close"))
    monkeypatch.setattr(database_connection, "engine", _StageEngine(raw))
    with pytest.raises(AssertionError) as raised:
        with database_connection.get_db() as db:
            db.execute("SELECT 1")
    assert getattr(raised.value, "_db_connect_stage") == "close"


def test_get_db_marks_commit_stage_and_closes_after_commit_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_connection, "ENGINE_DIALECT", "postgresql")
    raw = _StageRawConnection(
        _StageConnection(),
        commit_error=AssertionError("secret commit detail"),
    )
    monkeypatch.setattr(database_connection, "engine", _StageEngine(raw))

    token = database_connection._connect_observation_stage.set("engine_connect")
    try:
        with pytest.raises(AssertionError) as raised:
            with database_connection.get_db() as db:
                db.execute("SELECT 1")
    finally:
        database_connection._connect_observation_stage.reset(token)

    assert getattr(raised.value, "_db_connect_stage") == "commit"
    assert raw.close_called is True


def test_do_connect_observer_marks_start_without_calling_or_changing_dbapi_args() -> None:
    cargs = ["safe-arg"]
    cparams = {"safe_key": "safe-value"}
    original_args = list(cargs)
    original_params = dict(cparams)
    token = database_connection._connect_observation_stage.set("engine_connect")
    try:
        assert database_connection._observe_dbapi_connect(object(), None, cargs, cparams) is None
        assert database_connection._connect_observation_stage.get() == "dbapi_connect_start"
        assert cargs == original_args
        assert cparams == original_params
    finally:
        database_connection._connect_observation_stage.reset(token)


def test_connect_and_checkout_events_mark_post_dbapi_boundaries() -> None:
    connection = object()
    token = database_connection._connect_observation_stage.set("engine_connect")
    try:
        database_connection._observe_connect_event(connection, None)
        assert database_connection._connect_observation_stage.get() == "connect_event"

        database_connection._observe_checkout_event(connection, None, None)
        assert database_connection._connect_observation_stage.get() == "checkout_event"
    finally:
        database_connection._connect_observation_stage.reset(token)


def test_get_db_resets_connect_observation_context_after_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    outer_stage = "outer_context"
    token = database_connection._connect_observation_stage.set(outer_stage)
    try:
        monkeypatch.setattr(database_connection, "engine", _StageEngine(AssertionError("secret")))
        with pytest.raises(AssertionError):
            with database_connection.get_db():
                pass
        assert database_connection._connect_observation_stage.get() == outer_stage
    finally:
        database_connection._connect_observation_stage.reset(token)


def test_health_endpoint_reports_runtime_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_version"]
    assert body["environment"]
    assert "git" in body
    assert "commit" in body["git"]
    assert body["routes"]["beautiful_ai_status"] == "/api/beautiful-ai/status"
    assert body["routes"]["beautiful_ai_status_registered"] is True
    assert body["beautiful_ai"]["route_registered"] is True
    assert body["auth_configured"] is True
    assert body["mock_ai"] is True
    assert body["ai_api"] == "mock"
    assert body["pptx"] == "available"
    assert body["pdf"] == "available"
    assert body["db"] == "connected"
    assert body["db_connected"] is True
    assert body["db_type"] == "sqlite"
    assert body["db_tables_count"] >= 10
    assert isinstance(body["database_diagnostic"], dict)
    assert "postgresql://" not in str(body["database_diagnostic"])
    assert "DATABASE_URL" not in body["database_diagnostic"]
    assert body["timestamp"]
    assert "DATABASE_URL" not in body
    assert "OPENAI_API_KEY" not in body


def test_openapi_includes_beautiful_ai_status(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    body = response.json()
    assert "/api/beautiful-ai/status" in body["paths"]
    assert "get" in body["paths"]["/api/beautiful-ai/status"]


def test_health_live_endpoint_reports_process_status(client: TestClient) -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_version"]
    assert body["environment"]
    assert body["timestamp"]


def test_health_ready_endpoint_reports_dependency_status(client: TestClient) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db_connected"] is True
    assert body["auth_configured"] is True
    assert isinstance(body["database_diagnostic"], dict)
    assert "postgresql://" not in str(body["database_diagnostic"])
    assert "DATABASE_URL" not in body["database_diagnostic"]
