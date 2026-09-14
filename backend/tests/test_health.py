from fastapi.testclient import TestClient
import asyncio
from contextlib import contextmanager
import logging
import sys
import types
import enum
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


class _SchemaStateDb:
    def __init__(self, *, revision: str | None = None, existing: set[str] | None = None) -> None:
        self.queries: list[str] = []
        self.revision = revision
        self.existing = existing or set()

    def execute(self, statement: str):
        self.queries.append(statement)
        assert statement.lstrip().upper().startswith("SELECT")
        if "COUNT(*) AS public_table_count" in statement:
            return types.SimpleNamespace(fetchone=lambda: {"public_table_count": len(self.existing)})
        if "version_num" in statement:
            return types.SimpleNamespace(fetchone=lambda: {"version_num": self.revision} if self.revision else None)
        return types.SimpleNamespace(
            fetchone=lambda: {
                "alembic_version_table_exists": "alembic_version" in self.existing,
                "organizations_exists": "organizations" in self.existing,
                "workspaces_exists": "workspaces" in self.existing,
                "users_exists": "users" in self.existing,
                "organization_memberships_exists": "organization_memberships" in self.existing,
            }
        )


def test_schema_state_diagnostic_disabled_does_not_query(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_schema_state_diagnostic_cache", None)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_schema_state_diagnostic=False),
    )
    monkeypatch.setattr(database_health, "_run_schema_state_diagnostic", lambda: pytest.fail("diagnostic ran"))

    result = database_health.run_schema_state_diagnostic_once()

    assert result["enabled"] is False
    assert result["executed"] is False
    assert result["failure_category"] == "none"


def test_schema_state_diagnostic_reads_only_fixed_catalog_and_caches_result(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _SchemaStateDb(
        revision="20260711_1701",
        existing={"alembic_version", "organizations", "workspaces", "users", "organization_memberships"},
    )

    @contextmanager
    def db_context():
        yield db

    monkeypatch.setattr(database_health, "_schema_state_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "postgresql")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_schema_state_diagnostic=True),
    )
    monkeypatch.setattr(database_health, "get_db", db_context)

    first = database_health.run_schema_state_diagnostic_once()
    second = database_health.run_schema_state_diagnostic_once()

    assert first == second
    assert first["enabled"] is True
    assert first["executed"] is True
    assert first["public_table_count"] == 5
    assert first["alembic_version_table_exists"] is True
    assert first["alembic_current_revision"] == "20260711_1701"
    assert first["organizations_exists"] is True
    assert first["workspaces_exists"] is True
    assert first["users_exists"] is True
    assert first["organization_memberships_exists"] is True
    assert len(db.queries) == 3
    assert all(query.lstrip().upper().startswith("SELECT") for query in db.queries)


def test_schema_state_diagnostic_empty_schema_has_no_revision_or_secret_data(monkeypatch: pytest.MonkeyPatch) -> None:
    db = _SchemaStateDb()

    @contextmanager
    def db_context():
        yield db

    monkeypatch.setattr(database_health, "_schema_state_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "postgresql")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_schema_state_diagnostic=True),
    )
    monkeypatch.setattr(database_health, "get_db", db_context)

    result = database_health.run_schema_state_diagnostic_once()

    assert result["public_table_count"] == 0
    assert result["alembic_version_table_exists"] is False
    assert result["alembic_current_revision"] == ""
    assert not any(value in repr(result) for value in ("DATABASE_URL", "secret-host", "secret-user", "secret-db"))


def test_schema_state_diagnostic_failure_is_bounded_and_secret_free(monkeypatch: pytest.MonkeyPatch) -> None:
    class SecretDatabaseError(Exception):
        sqlstate = "08001"

        def __str__(self) -> str:
            return "postgresql://secret-user:secret-pass@secret-host:5432/secret-db"

    @contextmanager
    def db_context():
        raise SecretDatabaseError("secret")
        yield

    monkeypatch.setattr(database_health, "_schema_state_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "postgresql")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_schema_state_diagnostic=True),
    )
    monkeypatch.setattr(database_health, "get_db", db_context)

    result = database_health.run_schema_state_diagnostic_once()
    serialized = repr(result)

    assert result["executed"] is True
    assert result["failure_category"] == "database_unavailable"
    for secret in ("postgresql://", "secret-user", "secret-pass", "secret-host", "secret-db"):
        assert secret not in serialized


def test_schema_state_diagnostic_getter_returns_cached_result_without_query(monkeypatch: pytest.MonkeyPatch) -> None:
    cached = database_health._schema_state_result(True)
    cached["executed"] = True
    cached["users_exists"] = True
    monkeypatch.setattr(database_health, "_schema_state_diagnostic_cache", cached)
    monkeypatch.setattr(database_health, "_run_schema_state_diagnostic", lambda: pytest.fail("getter re-ran diagnostic"))

    assert database_health.get_schema_state_diagnostic() == cached


def test_database_diagnostic_exposes_schema_state_cache_without_rerunning(monkeypatch: pytest.MonkeyPatch) -> None:
    cached = database_health._schema_state_result(True)
    cached["executed"] = True
    cached["public_table_count"] = 5
    monkeypatch.setattr(database_health, "_schema_state_diagnostic_cache", cached)
    monkeypatch.setattr(database_health, "_run_schema_state_diagnostic", lambda: pytest.fail("health getter re-ran diagnostic"))

    assert database_health.get_database_diagnostic()["schema_state"] == cached


def test_startup_boundary_diagnostic_defaults_to_disabled() -> None:
    from app.config import Settings

    assert Settings.__dataclass_fields__["enable_startup_boundary_diagnostic"].default is False


def test_get_db_health_boundary_logging_preserves_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    error = RuntimeError("startup boundary test failure")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_startup_boundary_diagnostic=True),
    )
    monkeypatch.setattr(database_health, "check_db", lambda: (_ for _ in ()).throw(error))

    with pytest.raises(RuntimeError) as raised:
        database_health.get_db_health()

    assert raised.value is error


