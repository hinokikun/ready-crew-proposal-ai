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


def test_knowledge_entries_search_templates_and_permissions(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "knowledge-member@example.com", "member")
    manager_headers = _create_user_and_login(client, admin_headers, "knowledge-manager@example.com", "manager")
    viewer_headers = _create_user_and_login(client, admin_headers, "knowledge-viewer@example.com", "viewer")

    create_response = client.post(
        "/api/knowledge/entries",
        headers=member_headers,
        json={
            "industry": "manufacturing",
            "company_size": "100-300",
            "project_summary": "Manufacturing website renewal for lead generation and SEO improvement.",
            "adopted_proposal": "Technical content, case studies, and inquiry route improvement.",
            "proposal_story": "Business understanding, issue整理, web strategy, KPI, production plan.",
            "adoption_reason": "Clear ROI and strong case-study story.",
            "lost_reason": "",
            "result": "Inquiry quality improved.",
            "owner_memo": "No customer body text is stored.",
            "outcome": "success",
            "rating": 5,
            "evaluation_status": "effective",
            "tags": "seo,case-study,cms",
        },
    )
    assert create_response.status_code == 200
    created_entry = create_response.json()["entry"]
    entry_id = created_entry["id"]
    assert created_entry["approval_status"] == "pending_review"
    assert created_entry["quality_score"] > 0

    list_response = client.get("/api/knowledge/entries", headers=admin_headers)
    assert list_response.status_code == 200
    assert list_response.json()["entries"]
    assert client.get("/api/knowledge/entries", headers=member_headers).status_code == 403

    search_before_approval = client.post(
        "/api/knowledge/search",
        headers=member_headers,
        json={
            "project_summary": "Manufacturing company wants SEO and website renewal.",
            "industry": "manufacturing",
            "limit": 3,
        },
    )
    assert search_before_approval.status_code == 200
    assert search_before_approval.json()["insights"]["matches"] == []

    approve_response = client.patch(
        f"/api/knowledge/entries/{entry_id}/status",
        headers=manager_headers,
        json={"approval_status": "approved"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["entry"]["approval_status"] == "approved"

    search_response = client.post(
        "/api/knowledge/search",
        headers=member_headers,
        json={
            "project_summary": "Manufacturing company wants SEO and website renewal.",
            "industry": "manufacturing",
            "limit": 3,
        },
    )
    assert search_response.status_code == 200
    insights = search_response.json()["insights"]
    assert insights["matches"]
    assert insights["recommendation"]

    assert client.post("/api/knowledge/search", headers=viewer_headers, json={"project_summary": "manufacturing renewal"}).status_code == 403
    assert client.patch(f"/api/knowledge/entries/{entry_id}/status", headers=viewer_headers, json={"approval_status": "rejected"}).status_code == 403

    evaluation_response = client.patch(
        f"/api/knowledge/entries/{entry_id}/evaluation",
        headers=admin_headers,
        json={"rating": 4, "evaluation_status": "effective"},
    )
    assert evaluation_response.status_code == 200
    assert evaluation_response.json()["entry"]["rating"] == 4

    sensitive_response = client.post(
        "/api/knowledge/entries",
        headers=admin_headers,
        json={
            "industry": "real_estate",
            "project_summary": "Real estate renewal summary for inquiry growth. Contact test@example.com and https://example.com",
            "adopted_proposal": "CTA and property search route improvement.",
            "proposal_story": "Current state, issue, strategy, KPI.",
            "outcome": "success",
            "rating": 5,
            "tags": "real-estate,cta",
        },
    )
    assert sensitive_response.status_code == 200
    sensitive_entry = sensitive_response.json()["entry"]
    assert sensitive_entry["approval_status"] == "pending_review"
    assert "email" in sensitive_entry["confidential_flags"]
    assert "url" in sensitive_entry["confidential_flags"]

    recalculated = client.post(
        f"/api/knowledge/entries/{sensitive_entry['id']}/quality/recalculate",
        headers=admin_headers,
    )
    assert recalculated.status_code == 200
    assert recalculated.json()["entry"]["confidential_risk"] in {"medium", "high"}

    template_response = client.post(
        "/api/knowledge/templates",
        headers=admin_headers,
        json={
            "category": "web",
            "title": "Web renewal proposal",
            "template_summary": "For renewal projects with SEO and CMS needs.",
            "structure": "Summary, current state, issues, web strategy, KPI, schedule, estimate.",
            "recommended_for": "Website renewal",
            "is_active": True,
        },
    )
    assert template_response.status_code == 200
    template_id = template_response.json()["template"]["id"]

    template_list = client.get("/api/knowledge/templates", headers=viewer_headers)
    assert template_list.status_code == 200
    assert template_list.json()["templates"]

    deactivate_response = client.patch(
        f"/api/knowledge/templates/{template_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["template"]["is_active"] is False

    best_practices = client.get("/api/knowledge/best-practices", headers=member_headers)
    assert best_practices.status_code == 200
    assert "best_practices" in best_practices.json()

    assert client.post("/api/knowledge/templates", headers=member_headers, json={"category": "web", "title": "x"}).status_code == 403
