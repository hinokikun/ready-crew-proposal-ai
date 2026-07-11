import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    import sys

    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def make_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, pilot_mode: bool = True, maintenance_mode: bool = False, max_users: int = 5) -> TestClient:
    db_path = tmp_path / "pilot-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("USE_MOCK_AI", "true")
    monkeypatch.setenv("APP_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("INITIAL_ADMIN_PASSWORD", "test-password")
    monkeypatch.setenv("PILOT_MODE", "true" if pilot_mode else "false")
    monkeypatch.setenv("PILOT_MAX_USERS", str(max_users))
    monkeypatch.setenv("MAINTENANCE_MODE", "true" if maintenance_mode else "false")
    _reload_app_modules()
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def login(client: TestClient, email: str, password: str) -> tuple[int, dict]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    return response.status_code, response.json()


def admin_headers(client: TestClient) -> dict[str, str]:
    status, body = login(client, "admin@example.com", "test-password")
    assert status == 200
    return {"Authorization": f"Bearer {body['token']}"}


def create_user(client: TestClient, headers: dict[str, str], email: str, role: str = "member") -> dict:
    response = client.post(
        "/api/users",
        headers=headers,
        json={"email": email, "password": "member-password", "role": role},
    )
    assert response.status_code == 200
    return response.json()["user"]


def test_pilot_mode_blocks_non_enabled_member_login(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=True) as client:
        headers = admin_headers(client)
        user = create_user(client, headers, "pilot-member@example.com")

        status, _ = login(client, "pilot-member@example.com", "member-password")
        assert status == 403

        response = client.patch(f"/api/users/{user['id']}", headers=headers, json={"pilot_enabled": True})
        assert response.status_code == 200

        status, body = login(client, "pilot-member@example.com", "member-password")
        assert status == 200
        assert body["user"]["pilot_enabled"] in {1, True}


def test_pilot_mode_enforces_max_users(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=True, max_users=1) as client:
        headers = admin_headers(client)
        first = create_user(client, headers, "pilot-one@example.com")
        second = create_user(client, headers, "pilot-two@example.com")

        first_response = client.patch(f"/api/users/{first['id']}", headers=headers, json={"pilot_enabled": True})
        assert first_response.status_code == 200

        second_response = client.patch(f"/api/users/{second['id']}", headers=headers, json={"pilot_enabled": True})
        assert second_response.status_code == 400
        assert "Pilot対象者" in second_response.text


def test_pilot_dashboard_and_checklist(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=True) as client:
        headers = admin_headers(client)

        status_response = client.get("/api/pilot/status")
        assert status_response.status_code == 200
        assert status_response.json()["pilot"]["pilot_mode"] is True

        checklist_response = client.post("/api/pilot/checklist-confirmed", headers=headers, json={})
        assert checklist_response.status_code == 200

        dashboard_response = client.get("/api/pilot/dashboard", headers=headers)
        assert dashboard_response.status_code == 200
        dashboard = dashboard_response.json()["dashboard"]
        assert "summary" in dashboard
        assert isinstance(dashboard["success_criteria"], list)


def test_maintenance_mode_blocks_new_generation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=False, maintenance_mode=True) as client:
        headers = admin_headers(client)
        response = client.post(
            "/api/analyze",
            headers=headers,
            json={
                "project_brief": "Webサイトリニューアルの相談。問い合わせ増加とCMS改善を目的に提案書を作成したい。",
                "client_company_info": "株式会社サンプル",
                "budget_range": "300万円",
                "desired_launch_timing": "3か月以内",
            },
        )
        assert response.status_code == 503
        assert "メンテナンス" in response.text