def test_lifespan_logs_startup_boundaries_in_order(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    from app import main as main_module

    events: list[str] = []
    monkeypatch.setattr(main_module, "run_schema_state_diagnostic_once", lambda: None)
    monkeypatch.setattr(main_module, "run_conninfo_preflight_once", lambda: None)
    monkeypatch.setattr(main_module, "run_pgconn_stage_diagnostic_once", lambda: None)
    monkeypatch.setattr(main_module, "run_pgconn_level3_diagnostic_once", lambda: None)
    monkeypatch.setattr(main_module, "run_version_shape_diagnostic_once", lambda: None)
    monkeypatch.setattr(
        main_module,
        "settings",
        types.SimpleNamespace(
            enable_startup_boundary_diagnostic=True,
            initial_admin_email="",
            initial_admin_password="",
        ),
    )
    monkeypatch.setattr(main_module, "init_db", lambda: events.append("init_db"))
    monkeypatch.setattr(main_module, "get_db_health", lambda: {"db_tables_count": 1})

    @contextmanager
    def fake_db():
        yield object()

    monkeypatch.setattr(main_module, "get_db", fake_db)
    monkeypatch.setattr(main_module, "ensure_initial_admin", lambda _: events.append("bootstrap"))
    monkeypatch.setattr(main_module, "seed_default_organization", lambda _: events.append("organization"))
    monkeypatch.setattr(main_module, "seed_default_templates", lambda: events.append("templates"))
    monkeypatch.setattr(database_health, "settings", main_module.settings)
    caplog.set_level(logging.INFO, logger=database_health.logger.name)

    async def exercise() -> None:
        async with main_module.lifespan(main_module.app):
            pass

    asyncio.run(exercise())

    assert events == ["init_db", "bootstrap", "organization", "templates"]
    markers = [
        record.getMessage()
        for record in caplog.records
        if record.getMessage().startswith("startup_boundary ")
    ]
    assert markers == [
        "startup_boundary before_init_db",
        "startup_boundary after_init_db",
        "startup_boundary before_get_db_health",
        "startup_boundary after_get_db_health",
        "startup_boundary before_ensure_initial_admin",
        "startup_boundary after_ensure_initial_admin",
        "startup_boundary before_organization_workspace_seed",
        "startup_boundary after_organization_workspace_seed",
        "startup_boundary before_template_seed",
        "startup_boundary after_template_seed",
        "startup_boundary before_lifespan_yield",
    ]


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


class _VersionShapeCursor:
    def __init__(self, value: object = "PostgreSQL 18.0 on Linux") -> None:
        self.value = value
        self.execute_calls = 0
        self.close_calls = 0

    def execute(self, query: str) -> None:
        self.execute_calls += 1
        assert query == "select pg_catalog.version()"

    def fetchone(self) -> tuple[object]:
        return (self.value,)

    def close(self) -> None:
        self.close_calls += 1


class _VersionShapeConnection:
    def __init__(self, value: object = "PostgreSQL 18.0 on Linux") -> None:
        self.cursor_value = _VersionShapeCursor(value)
        self.close_calls = 0

    def cursor(self) -> _VersionShapeCursor:
        return self.cursor_value

    def close(self) -> None:
        self.close_calls += 1


def _version_shape_settings(enabled: bool = True) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        enable_db_version_shape_diagnostic=enabled,
        database_url="postgresql+psycopg://secret-user:secret-pass@secret-host/secret-db",
    )


def test_version_shape_diagnostic_disabled_does_not_connect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_version_shape_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "settings", _version_shape_settings(False))

    def fail_connect(_: str) -> None:
        pytest.fail("version shape diagnostic connected while disabled")

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=fail_connect))
    result = database_health.run_version_shape_diagnostic_once()

    assert result["enabled"] is False
    assert result["executed"] is False
    assert result["failure_category"] == "none"


