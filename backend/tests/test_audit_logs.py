from fastapi.testclient import TestClient


def test_admin_can_read_audit_logs(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.get("/api/logs/audit", headers=admin_headers)

    assert response.status_code == 200
    assert "logs" in response.json()


def test_member_cannot_read_audit_logs(client: TestClient, admin_headers: dict[str, str]) -> None:
    client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "member@example.com", "password": "member-password", "role": "member"},
    )
    login_response = client.post(
        "/api/auth/login",
        json={"email": "member@example.com", "password": "member-password"},
    )
    token = login_response.json()["token"]

    response = client.get("/api/logs/audit", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_user_management_audit_logs_do_not_store_passwords(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "audit-role@example.com", "password": "initial-password", "role": "user"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["id"]

    role_response = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"role": "viewer"})
    password_response = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"password": "changed-password"})
    active_response = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"is_active": False})

    assert role_response.status_code == 200
    assert password_response.status_code == 200
    assert active_response.status_code == 200

    logs = client.get("/api/logs/audit", headers=admin_headers).json()["logs"]
    event_types = {log["event_type"] for log in logs}
    combined = " ".join(str(log.get("metadata", "")) for log in logs)

    assert {"user_created", "role_changed", "password_reset", "user_disabled"}.issubset(event_types)
    assert "initial-password" not in combined
    assert "changed-password" not in combined
