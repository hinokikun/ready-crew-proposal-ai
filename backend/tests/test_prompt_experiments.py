from fastapi.testclient import TestClient


def _create_prompt(client: TestClient, headers: dict[str, str], name: str, version: str, status: str = "draft") -> dict:
    response = client.post(
        "/api/prompts/versions",
        headers=headers,
        json={
            "prompt_name": name,
            "version": version,
            "description": f"{name} {version}",
            "target_agent": "AI Sales",
            "prompt_template": "Summarize the case and propose the next best sales action.",
            "status": status,
        },
    )
    assert response.status_code == 200
    return response.json()["prompt_version"]


def _create_experiment(client: TestClient, headers: dict[str, str], name: str, ratio: int = 50) -> dict:
    response = client.post(
        "/api/prompts/experiments",
        headers=headers,
        json={
            "experiment_name": f"{name} test",
            "target_prompt": name,
            "control_version": "v1",
            "candidate_version": "v2",
            "traffic_ratio": ratio,
            "status": "testing",
            "start_at": "",
            "end_at": "",
        },
    )
    assert response.status_code == 200
    return response.json()["experiment"]


def test_prompt_version_create_status_and_rollback(client: TestClient, admin_headers: dict[str, str]) -> None:
    first = _create_prompt(client, admin_headers, "proposal_generation_test", "v1", "active")
    second = _create_prompt(client, admin_headers, "proposal_generation_test", "v2", "testing")

    update_response = client.patch(
        f"/api/prompts/versions/{second['id']}/status",
        headers=admin_headers,
        json={"status": "active"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["prompt_version"]["status"] == "active"

    rollback_response = client.post(
        "/api/prompts/rollback",
        headers=admin_headers,
        json={"prompt_name": "proposal_generation_test", "version": "v1"},
    )
    assert rollback_response.status_code == 200
    assert rollback_response.json()["prompt_version"]["id"] == first["id"]
    assert rollback_response.json()["prompt_version"]["status"] == "active"


def test_experiment_routing_respects_traffic_ratio(client: TestClient, admin_headers: dict[str, str]) -> None:
    _create_prompt(client, admin_headers, "routing_prompt", "v1", "active")
    _create_prompt(client, admin_headers, "routing_prompt", "v2", "testing")
    experiment = _create_experiment(client, admin_headers, "routing_prompt", ratio=100)

    route_response = client.post(
        "/api/prompts/route",
        headers=admin_headers,
        json={"prompt_name": "routing_prompt", "project_id": 1},
    )

    assert route_response.status_code == 200
    routing = route_response.json()["routing"]
    assert routing["experiment_id"] == experiment["id"]
    assert routing["version"] == "v2"


def test_prompt_metrics_winner_and_product_analytics(client: TestClient, admin_headers: dict[str, str]) -> None:
    _create_prompt(client, admin_headers, "winner_prompt", "v1", "active")
    _create_prompt(client, admin_headers, "winner_prompt", "v2", "testing")
    experiment = _create_experiment(client, admin_headers, "winner_prompt", ratio=50)

    for index in range(3):
        response = client.post(
            "/api/prompts/metrics",
            headers=admin_headers,
            json={
                "experiment_id": experiment["id"],
                "prompt_name": "winner_prompt",
                "prompt_version": "v1",
                "project_id": index + 1,
                "outcome": "lost",
                "review_count": 3,
                "quality_gate_passed": False,
                "proposal_time_seconds": 1800,
                "user_rating": "needs_revision",
            },
        )
        assert response.status_code == 200
        response = client.post(
            "/api/prompts/metrics",
            headers=admin_headers,
            json={
                "experiment_id": experiment["id"],
                "prompt_name": "winner_prompt",
                "prompt_version": "v2",
                "project_id": index + 11,
                "outcome": "won",
                "review_count": 1,
                "quality_gate_passed": True,
                "proposal_time_seconds": 900,
                "user_rating": "usable",
            },
        )
        assert response.status_code == 200

    judge_response = client.post(f"/api/prompts/experiments/{experiment['id']}/judge", headers=admin_headers)
    analytics_response = client.get("/api/analytics/dashboard", headers=admin_headers)

    assert judge_response.status_code == 200
    assert judge_response.json()["recommendation"]["recommended_version"] == "v2"
    assert analytics_response.status_code == 200
    assert analytics_response.json()["dashboard"]["prompt_experiments"]["metrics_count"] >= 6


def test_learning_improvement_can_create_prompt_experiment(client: TestClient, admin_headers: dict[str, str]) -> None:
    from app.db import get_db

    with get_db() as db:
        db.execute(
            """
            INSERT INTO learning_improvements
            (improvement_type, agent, category, current_version, suggested_prompt, recommendation, expected_effect, confidence, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "prompt",
                "AI Sales",
                "roi",
                "v1",
                "Add ROI explanation before the final recommendation.",
                "Strengthen ROI story.",
                "Review requests should decrease.",
                82,
                90,
            ),
        )

    response = client.post("/api/prompts/from-learning/1", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["result"]["experiment"]["status"] == "testing"
    assert response.json()["result"]["prompt"]["status"] == "testing"


def test_prompt_studio_requires_admin_or_manager(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "prompt-viewer@example.com", "password": "test-password", "role": "viewer"},
    )
    assert create_response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": "prompt-viewer@example.com", "password": "test-password"})
    viewer_headers = {"Authorization": f"Bearer {login_response.json()['token']}"}

    response = client.get("/api/prompts/dashboard", headers=viewer_headers)

    assert response.status_code == 403
