from fastapi.testclient import TestClient


def test_health_endpoint_reports_runtime_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_version"]
    assert body["environment"]
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
