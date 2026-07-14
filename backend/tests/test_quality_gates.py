from fastapi.testclient import TestClient


CHECKLIST_ITEMS = [
    "Company name checked",
    "Estimate conditions checked",
    "Schedule checked",
    "AI inferred items checked",
    "Case study notation checked",
    "Legal conditions checked",
    "Supervisor review checked",
    "Human final review checked",
]


def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": email, "password": "test-password", "role": role},
    )
    assert response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": email, "password": "test-password"})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def test_quality_gate_can_be_fetched_before_creation(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.get("/api/quality-gates/project-quality-empty", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["gate"] is None


def test_member_can_complete_quality_gate(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "quality-member@example.com", "member")

    response = client.patch(
        "/api/quality-gates/project-quality-complete/complete",
        headers=member_headers,
        json={"checklist_items": CHECKLIST_ITEMS},
    )

    assert response.status_code == 200
    gate = response.json()["gate"]
    assert gate["completed"] is True
    assert gate["bypassed"] is False
    assert gate["download_unlocked"] is True
    assert len(gate["checklist_items"]) == len(CHECKLIST_ITEMS)


def test_viewer_cannot_complete_quality_gate(client: TestClient, admin_headers: dict[str, str]) -> None:
    viewer_headers = _create_user_and_login(client, admin_headers, "quality-viewer@example.com", "viewer")

    response = client.patch(
        "/api/quality-gates/project-quality-viewer/complete",
        headers=viewer_headers,
        json={"checklist_items": CHECKLIST_ITEMS},
    )

    assert response.status_code == 403


def test_incomplete_quality_gate_keeps_download_locked(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "quality-start@example.com", "member")

    response = client.post(
        "/api/quality-gates/project-quality-start",
        headers=member_headers,
        json={"checklist_items": CHECKLIST_ITEMS[:2]},
    )

    assert response.status_code == 200
    gate = response.json()["gate"]
    assert gate["completed"] is False
    assert gate["bypassed"] is False
    assert gate["download_unlocked"] is False


def test_admin_can_bypass_quality_gate_with_reason(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.patch(
        "/api/quality-gates/project-quality-bypass/bypass",
        headers=admin_headers,
        json={"bypass_reason": "urgent internal review"},
    )

    assert response.status_code == 200
    gate = response.json()["gate"]
    assert gate["bypassed"] is True
    assert gate["download_unlocked"] is True
    assert gate["bypass_reason"] == "urgent internal review"


def test_admin_bypass_requires_reason(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.patch(
        "/api/quality-gates/project-quality-bypass-empty/bypass",
        headers=admin_headers,
        json={"bypass_reason": ""},
    )

    assert response.status_code in {400, 422}


def test_quality_gate_audit_log_is_recorded(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "quality-audit@example.com", "member")
    client.post(
        "/api/quality-gates/project-quality-audit",
        headers=member_headers,
        json={"checklist_items": CHECKLIST_ITEMS[:1]},
    )
    client.patch(
        "/api/quality-gates/project-quality-audit/complete",
        headers=member_headers,
        json={"checklist_items": CHECKLIST_ITEMS},
    )
    client.patch(
        "/api/quality-gates/project-quality-audit-bypass/bypass",
        headers=admin_headers,
        json={"bypass_reason": "admin emergency"},
    )

    audit_response = client.get("/api/logs/audit", headers=admin_headers)

    assert audit_response.status_code == 200
    event_types = {item["event_type"] for item in audit_response.json()["logs"]}
    assert "quality_gate_start" in event_types
    assert "quality_gate_complete" in event_types
    assert "quality_gate_bypass" in event_types
    assert "quality_gate_bypass_reason" in event_types


def test_quality_gate_is_separated_by_workspace(client: TestClient, admin_headers: dict[str, str]) -> None:
    project_id = "same-external-project"
    first = client.patch(
        f"/api/quality-gates/{project_id}/complete",
        headers=admin_headers,
        json={"checklist_items": CHECKLIST_ITEMS},
    )
    assert first.status_code == 200
    assert first.json()["gate"]["download_unlocked"] is True

    org_response = client.post("/api/organizations", headers=admin_headers, json={"name": "Quality Org", "slug": "quality-org"})
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

    empty = client.get(f"/api/quality-gates/{project_id}", headers=admin_headers)
    assert empty.status_code == 200
    assert empty.json()["gate"] is None

    second = client.patch(
        f"/api/quality-gates/{project_id}/complete",
        headers=admin_headers,
        json={"checklist_items": CHECKLIST_ITEMS[:4]},
    )
    assert second.status_code == 200
    assert second.json()["gate"]["download_unlocked"] is True