def test_version_shape_diagnostic_success_is_bounded_and_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_version_shape_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "settings", _version_shape_settings())
    connection = _VersionShapeConnection()
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=lambda _: connection))

    result = database_health.run_version_shape_diagnostic_once()

    assert result["enabled"] is True
    assert result["executed"] is True
    assert result["result_type"] == "str"
    assert result["contains_postgresql_token"] is True
    assert result["sqlalchemy_regex_match"] is True
    assert result["parsed_major_bucket"] == "18"
    assert result["failure_category"] == "none"
    assert connection.cursor_value.execute_calls == 1
    assert connection.cursor_value.close_calls == 1
    assert connection.close_calls == 1


@pytest.mark.parametrize(
    ("raw", "result_type", "failure_category"),
    [
        ("", "str", "empty"),
        (None, "none", "non_string"),
        (b"PostgreSQL 18.0", "bytes", "non_string"),
        (object(), "other", "non_string"),
    ],
)
def test_version_shape_diagnostic_rejects_non_string_shapes(
    raw: object,
    result_type: str,
    failure_category: str,
) -> None:
    result = database_health._classify_version_shape(raw)

    assert result["result_type"] == result_type
    assert result["failure_category"] == failure_category
    assert result["sqlalchemy_regex_match"] is False
    assert result["parsed_major_bucket"] == "unavailable"
    assert set(result["failure_category"]) <= set("none_regex_miss_non_string_empty_query_failed_connect_failed_diagnostic_failed")


def test_version_shape_diagnostic_preserves_regex_and_prefix_shape_without_raw_value() -> None:
    enterprise = database_health._classify_version_shape("EnterpriseDB 17.2 on x")
    token_miss = database_health._classify_version_shape("build PostgreSQL-ish")

    assert enterprise["contains_enterprisedb_token"] is True
    assert enterprise["prefix_category"] == "enterprisedb"
    assert enterprise["parsed_major_bucket"] == "other_numeric"
    assert token_miss["contains_postgresql_token"] is True
    assert token_miss["sqlalchemy_regex_match"] is False
    assert token_miss["failure_category"] == "regex_miss"


def test_version_shape_diagnostic_failure_is_secret_free_and_non_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_version_shape_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "settings", _version_shape_settings())

    class SecretError(Exception):
        pass

    def fail_connect(_: str) -> None:
        raise SecretError("postgresql://secret-user:secret-pass@secret-host/secret-db")

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=fail_connect))
    result = database_health.run_version_shape_diagnostic_once()
    serialized = repr(result)

    assert result["failure_category"] == "connect_failed"
    for secret in ("secret-user", "secret-pass", "secret-host", "secret-db", "postgresql://"):
        assert secret not in serialized


def test_version_shape_diagnostic_query_failure_is_non_fatal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_version_shape_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "settings", _version_shape_settings())

    class FailingCursor(_VersionShapeCursor):
        def execute(self, query: str) -> None:
            raise AssertionError("secret query detail")

    connection = _VersionShapeConnection()
    connection.cursor_value = FailingCursor()
    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=lambda _: connection))

    result = database_health.run_version_shape_diagnostic_once()

    assert result["failure_category"] == "query_failed"
    assert connection.close_calls == 1


def test_version_shape_diagnostic_runs_once_and_health_getter_only_reads_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_version_shape_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "settings", _version_shape_settings())
    calls = {"connect": 0}
    connection = _VersionShapeConnection()

    def connect(_: str) -> _VersionShapeConnection:
        calls["connect"] += 1
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))
    first = database_health.run_version_shape_diagnostic_once()
    second = database_health.run_version_shape_diagnostic_once()
    monkeypatch.setattr(database_health, "run_version_shape_diagnostic_once", lambda: pytest.fail("health getter executed diagnostic"))
    cached = database_health.get_version_shape_diagnostic()

    assert first == second == cached
    assert calls["connect"] == 1


def test_database_diagnostic_exposes_cached_version_shape_without_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    cached = database_health._classify_version_shape("PostgreSQL 18.0")
    monkeypatch.setattr(database_health, "_version_shape_diagnostic_cache", cached)
    monkeypatch.setattr(database_health, "ENGINE_DIALECT", "sqlite")
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(
            enable_db_version_shape_diagnostic=True,
            enable_db_conninfo_preflight=False,
            enable_db_pgconn_stage_diagnostic=False,
            enable_db_pgconn_level3_diagnostic=False,
            enable_db_safe_exception_location_diagnostic=False,
        ),
    )
    monkeypatch.setattr(database_health, "run_version_shape_diagnostic_once", lambda: pytest.fail("health getter executed diagnostic"))

    diagnostic = database_health.get_database_diagnostic()

    assert diagnostic["version_shape_diagnostic"] == cached


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


