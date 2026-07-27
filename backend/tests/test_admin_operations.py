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


def test_admin_user_management_profile_password_and_delete(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "managed-user@example.com", "password": "member-password", "role": "member", "display_name": "Managed User"},
    )
    assert create_response.status_code == 200
    user = create_response.json()["user"]
    assert user["display_name"] == "Managed User"
    assert user["role"] == "member"
    assert "password_hash" not in user

    update_response = client.patch(
        f"/api/users/{user['id']}",
        headers=admin_headers,
        json={"display_name": "Managed User Updated", "password": "temporary-password", "password_change_required": True},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["user"]
    assert updated["display_name"] == "Managed User Updated"
    assert bool(updated["password_change_required"]) is True

    login_response = client.post("/api/auth/login", json={"email": "managed-user@example.com", "password": "temporary-password"})
    assert login_response.status_code == 200
    assert login_response.json()["user"]["password_change_required"] is True

    delete_response = client.delete(f"/api/users/{user['id']}", headers=admin_headers)
    assert delete_response.status_code == 200
    assert client.post("/api/auth/login", json={"email": "managed-user@example.com", "password": "temporary-password"}).status_code == 403


def test_member_cannot_manage_users(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "no-admin@example.com", "member")
    assert client.patch("/api/users/1", headers=member_headers, json={"role": "viewer"}).status_code == 403
    assert client.delete("/api/users/1", headers=member_headers).status_code == 403


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


def test_creation_history_is_scoped_and_readable(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "history-member@example.com", "member")
    log_response = client.post(
        "/api/logs",
        headers=member_headers,
        json={"feature_name": "proposal_generation", "input_length": 120, "output_type": "markdown", "status": "success"},
    )
    assert log_response.status_code == 200

    member_history = client.get("/api/logs/creation-history", headers=member_headers)
    assert member_history.status_code == 200
    assert member_history.json()["items"]

    admin_history = client.get("/api/logs/creation-history", headers=admin_headers)
    assert admin_history.status_code == 200
    assert any(item["created_by_email"] == "history-member@example.com" for item in admin_history.json()["items"])


def test_business_improvement_report_calculates_savings_and_exports_csv(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "improvement-report@example.com", "member")

    create_response = client.post(
        "/api/logs/business-improvement-reports",
        headers=member_headers,
        json={
            "project_name": "研修用AI-OCR案件",
            "before_minutes": 120,
            "after_minutes": 45,
            "revision_minutes": 10,
            "review_minutes": 5,
            "quality_score": 4,
            "mistake_count": 1,
            "comment": "研修提出用",
        },
    )
    assert create_response.status_code == 200
    report = create_response.json()["report"]
    assert report["total_after_minutes"] == 60
    assert report["saved_minutes"] == 60
    assert report["reduction_rate"] == 50

    list_response = client.get("/api/logs/business-improvement-reports", headers=member_headers)
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["summary"]["total_saved_minutes"] == 60
    assert body["summary"]["average_reduction_rate"] == 50
    assert body["summary"]["total_mistake_count"] == 1

    csv_response = client.get("/api/logs/business-improvement-reports.csv", headers=member_headers)
    assert csv_response.status_code == 200
    csv_body = csv_response.content.decode("utf-8-sig")
    assert "測定日" in csv_body
    assert "使用前時間" in csv_body
    assert "研修用AI-OCR案件" in csv_body

    split_response = client.post(
        "/api/logs/business-improvement-reports",
        headers=member_headers,
        json={
            "project_name": "研修用分割計測案件",
            "before_minutes": 100,
            "ai_input_minutes": 10,
            "ai_wait_minutes": 20,
            "revision_minutes": 5,
            "review_minutes": 15,
            "quality_score": 5,
            "mistake_count": 0,
            "comment": "=CSV注入確認",
        },
    )
    assert split_response.status_code == 200
    split_report = split_response.json()["report"]
    assert split_report["total_after_minutes"] == 50
    assert split_report["saved_minutes"] == 50
    assert split_report["reduction_rate"] == 50

    invalid_response = client.post(
        "/api/logs/business-improvement-reports",
        headers=member_headers,
        json={
            "project_name": "不正値",
            "before_minutes": 0,
            "ai_input_minutes": 1,
            "ai_wait_minutes": 1,
            "revision_minutes": 1,
            "review_minutes": 1,
            "quality_score": 4,
            "mistake_count": 0,
            "comment": "保存されない",
        },
    )
    assert invalid_response.status_code == 400


def test_business_improvement_demo_data_creates_reports_and_history(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "improvement-demo@example.com", "member")

    demo_response = client.post("/api/logs/business-improvement-reports/demo-data", headers=member_headers)
    assert demo_response.status_code == 200
    demo_body = demo_response.json()
    assert demo_body["created"] >= 4
    assert demo_body["history_created"] >= 4
    assert demo_body["summary"]["total_count"] >= 4
    assert demo_body["summary"]["total_saved_minutes"] > 0

    reports_response = client.get("/api/logs/business-improvement-reports", headers=member_headers)
    assert reports_response.status_code == 200
    report_names = {item["project_name"] for item in reports_response.json()["items"]}
    assert "AI-OCR請求書処理" not in report_names

    reports_with_demo_response = client.get("/api/logs/business-improvement-reports?include_demo=true", headers=member_headers)
    assert reports_with_demo_response.status_code == 200
    report_names = {item["project_name"] for item in reports_with_demo_response.json()["items"]}
    assert "AI-OCR請求書処理" in report_names
    assert any(item["is_demo"] for item in reports_with_demo_response.json()["items"])

    history_response = client.get("/api/logs/creation-history", headers=member_headers)
    assert history_response.status_code == 200
    history_names = {item["project_name"] for item in history_response.json()["items"]}
    assert "AI-OCR請求書処理" not in history_names

    history_with_demo_response = client.get("/api/logs/creation-history?include_demo=true", headers=member_headers)
    assert history_with_demo_response.status_code == 200
    history_names = {item["project_name"] for item in history_with_demo_response.json()["items"]}
    assert "AI-OCR請求書処理" in history_names


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
