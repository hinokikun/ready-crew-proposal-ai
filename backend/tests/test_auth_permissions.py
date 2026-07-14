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
    assert body["user"]["role_label"] == "管理者"
    assert body["token"]


def test_login_mode_admin_accepts_admin_and_manager(client: TestClient, admin_headers: dict[str, str]) -> None:
    admin_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "test-password", "login_mode": "admin"},
    )
    assert admin_response.status_code == 200
    assert admin_response.json()["login_mode"] == "admin"

    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "manager-login@example.com", "password": "manager-password", "role": "manager"},
    )
    assert create_response.status_code == 200
    manager_response = client.post(
        "/api/auth/login",
        json={"email": "manager-login@example.com", "password": "manager-password", "login_mode": "admin"},
    )
    assert manager_response.status_code == 200
    assert manager_response.json()["user"]["role"] == "manager"


def test_login_mode_user_accepts_member_and_viewer(client: TestClient, admin_headers: dict[str, str]) -> None:
    for role in ("member", "viewer"):
        email = f"{role}-mode@example.com"
        create_response = client.post(
            "/api/users",
            headers=admin_headers,
            json={"email": email, "password": "user-password", "role": role},
        )
        assert create_response.status_code == 200
        login_response = client.post(
            "/api/auth/login",
            json={"email": email, "password": "user-password", "login_mode": "user"},
        )
        assert login_response.status_code == 200
        assert login_response.json()["user"]["role"] == role


def test_login_mode_rejects_role_mismatch(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "member-admin-mode@example.com", "password": "member-password", "role": "member"},
    )
    assert create_response.status_code == 200

    member_admin = client.post(
        "/api/auth/login",
        json={"email": "member-admin-mode@example.com", "password": "member-password", "login_mode": "admin"},
    )
    assert member_admin.status_code == 403
    assert "管理者権限" in member_admin.json()["detail"]

    admin_user = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "test-password", "login_mode": "user"},
    )
    assert admin_user.status_code == 403
    assert "管理者ログイン" in admin_user.json()["detail"]


def test_login_mode_missing_keeps_legacy_compatibility(client: TestClient) -> None:
    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-password"})
    assert response.status_code == 200
    assert response.json()["login_mode"] is None


def test_inactive_user_login_is_rejected_with_safe_message(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "inactive-login@example.com", "password": "member-password", "role": "member"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["id"]
    assert client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"is_active": False}).status_code == 200

    response = client.post(
        "/api/auth/login",
        json={"email": "inactive-login@example.com", "password": "member-password", "login_mode": "user"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "このアカウントは現在無効です"


def test_login_audit_does_not_store_password_or_full_email(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "missing-login@example.com", "password": "secret-password", "login_mode": "user"},
    )
    assert response.status_code == 401

    audits = client.get("/api/logs/audit", headers=admin_headers)
    assert audits.status_code == 200
    serialized = str(audits.json()).lower()
    assert "secret-password" not in serialized
    assert "missing-login@example.com" not in serialized
    assert "authorization" not in serialized


def test_logout_records_audit_log(client: TestClient) -> None:
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "test-password", "login_mode": "admin"},
    )
    assert login_response.status_code == 200
    headers = {"Authorization": f"Bearer {login_response.json()['token']}"}

    logout_response = client.post("/api/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    audits = client.get("/api/logs/audit", headers=headers)
    assert audits.status_code == 200
    assert any(log["event_type"] == "logout" for log in audits.json()["logs"])


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_user_role_alias_is_stored_as_member_and_can_generate(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_proposal_payload: dict,
) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "user-alias@example.com", "password": "user-password", "role": "user"},
    )
    assert create_response.status_code == 200
    created = create_response.json()["user"]
    assert created["role"] == "member"
    assert created["role_label"] == "一般利用者"

    headers = _login(client, "user-alias@example.com", "user-password")
    generate = client.post("/api/analyze", headers=headers, json=sample_proposal_payload)
    assert generate.status_code == 200
    assert client.get("/api/users", headers=headers).status_code == 403


def test_role_change_and_password_reset_invalidate_old_token(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "reset-target@example.com", "password": "old-password", "role": "user"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["user"]["id"]
    old_headers = _login(client, "reset-target@example.com", "old-password")

    role_response = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"role": "viewer"})
    assert role_response.status_code == 200
    assert client.get("/api/auth/status", headers=old_headers).status_code == 401

    viewer_headers = _login(client, "reset-target@example.com", "old-password")
    password_response = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"password": "new-password"})
    assert password_response.status_code == 200
    assert client.get("/api/auth/status", headers=viewer_headers).status_code == 401

    new_login = client.post("/api/auth/login", json={"email": "reset-target@example.com", "password": "new-password"})
    assert new_login.status_code == 200


def test_admin_cannot_remove_last_admin(client: TestClient, admin_headers: dict[str, str]) -> None:
    users = client.get("/api/users", headers=admin_headers).json()["users"]
    admin_user = next(user for user in users if user["role"] == "admin")

    demote = client.patch(f"/api/users/{admin_user['id']}", headers=admin_headers, json={"role": "user"})
    disable = client.patch(f"/api/users/{admin_user['id']}", headers=admin_headers, json={"is_active": False})

    assert demote.status_code == 400
    assert disable.status_code == 400


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
