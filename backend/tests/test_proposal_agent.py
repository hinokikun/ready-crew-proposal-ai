from fastapi.testclient import TestClient


def test_proposal_agent_dashboard_and_memory(client: TestClient, admin_headers: dict[str, str]) -> None:
    project_response = client.post(
        "/api/projects",
        headers=admin_headers,
        json={
            "customer_name": "株式会社エージェント検証",
            "project_name": "AI-OCR提案支援",
            "summary": "請求書と申込書の確認をAI-OCRで支援し、提案書作成まで短縮する案件。",
            "win_probability": 55,
            "next_action": "予算と対象帳票を確認",
        },
    )
    assert project_response.status_code == 200
    project_id = int(project_response.json()["lifecycle"]["project"]["id"])

    dashboard_response = client.get("/api/proposal-agent/dashboard", headers=admin_headers)
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()["dashboard"]
    assert len(dashboard["status_cards"]) == 6
    assert any(item["label"] == "提案待ち" for item in dashboard["status_cards"])
    assert dashboard["todo"]
    assert any(item["project_id"] == project_id for item in dashboard["scores"])
    assert "executive_30s" in dashboard["summaries"]
    assert dashboard["priorities"]
    assert dashboard["win_probabilities"]
    assert dashboard["health"]
    assert "proposal_count" in dashboard["kpi"]
    assert dashboard["competitors"]
    assert dashboard["sales_actions"]
    assert dashboard["insights"]

    memory_response = client.post(
        "/api/proposal-agent/memory",
        headers=admin_headers,
        json={
            "project_id": project_id,
            "project_name": "AI-OCR提案支援",
            "hearing_notes": "対象帳票、現場確認フロー、既存システム連携を確認済み。",
            "confirmation_items": "予算上限、PoC対象、精度評価方法。",
            "proposal_content": "AI候補提示と人の最終確認を組み合わせた運用。",
            "competitor_analysis": "既存OCRツールとの差分は運用設計と提案書連携。",
            "improvement_history": "競合比較と見積条件を追記。",
        },
    )
    assert memory_response.status_code == 200
    assert memory_response.json()["memory"]["project_id"] == project_id

    refreshed = client.get("/api/proposal-agent/dashboard", headers=admin_headers).json()["dashboard"]
    assert refreshed["memories"]
    score = next(item for item in refreshed["scores"] if item["project_id"] == project_id)
    assert score["score"] >= 70
    priority = next(item for item in refreshed["priorities"] if item["project_id"] == project_id)
    assert priority["grade"] in {"A", "B", "C", "D", "E"}
    probability = next(item for item in refreshed["win_probabilities"] if item["project_id"] == project_id)
    assert probability["probability"] > 0

    for export_format in ["markdown", "csv", "pdf", "pptx"]:
        export_response = client.get(f"/api/proposal-agent/dashboard/export?format={export_format}", headers=admin_headers)
        assert export_response.status_code == 200
        assert export_response.content


def test_viewer_cannot_save_proposal_agent_memory(client: TestClient, admin_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": "agent-viewer@example.com", "password": "viewer-password", "role": "viewer"},
    )
    assert create_response.status_code == 200
    login_response = client.post("/api/auth/login", json={"email": "agent-viewer@example.com", "password": "viewer-password"})
    assert login_response.status_code == 200
    viewer_headers = {"Authorization": f"Bearer {login_response.json()['token']}"}

    dashboard_response = client.get("/api/proposal-agent/dashboard", headers=viewer_headers)
    assert dashboard_response.status_code == 200

    save_response = client.post(
        "/api/proposal-agent/memory",
        headers=viewer_headers,
        json={"project_name": "閲覧のみ", "hearing_notes": "保存不可"},
    )
    assert save_response.status_code == 403
