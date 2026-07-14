from fastapi.testclient import TestClient


def _login(client: TestClient, email: str, password: str = "test-password") -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _create_member(client: TestClient, admin_headers: dict[str, str], email: str) -> tuple[int, dict[str, str]]:
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": email, "password": "test-password", "role": "member"},
    )
    assert response.status_code == 200
    user_id = int(response.json()["user"]["id"])
    return user_id, _login(client, email)


def _create_project(client: TestClient, headers: dict[str, str], name: str) -> int:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "customer_name": "Workspace Test Customer",
            "project_name": name,
            "summary": "Workspace separation test project.",
            "win_probability": 70,
            "next_action": "Confirm scope.",
        },
    )
    assert response.status_code == 200
    return int(response.json()["lifecycle"]["project"]["id"])


def test_workspace_context_switch_and_project_separation(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_id, member_headers = _create_member(client, admin_headers, "workspace-member@example.com")

    org_response = client.post("/api/organizations", headers=admin_headers, json={"name": "株式会社BBB", "slug": "bbb"})
    assert org_response.status_code == 200
    organization_id = int(org_response.json()["organization"]["id"])

    workspace_response = client.post(
        f"/api/organizations/{organization_id}/workspaces",
        headers=admin_headers,
        json={"name": "制作", "slug": "production"},
    )
    assert workspace_response.status_code == 200
    workspace_id = int(workspace_response.json()["workspace"]["id"])

    membership = client.post(
        "/api/organizations/memberships",
        headers=admin_headers,
        json={
            "user_id": member_id,
            "organization_id": organization_id,
            "workspace_id": workspace_id,
            "membership_role": "member",
        },
    )
    assert membership.status_code == 200

    default_project_id = _create_project(client, member_headers, "Default Workspace Project")
    switch_response = client.patch(
        "/api/organizations/context",
        headers=member_headers,
        json={"organization_id": organization_id, "workspace_id": workspace_id},
    )
    assert switch_response.status_code == 200
    assert switch_response.json()["current"]["organization_id"] == organization_id

    other_project_id = _create_project(client, member_headers, "Other Workspace Project")
    crm_response = client.get("/api/projects/crm", headers=member_headers)
    assert crm_response.status_code == 200
    project_ids = {int(project["id"]) for project in crm_response.json()["projects"]}
    assert other_project_id in project_ids
    assert default_project_id not in project_ids


def test_member_cannot_switch_to_unassigned_organization(client: TestClient, admin_headers: dict[str, str]) -> None:
    _, member_headers = _create_member(client, admin_headers, "workspace-denied@example.com")
    org_response = client.post("/api/organizations", headers=admin_headers, json={"name": "株式会社CCC", "slug": "ccc"})
    assert org_response.status_code == 200
    organization_id = int(org_response.json()["organization"]["id"])

    context_response = client.patch(
        "/api/organizations/context",
        headers=member_headers,
        json={"organization_id": organization_id, "workspace_id": 1},
    )

    assert context_response.status_code in {403, 404}


def test_analytics_dashboard_has_organization_workspace_breakdown(client: TestClient, admin_headers: dict[str, str]) -> None:
    first = client.post(
        "/api/analytics/events",
        headers=admin_headers,
        json={"session_id": "org-session-1", "event_name": "proposal_generated", "feature_name": "proposal", "status": "success"},
    )
    assert first.status_code == 200

    org_response = client.post("/api/organizations", headers=admin_headers, json={"name": "Analytics Org", "slug": "analytics-org"})
    assert org_response.status_code == 200
    organization_id = int(org_response.json()["organization"]["id"])
    context = client.get("/api/organizations/context", headers=admin_headers)
    workspace_id = next(item["workspace_id"] for item in context.json()["available"] if item["organization_id"] == organization_id)
    switched = client.patch(
        "/api/organizations/context",
        headers=admin_headers,
        json={"organization_id": organization_id, "workspace_id": workspace_id},
    )
    assert switched.status_code == 200

    second = client.post(
        "/api/analytics/events",
        headers=admin_headers,
        json={"session_id": "org-session-2", "event_name": "summary_ppt_download", "feature_name": "summary_ppt", "status": "success"},
    )
    assert second.status_code == 200

    dashboard = client.get("/api/analytics/dashboard?scope=system", headers=admin_headers)
    assert dashboard.status_code == 200
    breakdown = dashboard.json()["dashboard"]["organization_workspace"]
    assert any(item["organization_id"] == 1 for item in breakdown["organizations"])
    assert any(item["organization_id"] == organization_id for item in breakdown["organizations"])
