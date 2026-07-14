from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    password = "test-password"
    response = client.post("/api/users", headers=admin_headers, json={"email": email, "password": password, "role": role})
    assert response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def _review_payload(sample_pptx_payload: dict[str, Any], project_id: str) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "project_name": "Optimization Test",
        "beautiful_ai_presentation_id": "beautiful-optimization-test",
        "powerpoint_generation_data": sample_pptx_payload["powerpoint_generation_data"],
    }


def _seed_review(client: TestClient, headers: dict[str, str], sample_pptx_payload: dict[str, Any], project_id: str) -> dict[str, Any]:
    response = client.post("/api/presentation-review/reviews", headers=headers, json=_review_payload(sample_pptx_payload, project_id))
    assert response.status_code == 200
    return response.json()["review"]


def test_member_can_run_and_adopt_optimization(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "optimization-member@example.com", "member")
    project_id = "optimization-project"
    _seed_review(client, member_headers, sample_pptx_payload, project_id)

    run = client.post("/api/proposal-optimization/run", headers=member_headers, json={"project_id": project_id})
    assert run.status_code == 200
    body = run.json()
    assert body["recommendations"]
    item = body["recommendations"][0]
    assert item["expected_improvement"] > 0
    assert item["simulation"]["is_estimated"] is True
    assert item["is_estimate"] is True
    assert item["sample_size"] >= 1
    assert item["evidence_type"] in {"workspace_history", "presentation_review", "ai_estimate", "insufficient_data"}
    assert item["calculation_method"] == "weighted_score_v20_1"
    assert item["requires_human_review"] is True
    assert "api_key" not in str(body).lower()

    adopted = client.patch(f"/api/proposal-optimization/backlog/{item['id']}/status", headers=member_headers, json={"status": "selected"})
    assert adopted.status_code == 200
    assert adopted.json()["item"]["status"] == "selected"

    approve_via_status = client.patch(f"/api/proposal-optimization/backlog/{item['id']}/status", headers=member_headers, json={"status": "approved"})
    assert approve_via_status.status_code == 403

    invalid_transition = client.patch(f"/api/proposal-optimization/backlog/{item['id']}/status", headers=member_headers, json={"status": "measured"})
    assert invalid_transition.status_code == 403


