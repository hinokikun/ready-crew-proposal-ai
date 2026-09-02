from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient



def _create_user_and_login(client: TestClient, admin_headers: dict[str, str], email: str, role: str) -> dict[str, str]:
    password = f"{role}-password"
    create_response = client.post(
        "/api/users",
        headers=admin_headers,
        json={"email": email, "password": password, "role": role},
    )
    assert create_response.status_code == 200

    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    return {"Authorization": f"Bearer {login_response.json()['token']}"}


def test_product_analytics_dashboard_release_notes_and_permissions(client: TestClient, admin_headers: dict[str, str]) -> None:
    member_headers = _create_user_and_login(client, admin_headers, "analytics-member@example.com", "member")

    events = [
        ("login", "auth", "success", 0, ""),
        ("case_paste", "proposal", "success", 100, ""),
        ("ai_analysis_start", "proposal", "start", 0, ""),
        ("ai_analysis_complete", "proposal", "success", 1200, ""),
        ("proposal_generated", "proposal", "success", 3000, ""),
        ("summary_ppt_download", "summary_ppt", "success", 900, ""),
        ("detail_ppt_download", "detail_ppt", "success", 1100, ""),
        ("estimate_pdf_download", "estimate_pdf", "failure", 600, "pdf_generation_failed"),
    ]
    for event_name, feature_name, status, duration_ms, error_type in events:
        response = client.post(
            "/api/analytics/events",
            headers=member_headers,
            json={
                "session_id": "test-session-analytics-001",
                "event_name": event_name,
                "feature_name": feature_name,
                "status": status,
                "duration_ms": duration_ms,
                "error_type": error_type,
                "metadata": {"source": "pytest", "unsafe_customer_name": "not-saved"},
            },
        )
        assert response.status_code == 200

    dashboard_response = client.get("/api/analytics/dashboard", headers=admin_headers)
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()["dashboard"]
    assert dashboard["summary"]["total_sessions"] >= 1
    assert any(step["step"] == "proposal_generated" for step in dashboard["funnel"])
    assert dashboard["feature_usage"]
    assert dashboard["sessions"]
    assert dashboard["errors"]
    assert dashboard["improvement_candidates"]

    error_id = dashboard["errors"][0]["id"]
    resolved_response = client.patch(
        f"/api/analytics/errors/{error_id}",
        headers=admin_headers,
        json={"resolved": True},
    )
    assert resolved_response.status_code == 200
    assert resolved_response.json()["error"]["resolved"] is True

    note_response = client.post(
        "/api/analytics/release-notes",
        headers=admin_headers,
        json={
            "version": "7.0",
            "release_date": "2026-07-10",
            "title": "Product Analytics",
            "improvements": "Added funnel, session, error, and feature usage analytics.",
        },
    )
    assert note_response.status_code == 200
    assert note_response.json()["release_note"]["version"] == "7.0"

    notes_response = client.get("/api/analytics/release-notes", headers=admin_headers)
    assert notes_response.status_code == 200
    assert notes_response.json()["release_notes"]

    assert client.get("/api/analytics/dashboard", headers=member_headers).status_code == 403
    assert client.get("/api/analytics/release-notes", headers=member_headers).status_code == 403


def test_candidate_boundary_events_are_bounded_scoped_and_fail_closed(client: TestClient, admin_headers: dict[str, str]) -> None:
    manager_headers = _create_user_and_login(client, admin_headers, "analytics-manager@example.com", "manager")
    from app.db import get_db as current_get_db

    with current_get_db() as db:
        for event_name, metadata in (
            ("presentation_candidate_boundary_analysis", '{"semantic_candidates_state":"EMPTY","candidate_count":0}'),
            ("presentation_candidate_boundary_transport", '{"semantic_candidates_state":"NONEMPTY","candidate_count":2}'),
            ("unrelated_event", '{"semantic_candidates_state":"NONEMPTY","candidate_count":9}'),
            ("presentation_candidate_boundary_analysis", '{"semantic_candidates_state":"INVALID","candidate_count":1}'),
            ("presentation_candidate_boundary_transport", '{"semantic_candidates_state":"NONEMPTY","candidate_count":true}'),
        ):
            db.execute(
                "INSERT INTO analytics_events (session_key, event_name, metadata, organization_id, workspace_id) VALUES (?, ?, ?, ?, ?)",
                ("candidate-boundary-analytics", event_name, metadata, 1, 1),
            )
        created_at = db.execute("SELECT MIN(created_at) AS created_at FROM analytics_events WHERE session_key = ?", ("candidate-boundary-analytics",)).fetchone()["created_at"]
    event_time = datetime.fromisoformat(str(created_at).replace(" ", "T")).replace(tzinfo=timezone.utc)
    start = (event_time - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
    end = (event_time + timedelta(seconds=2)).isoformat().replace("+00:00", "Z")

    response = client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}", headers=admin_headers)
    assert response.status_code == 200
    events = response.json()["events"]
    assert [event["event_name"] for event in events] == [
        "presentation_candidate_boundary_analysis",
        "presentation_candidate_boundary_transport",
    ]
    assert all(set(event) == {"event_name", "created_at", "semantic_candidates_state", "candidate_count"} for event in events)
    assert events[0]["candidate_count"] == 0
    assert events[1]["candidate_count"] == 2

    assert client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}&scope=system", headers=admin_headers).status_code == 422
    assert client.get(f"/api/analytics/candidate-boundary-events?start={end}&end={start}", headers=admin_headers).status_code == 400
    too_wide = (event_time + timedelta(hours=25)).isoformat().replace("+00:00", "Z")
    assert client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={too_wide}", headers=admin_headers).status_code == 400
    assert client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}", headers=manager_headers).status_code == 200
    assert client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}").status_code == 401


