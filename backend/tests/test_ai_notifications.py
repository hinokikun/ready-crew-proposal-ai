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


def _create_project(client: TestClient, headers: dict[str, str], name: str, win_probability: int = 25) -> int:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "customer_name": "株式会社通知テスト",
            "project_name": name,
            "summary": "期限とレビュー確認が必要なWeb提案案件。",
            "win_probability": win_probability,
            "next_action": "今日中に提案提出期限と上司レビューを確認する。",
        },
    )
    assert response.status_code == 200
    return int(response.json()["lifecycle"]["project"]["id"])


def test_ai_watch_generates_notifications_with_priority(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "notify-member@example.com", "member")
    project_id = _create_project(client, member_headers, "レビュー停滞案件", 25)
    review_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": str(project_id), "project_name": "レビュー停滞案件"},
    )
    assert review_response.status_code == 200

    from app.db import get_db

    with get_db() as db:
        db.execute("UPDATE projects SET status = 'レビュー中', updated_at = DATETIME('now', '-4 days') WHERE id = ?", (project_id,))
        db.execute(
            "UPDATE proposal_reviews SET review_requested_at = DATETIME('now', '-4 days'), updated_at = DATETIME('now', '-4 days') WHERE project_id = ?",
            (str(project_id),),
        )

    response = client.get("/api/notifications", headers=member_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["total"] >= 1
    assert body["summary"]["high"] >= 1
    assert any(item["priority"] == "高" for item in body["notifications"])
    assert any("レビュー" in item["title"] or "提出前確認" in item["title"] for item in body["notifications"])


def test_notification_read_actioned_and_archive(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "notify-actions@example.com", "member")
    project_id = _create_project(client, member_headers, "通知操作案件", 20)

    from app.db import get_db

    with get_db() as db:
        db.execute("UPDATE projects SET status = '提案中', updated_at = DATETIME('now', '-4 days') WHERE id = ?", (project_id,))

    list_response = client.get("/api/notifications", headers=member_headers)
    notification_id = list_response.json()["notifications"][0]["id"]

    read_response = client.patch(f"/api/notifications/{notification_id}/read", headers=member_headers)
    actioned_response = client.patch(f"/api/notifications/{notification_id}/actioned", headers=member_headers)
    archive_response = client.patch(f"/api/notifications/{notification_id}/archive", headers=member_headers)

    assert read_response.status_code == 200
    assert read_response.json()["notification"]["status"] == "read"
    assert actioned_response.status_code == 200
    assert actioned_response.json()["notification"]["actioned_at"]
    assert archive_response.status_code == 200
    assert archive_response.json()["notification"]["status"] == "archived"


def test_notification_analytics_are_in_product_dashboard(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "notify-analytics@example.com", "member")
    project_id = _create_project(client, member_headers, "通知Analytics案件", 15)

    from app.db import get_db

    with get_db() as db:
        db.execute("UPDATE projects SET status = '提案中', updated_at = DATETIME('now', '-4 days') WHERE id = ?", (project_id,))

    list_response = client.get("/api/notifications", headers=member_headers)
    notification_id = list_response.json()["notifications"][0]["id"]
    client.patch(f"/api/notifications/{notification_id}/read", headers=member_headers)
    client.patch(f"/api/notifications/{notification_id}/actioned", headers=member_headers)

    dashboard_response = client.get("/api/analytics/dashboard", headers=admin_headers)

    assert dashboard_response.status_code == 200
    notification_center = dashboard_response.json()["dashboard"]["notification_center"]
    assert notification_center["total"] >= 1
    assert notification_center["read_rate"] >= 0
    assert notification_center["action_rate"] >= 0
    assert notification_center["ignored_rate"] >= 0