def test_sqlalchemy_row_machinery_receives_sequence_rows_for_version_scalar() -> None:
    from sqlalchemy.engine.result import result_tuple

    make_row = result_tuple(["version"])
    row = make_row(("PostgreSQL 18.0 on Linux",))

    assert row[0] == "PostgreSQL 18.0 on Linux"
    assert database_health._VERSION_SHAPE_REGEX.match(row[0]) is not None


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


def test_conninfo_preflight_disabled_does_not_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_conninfo_preflight_cache", None)
    monkeypatch.setattr(database_health, "settings", types.SimpleNamespace(enable_db_conninfo_preflight=False))
    monkeypatch.setattr(database_health, "_run_conninfo_preflight", lambda _: pytest.fail("preflight ran"))

    result = database_health.run_conninfo_preflight_once()

    assert result["enabled"] is False
    assert result["executed"] is False
    assert result["conninfo_parse_status"] == "not_run"
    assert result["attempts_count"] == "unknown"


def _install_fake_conninfo(
    monkeypatch: pytest.MonkeyPatch,
    *,
    parse,
    timeout,
    attempts,
) -> None:
    conninfo_module = types.ModuleType("psycopg.conninfo")
    conninfo_module.conninfo_to_dict = parse
    conninfo_module.timeout_from_conninfo = timeout
    conninfo_module.conninfo_attempts = attempts
    psycopg_module = types.ModuleType("psycopg")
    psycopg_module.__path__ = []
    monkeypatch.setitem(sys.modules, "psycopg", psycopg_module)
    monkeypatch.setitem(sys.modules, "psycopg.conninfo", conninfo_module)


def test_run_conninfo_preflight_success_exercises_direct_stages(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def parse(value: str) -> dict[str, str]:
        calls.append("parse")
        assert value.startswith("postgresql://")
        return {"hostaddr": "127.0.0.1", "user": "secret-user", "password": "secret-pass", "dbname": "secret-db"}

    def timeout(params: dict[str, str]) -> int:
        calls.append("timeout")
        return 130

    def attempts(params: dict[str, str]) -> list[dict[str, str]]:
        calls.append("attempts")
        return [{"hostaddr": "127.0.0.1"}]

    _install_fake_conninfo(monkeypatch, parse=parse, timeout=timeout, attempts=attempts)
    result = database_health._run_conninfo_preflight("postgresql://secret-user:secret-pass@secret-host/secret-db")

    assert calls == ["parse", "timeout", "attempts"]
    assert result["executed"] is True
    assert result["conninfo_parse_status"] == "success"
    assert result["timeout_status"] == "success"
    assert result["conninfo_attempts_status"] == "success"
    assert result["attempts_count"] == 1
    assert result["dns_resolution_status"] == "not_required"
    assert "secret-host" not in repr(result)
    assert "secret-user" not in repr(result)
    assert "secret-pass" not in repr(result)
    assert "secret-db" not in repr(result)


def test_run_conninfo_preflight_parse_failure_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    class ProgrammingError(Exception):
        pass

    def parse(_: str) -> dict[str, str]:
        raise ProgrammingError("postgresql://secret-user:secret-pass@secret-host/secret-db")

    _install_fake_conninfo(
        monkeypatch,
        parse=parse,
        timeout=lambda _: pytest.fail("timeout ran"),
        attempts=lambda _: pytest.fail("attempts ran"),
    )
    result = database_health._run_conninfo_preflight("postgresql://secret")

    assert result["executed"] is True
    assert result["conninfo_parse_status"] == "failure"
    assert result["timeout_status"] == "not_run"
    assert result["conninfo_attempts_status"] == "not_run"
    assert result["exception_class"] == "ProgrammingError"
    assert "secret-user" not in repr(result)


def test_run_conninfo_preflight_timeout_failure_is_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    def timeout(_: dict[str, str]) -> int:
        raise TimeoutError("secret timeout")

    _install_fake_conninfo(
        monkeypatch,
        parse=lambda _: {"host": "secret-host"},
        timeout=timeout,
        attempts=lambda _: pytest.fail("attempts ran"),
    )
    result = database_health._run_conninfo_preflight("postgresql://secret")

    assert result["conninfo_parse_status"] == "success"
    assert result["timeout_status"] == "failure"
    assert result["conninfo_attempts_status"] == "not_run"
    assert result["exception_class"] == "TimeoutError"


@pytest.mark.parametrize("error_type", ["OperationalError", "AssertionError"])
def test_run_conninfo_preflight_attempts_failures_are_bounded(
    monkeypatch: pytest.MonkeyPatch,
    error_type: str,
) -> None:
    class OperationalError(Exception):
        pass

    error_class = OperationalError if error_type == "OperationalError" else AssertionError

    def attempts(_: dict[str, str]) -> list[dict[str, str]]:
        raise error_class("postgresql://secret-user:secret-pass@secret-host/secret-db")

    _install_fake_conninfo(
        monkeypatch,
        parse=lambda _: {"host": "secret-host"},
        timeout=lambda _: 130,
        attempts=attempts,
    )
    result = database_health._run_conninfo_preflight("postgresql://secret")

    assert result["conninfo_parse_status"] == "success"
    assert result["timeout_status"] == "success"
    assert result["conninfo_attempts_status"] == "failure"
    assert result["attempts_count"] == "unknown"
    assert result["dns_resolution_status"] == "unknown"
    assert result["exception_class"] == error_type
    assert "secret-host" not in repr(result)
    assert "secret-user" not in repr(result)
    assert "secret-pass" not in repr(result)
    assert "secret-db" not in repr(result)


def test_conninfo_preflight_runs_once_and_returns_bounded_result(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_conninfo_preflight_cache", None)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_conninfo_preflight=True, database_url="postgresql://secret-user:secret-pass@secret-host/secret-db"),
    )
    calls: list[str] = []

    def fake_preflight(url: str) -> dict[str, object]:
        calls.append(url)
        return {
            "enabled": True,
            "executed": True,
            "conninfo_parse_status": "success",
            "timeout_status": "success",
            "conninfo_attempts_status": "success",
            "attempts_count": 1,
            "dns_resolution_status": "success",
            "exception_class": "unknown",
        }

    monkeypatch.setattr(database_health, "_run_conninfo_preflight", fake_preflight)
    first = database_health.run_conninfo_preflight_once()
    second = database_health.run_conninfo_preflight_once()

    assert len(calls) == 1
    assert first == second
    assert first["attempts_count"] == 1
    assert set(first) == {
        "enabled", "executed", "conninfo_parse_status", "timeout_status",
        "conninfo_attempts_status", "attempts_count", "dns_resolution_status", "exception_class",
    }


def test_conninfo_preflight_once_cache_runs_direct_preflight_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_health, "_conninfo_preflight_cache", None)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_conninfo_preflight=True, database_url="postgresql://secret"),
    )
    attempts_calls = 0

    def attempts(_: dict[str, str]) -> list[dict[str, str]]:
        nonlocal attempts_calls
        attempts_calls += 1
        return [{"hostaddr": "127.0.0.1"}]

    _install_fake_conninfo(
        monkeypatch,
        parse=lambda _: {"host": "secret-host"},
        timeout=lambda _: 130,
        attempts=attempts,
    )
    first = database_health.run_conninfo_preflight_once()
    second = database_health.run_conninfo_preflight_once()

    assert attempts_calls == 1
    assert first == second
    assert first["executed"] is True
    assert first["attempts_count"] == 1


