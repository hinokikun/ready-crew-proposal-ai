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


def _create_project(client: TestClient, headers: dict[str, str], name: str = "Webサイトリニューアル案件") -> int:
    response = client.post(
        "/api/projects",
        headers=headers,
        json={
            "customer_name": "株式会社サンプル不動産",
            "project_name": name,
            "summary": "問い合わせ増加とCMS更新性改善を目的としたWebサイトリニューアル。",
            "win_probability": 65,
            "next_action": "ヒアリングで予算、納期、決裁者を確認する。",
        },
    )
    assert response.status_code == 200
    return int(response.json()["lifecycle"]["project"]["id"])


def test_member_can_create_project_and_change_status(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "project-member@example.com", "member")
    project_id = _create_project(client, member_headers)

    status_response = client.patch(
        f"/api/projects/{project_id}/status",
        headers=member_headers,
        json={"status": "提案中", "note": "提案書の初稿を作成中。"},
    )
    detail_response = client.get(f"/api/projects/{project_id}/lifecycle", headers=member_headers)

    assert status_response.status_code == 200
    assert status_response.json()["lifecycle"]["project"]["status"] == "提案中"
    assert detail_response.status_code == 200
    assert any(event["event_type"] == "status_changed" for event in detail_response.json()["lifecycle"]["timeline"])


def test_project_won_lost_and_handoff_flow(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "project-flow@example.com", "member")
    won_project_id = _create_project(client, member_headers, "Webサイトリニューアル受注案件")

    won_response = client.post(
        f"/api/projects/{won_project_id}/outcome",
        headers=member_headers,
        json={"outcome": "won", "lost_reason": "", "note": "条件合意により受注。"},
    )
    handoff_response = client.post(
        f"/api/projects/{won_project_id}/handoff",
        headers=member_headers,
        json={
            "proposal_summary": "問い合わせ導線とCMS運用を改善する提案。",
            "cautions": "公開前にフォーム通知先を確認する。",
            "deadline": "2026年9月末",
            "owner": "営業 山田",
            "special_functions": "物件検索",
            "cms": "WordPress",
        },
    )

    lost_project_id = _create_project(client, member_headers, "Webサイトリニューアル失注案件")
    lost_response = client.post(
        f"/api/projects/{lost_project_id}/outcome",
        headers=member_headers,
        json={"outcome": "lost", "lost_reason": "price", "note": "価格差により失注。"},
    )

    assert won_response.status_code == 200
    assert won_response.json()["lifecycle"]["project"]["status"] == "受注"
    assert handoff_response.status_code == 200
    assert "制作チーム向け引継ぎ" in handoff_response.json()["lifecycle"]["handoff"]["handoff_text"]
    assert lost_response.status_code == 200
    assert lost_response.json()["lifecycle"]["outcome"]["lost_reason"] == "price"


def test_project_completion_creates_retrospective_and_knowledge_candidate(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "project-complete@example.com", "member")
    project_id = _create_project(client, member_headers)
    client.post(f"/api/projects/{project_id}/outcome", headers=member_headers, json={"outcome": "won"})

    complete_response = client.post(
        f"/api/projects/{project_id}/complete",
        headers=member_headers,
        json={
            "success_factors": "早期に問い合わせ導線とCMS要件を整理できた。",
            "improvements": "競合比較を初回提案前に深める。",
            "next_learnings": "不動産案件では物件検索とCTAを早めに確認する。",
        },
    )

    assert complete_response.status_code == 200
    lifecycle = complete_response.json()["lifecycle"]
    assert lifecycle["project"]["status"] == "完了"
    assert lifecycle["retrospective"]["knowledge_candidate_id"]
    assert lifecycle["retrospective"]["success_factors"]


def test_project_lifecycle_analytics_and_permissions(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "project-analytics-member@example.com", "member")
    viewer_headers = _create_user_and_login(client, admin_headers, "project-viewer@example.com", "viewer")
    project_id = _create_project(client, member_headers)
    client.patch(f"/api/projects/{project_id}/status", headers=member_headers, json={"status": "レビュー中", "note": "上司レビュー中。"})
    client.post(f"/api/projects/{project_id}/outcome", headers=member_headers, json={"outcome": "lost", "lost_reason": "competitor"})

    analytics_response = client.get("/api/projects/lifecycle/analytics", headers=admin_headers)
    dashboard_response = client.get("/api/analytics/dashboard", headers=admin_headers)
    viewer_status_response = client.patch(
        f"/api/projects/{project_id}/status",
        headers=viewer_headers,
        json={"status": "受注", "note": "viewer cannot update"},
    )

    assert analytics_response.status_code == 200
    analytics = analytics_response.json()["lifecycle_analytics"]
    assert analytics["total_projects"] >= 1
    assert analytics["lost_reasons"]
    assert dashboard_response.status_code == 200
    assert "project_lifecycle" in dashboard_response.json()["dashboard"]
    assert viewer_status_response.status_code == 403
