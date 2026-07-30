from __future__ import annotations

from typing import Any

from app.beautiful_ai.presentation_mapper import map_to_beautiful_ai_payload
from app.beautiful_ai.schemas import BeautifulAiPresentationRequest
from app.models import PptxDownloadRequest
from app.services.pptx_service import build_pptx_context, build_pptx_result
from app.services.proposal_quality_upgrade import upgrade_slides_for_v11


def test_v11_quality_upgrade_adds_customer_facing_story_slides(sample_pptx_payload: dict[str, Any]) -> None:
    payload = PptxDownloadRequest(**sample_pptx_payload)
    context = build_pptx_context(payload)

    upgraded = upgrade_slides_for_v11(payload.powerpoint_generation_data.slides, context, summary_mode=False)

    titles = {slide.title for slide in upgraded}
    assert "経営判断の要点" in titles
    assert "本提案の結論と期待効果" in titles
    assert "課題から導入判断までの流れ" in titles
    assert "選定基準と勝ち筋を明確にします" in titles
    assert "KPIは現状値から測定します" in titles
    assert "費用は必須・推奨・任意で説明します" in titles
    assert "リスクは役割分担で抑えます" in titles
    assert "次回は範囲・KPI・体制を合意します" in titles
    assert "提出前レビュー" in titles

    body = "\n".join("\n".join(slide.bullets) for slide in upgraded)
    assert "なぜ今" in body
    assert "比較対象" in body
    assert "測定方法" in body
    assert "ROI" in body
    assert "次回" in body


def test_v11_quality_upgrade_avoids_three_identical_layouts(sample_pptx_payload: dict[str, Any]) -> None:
    payload = PptxDownloadRequest(**sample_pptx_payload)
    context = build_pptx_context(payload)
    upgraded = upgrade_slides_for_v11(payload.powerpoint_generation_data.slides * 5, context, summary_mode=False)

    for index in range(2, len(upgraded)):
        layouts = [upgraded[index - offset].layout for offset in (0, 1, 2)]
        assert len(set(layouts)) > 1


def test_v11_summary_pptx_keeps_existing_summary_limit(sample_pptx_payload: dict[str, Any]) -> None:
    payload = PptxDownloadRequest(**{**sample_pptx_payload, "summary": True})

    result = build_pptx_result(payload)

    assert result.quality_report.slide_count_after <= 12
    assert result.quality_report.overall_score > 0


def test_beautiful_ai_prompt_contains_v11_design_direction(sample_pptx_payload: dict[str, Any]) -> None:
    request = BeautifulAiPresentationRequest(
        project_id="v11-quality",
        powerpoint_generation_data=sample_pptx_payload["powerpoint_generation_data"],
        project_brief=sample_pptx_payload["project_brief"],
        client_company_info=sample_pptx_payload["client_company_info"],
        competitor_company_name=sample_pptx_payload["competitor_company_name"],
        desired_launch_timing=sample_pptx_payload["desired_launch_timing"],
        budget_range=sample_pptx_payload["budget_range"],
        special_function_required=sample_pptx_payload["special_function_required"],
    )

    payload = map_to_beautiful_ai_payload(request)

    assert "Version 1.1 design direction" in payload.prompt
    assert "comparison cards" in payload.prompt
    assert "SMART framing" in payload.prompt
    assert "required, recommended, optional" in payload.prompt
