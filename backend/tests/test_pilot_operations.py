import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from test_pilot_mode import admin_headers, create_user, login, make_client


def _headers_for(client: TestClient, email: str, password: str = "member-password") -> dict[str, str]:
    status, body = login(client, email, password)
    assert status == 200
    return {"Authorization": f"Bearer {body['token']}"}


def _enable_pilot(client: TestClient, admin: dict[str, str], user_id: int) -> None:
    response = client.patch(f"/api/users/{user_id}", headers=admin, json={"pilot_enabled": True})
    assert response.status_code == 200


def test_pilot_issue_create_and_update_permissions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=False) as client:
        admin = admin_headers(client)
        manager_user = create_user(client, admin, "manager@example.com", "manager")
        viewer_user = create_user(client, admin, "viewer@example.com", "viewer")
        manager = _headers_for(client, manager_user["email"])
        viewer = _headers_for(client, viewer_user["email"])

        create_response = client.post(
            "/api/pilot/issues",
            headers=manager,
            json={
                "category": "PPT/PDF",
                "severity": "high",
                "title": "要約PPTが出力できない",
                "summary": "3名の試験利用者で同じエラーが発生",
                "reproduction_steps": "要約PPTを押す",
            },
        )
        assert create_response.status_code == 200
        issue_id = create_response.json()["issue"]["issue_id"]

        viewer_update = client.patch(f"/api/pilot/issues/{issue_id}", headers=viewer, json={"status": "resolved"})
        assert viewer_update.status_code == 403

        manager_update = client.patch(
            f"/api/pilot/issues/{issue_id}",
            headers=manager,
            json={"status": "resolved", "resolution_note": "再試行で復旧確認"},
        )
        assert manager_update.status_code == 200
        assert manager_update.json()["issue"]["status"] == "resolved"


def test_feedback_can_be_sanitized_into_issue(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=False) as client:
        admin = admin_headers(client)
        feedback = client.post(
            "/api/feedback",
            headers=admin,
            json={
                "rating": "needs_revision",
                "comment": "sample@example.com への提案で金額欄が分かりにくい。https://example.com は保存しないでほしい。",
                "feature_name": "pilot",
            },
        )
        assert feedback.status_code == 200
        feedback_id = feedback.json()["feedback"]["id"]

        response = client.post(
            f"/api/pilot/issues/from-feedback/{feedback_id}",
            headers=admin,
            json={"category": "UI表示", "severity": "medium", "title": "金額欄が分かりにくい"},
        )
        assert response.status_code == 200
        summary = response.json()["issue"]["summary"]
        assert "sample@example.com" not in summary
        assert "https://example.com" not in summary
        assert "[email]" in summary
        assert "[url]" in summary


def test_runtime_maintenance_mode_blocks_generation(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=False, maintenance_mode=False) as client:
        admin = admin_headers(client)
        member_user = create_user(client, admin, "member@example.com", "member")
        member = _headers_for(client, member_user["email"])

        member_toggle = client.patch("/api/pilot/maintenance", headers=member, json={"enabled": True, "reason": "test"})
        assert member_toggle.status_code == 403

        toggle = client.patch("/api/pilot/maintenance", headers=admin, json={"enabled": True, "reason": "障害確認中"})
        assert toggle.status_code == 200
        assert toggle.json()["maintenance"]["enabled"] is True

        response = client.post(
            "/api/analyze",
            headers=member,
            json={
                "project_brief": "Ready Crew案件。Webサイトリニューアルの相談。問い合わせ増加とCMS改善が目的です。",
                "client_company_info": "株式会社サンプル",
            },
        )
        assert response.status_code == 503
        assert "メンテナンス" in response.text


def test_pilot_judgment_and_report_use_actual_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=True) as client:
        admin = admin_headers(client)
        member_user = create_user(client, admin, "pilot-report@example.com", "member")
        _enable_pilot(client, admin, member_user["id"])
        main = importlib.import_module("app.main")
        db_module = importlib.import_module("app.db")
        with db_module.get_db() as db:
            db.execute("UPDATE users SET pilot_started_at = CURRENT_TIMESTAMP, pilot_last_used_at = CURRENT_TIMESTAMP WHERE id = ?", (member_user["id"],))
            db.execute("INSERT INTO pilot_events (user_id, event_type, status, duration_ms, metadata) VALUES (?, 'proposal_generation', 'success', 1200, '')", (member_user["id"],))
            db.execute("INSERT INTO pilot_events (user_id, event_type, status, duration_ms, metadata) VALUES (?, 'download', 'success', 400, 'output_type=summary-pptx')", (member_user["id"],))
            db.execute(
                "INSERT INTO feedback_entries (user_id, user_role, rating, comment, feature_name) VALUES (?, 'member', 'usable', ?, 'pilot')",
                (member_user["id"], "迷わず使えた: 5/5\n作成時間を短縮できた: 5/5\n今後も使いたい: 5/5"),
            )
        assert main.app

        dashboard_response = client.get("/api/pilot/dashboard", headers=admin)
        assert dashboard_response.status_code == 200
        judgment = dashboard_response.json()["dashboard"]["judgment"]
        assert judgment["result"] in {"合格", "条件付き合格", "延長推奨", "中止推奨"}
        assert any(item["key"] == "proposal_success" for item in judgment["criteria"])

        report_response = client.post("/api/pilot/end", headers=admin, json={"admin_comment": "Pilot確認済み"})
        assert report_response.status_code == 200
        markdown = report_response.json()["report"]["markdown"]
        assert "Pilot 終了レポート" in markdown
        assert "顧客本文" in markdown


def test_pilot_data_retention_does_not_delete_production_projects(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    with make_client(monkeypatch, tmp_path, pilot_mode=False) as client:
        admin = admin_headers(client)
        db_module = importlib.import_module("app.db")
        with db_module.get_db() as db:
            db.execute("INSERT INTO customers (company_name) VALUES ('本番顧客')")
            db.execute("INSERT INTO projects (customer_id, name, summary) VALUES (1, '本番案件', '削除してはいけない')")
            db.execute("INSERT INTO pilot_events (user_id, event_type, status, metadata) VALUES (NULL, 'proposal_generation', 'success', 'test')")
            db.execute("INSERT INTO feedback_entries (user_id, user_role, rating, comment, feature_name) VALUES (NULL, 'member', 'usable', 'test', 'pilot')")

        preview = client.get("/api/pilot/data-retention/preview", headers=admin)
        assert preview.status_code == 200
        assert preview.json()["preview"]["production_projects"] == 1

        response = client.post(
            "/api/pilot/data-retention",
            headers=admin,
            json={"action": "delete_events", "confirm_text": "PILOT"},
        )
        assert response.status_code == 200
        with db_module.get_db() as db:
            project_count = db.execute("SELECT COUNT(*) AS count FROM projects").fetchone()["count"]
            event_count = db.execute("SELECT COUNT(*) AS count FROM pilot_events").fetchone()["count"]
        assert int(project_count) == 1
        assert int(event_count) == 0
