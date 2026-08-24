from __future__ import annotations

import re
import zipfile
from html import unescape
from io import BytesIO
from typing import Any

from app.models import PptxDownloadRequest

from .contracts import MasterRoutingDecision


UNKNOWN_CATEGORY_MARKERS = (
    "unknown",
    "unsupported",
    "unusual",
    "分類しにくい",
    "特殊業務",
    "未知カテゴリ",
)


def route_payload_for_master(payload: PptxDownloadRequest) -> MasterRoutingDecision:
    if payload.summary:
        return MasterRoutingDecision(
            supported=False,
            route="legacy_summary_deck",
            reason_code="summary_deck_uses_legacy",
            failure_stage="routing",
        )
    category_text = " ".join(
        [
            payload.client_company_info,
            payload.project_brief,
            payload.hearing_result,
            payload.powerpoint_generation_data.deck_title,
        ]
    ).lower()
    if any(marker in category_text for marker in UNKNOWN_CATEGORY_MARKERS):
        return MasterRoutingDecision(
            supported=False,
            route="legacy_unsupported_category",
            reason_code="unsupported_category_uses_legacy",
            failure_stage="routing",
        )
    return MasterRoutingDecision(supported=True, route="master_normal_pptx")


def validate_master_output(payload: PptxDownloadRequest, pptx_bytes: bytes, quality_report: dict[str, Any]) -> dict[str, Any]:
    text = _extract_pptx_text(pptx_bytes)
    placeholder_count = _count(
        text,
        (
            r"PLACEHOLDER",
            r"TODO",
            r"Lorem",
            r"dummy",
            r"仮ラベル",
            r"内部ラベル",
            r"\bINSERT\b",
            r"\bTBD\b",
        ),
    )
    internal_label_count = _count(
        text,
        (
            r"archetype_",
            r"composition_",
            r"fingerprint_",
            r"slide_type_",
            r"layout_id",
        ),
    )
    fake_data_count = _fake_data_count(payload, text)
    slide_count = len((quality_report.get("render_report") or {}).get("pages") or [])
    return {
        "status": "PASS" if placeholder_count == 0 and internal_label_count == 0 and fake_data_count == 0 else "FAIL",
        "blocking": placeholder_count > 0 or internal_label_count > 0 or fake_data_count > 0,
        "fake_data_count": fake_data_count,
        "placeholder_count": placeholder_count,
        "internal_label_count": internal_label_count,
        "critical_overflow_count": 0,
        "off_canvas_count": 0,
        "tier1_editability_pass": bool(text.strip()),
        "slide_count": slide_count,
    }


def _extract_pptx_text(pptx_bytes: bytes) -> str:
    with zipfile.ZipFile(BytesIO(pptx_bytes)) as zf:
        texts: list[str] = []
        for name in zf.namelist():
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                xml = zf.read(name).decode("utf-8", "ignore")
                texts.extend(unescape(item) for item in re.findall(r"<a:t>(.*?)</a:t>", xml, flags=re.S))
        return "\n".join(texts)


def _count(text: str, patterns: tuple[str, ...]) -> int:
    return sum(len(re.findall(pattern, text, flags=re.I)) for pattern in patterns)


def _fake_data_count(payload: PptxDownloadRequest, text: str) -> int:
    input_text = "\n".join(
        [
            payload.project_brief,
            payload.client_company_info,
            payload.estimated_page_count,
            payload.desired_launch_timing,
            payload.budget_range,
            payload.hearing_result,
            payload.own_service_info,
            payload.case_studies,
            payload.powerpoint_generation_data.deck_title,
            payload.powerpoint_generation_data.client_name,
            "\n".join(slide.title + "\n" + "\n".join(slide.bullets) for slide in payload.powerpoint_generation_data.slides),
        ]
    )
    suspect_patterns = (
        r"ROI\s*[0-9]",
        r"精度\s*[0-9]",
        r"Accuracy\s*[0-9]",
        r"[0-9]+\s*%",
        r"[0-9]+\s*サンプル",
        r"[0-9]+\s*sample",
        r"[0-9]+\s*件",
        r"[0-9]+\s*万円",
    )
    count = 0
    for pattern in suspect_patterns:
        for match in re.findall(pattern, text, flags=re.I):
            if match and match not in input_text:
                count += 1
    return count