@pytest.mark.parametrize(
    ("failure", "expected_stage"),
    [
        ("parse", "conninfo_parse_status"),
        ("timeout", "timeout_status"),
        ("attempts", "conninfo_attempts_status"),
    ],
)
def test_conninfo_preflight_failures_are_non_fatal_and_allowlisted(
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    expected_stage: str,
) -> None:
    monkeypatch.setattr(database_health, "_conninfo_preflight_cache", None)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(enable_db_conninfo_preflight=True, database_url="postgresql://secret"),
    )

    def fake_preflight(_: str) -> dict[str, object]:
        result = database_health._preflight_result(True)
        result["executed"] = True
        result[expected_stage] = "failure"
        result["exception_class"] = "AssertionError" if failure == "attempts" else "unknown"
        return result

    monkeypatch.setattr(database_health, "_run_conninfo_preflight", fake_preflight)
    result = database_health.run_conninfo_preflight_once()

    assert result["executed"] is True
    assert result[expected_stage] == "failure"
    assert result["exception_class"] in database_health._PREFLIGHT_EXCEPTION_CLASSES | {"unknown"}


class _FakePollingStatus(enum.Enum):
    FAILED = 0
    READING = 1
    WRITING = 2
    OK = 3
    ACTIVE = 4


def _install_fake_pgconn(
    monkeypatch: pytest.MonkeyPatch,
    *,
    start_error: Exception | None = None,
    poll_error: Exception | None = None,
    poll_status: _FakePollingStatus = _FakePollingStatus.READING,
    finish_error: Exception | None = None,
) -> dict[str, int]:
    calls = {"start": 0, "poll": 0, "finish": 0}

    class FakePGconn:
        @classmethod
        def connect_start(cls, conninfo: bytes) -> "FakePGconn":
            assert isinstance(conninfo, bytes)
            calls["start"] += 1
            if start_error is not None:
                raise start_error
            return cls()

        def connect_poll(self) -> _FakePollingStatus:
            calls["poll"] += 1
            if poll_error is not None:
                raise poll_error
            return poll_status

        def finish(self) -> None:
            calls["finish"] += 1
            if finish_error is not None:
                raise finish_error

    conninfo_module = types.ModuleType("psycopg.conninfo")
    conninfo_module.conninfo_to_dict = lambda _: {"host": "secret-host"}
    conninfo_module.timeout_from_conninfo = lambda _: 5
    conninfo_module.conninfo_attempts = lambda _: [{"host": "secret-host"}]
    conninfo_module.make_conninfo = lambda _, **kwargs: "host=secret-host"
    pq_module = types.ModuleType("psycopg.pq")
    pq_module.PGconn = FakePGconn
    pq_module.PollingStatus = _FakePollingStatus
    psycopg_module = types.ModuleType("psycopg")
    psycopg_module.__path__ = []
    monkeypatch.setitem(sys.modules, "psycopg", psycopg_module)
    monkeypatch.setitem(sys.modules, "psycopg.conninfo", conninfo_module)
    monkeypatch.setitem(sys.modules, "psycopg.pq", pq_module)
    return calls


