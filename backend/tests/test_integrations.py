import json

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


def _intake_payload() -> dict:
    return {
        "source_provider": "Gmail",
        "source_type": "email",
        "title": "株式会社サンプル Webサイト相談",
        "summary": "問い合わせ導線とCMS運用を改善したい案件相談。担当者メール test@example.com は保存時に伏せる。",
        "received_at": "2026-07-10T09:00:00",
        "metadata": {
            "company_name": "株式会社サンプル",
            "industry": "不動産",
            "source_url": "https://example.com/thread/123",
            "provider_item_id": "gmail-demo-1",
            "api_key": "secret-key-should-not-save",
            "refresh_token": "refresh-token-should-not-save",
            "password": "password-should-not-save",
            "body": "メール本文全文は保存しない",
            "attachment": "proposal.pdf",
        },
    }


def test_integration_settings_are_seeded(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.get("/api/integrations/settings", headers=admin_headers)

    assert response.status_code == 200
    providers = {item["provider"] for item in response.json()["settings"]}
    assert {"gmail", "outlook", "slack", "salesforce"}.issubset(providers)


def test_admin_can_update_integration_setting(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.patch(
        "/api/integrations/settings/gmail",
        headers=admin_headers,
        json={
            "status": "接続準備中",
            "display_name": "Gmail",
            "enabled": True,
            "error_message": "",
            "allowed_roles": ["admin", "manager", "member"],
            "requires_admin_approval": True,
            "data_retention_days": 120,
            "security_note": "Token and raw body are not stored.",
        },
    )

    assert response.status_code == 200
    setting = response.json()["setting"]
    assert setting["provider"] == "gmail"
    assert setting["status"] == "接続準備中"
    assert setting["enabled"] is True
    assert setting["allowed_roles"] == ["admin", "manager", "member"]
    assert setting["requires_admin_approval"] is True
    assert setting["data_retention_days"] == 120

    audit_response = client.get("/api/logs/audit", headers=admin_headers)
    assert any(item["event_type"] == "integration_setting_change" for item in audit_response.json()["logs"])


def test_external_intake_saves_candidate_without_tokens(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "integration-member@example.com", "member")

    response = client.post("/api/integrations/intake", headers=member_headers, json=_intake_payload())

    assert response.status_code == 200
    candidate = response.json()["candidate"]
    assert candidate["source_provider"] == "gmail"
    assert candidate["candidate_status"] == "pending_review"
    assert candidate["security_flags"]
    saved = json.dumps(candidate, ensure_ascii=False)
    assert "secret-key-should-not-save" not in saved
    assert "refresh-token-should-not-save" not in saved
    assert "password-should-not-save" not in saved
    assert "メール本文全文" not in saved
    assert "test@example.com" not in saved


def test_approved_candidate_can_be_converted_to_project_and_workspace_message_is_created(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "integration-convert@example.com", "member")
    intake_response = client.post("/api/integrations/intake", headers=member_headers, json=_intake_payload())
    candidate_id = intake_response.json()["candidate"]["id"]

    pending_convert_response = client.post(f"/api/integrations/candidates/{candidate_id}/convert", headers=member_headers)
    assert pending_convert_response.status_code == 400

    approve_response = client.patch(
        f"/api/integrations/candidates/{candidate_id}/review",
        headers=admin_headers,
        json={"status": "approved", "review_comment": "safe to convert"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["candidate"]["candidate_status"] == "approved"

    convert_response = client.post(f"/api/integrations/candidates/{candidate_id}/convert", headers=member_headers)

    assert convert_response.status_code == 200
    converted = convert_response.json()["candidate"]
    assert converted["candidate_status"] == "converted"
    assert converted["project_id"]

    project_response = client.get(f"/api/projects/{converted['project_id']}", headers=member_headers)
    assert project_response.status_code == 200
    conversations = project_response.json()["project"]["workspace_conversations"]
    assert any("外部連携から案件候補を受け取りました" in item["message_body"] for item in conversations)


def test_only_admin_or_manager_can_review_external_intake(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "integration-review-member@example.com", "member")
    manager_headers = _create_user_and_login(client, admin_headers, "integration-review-manager@example.com", "manager")
    intake_response = client.post("/api/integrations/intake", headers=member_headers, json=_intake_payload())
    candidate_id = intake_response.json()["candidate"]["id"]

    member_review = client.patch(
        f"/api/integrations/candidates/{candidate_id}/review",
        headers=member_headers,
        json={"status": "approved", "review_comment": "member cannot approve"},
    )
    manager_review = client.patch(
        f"/api/integrations/candidates/{candidate_id}/review",
        headers=manager_headers,
        json={"status": "approved", "review_comment": "manager approved"},
    )

    assert member_review.status_code == 403
    assert manager_review.status_code == 200
    assert manager_review.json()["candidate"]["candidate_status"] == "approved"


def test_integration_dry_run_creates_pending_review_candidate_and_log(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/integrations/dry-run",
        headers=admin_headers,
        json={"provider": "gmail", "template_type": "case_email"},
    )

    assert response.status_code == 200
    body = response.json()
    candidate = body["candidate"]
    assert candidate["candidate_status"] == "pending_review"
    assert candidate["security_flags"]
    assert body["dry_run"]["checks"]["registered"] is True
    assert body["dry_run"]["checks"]["security_scanned"] is True
    assert body["dry_run"]["checks"]["pending_review"] is True

    logs_response = client.get("/api/integrations/dry-run/logs", headers=admin_headers)
    saved = json.dumps(logs_response.json(), ensure_ascii=False)
    assert logs_response.status_code == 200
    assert logs_response.json()["logs"][0]["status"] == "success"
    assert "dry-run-api-key-should-not-save" not in saved


def test_connector_readiness_score_is_returned(client: TestClient, admin_headers: dict[str, str]) -> None:
    client.post(
        "/api/integrations/dry-run",
        headers=admin_headers,
        json={"provider": "slack", "template_type": "slack_consultation"},
    )

    response = client.get("/api/integrations/readiness", headers=admin_headers)

    assert response.status_code == 200
    readiness = response.json()["readiness"]
    assert any(item["provider"] == "slack" for item in readiness)
    slack = next(item for item in readiness if item["provider"] == "slack")
    assert slack["score"] >= 0
    assert "dry_run_success" in slack["checks"]


def test_viewer_cannot_convert_external_candidate(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "integration-owner@example.com", "member")
    viewer_headers = _create_user_and_login(client, admin_headers, "integration-viewer@example.com", "viewer")
    intake_response = client.post("/api/integrations/intake", headers=member_headers, json=_intake_payload())
    candidate_id = intake_response.json()["candidate"]["id"]

    response = client.post(f"/api/integrations/candidates/{candidate_id}/convert", headers=viewer_headers)

    assert response.status_code == 403


def test_integration_analytics_are_in_product_dashboard(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "integration-analytics@example.com", "member")
    intake_response = client.post("/api/integrations/intake", headers=member_headers, json=_intake_payload())
    candidate_id = intake_response.json()["candidate"]["id"]
    client.patch(
        f"/api/integrations/candidates/{candidate_id}/review",
        headers=admin_headers,
        json={"status": "approved", "review_comment": "ok"},
    )
    client.post(f"/api/integrations/candidates/{candidate_id}/convert", headers=member_headers)

    dashboard_response = client.get("/api/analytics/dashboard", headers=admin_headers)

    assert dashboard_response.status_code == 200
    integrations = dashboard_response.json()["dashboard"]["integrations"]
    assert integrations["external_input_count"] >= 1
    assert integrations["converted_count"] >= 1
    assert integrations["conversion_rate"] >= 0
    assert any(item["provider"] == "gmail" for item in integrations["provider_counts"])
    assert integrations["dry_run_count"] >= 0
    assert integrations["average_readiness_score"] >= 0
