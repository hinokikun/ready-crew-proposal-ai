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


def test_member_can_request_review(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-member@example.com", "member")

    response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "review-project-001", "project_name": "サンプル提案"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["review"]["status"] == "review_requested"
    assert body["review"]["project_id"] == "review-project-001"


def test_viewer_cannot_request_review(client: TestClient, admin_headers: dict[str, str]) -> None:
    viewer_headers = _create_user_and_login(client, admin_headers, "review-viewer@example.com", "viewer")

    response = client.post(
        "/api/reviews/request",
        headers=viewer_headers,
        json={"project_id": "viewer-project", "project_name": "閲覧案件"},
    )

    assert response.status_code == 403


def test_admin_and_manager_can_update_review_status(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-owner@example.com", "member")
    manager_headers = _create_user_and_login(client, admin_headers, "review-manager@example.com", "manager")
    request_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "approval-project", "project_name": "承認確認案件"},
    )
    review_id = request_response.json()["review"]["id"]

    manager_response = client.patch(
        f"/api/reviews/{review_id}",
        headers=manager_headers,
        json={"status": "approved", "review_comment": "この内容で進めてください。"},
    )

    assert manager_response.status_code == 200
    assert manager_response.json()["review"]["status"] == "approved"


def test_member_cannot_approve_review(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-member-approver@example.com", "member")
    request_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "member-approval-project", "project_name": "member承認不可案件"},
    )
    review_id = request_response.json()["review"]["id"]

    response = client.patch(
        f"/api/reviews/{review_id}",
        headers=member_headers,
        json={"status": "approved", "review_comment": "承認します。"},
    )

    assert response.status_code == 403


def test_changes_requested_comment_and_audit_log_are_saved(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-comment-owner@example.com", "member")
    request_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "changes-project", "project_name": "修正依頼案件"},
    )
    review_id = request_response.json()["review"]["id"]

    update_response = client.patch(
        f"/api/reviews/{review_id}",
        headers=admin_headers,
        json={"status": "changes_requested", "review_comment": "見積条件をもう少し明確にしてください。"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()["review"]
    assert updated["status"] == "changes_requested"
    assert "見積条件" in updated["review_comment"]

    audit_response = client.get("/api/logs/audit", headers=admin_headers)
    assert audit_response.status_code == 200
    event_types = {item["event_type"] for item in audit_response.json()["logs"]}
    assert "review_request" in event_types
    assert "changes_requested" in event_types
    assert "comment_update" in event_types


def test_changes_requested_comment_can_be_fetched(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-fetch-owner@example.com", "member")
    request_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "fetch-comment-project", "project_name": "コメント取得案件"},
    )
    review_id = request_response.json()["review"]["id"]
    client.patch(
        f"/api/reviews/{review_id}",
        headers=admin_headers,
        json={"status": "changes_requested", "review_comment": "費用対効果の説明を強めてください。"},
    )

    response = client.get("/api/reviews/fetch-comment-project", headers=member_headers)

    assert response.status_code == 200
    review = response.json()["review"]
    assert review["status"] == "changes_requested"
    assert "費用対効果" in review["review_comment"]


def test_member_can_apply_review_feedback_and_get_diff_summary(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-loop-member@example.com", "member")
    request_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "feedback-loop-project", "project_name": "Feedback Loop案件"},
    )
    review_id = request_response.json()["review"]["id"]
    client.patch(
        f"/api/reviews/{review_id}",
        headers=admin_headers,
        json={"status": "changes_requested", "review_comment": "費用対効果の説明を強めてください。"},
    )

    response = client.post(
        f"/api/reviews/{review_id}/apply-feedback",
        headers=member_headers,
        json={"current_summary": "問い合わせ改善とSEO改善を中心にした提案"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["review"]["status"] == "draft"
    assert "AI営業" in body["ai_improvement_policy"]
    assert len(body["diff_summary"]) >= 3


def test_viewer_cannot_apply_review_feedback(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-loop-owner@example.com", "member")
    viewer_headers = _create_user_and_login(client, admin_headers, "review-loop-viewer@example.com", "viewer")
    request_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "viewer-feedback-project", "project_name": "viewer不可案件"},
    )
    review_id = request_response.json()["review"]["id"]

    response = client.post(
        f"/api/reviews/{review_id}/apply-feedback",
        headers=viewer_headers,
        json={"current_summary": "閲覧者は実行できない"},
    )

    assert response.status_code == 403


def test_rerequest_returns_status_to_review_requested_and_audit_log_is_recorded(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "review-rerequest-member@example.com", "member")
    request_response = client.post(
        "/api/reviews/request",
        headers=member_headers,
        json={"project_id": "rerequest-project", "project_name": "再レビュー案件"},
    )
    review_id = request_response.json()["review"]["id"]
    client.patch(
        f"/api/reviews/{review_id}",
        headers=admin_headers,
        json={"status": "changes_requested", "review_comment": "ROIを追加してください。"},
    )
    client.post(f"/api/reviews/{review_id}/apply-feedback", headers=member_headers, json={"current_summary": "初稿"})

    rerequest_response = client.post(f"/api/reviews/{review_id}/rerequest", headers=member_headers)
    revisions_response = client.get(f"/api/reviews/{review_id}/revisions", headers=member_headers)
    audit_response = client.get("/api/logs/audit", headers=admin_headers)

    assert rerequest_response.status_code == 200
    assert rerequest_response.json()["review"]["status"] == "review_requested"
    assert revisions_response.status_code == 200
    assert len(revisions_response.json()["revisions"]) >= 2
    event_types = {item["event_type"] for item in audit_response.json()["logs"]}
    assert "apply_review_feedback" in event_types
    assert "regenerate" in event_types
    assert "rereview_request" in event_types
    assert "diff_summary" in event_types