def _assert_pgconn_safe_result(result: dict[str, object]) -> None:
    assert "secret-host" not in repr(result)
    assert "postgresql://" not in repr(result)
    assert result["exception_class"] in database_health._PREFLIGHT_EXCEPTION_CLASSES | {"unknown"}


def test_pgconn_stage_diagnostic_level_two_first_poll_and_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_fake_pgconn(monkeypatch)

    result = database_health._run_pgconn_stage_diagnostic("postgresql://secret")

    assert calls == {"start": 1, "poll": 1, "finish": 1}
    assert result["pgconn_connect_start_status"] == "success"
    assert result["pgconn_connect_poll_status"] == "success"
    assert result["first_poll_result"] == "reading"
    assert result["poll_iterations"] == 1
    assert result["cleanup_status"] == "success"
    assert result["exception_stage"] == "none"
    _assert_pgconn_safe_result(result)


def test_pgconn_stage_diagnostic_start_assertion_stops_before_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_fake_pgconn(monkeypatch, start_error=AssertionError("secret-host"))

    result = database_health._run_pgconn_stage_diagnostic("postgresql://secret")

    assert calls == {"start": 1, "poll": 0, "finish": 0}
    assert result["pgconn_connect_start_status"] == "failure"
    assert result["pgconn_connect_poll_status"] == "not_run"
    assert result["exception_stage"] == "connect_start"
    assert result["exception_class"] == "AssertionError"
    _assert_pgconn_safe_result(result)


def test_pgconn_stage_diagnostic_first_poll_assertion_finishes_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _install_fake_pgconn(monkeypatch, poll_error=AssertionError("secret-host"))

    result = database_health._run_pgconn_stage_diagnostic("postgresql://secret")

    assert calls == {"start": 1, "poll": 1, "finish": 1}
    assert result["pgconn_connect_start_status"] == "success"
    assert result["pgconn_connect_poll_status"] == "failure"
    assert result["first_poll_result"] == "not_run"
    assert result["exception_stage"] == "first_connect_poll"
    assert result["exception_class"] == "AssertionError"
    _assert_pgconn_safe_result(result)


def test_pgconn_stage_diagnostic_cleanup_failure_does_not_replace_primary_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fake_pgconn(
        monkeypatch,
        poll_error=AssertionError("secret-host"),
        finish_error=RuntimeError("secret-cleanup"),
    )

    result = database_health._run_pgconn_stage_diagnostic("postgresql://secret")

    assert calls == {"start": 1, "poll": 1, "finish": 1}
    assert result["exception_stage"] == "first_connect_poll"
    assert result["exception_class"] == "AssertionError"
    assert result["cleanup_status"] == "failure"
    _assert_pgconn_safe_result(result)


def test_pgconn_stage_diagnostic_once_cache_and_disabled_state(monkeypatch: pytest.MonkeyPatch) -> None:
    original_runner = database_health._run_pgconn_stage_diagnostic
    monkeypatch.setattr(database_health, "_pgconn_stage_diagnostic_cache", None)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(
            enable_db_pgconn_stage_diagnostic=False,
            database_url="postgresql://secret",
        ),
    )
    monkeypatch.setattr(database_health, "_run_pgconn_stage_diagnostic", lambda _: pytest.fail("diagnostic ran"))
    disabled = database_health.run_pgconn_stage_diagnostic_once()
    assert disabled["executed"] is False
    assert disabled["pgconn_connect_start_status"] == "not_run"

    calls = _install_fake_pgconn(monkeypatch)
    monkeypatch.setattr(database_health, "_run_pgconn_stage_diagnostic", original_runner)
    monkeypatch.setattr(database_health, "_pgconn_stage_diagnostic_cache", None)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(
            enable_db_pgconn_stage_diagnostic=True,
            database_url="postgresql://secret",
        ),
    )
    first = database_health.run_pgconn_stage_diagnostic_once()
    second = database_health.run_pgconn_stage_diagnostic_once()
    assert first == second
    assert calls == {"start": 1, "poll": 1, "finish": 1}


