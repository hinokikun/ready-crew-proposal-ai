from fastapi.testclient import TestClient


def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    password = f"{role}-password"
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": email, "password": password, "role": role},
    )
    assert create_response.status_code == 200

    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def test_admin_member_viewer_permissions(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_proposal_payload: dict,
) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "member-role@example.com", "member")
    viewer_headers = _create_user_and_login(client, admin_headers, "viewer-role@example.com", "viewer")

    users_response = client.get("/api/users", headers=admin_headers)
    assert users_response.status_code == 200
    assert len(users_response.json()["users"]) >= 3

    assert client.get("/api/users", headers=member_headers).status_code == 403
    assert client.get("/api/users", headers=viewer_headers).status_code == 403

    member_generate = client.post("/api/analyze", headers=member_headers, json=sample_proposal_payload)
    assert member_generate.status_code == 200

    viewer_generate = client.post("/api/analyze", headers=viewer_headers, json=sample_proposal_payload)
    assert viewer_generate.status_code == 403


def test_feedback_api_permissions_and_summary(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "feedback-member@example.com", "member")

    post_response = client.post(
        "/api/feedback",
        headers=member_headers,
        json={"rating": "usable", "comment": "社内確認に使えそうです", "feature_name": "proposal"},
    )
    assert post_response.status_code == 200
    assert post_response.json()["summary"]["usable"] >= 1

    admin_list = client.get("/api/feedback", headers=admin_headers)
    assert admin_list.status_code == 200
    assert admin_list.json()["feedback"]

    member_list = client.get("/api/feedback", headers=member_headers)
    assert member_list.status_code == 403


def test_usage_dashboard_api_and_csv_are_admin_only(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "usage-member@example.com", "member")

    log_response = client.post(
        "/api/logs",
        headers=member_headers,
        json={"feature_name": "proposal_generation", "input_length": 120, "output_type": "markdown", "status": "success"},
    )
    assert log_response.status_code == 200

    dashboard_response = client.get("/api/logs/usage-dashboard", headers=admin_headers)
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()["dashboard"]
    assert dashboard["summary"]["total_usage"] >= 1
    assert "error_analysis" in dashboard
    assert "features" in dashboard

    csv_response = client.get("/api/logs/usage-dashboard.csv", headers=admin_headers)
    assert csv_response.status_code == 200
    assert csv_response.headers["content-type"].startswith("text/csv")

    assert client.get("/api/logs/usage-dashboard", headers=member_headers).status_code == 403
    assert client.get("/api/logs/usage-dashboard.csv", headers=member_headers).status_code == 403


def test_trial_report_operation_readiness_and_improvement_dashboard_are_admin_only(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "ops-member@example.com", "member")

    report_response = client.post(
        "/api/logs/trial-report",
        headers=admin_headers,
        json={"admin_comment": "試験導入を継続します"},
    )
    assert report_response.status_code == 200
    assert "report" in report_response.json()

    readiness_response = client.get("/api/logs/operation-readiness", headers=admin_headers)
    assert readiness_response.status_code == 200
    assert "readiness" in readiness_response.json()

    improvement_response = client.get("/api/logs/improvement-dashboard", headers=admin_headers)
    assert improvement_response.status_code == 200
    assert "dashboard" in improvement_response.json()

    assert client.post("/api/logs/trial-report", headers=member_headers, json={"admin_comment": ""}).status_code == 403
    assert client.get("/api/logs/operation-readiness", headers=member_headers).status_code == 403
    assert client.get("/api/logs/improvement-dashboard", headers=member_headers).status_code == 403
