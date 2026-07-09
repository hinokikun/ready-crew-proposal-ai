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