def test_manager_can_approve_and_view_dashboard(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    manager_headers = _create_user_and_login(client, admin_headers, "optimization-manager@example.com", "manager")
    project_id = "optimization-approval-project"
    _seed_review(client, admin_headers, sample_pptx_payload, project_id)
    run = client.post("/api/proposal-optimization/run", headers=admin_headers, json={"project_id": project_id})
    assert run.status_code == 200
    item_id = run.json()["recommendations"][0]["id"]

    approved = client.patch(f"/api/proposal-optimization/backlog/{item_id}/approve", headers=manager_headers)
    assert approved.status_code == 200
    assert approved.json()["item"]["status"] == "approved"

    measured = client.patch(
        f"/api/proposal-optimization/backlog/{item_id}/measurement",
        headers=manager_headers,
        json={
            "measurement_status": "measured",
            "measurement_period": "pilot-week-1",
            "outcome_type": "review",
            "measured_effect": {"review_count_delta": -1, "sample_size": 3, "note": "safe aggregate only"},
        },
    )
    assert measured.status_code == 200
    assert measured.json()["item"]["measurement_status"] == "measured"
    assert measured.json()["item"]["status"] == "measured"

    dashboard = client.get("/api/proposal-optimization/dashboard", headers=manager_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["dashboard"]["backlog_count"] >= 1
    assert "insufficient_sample_count" in dashboard.json()["dashboard"]


def test_viewer_cannot_update_optimization(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    viewer_headers = _create_user_and_login(client, admin_headers, "optimization-viewer@example.com", "viewer")
    project_id = "optimization-viewer-project"
    _seed_review(client, admin_headers, sample_pptx_payload, project_id)
    run = client.post("/api/proposal-optimization/run", headers=admin_headers, json={"project_id": project_id})
    assert run.status_code == 200
    item_id = run.json()["recommendations"][0]["id"]

    read = client.get(f"/api/proposal-optimization/recommendations?project_id={project_id}", headers=viewer_headers)
    assert read.status_code == 200
    update = client.patch(f"/api/proposal-optimization/backlog/{item_id}/status", headers=viewer_headers, json={"status": "adopted"})
    assert update.status_code == 403


def test_optimization_is_workspace_isolated(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    project_id = "optimization-isolated-project"
    _seed_review(client, admin_headers, sample_pptx_payload, project_id)
    run = client.post("/api/proposal-optimization/run", headers=admin_headers, json={"project_id": project_id})
    assert run.status_code == 200
    assert run.json()["recommendations"]

    org_response = client.post("/api/organizations", headers=admin_headers, json={"name": "Optimization Org", "slug": "optimization-org"})
    assert org_response.status_code == 200
    organization_id = int(org_response.json()["organization"]["id"])
    context = client.get("/api/organizations/context", headers=admin_headers)
    workspace_id = next(item["workspace_id"] for item in context.json()["available"] if item["organization_id"] == organization_id)
    switch_response = client.patch(
        "/api/organizations/context",
        headers=admin_headers,
        json={"organization_id": organization_id, "workspace_id": workspace_id},
    )
    assert switch_response.status_code == 200

    separated = client.get(f"/api/proposal-optimization/recommendations?project_id={project_id}", headers=admin_headers)
    assert separated.status_code == 200
    assert separated.json()["recommendations"] == []


def test_best_practices_are_summary_only(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    project_id = "optimization-best-practice"
    review = _seed_review(client, admin_headers, sample_pptx_payload, project_id)
    revision = client.post(
        "/api/presentation-review/revisions",
        headers=admin_headers,
        json={"review_id": review["id"], "selected_actions": review["actions"][:1]},
    )
    assert revision.status_code == 200
    revision_id = revision.json()["revision"]["id"]
    approved = client.patch(f"/api/presentation-review/revisions/{revision_id}/approve", headers=admin_headers)
    assert approved.status_code == 200
    from app import db as db_module

    with db_module.get_db() as db:
        db.execute("UPDATE presentation_revisions SET status = 'generated' WHERE id = ?", (revision_id,))
    extracted = client.post("/api/proposal-optimization/best-practices/extract", headers=admin_headers)
    assert extracted.status_code == 200
    assert "password" not in str(extracted.json()).lower()


def test_best_practice_requires_manager_approval(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    manager_headers = _create_user_and_login(client, admin_headers, "optimization-bp-manager@example.com", "manager")
    member_headers = _create_user_and_login(client, admin_headers, "optimization-bp-member@example.com", "member")
    project_id = "optimization-best-practice-approval"
    review = _seed_review(client, admin_headers, sample_pptx_payload, project_id)
    revision = client.post(
        "/api/presentation-review/revisions",
        headers=admin_headers,
        json={"review_id": review["id"], "selected_actions": review["actions"][:1]},
    )
    assert revision.status_code == 200
    revision_id = revision.json()["revision"]["id"]
    approved = client.patch(f"/api/presentation-review/revisions/{revision_id}/approve", headers=admin_headers)
    assert approved.status_code == 200
    from app import db as db_module

    with db_module.get_db() as db:
        db.execute("UPDATE presentation_revisions SET status = 'generated' WHERE id = ?", (revision_id,))
    extract = client.post("/api/proposal-optimization/best-practices/extract", headers=admin_headers)
    assert extract.status_code == 200
    if not extract.json()["best_practices"]:
        return
    best_practice_id = extract.json()["best_practices"][0]["id"]

    member_list = client.get("/api/proposal-optimization/best-practices", headers=member_headers)
    assert member_list.status_code == 200
    assert member_list.json()["best_practices"] == []

    member_approve = client.patch(
        f"/api/proposal-optimization/best-practices/{best_practice_id}/status",
        headers=member_headers,
        json={"status": "approved", "reason": "member cannot approve"},
    )
    assert member_approve.status_code == 403

    manager_approve = client.patch(
        f"/api/proposal-optimization/best-practices/{best_practice_id}/status",
        headers=manager_headers,
        json={"status": "approved", "reason": "safe reusable pattern"},
    )
    assert manager_approve.status_code == 200
    assert manager_approve.json()["best_practice"]["status"] == "approved"

    member_list_after = client.get("/api/proposal-optimization/best-practices", headers=member_headers)
    assert member_list_after.status_code == 200
    assert member_list_after.json()["best_practices"]
