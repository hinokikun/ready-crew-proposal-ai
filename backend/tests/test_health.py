from fastapi.testclient import TestClient
from contextlib import contextmanager
import logging

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
