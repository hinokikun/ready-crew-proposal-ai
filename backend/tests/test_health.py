from fastapi.testclient import TestClient
from contextlib import contextmanager
import logging

import pytest

from app.database import health as database_health


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

    record = next(record for record in caplog.records if record.getMessage() == "database_connectivity_failed")
    assert record.db_dialect == database_health.ENGINE_DIALECT
    assert record.exception_class == "SecretConnectionError"
    assert record.sqlstate == "28P01"
    assert record.failure_category == "authentication"
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

    record = next(record for record in caplog.records if record.getMessage() == "database_connectivity_failed")
    assert record.exception_class == "UnclassifiedConnectionError"
    assert record.failure_category == "unknown"
    assert not hasattr(record, "sqlstate")


def test_check_db_success_remains_true(monkeypatch: pytest.MonkeyPatch) -> None:
    @contextmanager
    def successful_db():
        class Cursor:
            def execute(self, query: str) -> None:
                assert query == "SELECT 1"

        yield Cursor()

    monkeypatch.setattr(database_health, "get_db", successful_db)
    assert database_health.check_db() is True


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
