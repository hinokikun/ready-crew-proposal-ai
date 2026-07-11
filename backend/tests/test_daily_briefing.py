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


def _create_project(client: TestClient, headers: dict[str, str], name: str, win_probability: int = 60) -> int:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "customer_name": "株式会社ブリーフィング",
            "project_name": name,
            "summary": "今日提出予定のWebサイト提案案件。",
            "win_probability": win_probability,
            "next_action": "今日中に提案提出とレビュー確認を行う。",
        },
    )
    assert response.status_code == 200
    return int(response.json()["lifecycle"]["project"]["id"])


def test_daily_briefing_generates_review_waiting_and_priorities(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "briefing-member@example.com", "member")
    project_id = _create_project(client, member_headers, "レビュー待ち提案案件", 80)
    review_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": str(project_id), "project_name": "レビュー待ち提案案件"},
    )
    assert review_response.status_code == 200

    response = client.get("/api/briefing/today", headers=member_headers)

    assert response.status_code == 200
    briefing = response.json()["briefing"]
    assert briefing["summary"]["review_waiting"] >= 1
    assert briefing["suggestions"]
    assert briefing["suggestions"][0]["priority"] in {"高", "中", "低"}
    assert briefing["recommended_project"]


def test_daily_briefing_detects_stagnant_projects(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "briefing-stagnant@example.com", "member")
    project_id = _create_project(client, member_headers, "停滞案件", 45)

    from app.db import get_db

    with get_db() as db:
        db.execute("UPDATE projects SET status = '提案中', updated_at = DATETIME('now', '-3 days') WHERE id = ?", (project_id,))

    response = client.get("/api/briefing/today", headers=member_headers)

    assert response.status_code == 200
    briefing = response.json()["briefing"]
    assert briefing["summary"]["stagnant"] >= 1
    assert any("2日以上" in item["reason"] for item in briefing["suggestions"])


def test_daily_briefing_event_analytics_are_saved(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "briefing-analytics@example.com", "member")
    project_id = _create_project(client, member_headers, "朝会Analytics案件", 70)

    viewed = client.post(
        "/api/briefing/events",
        headers=member_headers,
        json={"session_id": "daily-briefing-session-001", "event_type": "viewed", "project_id": project_id, "item_key": "view"},
    )
    clicked = client.post(
        "/api/briefing/events",
        headers=member_headers,
        json={"session_id": "daily-briefing-session-001", "event_type": "priority_clicked", "project_id": project_id, "item_key": "priority"},
    )
    completed = client.post(
        "/api/briefing/events",
        headers=member_headers,
        json={"session_id": "daily-briefing-session-001", "event_type": "item_completed", "project_id": project_id, "item_key": "priority"},
    )
    dashboard_response = client.get("/api/analytics/dashboard", headers=admin_headers)

    assert viewed.status_code == 200
    assert clicked.status_code == 200
    assert completed.status_code == 200
    assert dashboard_response.status_code == 200
    daily = dashboard_response.json()["dashboard"]["daily_briefing"]
    assert daily["views"] >= 1
    assert daily["priority_clicks"] >= 1
    assert daily["completed"] >= 1
    assert daily["completion_rate"] >= 0
