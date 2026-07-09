from fastapi.testclient import TestClient


def test_analyze_generates_markdown_and_saves_logs(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_proposal_payload: dict,
) -> None:
    response = client.post("/api/analyze", headers=admin_headers, json=sample_proposal_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["markdown"]
    assert body["powerpoint_generation_data"]["slides"]

    crm_response = client.get("/api/projects/crm", headers=admin_headers)
    assert crm_response.status_code == 200
    assert crm_response.json()["projects"]

    logs_response = client.get("/api/logs", headers=admin_headers)
    assert logs_response.status_code == 200
    assert logs_response.json()["logs"]


def test_pptx_download_returns_powerpoint(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict,
) -> None:
    response = client.post("/api/download-pptx", headers=admin_headers, json=sample_pptx_payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/vnd.openxmlformats-officedocument.presentationml.presentation")
    assert response.content[:2] == b"PK"


def test_summary_pptx_download_returns_powerpoint(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict,
) -> None:
    response = client.post(
        "/api/download-pptx",
        headers=admin_headers,
        json={**sample_pptx_payload, "summary": True},
    )

    assert response.status_code == 200
    assert response.content[:2] == b"PK"
    assert "%E8%A6%81%E7%B4%84%E7%89%88" in response.headers.get("content-disposition", "")


def test_estimate_pdf_download_returns_pdf(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict,
) -> None:
    response = client.post("/api/download-estimate-pdf", headers=admin_headers, json=sample_pptx_payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")
