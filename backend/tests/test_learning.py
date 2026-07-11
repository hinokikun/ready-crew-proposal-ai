import json

from fastapi.testclient import TestClient


def _seed_learning_signals() -> None:
    from app.db import get_db

    with get_db() as db:
        db.execute(
            "INSERT INTO proposal_reviews (project_id, project_name, status, review_comment) VALUES (?, ?, ?, ?)",
            ("learning-project-1", "匿名案件", "changes_requested", "競合比較と費用対効果の説明を強めてください。secret-token=should-not-save"),
        )
        db.execute(
            """
            INSERT INTO proposal_review_revisions
            (review_id, project_id, previous_status, next_status, review_comment, ai_improvement_policy, diff_summary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (1, "learning-project-1", "changes_requested", "review_requested", "ROI説明を追加", "ROI説明を強化", "費用対効果を追加"),
        )
        db.execute(
            "INSERT INTO quality_gates (project_id, checklist_items, completed, bypassed, bypass_reason) VALUES (?, ?, ?, ?, ?)",
            ("learning-project-1", "[]", 0, 1, "納期確認が未完了"),
        )
        db.execute(
            "INSERT INTO project_outcomes (project_id, outcome, lost_reason, note) VALUES (?, ?, ?, ?)",
            (1, "lost", "competitor", "匿名化済み"),
        )
        db.execute(
            """
            INSERT INTO proposal_knowledge
            (industry, project_summary, rating, evaluation_status, quality_score, confidential_risk, approval_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            ("Web", "匿名要約のみ", 3, "needs_improvement", 55, "low", "approved"),
        )
        db.execute(
            """
            INSERT INTO ai_notifications
            (notification_key, agent_name, priority, title, message, recommended_action, source_type, source_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("learning-notification-1", "AI営業", "高", "匿名通知", "レビュー待ち", "レビュー確認", "review", "1", "unread"),
        )
        db.execute(
            "INSERT INTO action_queue (project_id, action_type, agent, status, priority, retry_count) VALUES (?, ?, ?, ?, ?, ?)",
            (1, "director_review", "AIディレクター", "success", 70, 1),
        )


def test_learning_run_generates_prompt_workflow_simulation_and_release_candidate(client: TestClient, admin_headers: dict[str, str]) -> None:
    _seed_learning_signals()

    response = client.post("/api/learning/run", headers=admin_headers)

    assert response.status_code == 200
    dashboard = response.json()["dashboard"]
    assert dashboard["run"]["analyzed_items_count"] > 0
    assert dashboard["improvements"]
    assert any(item["improvement_type"] == "prompt" for item in dashboard["improvements"])
    assert any(item["improvement_type"] == "workflow" for item in dashboard["improvements"])
    assert any(item["simulation"] for item in dashboard["improvements"])
    assert dashboard["release_candidate"]["version"] == "13.6候補"
    saved = json.dumps(dashboard, ensure_ascii=False)
    assert "should-not-save" not in saved


def test_learning_dashboard_and_analytics(client: TestClient, admin_headers: dict[str, str]) -> None:
    _seed_learning_signals()
    client.post("/api/learning/run", headers=admin_headers)

    dashboard_response = client.get("/api/learning/dashboard", headers=admin_headers)
    analytics_response = client.get("/api/analytics/dashboard", headers=admin_headers)

    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()["dashboard"]
    assert dashboard["analytics"]["learning_runs"] >= 1
    assert dashboard["analytics"]["prompt_improvements"] >= 1
    assert dashboard["analytics"]["workflow_improvements"] >= 1

    assert analytics_response.status_code == 200
    assert "learning" in analytics_response.json()["dashboard"]


def test_learning_improvement_status_update(client: TestClient, admin_headers: dict[str, str]) -> None:
    _seed_learning_signals()
    run_response = client.post("/api/learning/run", headers=admin_headers)
    improvement_id = run_response.json()["dashboard"]["improvements"][0]["id"]

    update_response = client.patch(
        f"/api/learning/improvements/{improvement_id}/status",
        headers=admin_headers,
        json={"status": "adopted"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["improvement"]["status"] == "adopted"


def test_learning_requires_admin_or_manager(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "learning-viewer@example.com", "password": "test-password", "role": "viewer"},
    )
    assert create_response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": "learning-viewer@example.com", "password": "test-password"})
    viewer_headers = {"Authorization": f"Bearer {login_response.json()['token']}"}

    response = client.post("/api/learning/run", headers=viewer_headers)

    assert response.status_code == 403
