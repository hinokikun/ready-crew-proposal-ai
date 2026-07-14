from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


def _reload_app_modules() -> None:
    for module_name in list(sys.modules):
        if module_name == "app" or module_name.startswith("app."):
            del sys.modules[module_name]


def _client_with_beautiful_ai(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    env = {
        "DATABASE_URL": f"sqlite:///{tmp_path / 'presentation-review-beautiful.db'}",
        "USE_MOCK_AI": "true",
        "APP_AUTH_SECRET": "test-secret",
        "INITIAL_ADMIN_EMAIL": "admin@example.com",
        "INITIAL_ADMIN_PASSWORD": "test-password",
        "CORS_ORIGINS": "http://localhost:3000",
        "RATE_LIMIT_LOGIN_LIMIT": "1000",
        "RATE_LIMIT_GENERATION_LIMIT": "1000",
        "RATE_LIMIT_ADMIN_LIMIT": "1000",
        "BEAUTIFUL_AI_ENABLED": "true",
        "BEAUTIFUL_AI_MOCK": "true",
        "PRESENTATION_MAX_REVISIONS": "3",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    _reload_app_modules()
    main = importlib.import_module("app.main")
    return TestClient(main.app)


def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    password = "test-password"
    response = client.post("/api/users", headers=admin_headers, json={"email": email, "password": password, "role": role})
    assert response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def _payload(sample_pptx_payload: dict[str, Any], project_id: str = "presentation-review-project") -> dict[str, Any]:
    return {
        "project_id": project_id,
        "project_name": "Presentation Review Test",
        "beautiful_ai_presentation_id": "beautiful-test-001",
        "powerpoint_generation_data": sample_pptx_payload["powerpoint_generation_data"],
    }


def _beautiful_payload(sample_pptx_payload: dict[str, Any], project_id: str) -> dict[str, Any]:
    return {**sample_pptx_payload, "project_id": project_id}


def _complete_quality_gate(client: TestClient, headers: dict[str, str], project_id: str) -> None:
    response = client.patch(
        f"/api/quality-gates/{project_id}/complete",
        headers=headers,
        json={"checklist_items": ["company", "budget", "deadline", "human_review"]},
    )
    assert response.status_code == 200


def test_member_can_review_create_revision_and_compare(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict[str, Any]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "presentation-member@example.com", "member")
    response = client.post("/api/presentation-review/reviews", headers=member_headers, json=_payload(sample_pptx_payload))
    assert response.status_code == 200
    review = response.json()["review"]
    assert review["average_score"] > 0
    assert review["scores"]
    assert {"reason", "evidence", "confidence", "requires_human_review"}.issubset(review["scores"][0])
    assert review["actions"]
    assert review["improvements"]
    assert review["beautiful_ai_presentation_id"] == "beautiful-test-001"

    revision_response = client.post(
        "/api/presentation-review/revisions",
        headers=member_headers,
        json={"review_id": review["id"], "beautiful_ai_presentation_id": "beautiful-test-002"},
    )
    assert revision_response.status_code == 200
    revision = revision_response.json()["revision"]
    assert revision["revision_number"] == 2
    assert revision["beautiful_ai_presentation_id"] == "beautiful-test-002"
    assert revision["status"] == "draft"
    assert revision["selected_actions"]
    assert revision["diff"]

    timeline = client.get("/api/presentation-review/projects/presentation-review-project", headers=member_headers)
    assert timeline.status_code == 200
    assert len(timeline.json()["revisions"]) == 2

    compare = client.get("/api/presentation-review/projects/presentation-review-project/compare", headers=member_headers)
    assert compare.status_code == 200
    assert compare.json()["changes"]


def test_presentation_review_permissions(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict[str, Any]) -> None:
    viewer_headers = _create_user_and_login(client, admin_headers, "presentation-viewer@example.com", "viewer")
    create_response = client.post("/api/presentation-review/reviews", headers=viewer_headers, json=_payload(sample_pptx_payload, "viewer-project"))
    assert create_response.status_code == 403

    admin_create = client.post("/api/presentation-review/reviews", headers=admin_headers, json=_payload(sample_pptx_payload, "approve-project"))
    assert admin_create.status_code == 200
    review_id = admin_create.json()["review"]["id"]
    revision = client.post("/api/presentation-review/revisions", headers=admin_headers, json={"review_id": review_id})
    assert revision.status_code == 200

    viewer_approve = client.patch(f"/api/presentation-review/revisions/{revision.json()['revision']['id']}/approve", headers=viewer_headers)
    assert viewer_approve.status_code == 403
    admin_approve = client.patch(f"/api/presentation-review/revisions/{revision.json()['revision']['id']}/approve", headers=admin_headers)
    assert admin_approve.status_code == 200
    assert admin_approve.json()["revision"]["approved"] is True

    viewer_generate = client.post(
        f"/api/presentation-review/revisions/{revision.json()['revision']['id']}/generate-beautiful-ai",
        headers=viewer_headers,
        json={"beautiful_ai_payload": _beautiful_payload(sample_pptx_payload, "approve-project")},
    )
    assert viewer_generate.status_code == 403


def test_presentation_review_is_workspace_isolated(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict[str, Any]) -> None:
    project_id = "isolated-presentation-project"
    created = client.post("/api/presentation-review/reviews", headers=admin_headers, json=_payload(sample_pptx_payload, project_id))
    assert created.status_code == 200
    assert client.get(f"/api/presentation-review/projects/{project_id}", headers=admin_headers).json()["reviews"]

    org_response = client.post("/api/organizations", headers=admin_headers, json={"name": "Presentation Org", "slug": "presentation-org"})
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

    separated = client.get(f"/api/presentation-review/projects/{project_id}", headers=admin_headers)
    assert separated.status_code == 200
    assert separated.json()["reviews"] == []


def test_presentation_review_metrics_are_available_to_learning(client: TestClient, admin_headers: dict[str, str], sample_pptx_payload: dict[str, Any]) -> None:
    response = client.post("/api/presentation-review/reviews", headers=admin_headers, json=_payload(sample_pptx_payload, "learning-presentation-project"))
    assert response.status_code == 200
    learning = client.post("/api/learning/run", headers=admin_headers)
    assert learning.status_code == 200
    metrics = learning.json()["dashboard"]["run"]["metrics_summary"]
    assert metrics["presentation_review"]["reviews"] >= 1
    assert metrics["presentation_review"]["review_issue_count"] >= 0
    assert "generation_success_rate" in metrics["presentation_review"]
    assert "accepted_action_count" in metrics["presentation_review"]

    analytics = client.get("/api/analytics/dashboard?scope=workspace", headers=admin_headers)
    assert analytics.status_code == 200
    assert analytics.json()["dashboard"]["presentation"]["review_count"] >= 1


def test_presentation_revision_generates_separate_beautiful_ai_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_beautiful_ai(monkeypatch, tmp_path) as client:
        headers = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-password"})
        assert headers.status_code == 200
        admin_headers = {"Authorization": f"Bearer {headers.json()['token']}"}
        project_id = "presentation-beautiful-revision"
        _complete_quality_gate(client, admin_headers, project_id)
        review_response = client.post("/api/presentation-review/reviews", headers=admin_headers, json=_payload(sample_pptx_payload, project_id))
        assert review_response.status_code == 200
        review = review_response.json()["review"]
        revision_response = client.post(
            "/api/presentation-review/revisions",
            headers=admin_headers,
            json={"review_id": review["id"], "selected_actions": review["actions"][:2]},
        )
        assert revision_response.status_code == 200
        revision = revision_response.json()["revision"]
        approval = client.patch(f"/api/presentation-review/revisions/{revision['id']}/approve", headers=admin_headers)
        assert approval.status_code == 200
        generation = client.post(
            f"/api/presentation-review/revisions/{revision['id']}/generate-beautiful-ai",
            headers=admin_headers,
            json={"beautiful_ai_payload": _beautiful_payload(sample_pptx_payload, project_id)},
        )
        assert generation.status_code == 200
        generated = generation.json()["revision"]
        assert generated["status"] == "generated"
        assert generated["beautiful_ai_presentation_id"].startswith("mock-")
        assert generated["editor_url"].startswith("https://www.beautiful.ai/")
        assert generated["beautiful_ai_presentation_id"] != review["beautiful_ai_presentation_id"]


def test_presentation_revision_max_limit_and_sensitive_values_are_not_stored(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sample_pptx_payload: dict[str, Any],
) -> None:
    with _client_with_beautiful_ai(monkeypatch, tmp_path) as client:
        login = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "test-password"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['token']}"}
        project_id = "presentation-max-revisions"
        review_response = client.post("/api/presentation-review/reviews", headers=headers, json=_payload(sample_pptx_payload, project_id))
        assert review_response.status_code == 200
        review = review_response.json()["review"]
        first = client.post("/api/presentation-review/revisions", headers=headers, json={"review_id": review["id"], "selected_actions": review["actions"][:1]})
        assert first.status_code == 200
        second = client.post("/api/presentation-review/revisions", headers=headers, json={"review_id": review["id"], "selected_actions": review["actions"][1:2] or review["actions"][:1]})
        assert second.status_code == 200
        third = client.post("/api/presentation-review/revisions", headers=headers, json={"review_id": review["id"], "selected_actions": review["actions"][:1]})
        assert third.status_code == 409

        db_path = tmp_path / "presentation-review-beautiful.db"
        with sqlite3.connect(db_path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute(
                "SELECT r.actions_json, r.outline_json AS review_outline_json, v.diff_json FROM presentation_reviews r JOIN presentation_revisions v ON v.review_id = r.id WHERE r.project_id = ? LIMIT 1",
                (project_id,),
            ).fetchone()
        saved = str(dict(row))
        assert "test-password" not in saved
        assert "BEAUTIFUL_AI_API_KEY" not in saved
        assert "api_key" not in saved.lower()