def _candidate_window_and_seed(client: TestClient, rows: list[tuple[str, str, int, int]]) -> tuple[str, str]:
    from app.db import get_db as current_get_db

    with current_get_db() as db:
        for event_name, metadata, organization_id, workspace_id in rows:
            db.execute(
                "INSERT INTO analytics_events (session_key, event_name, metadata, organization_id, workspace_id) VALUES (?, ?, ?, ?, ?)",
                ("candidate-boundary-seed", event_name, metadata, organization_id, workspace_id),
            )
        created_at = db.execute("SELECT MIN(created_at) AS created_at FROM analytics_events WHERE session_key = ?", ("candidate-boundary-seed",)).fetchone()["created_at"]
    event_time = datetime.fromisoformat(str(created_at).replace(" ", "T")).replace(tzinfo=timezone.utc)
    return (
        (event_time - timedelta(seconds=1)).isoformat().replace("+00:00", "Z"),
        (event_time + timedelta(seconds=2)).isoformat().replace("+00:00", "Z"),
    )


def test_candidate_boundary_endpoint_is_read_only(client: TestClient, admin_headers: dict[str, str]) -> None:
    start, end = _candidate_window_and_seed(
        client,
        [("presentation_candidate_boundary_analysis", '{"semantic_candidates_state":"EMPTY","candidate_count":0}', 1, 1)],
    )
    from app.db import get_db as current_get_db

    with current_get_db() as db:
        before = [tuple(row) for row in db.execute("SELECT id, event_name, metadata, organization_id, workspace_id FROM analytics_events ORDER BY id").fetchall()]
    response = client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}", headers=admin_headers)
    assert response.status_code == 200
    with current_get_db() as db:
        after = [tuple(row) for row in db.execute("SELECT id, event_name, metadata, organization_id, workspace_id FROM analytics_events ORDER BY id").fetchall()]
    assert after == before


def test_candidate_boundary_endpoint_enforces_organization_and_workspace_isolation(client: TestClient, admin_headers: dict[str, str]) -> None:
    start, end = _candidate_window_and_seed(
        client,
        [
            ("presentation_candidate_boundary_analysis", '{"semantic_candidates_state":"NONEMPTY","candidate_count":1}', 1, 1),
            ("presentation_candidate_boundary_transport", '{"semantic_candidates_state":"NONEMPTY","candidate_count":2}', 2, 2),
            ("presentation_candidate_boundary_transport", '{"semantic_candidates_state":"NONEMPTY","candidate_count":3}', 1, 99),
        ],
    )
    organization_response = client.get(
        f"/api/analytics/candidate-boundary-events?start={start}&end={end}&scope=organization",
        headers=admin_headers,
    )
    assert organization_response.status_code == 200
    assert [event["candidate_count"] for event in organization_response.json()["events"]] == [1, 3]
    workspace_response = client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}", headers=admin_headers)
    assert workspace_response.status_code == 200
    assert [event["candidate_count"] for event in workspace_response.json()["events"]] == [1]


def test_candidate_boundary_endpoint_caps_valid_rows_at_twenty_in_order(client: TestClient, admin_headers: dict[str, str]) -> None:
    start, end = _candidate_window_and_seed(
        client,
        [
            (
                "presentation_candidate_boundary_analysis" if index % 2 == 0 else "presentation_candidate_boundary_transport",
                f'{{"semantic_candidates_state":"NONEMPTY","candidate_count":{index}}}',
                1,
                1,
            )
            for index in range(25)
        ],
    )
    response = client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}", headers=admin_headers)
    assert response.status_code == 200
    events = response.json()["events"]
    assert len(events) == 20
    assert [event["candidate_count"] for event in events] == list(range(20))


def test_candidate_boundary_endpoint_has_bounded_malformed_scan(client: TestClient, admin_headers: dict[str, str]) -> None:
    rows = [
        (
            "presentation_candidate_boundary_analysis",
            '{"semantic_candidates_state":"INVALID","candidate_count":1}',
            1,
            1,
        )
        for _ in range(200)
    ]
    rows.append(
        ("presentation_candidate_boundary_transport", '{"semantic_candidates_state":"NONEMPTY","candidate_count":7}', 1, 1)
    )
    start, end = _candidate_window_and_seed(client, rows)
    response = client.get(f"/api/analytics/candidate-boundary-events?start={start}&end={end}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["events"] == []