class _RecordingSelector:
    instances: list["_RecordingSelector"] = []

    def __init__(self) -> None:
        self.registered: list[tuple[int, int]] = []
        self.unregistered: list[int] = []
        self.closed = False
        _RecordingSelector.instances.append(self)

    def register(self, fileobj: int, events: int) -> None:
        self.registered.append((fileobj, events))

    def select(self, timeout: float) -> list[object]:
        assert timeout > 0
        return [object()]

    def unregister(self, fileobj: int) -> None:
        self.unregistered.append(fileobj)

    def close(self) -> None:
        self.closed = True


def _install_fake_level3(
    monkeypatch: pytest.MonkeyPatch,
    poll_values: list[object],
    *,
    start_error: Exception | None = None,
    poll_error_at: int | None = None,
    status: object | None = None,
    socket_value: int = 42,
    finish_error: Exception | None = None,
) -> dict[str, int]:
    from psycopg.pq import ConnStatus, PollingStatus

    calls = {"start": 0, "poll": 0, "finish": 0}

    class FakePGconn:
        socket = socket_value

        @classmethod
        def connect_start(cls, conninfo: bytes) -> "FakePGconn":
            assert isinstance(conninfo, bytes)
            calls["start"] += 1
            if start_error is not None:
                raise start_error
            return cls()

        @property
        def status(self) -> object:
            return ConnStatus.OK if status is None else status

        def connect_poll(self) -> object:
            index = calls["poll"]
            calls["poll"] += 1
            if poll_error_at == index:
                raise AssertionError("secret-host")
            return poll_values[index]

        def finish(self) -> None:
            calls["finish"] += 1
            if finish_error is not None:
                raise finish_error

    conninfo_module = types.ModuleType("psycopg.conninfo")
    conninfo_module.conninfo_to_dict = lambda _: {"host": "secret-host"}
    conninfo_module.timeout_from_conninfo = lambda _: 5
    conninfo_module.conninfo_attempts = lambda _: [{"host": "secret-host"}]
    conninfo_module.make_conninfo = lambda _, **__: "host=secret-host"
    pq_module = types.ModuleType("psycopg.pq")
    pq_module.PGconn = FakePGconn
    pq_module.ConnStatus = ConnStatus
    pq_module.PollingStatus = PollingStatus
    psycopg_module = types.ModuleType("psycopg")
    psycopg_module.__path__ = []
    monkeypatch.setitem(sys.modules, "psycopg", psycopg_module)
    monkeypatch.setitem(sys.modules, "psycopg.conninfo", conninfo_module)
    monkeypatch.setitem(sys.modules, "psycopg.pq", pq_module)
    _RecordingSelector.instances = []
    monkeypatch.setattr(database_health.selectors, "DefaultSelector", _RecordingSelector)
    return calls


def test_pgconn_level3_writing_reading_and_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg.pq import PollingStatus

    calls = _install_fake_level3(
        monkeypatch,
        [PollingStatus.WRITING, PollingStatus.READING, PollingStatus.OK],
    )
    result = database_health._run_pgconn_level3_diagnostic("postgresql://secret")

    assert calls == {"start": 1, "poll": 3, "finish": 1}
    assert result["poll_sequence"] == ["writing", "reading", "ok"]
    assert result["low_level_connection_status"] == "success"
    assert len(_RecordingSelector.instances) == 2
    assert _RecordingSelector.instances[0].registered[0][1] == database_health.selectors.EVENT_WRITE
    assert _RecordingSelector.instances[1].registered[0][1] == database_health.selectors.EVENT_READ
    assert all(item.closed for item in _RecordingSelector.instances)
    assert all(item.unregistered == [42] for item in _RecordingSelector.instances)
    _assert_pgconn_safe_result(result)


