from fastapi.testclient import TestClient


ROLLOUT_CHECKLIST = [
    "GitHub Actions成功",
    "Vercel Build成功",
    "Render /health 正常",
    "ログイン確認",
    "admin/member/viewer権限確認",
    "提案書作成確認",
    "要約PPT確認",
    "詳細PPT確認",
    "見積PDF確認",
    "品質ゲート確認",
    "上司レビュー確認",
    "監査ログ確認",
    "フィードバック送信確認",
]


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


def _release_payload(version: str = "9.5") -> dict:
    return {
        "version": version,
        "release_date": "2026-07-10",
        "status": "internal_test",
        "summary": "Release management and internal rollout",
        "changes": "Added release records, rollout checklist, publish workflow",
        "impact_scope": "Admin operations and internal rollout",
        "checklist": ROLLOUT_CHECKLIST,
        "known_issues": "No automatic rollback",
        "rollback_note": "Promote previous Vercel deployment and confirm Render deploy logs.",
    }


def test_admin_can_create_release_record_and_checklist_is_saved(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post("/api/releases", headers=admin_headers, json=_release_payload())

    assert response.status_code == 200
    release = response.json()["release"]
    assert release["version"] == "9.5"
    assert release["status"] == "internal_test"
    assert "品質ゲート確認" in release["checklist"]


def test_manager_can_publish_release_and_audit_log_is_recorded(client: TestClient, admin_headers: dict[str, str]) -> None:
    manager_headers = _create_user_and_login(client, admin_headers, "release-manager@example.com", "manager")
    create_response = client.post("/api/releases", headers=admin_headers, json=_release_payload("9.5.1"))
    release_id = create_response.json()["release"]["id"]

    publish_response = client.post(
        f"/api/releases/{release_id}/publish",
        headers=manager_headers,
        json={"comment": "internal rollout approved"},
    )
    audit_response = client.get("/api/logs/audit", headers=admin_headers)

    assert publish_response.status_code == 200
    assert publish_response.json()["release"]["status"] == "released"
    event_types = {item["event_type"] for item in audit_response.json()["logs"]}
    assert "release_publish" in event_types


def test_member_and_viewer_cannot_edit_release_records(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "release-member@example.com", "member")
    viewer_headers = _create_user_and_login(client, admin_headers, "release-viewer@example.com", "viewer")

    member_response = client.post("/api/releases", headers=member_headers, json=_release_payload("9.5-member"))
    viewer_response = client.patch(
        "/api/releases/1",
        headers=viewer_headers,
        json={"summary": "viewer cannot update"},
    )

    assert member_response.status_code == 403
    assert viewer_response.status_code == 403


def test_released_records_are_visible_to_member_and_viewer(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "release-read-member@example.com", "member")
    viewer_headers = _create_user_and_login(client, admin_headers, "release-read-viewer@example.com", "viewer")
    draft_response = client.post("/api/releases", headers=admin_headers, json={**_release_payload("9.5-draft"), "status": "draft"})
    released_response = client.post("/api/releases", headers=admin_headers, json=_release_payload("9.5-released"))
    client.post(f"/api/releases/{released_response.json()['release']['id']}/publish", headers=admin_headers, json={"comment": "ready"})

    member_list = client.get("/api/releases", headers=member_headers)
    viewer_list = client.get("/api/releases", headers=viewer_headers)

    assert draft_response.status_code == 200
    assert member_list.status_code == 200
    assert viewer_list.status_code == 200
    member_versions = {item["version"] for item in member_list.json()["releases"]}
    viewer_versions = {item["version"] for item in viewer_list.json()["releases"]}
    assert "9.5-released" in member_versions
    assert "9.5-released" in viewer_versions
    assert "9.5-draft" not in member_versions
    assert "9.5-draft" not in viewer_versions
