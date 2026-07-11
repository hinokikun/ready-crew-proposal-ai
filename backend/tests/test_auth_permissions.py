from fastapi.testclient import TestClient


def test_admin_login_success(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "test-password"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["authenticated"] is True
    assert body["user"]["role"] == "admin"
    assert body["token"]


def test_viewer_cannot_generate(client: TestClient, admin_headers: dict[str, str], sample_proposal_payload: dict) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "viewer@example.com", "password": "viewer-password", "role": "viewer"},
    )
    assert create_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": "viewer@example.com", "password": "viewer-password"},
    )
    token = login_response.json()["token"]

    response = client.post(
        "/api/analyze",
        headers={"Authorization": f"Bearer {token}"},
        json=sample_proposal_payload,
    )

    assert response.status_code == 403