def test_pgconn_level3_second_poll_assertion_is_classified_and_cleaned(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg.pq import PollingStatus

    calls = _install_fake_level3(
        monkeypatch,
        [PollingStatus.WRITING, PollingStatus.READING],
        poll_error_at=1,
    )
    result = database_health._run_pgconn_level3_diagnostic("postgresql://secret")

    assert calls == {"start": 1, "poll": 2, "finish": 1}
    assert result["exception_stage"] == "connect_poll_2_or_later"
    assert result["exception_class"] == "AssertionError"
    assert result["low_level_connection_status"] == "exception"
    _assert_pgconn_safe_result(result)


def test_pgconn_level3_first_poll_assertion_and_failed_poll_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg.pq import PollingStatus

    calls = _install_fake_level3(monkeypatch, [PollingStatus.READING], poll_error_at=0)
    first_failure = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert first_failure["exception_stage"] == "connect_poll_1"
    assert first_failure["poll_iterations"] == 1
    assert calls["finish"] == 1

    calls = _install_fake_level3(monkeypatch, [PollingStatus.FAILED])
    failed = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert failed["low_level_connection_status"] == "failed"
    assert failed["poll_sequence"] == ["failed"]
    assert calls["finish"] == 1


def test_pgconn_level3_selector_timeout_and_cleanup_failure_preserve_primary_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from psycopg.pq import PollingStatus

    calls = _install_fake_level3(monkeypatch, [PollingStatus.WRITING])
    monkeypatch.setattr(_RecordingSelector, "select", lambda self, timeout: [])
    timeout = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert timeout["low_level_connection_status"] == "diagnostic_timeout"
    assert timeout["cleanup_status"] == "success"
    assert calls["finish"] == 1

    calls = _install_fake_level3(
        monkeypatch,
        [PollingStatus.WRITING],
        poll_error_at=0,
        finish_error=RuntimeError("secret-cleanup"),
    )
    cleanup_failure = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert cleanup_failure["exception_stage"] == "connect_poll_1"
    assert cleanup_failure["exception_class"] == "AssertionError"
    assert cleanup_failure["cleanup_status"] == "failure"
    assert calls["finish"] == 1


def test_pgconn_level3_timeout_active_and_status_mismatch_are_bounded(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg.pq import ConnStatus, PollingStatus

    calls = _install_fake_level3(monkeypatch, [PollingStatus.ACTIVE])
    active = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert active["low_level_connection_status"] == "unexpected_active"
    assert calls == {"start": 1, "poll": 1, "finish": 1}

    calls = _install_fake_level3(monkeypatch, [PollingStatus.OK], status=ConnStatus.BAD)
    mismatch = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert mismatch["low_level_connection_status"] == "status_mismatch"
    assert calls == {"start": 1, "poll": 1, "finish": 1}


def test_pgconn_level3_invalid_socket_and_failed_poll_do_not_close_socket(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg.pq import PollingStatus

    calls = _install_fake_level3(monkeypatch, [PollingStatus.WRITING], socket_value=-1)
    monkeypatch.setattr(
        database_health,
        "selectors",
        types.SimpleNamespace(
            EVENT_READ=1,
            EVENT_WRITE=2,
            DefaultSelector=lambda: pytest.fail("selector must not run"),
        ),
    )
    result = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert result["low_level_connection_status"] == "exception"
    assert result["exception_stage"] == "socket_check"
    assert calls["finish"] == 1


def test_pgconn_level3_deadline_and_iteration_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg.pq import PollingStatus

    calls = _install_fake_level3(monkeypatch, [PollingStatus.WRITING])
    monkeypatch.setattr(database_health, "monotonic", lambda: 100.0)
    monkeypatch.setattr(database_health, "LEVEL3_HARD_DEADLINE_SECONDS", -1.0)
    timeout = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert timeout["low_level_connection_status"] == "diagnostic_timeout"
    assert timeout["poll_iterations"] == 0
    assert calls == {"start": 1, "poll": 0, "finish": 1}

    calls = _install_fake_level3(monkeypatch, [PollingStatus.WRITING] * 64)
    monkeypatch.setattr(database_health, "monotonic", lambda: 0.0)
    monkeypatch.setattr(database_health, "LEVEL3_HARD_DEADLINE_SECONDS", 5.0)
    monkeypatch.setattr(_RecordingSelector, "select", lambda self, timeout: [object()])
    limited = database_health._run_pgconn_level3_diagnostic("postgresql://secret")
    assert limited["low_level_connection_status"] == "iteration_limit"
    assert limited["poll_iterations"] == 64
    assert calls == {"start": 1, "poll": 64, "finish": 1}


def test_pgconn_level3_flag_disabled_and_cache_prevent_reexecution(monkeypatch: pytest.MonkeyPatch) -> None:
    from psycopg.pq import PollingStatus

    original_runner = database_health._run_pgconn_level3_diagnostic
    monkeypatch.setattr(database_health, "_pgconn_level3_diagnostic_cache", None)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(
            enable_db_pgconn_level3_diagnostic=False,
            database_url="postgresql://secret",
        ),
    )
    monkeypatch.setattr(
        database_health,
        "_run_pgconn_level3_diagnostic",
        lambda _: pytest.fail("level3 diagnostic ran while disabled"),
    )
    disabled = database_health.run_pgconn_level3_diagnostic_once()
    assert disabled["executed"] is False
    assert disabled["low_level_connection_status"] == "not_run"

    calls = _install_fake_level3(monkeypatch, [PollingStatus.OK])
    monkeypatch.setattr(database_health, "_pgconn_level3_diagnostic_cache", None)
    monkeypatch.setattr(database_health, "_run_pgconn_level3_diagnostic", original_runner)
    monkeypatch.setattr(
        database_health,
        "settings",
        types.SimpleNamespace(
            enable_db_pgconn_level3_diagnostic=True,
            database_url="postgresql://secret",
        ),
    )
    first = database_health.run_pgconn_level3_diagnostic_once()
    second = database_health.run_pgconn_level3_diagnostic_once()
    assert first == second
    assert calls == {"start": 1, "poll": 1, "finish": 1}


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
