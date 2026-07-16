from typing import Any

from fastapi.testclient import TestClient


def _base_payload(project_brief: str) -> dict[str, str]:
    return {
        "project_brief": project_brief,
        "client_company_info": "株式会社サンプル\n担当者：テスト担当",
        "competitor_site_url": "",
        "competitor_company_name": "",
        "estimated_page_count": "",
        "cms_required": "",
        "contact_form_required": "",
        "special_function_required": "",
        "seo_required": "",
        "content_creation_required": "",
        "desired_launch_timing": "",
        "budget_range": "",
        "hearing_result": "",
        "own_service_info": "",
        "past_proposal_template": "",
        "case_studies": "",
    }


def _analyze(client: TestClient, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post("/api/analyze", headers=headers, json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_mock_ai_preserves_ai_ocr_input(client: TestClient, admin_headers: dict[str, str]) -> None:
    payload = _base_payload(
        "請求書をAI-OCRで読み取り、会社名、日付、金額、請求書番号を抽出したい。CSVまたは会計システムへ連携する。"
    )

    data = _analyze(client, admin_headers, payload)
    combined = "\n".join(
        [
            data["analysis"]["project_summary"],
            data["analysis"]["proposal_policy"],
            data["powerpoint_generation_data"]["deck_title"],
        ]
    )

    assert "AI-OCR" in combined
    assert "請求書" in combined or "帳票" in combined
    assert "Webサイト制作" not in combined
    assert "CMS" not in combined
    assert "SEO" not in combined


def test_mock_ai_keeps_web_project_as_web(client: TestClient, admin_headers: dict[str, str]) -> None:
    payload = _base_payload("コーポレートサイトをリニューアルし、CMS導入とSEO改善を行いたい。")

    data = _analyze(client, admin_headers, payload)
    combined = "\n".join(
        [
            data["analysis"]["project_summary"],
            data["powerpoint_generation_data"]["deck_title"],
        ]
    )

    assert "Web" in combined or "サイト" in combined
    assert "CMS" in combined or "SEO" in combined or "改善" in combined
    assert "AI-OCR" not in combined


def test_mock_ai_uses_neutral_unknown_project(client: TestClient, admin_headers: dict[str, str]) -> None:
    payload = _base_payload("工場の設備保全記録をAIで分析し、故障予兆と点検計画の見直しを提案したい。")

    data = _analyze(client, admin_headers, payload)
    combined = "\n".join(
        [
            data["analysis"]["project_summary"],
            data["analysis"]["proposal_policy"],
            data["powerpoint_generation_data"]["deck_title"],
        ]
    )

    assert "設備保全" in combined or "入力案件" in combined
    assert "Webサイト制作" not in combined
    assert "CMS" not in combined
    assert "SEO" not in combined
    assert "AI-OCR" not in combined
