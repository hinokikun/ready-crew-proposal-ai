from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


SNAPSHOT_DIR = Path(__file__).with_name("snapshots")
PPTX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def _shape_text(shape: Any) -> str:
    if not getattr(shape, "has_text_frame", False):
        return ""
    return "\n".join(paragraph.text for paragraph in shape.text_frame.paragraphs).strip()


def _font_names(prs: Presentation) -> list[str]:
    names: set[str] = set()
    for slide in prs.slides:
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False):
                continue
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    if run.font.name:
                        names.add(run.font.name)
    return sorted(names)


def _broken_relationship_count(prs: Presentation) -> int:
    broken = 0
    for slide in prs.slides:
        for relationship in slide.part.rels.values():
            try:
                _ = relationship.target_ref
            except Exception:
                broken += 1
    return broken


def extract_pptx_structure(content: bytes) -> dict[str, Any]:
    prs = Presentation(BytesIO(content))
    slides = []
    for index, slide in enumerate(prs.slides, start=1):
        text_values = [_shape_text(shape) for shape in slide.shapes]
        non_empty_text = [text for text in text_values if text]
        slides.append(
            {
                "index": index,
                "title": non_empty_text[0] if non_empty_text else "",
                "shape_count": len(slide.shapes),
                "text_shape_count": sum(1 for text in text_values if text),
                "table_count": sum(1 for shape in slide.shapes if getattr(shape, "has_table", False)),
                "chart_count": sum(1 for shape in slide.shapes if getattr(shape, "has_chart", False)),
                "picture_count": sum(1 for shape in slide.shapes if shape.shape_type == MSO_SHAPE_TYPE.PICTURE),
            }
        )
    return {
        "slide_count": len(prs.slides),
        "slide_width": prs.slide_width,
        "slide_height": prs.slide_height,
        "total_shapes": sum(slide["shape_count"] for slide in slides),
        "total_tables": sum(slide["table_count"] for slide in slides),
        "total_charts": sum(slide["chart_count"] for slide in slides),
        "total_pictures": sum(slide["picture_count"] for slide in slides),
        "font_names": _font_names(prs),
        "broken_relationship_count": _broken_relationship_count(prs),
        "slides": slides,
    }


def _load_snapshot(name: str) -> dict[str, Any]:
    return json.loads((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _assert_pptx_matches_snapshot(response_content: bytes, snapshot_name: str) -> None:
    assert response_content[:2] == b"PK"
    assert len(response_content) > 10_000
    actual = extract_pptx_structure(response_content)
    expected = _load_snapshot(snapshot_name)
    assert actual == expected
    assert actual["broken_relationship_count"] == 0
    assert all(slide["text_shape_count"] > 0 for slide in actual["slides"])


def test_detailed_pptx_structure_matches_snapshot(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    response = client.post("/api/download-pptx", headers=admin_headers, json=sample_pptx_payload)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(PPTX_MEDIA_TYPE)
    _assert_pptx_matches_snapshot(response.content, "detailed_pptx_structure.json")


def test_summary_pptx_structure_matches_snapshot(
    client: TestClient,
    admin_headers: dict[str, str],
    sample_pptx_payload: dict[str, Any],
) -> None:
    response = client.post(
        "/api/download-pptx",
        headers=admin_headers,
        json={**sample_pptx_payload, "summary": True},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(PPTX_MEDIA_TYPE)
    _assert_pptx_matches_snapshot(response.content, "summary_pptx_structure.json")
