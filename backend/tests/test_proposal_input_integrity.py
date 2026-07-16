from html import unescape
from io import BytesIO
import json
import re
from typing import Any
from zipfile import ZipFile

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


WEB_FORBIDDEN_TERMS = [
    "Webサイト制作",
    "Web戦略",
    "サイトマップ",
    "SEO",
    "CMS",
    "ワイヤーフレーム",
    "フロントエンド実装",
    "デザイン制作",
    "自然検索流入",
    "問い合わせ導線",
]


def _pptx_text(blob: bytes) -> str:
    fragments: list[str] = []
    with ZipFile(BytesIO(blob)) as deck:
        for name in deck.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                xml = deck.read(name).decode("utf-8", errors="ignore")
                fragments.append(unescape(re.sub(r"<[^>]+>", " ", xml)))
    return "\n".join(fragments)


def _story_text(items: list[Any]) -> str:
    fragments: list[str] = []

    def collect(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            fragments.append(value)
            return
        text = getattr(value, "text", "")
        if text:
            fragments.append(str(text))
        cells = getattr(value, "_cellvalues", None)
        if cells:
            for row in cells:
                for cell in row:
                    collect(cell)
        if isinstance(value, (list, tuple)):
            for item in value:
                collect(item)

    collect(items)
    return "\n".join(fragments)


def test_mock_ai_preserves_ai_ocr_input(client: TestClient, admin_headers: dict[str, str]) -> None:
    payload = _base_payload(
        "請求書をAI-OCRで読み取り、会社名、日付、金額、請求書番号を抽出したい。CSVまたは会計システムへ連携する。"
    )

    data = _analyze(client, admin_headers, payload)
    combined = json.dumps(data["analysis"], ensure_ascii=False)

    assert "AI-OCR" in combined
    assert "請求書" in combined or "帳票" in combined
    assert "PoC" in combined
    assert "AIモデル学習" in combined
    assert "API/CSV" in combined or "API連携" in combined
    for term in WEB_FORBIDDEN_TERMS:
        assert term not in combined


def test_ai_ocr_pptx_and_pdf_estimate_are_not_web_templates(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    from app.models import PptxDownloadRequest
    from app.services.pdf_service import build_estimate_pdf_story, register_japanese_fonts
    from app.services.pptx_service import build_pptx_bytes, build_pptx_context

    payload = _base_payload(
        "請求書をAI-OCRで読み取り、会社名、日付、金額、請求書番号を抽出したい。CSVまたは会計システムへ連携する。"
    )
    data = _analyze(client, admin_headers, payload)
    request = PptxDownloadRequest(
        **payload,
        powerpoint_generation_data=data["powerpoint_generation_data"],
        win_probability=data["analysis"]["win_probability"],
    )

    context = build_pptx_context(request)
    assert context.proposal_category == "ai_ocr"
    estimate_text = "\n".join(str(line.get("name", "")) for line in context.estimate.lines)
    assert "PoC設計・検証" in estimate_text
    assert "AIモデル学習・精度改善" in estimate_text
    assert "API/CSV連携" in estimate_text
    for term in WEB_FORBIDDEN_TERMS:
        assert term not in estimate_text

    deck_text = _pptx_text(build_pptx_bytes(request))
    assert "AI-OCR" in deck_text
    assert "導入構成" in deck_text
    for term in WEB_FORBIDDEN_TERMS:
        assert term not in deck_text

    register_japanese_fonts()
    pdf_story = _story_text(build_estimate_pdf_story(request, 520))
    assert "PoC設計・検証" in pdf_story
    assert "AIモデル学習・精度改善" in pdf_story
    for term in WEB_FORBIDDEN_TERMS:
        assert term not in pdf_story


def test_ai_ocr_beautiful_ai_prompt_is_category_specific(client: TestClient, admin_headers: dict[str, str]) -> None:
    from app.beautiful_ai.presentation_mapper import map_to_beautiful_ai_payload
    from app.beautiful_ai.schemas import BeautifulAiPresentationRequest

    payload = _base_payload(
        "請求書をAI-OCRで読み取り、会社名、日付、金額、請求書番号を抽出したい。CSVまたは会計システムへ連携する。"
    )
    data = _analyze(client, admin_headers, payload)
    request = BeautifulAiPresentationRequest(
        **payload,
        project_id="ai-ocr-integrity",
        powerpoint_generation_data=data["powerpoint_generation_data"],
        win_probability=data["analysis"]["win_probability"],
    )

    mapped = map_to_beautiful_ai_payload(request)
    prompt = mapped.prompt
    assert "案件カテゴリ: AI-OCR" in prompt
    assert "請求書" in prompt or "帳票" in prompt
    assert "AIモデル学習" in prompt or "API/CSV" in prompt or "例外確認" in prompt
    for term in WEB_FORBIDDEN_TERMS:
        assert term not in prompt


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
