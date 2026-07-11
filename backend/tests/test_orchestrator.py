from fastapi.testclient import TestClient


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


def _create_project(client: TestClient, headers: dict[str, str]) -> int:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "customer_name": "株式会社サンプル",
            "project_name": "Webリニューアル案件",
            "summary": "問い合わせ増加、SEO改善、CMS更新性改善を目的としたWebサイトリニューアル。予算300万円、納期3か月。",
            "win_probability": 70,
            "next_action": "提案書と見積を作成し、上司レビューへ進める。",
        },
    )
    assert response.status_code == 200
    lifecycle = response.json()["lifecycle"]
    assert "orchestrator" in lifecycle
    return int(lifecycle["project"]["id"])


def test_project_creation_generates_and_runs_queue(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "orchestrator-member@example.com", "member")
    project_id = _create_project(client, member_headers)

    queue_response = client.get("/api/orchestrator/queue", headers=admin_headers)
    status_response = client.get(f"/api/orchestrator/projects/{project_id}/status", headers=member_headers)

    assert queue_response.status_code == 200
    queue = [item for item in queue_response.json()["queue"] if item["project_id"] == project_id]
    assert len(queue) >= 8
    assert any(item["action_type"] == "competitive_analysis" for item in queue)
    assert all(item["status"] == "success" for item in queue)

    assert status_response.status_code == 200
    status = status_response.json()["orchestrator"]
    assert status["counts"]["success"] >= 8


def test_queue_monitor_requires_manager_or_admin(client: TestClient, admin_headers: dict[str, str]) -> None:
    viewer_headers = _create_user_and_login(client, admin_headers, "orchestrator-viewer@example.com", "viewer")

    response = client.get("/api/orchestrator/queue", headers=viewer_headers)

    assert response.status_code == 403


def test_retry_failed_action(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "orchestrator-retry@example.com", "member")
    project_id = _create_project(client, member_headers)

    from app.db import get_db

    with get_db() as db:
        row = db.execute("SELECT id FROM action_queue WHERE project_id = ? LIMIT 1", (project_id,)).fetchone()
        assert row
        action_id = int(row["id"])
        db.execute("UPDATE action_queue SET status = 'failure', retry_count = 0, error_type = 'test_error' WHERE id = ?", (action_id,))

    retry_response = client.post(f"/api/orchestrator/actions/{action_id}/retry", headers=admin_headers)

    assert retry_response.status_code == 200
    action = retry_response.json()["action"]
    assert action["status"] == "pending"
    assert action["retry_count"] == 1


def test_orchestrator_analytics_in_product_dashboard(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "orchestrator-analytics@example.com", "member")
    _create_project(client, member_headers)

    analytics_response = client.get("/api/orchestrator/analytics", headers=admin_headers)
    dashboard_response = client.get("/api/analytics/dashboard", headers=admin_headers)

    assert analytics_response.status_code == 200
    analytics = analytics_response.json()["orchestrator"]
    assert analytics["total_actions"] >= 8
    assert "autonomous_completion_rate" in analytics

    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()["dashboard"]
    assert "orchestrator" in dashboard
    assert dashboard["orchestrator"]["total_actions"] >= 8
