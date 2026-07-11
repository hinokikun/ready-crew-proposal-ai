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


def test_product_analytics_dashboard_release_notes_and_permissions(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "analytics-member@example.com", "member")

    events = [
        ("login", "auth", "success", 0, ""),
        ("case_paste", "proposal", "success", 100, ""),
        ("ai_analysis_start", "proposal", "start", 0, ""),
        ("ai_analysis_complete", "proposal", "success", 1200, ""),
        ("proposal_generated", "proposal", "success", 3000, ""),
        ("summary_ppt_download", "summary_ppt", "success", 900, ""),
        ("detail_ppt_download", "detail_ppt", "success", 1100, ""),
        ("estimate_pdf_download", "estimate_pdf", "failure", 600, "pdf_generation_failed"),
    ]
    for event_name, feature_name, status, duration_ms, error_type in events:
        response = client.post(
            "/api/analytics/events",
            headers=member_headers,
            json={
                "session_id": "test-session-analytics-001",
                "event_name": event_name,
                "feature_name": feature_name,
                "status": status,
                "duration_ms": duration_ms,
                "error_type": error_type,
                "metadata": {"source": "pytest", "unsafe_customer_name": "not-saved"},
            },
        )
        assert response.status_code == 200

    dashboard_response = client.get("/api/analytics/dashboard", headers=admin_headers)
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()["dashboard"]
    assert dashboard["summary"]["total_sessions"] >= 1
    assert any(step["step"] == "proposal_generated" for step in dashboard["funnel"])
    assert dashboard["feature_usage"]
    assert dashboard["sessions"]
    assert dashboard["errors"]
    assert dashboard["improvement_candidates"]

    error_id = dashboard["errors"][0]["id"]
    resolved_response = client.patch(
        f"/api/analytics/errors/{error_id}",
        headers=admin_headers,
        json={"resolved": True},
    )
    assert resolved_response.status_code == 200
    assert resolved_response.json()["error"]["resolved"] is True

    note_response = client.post(
        "/api/analytics/release-notes",
        headers=admin_headers,
        json={
            "version": "7.0",
            "release_date": "2026-07-10",
            "title": "Product Analytics",
            "improvements": "Added funnel, session, error, and feature usage analytics.",
        },
    )
    assert note_response.status_code == 200
    assert note_response.json()["release_note"]["version"] == "7.0"

    notes_response = client.get("/api/analytics/release-notes", headers=admin_headers)
    assert notes_response.status_code == 200
    assert notes_response.json()["release_notes"]

    assert client.get("/api/analytics/dashboard", headers=member_headers).status_code == 403
    assert client.get("/api/analytics/release-notes", headers=member_headers).status_code == 403
