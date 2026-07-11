from fastapi.testclient import TestClient


def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": email, "password": "test-password", "role": role},
    )
    assert create_response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": email, "password": "test-password"})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def test_workspace_conversation_save_and_get(client: TestClient, admin_headers: dict[str, str]) -> None:
    payload = {
        "project_id": "project-001",
        "conversations": [
            {
                "client_message_id": "010-secretary",
                "agent_name": "AI秘書",
                "message_type": "done",
                "message_body": "案件メールを受付しました。",
                "status": "done",
            },
            {
                "client_message_id": "030-sales",
                "agent_name": "AI営業",
                "message_type": "handoff",
                "message_body": "AIディレクターへレビュー依頼しました。",
                "status": "done",
            },
        ],
        "work_logs": [
            {
                "client_log_id": "secretary-log",
                "agent_name": "AI秘書",
                "action_summary": "AI秘書が案件受付",
                "status": "done",
            }
        ],
    }

    save_response = client.post("/api/workspace/conversations", headers=admin_headers, json=payload)
    assert save_response.status_code == 200
    assert save_response.json()["saved_conversations"] == 2

    get_response = client.get("/api/workspace/conversations/project-001", headers=admin_headers)
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["project_id"] == "project-001"
    assert len(body["conversations"]) == 2
    assert body["work_logs"][0]["action_summary"] == "AI秘書が案件受付"


def test_viewer_can_read_but_cannot_save_workspace_conversation(client: TestClient, admin_headers: dict[str, str]) -> None:
    viewer_headers = _create_user_and_login(client, admin_headers, "workspace-viewer@example.com", "viewer")

    read_response = client.get("/api/workspace/conversations/project-001", headers=viewer_headers)
    assert read_response.status_code == 200

    save_response = client.post(
        "/api/workspace/conversations",
        headers=viewer_headers,
        json={"project_id": "project-001", "conversations": [], "work_logs": []},
    )
    assert save_response.status_code == 403


def test_workspace_summary_api(client: TestClient, admin_headers: dict[str, str]) -> None:
    client.post(
        "/api/workspace/conversations",
        headers=admin_headers,
        json={
            "project_id": "summary-project",
            "conversations": [
                {
                    "client_message_id": "100-president-approved",
                    "agent_name": "AI社長",
                    "message_type": "explanation",
                    "message_body": "承認しました。導線改善を優先しました。",
                    "status": "done",
                }
            ],
            "work_logs": [],
        },
    )

    response = client.get("/api/workspace/summary/summary-project", headers=admin_headers)
    assert response.status_code == 200
    summary = response.json()["summary"]
    assert "AI Workspace作業まとめ" in summary["markdown"]
    assert summary["final_decision"] == "承認しました。導線改善を優先しました。"


def test_workspace_conversation_sanitizes_sensitive_text(client: TestClient, admin_headers: dict[str, str]) -> None:
    sensitive_text = "連絡先 taro@example.com https://example.com API_KEY=sk-secretsecretsecret 電話 03-1234-5678"
    response = client.post(
        "/api/workspace/conversations",
        headers=admin_headers,
        json={
            "project_id": "safe-project",
            "conversations": [
                {
                    "client_message_id": "sensitive",
                    "agent_name": "AI営業",
                    "message_type": "normal",
                    "message_body": sensitive_text,
                    "status": "active",
                }
            ],
            "work_logs": [],
        },
    )
    assert response.status_code == 200

    body = client.get("/api/workspace/conversations/safe-project", headers=admin_headers).json()
    saved_text = body["conversations"][0]["message_body"]
    assert "taro@example.com" not in saved_text
    assert "https://example.com" not in saved_text
    assert "sk-secretsecretsecret" not in saved_text
    assert "03-1234-5678" not in saved_text
