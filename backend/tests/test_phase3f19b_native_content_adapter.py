from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
from zipfile import ZipFile
import xml.etree.ElementTree as ET

import pytest

from app.services.pptx_parts.native_trace_content_adapter import (
    FailureReason,
    NativeSlotPayload,
    ROLE_ADAPTERS,
    adapt_role,
    adapter_registry_summary,
    preflight_text_fit,
    render_native_role_dry_run,
    write_slot_payload,
)
from app.services.pptx_parts.native_trace_registry import load_runtime_native_registry
from app.services.pptx_parts.native_trace_validation import (
    clone_template_package,
    inspect_template_package,
    sha256_file,
    validate_injected_template_package,
)


ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "backend" / "app" / "presentation_assets" / "native_trace"


def _asset(surface: str, role: str) -> Path:
    registry = load_runtime_native_registry()
    item = next(item for item in registry["roles"] if item["surface"] == surface and item["role"] == role)
    return ROOT / item["runtime_asset"]


def _slide(title: str = "テスト案件") -> SimpleNamespace:
    return SimpleNamespace(title=title)


def _xml_text(path: Path) -> str:
    with ZipFile(path, "r") as package:
        return "\n".join(
            package.read(name).decode("utf-8", errors="ignore")
            for name in package.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )


def _slot_text(path: Path, slot: str) -> str:
    with ZipFile(path, "r") as package:
        for name in package.namelist():
            if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                continue
            root = ET.fromstring(package.read(name))
            for shape in root.iter():
                if shape.tag.rsplit("}", 1)[-1] not in {"sp", "pic", "graphicFrame", "grpSp", "cxnSp"}:
                    continue
                names = [node.attrib.get("name", "") for node in shape.iter() if node.tag.rsplit("}", 1)[-1] == "cNvPr"]
                if slot in names:
                    return "".join(node.text or "" for node in shape.iter() if node.tag.rsplit("}", 1)[-1] == "t")
    return ""


def test_adapter_registry_covers_every_runtime_role() -> None:
    registry = load_runtime_native_registry()
    assert len(registry["roles"]) == 32
    assert len(ROLE_ADAPTERS) == 32
    for role in registry["roles"]:
        assert (role["surface"], role["role"]) in ROLE_ADAPTERS
    assert adapter_registry_summary()["production_dispatch_connected"] is True


def test_contracts_are_role_specific_and_have_fit_controls() -> None:
    registry = load_runtime_native_registry()
    contracts = __import__(
        "json"
    ).loads((ASSET_ROOT / "schemas" / "role_contracts.json").read_text(encoding="utf-8"))
    assert len(contracts["roles"]) == 32
    assert contracts["activation_status"] == "ADAPTER_ONLY_NOT_ACTIVATED"
    for item in contracts["roles"]:
        assert item["required_slots"]
        assert item["sample_content_policy"] == "STATIC_SAMPLE_PROHIBITED"
        assert item["slot_constraints"]["title.primary"]["minimum_font_size"] > 0
        assert "evidence_sensitive" in item
    assert {item["role"] for item in registry["roles"]} == {item["role"] for item in contracts["roles"]}


def test_summary_detail_and_conditional_dispatch_is_explicit() -> None:
    assert adapt_role("COVER", surface="summary", slide=_slide()).failure_reason is None
    assert adapt_role("COVER", surface="detail", slide=_slide()).failure_reason is None
    assert adapt_role("COMPETITION", surface="conditional", slide=_slide()).failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert adapt_role("COMPETITIVE_COMPARISON", surface="conditional", slide=_slide()).failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert adapt_role("WIN_PROBABILITY", surface="conditional", slide=_slide()).failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_unknown_role_fails_closed() -> None:
    payload = adapt_role("NOT_A_REGISTERED_ROLE", surface="summary", slide=_slide())
    assert payload.renderable is False
    assert payload.failure_reason == FailureReason.ROLE_NOT_REGISTERED.value


def test_static_template_is_not_mutated_by_dry_run() -> None:
    source = _asset("summary", "COVER")
    before = sha256_file(source)
    result = render_native_role_dry_run("COVER", slide=_slide("現在案件"), surface="summary")
    assert result.success is True
    assert sha256_file(source) == before
    assert result.package_path and Path(result.package_path).is_file()


def test_dynamic_title_is_injected_into_runtime_copy() -> None:
    result = render_native_role_dry_run("COVER", slide=_slide("現在案件のタイトル"), surface="summary")
    assert result.success is True
    assert "trace:S01:title.primary" in result.injected_slots
    assert _slot_text(Path(result.package_path), "trace:S01:title.primary") == "現在案件のタイトル"


def test_optional_text_can_be_cleared_without_geometry_change() -> None:
    source = _asset("summary", "COVER")
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "cover.pptx"
        clone_template_package(source, target, approved_slide_id="S01", required_slots=["trace:S01:title.primary", "trace:S01:footer.brand"])
        sample = _slot_text(target, "trace:S01:footer.tagline.jp")
        assert sample
        payload = NativeSlotPayload(
            role="COVER",
            slide_id="S01",
            surface="summary",
            slots={"trace:S01:title.primary": "現在案件"},
            clear_matching_text=[sample],
        )
        before = inspect_template_package(target)
        report = write_slot_payload(target, payload, required_slots=["trace:S01:title.primary", "trace:S01:footer.brand"])
        after = inspect_template_package(target)
        assert report["injected_slots"] == ["trace:S01:title.primary"]
        assert sample not in _xml_text(target)
        assert before["slide_size_emu"] == after["slide_size_emu"]
        assert before["image_count"] == after["image_count"]


def test_unbound_required_title_fails_before_clone() -> None:
    payload = adapt_role("COVER", surface="summary")
    assert payload.renderable is False
    assert payload.failure_reason == FailureReason.UNBOUND_REQUIRED_CONTENT.value
    assert "trace:S01:title.primary" in payload.unresolved_required_slots


def test_sample_leak_detector_blocks_prohibited_text() -> None:
    source = _asset("summary", "COVER")
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "cover.pptx"
        clone_template_package(source, target, approved_slide_id="S01", required_slots=["trace:S01:title.primary", "trace:S01:footer.brand"])
        sample = _slot_text(target, "trace:S01:header.brand")
        report = validate_injected_template_package(
            target,
            source_template=source,
            approved_slide_id="S01",
            required_slots=["trace:S01:title.primary", "trace:S01:footer.brand"],
            prohibited_sample_strings=[sample],
            text_fit_diagnostics={"valid": True, "fields": {}},
        )
        assert report["sample_content_leak_free"] is False
        assert report["valid"] is False


def test_text_fit_accepts_contract_safe_content() -> None:
    fit = preflight_text_fit("提案クエスト", max_characters=32, max_lines=2)
    assert fit["valid"] is True
    assert fit["status"] == "FIT"


def test_text_fit_rejects_unhandled_overflow() -> None:
    fit = preflight_text_fit("長すぎる文章" * 20, max_characters=10, max_lines=1, allow_font_shrink=False)
    assert fit["valid"] is False
    assert fit["status"] == "TEXT_OVERFLOW_RISK"


def test_rich_text_payload_preserves_editability_and_applies_accent() -> None:
    source = _asset("summary", "SOLUTION_CONCEPT")
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "rich.pptx"
        clone_template_package(source, target, approved_slide_id="S05", required_slots=["trace:S05:title.primary", "trace:S05:footer.brand"])
        payload = NativeSlotPayload(
            role="SOLUTION_CONCEPT",
            slide_id="S05",
            surface="summary",
            slots={
                "trace:S05:title.primary": [
                    {"text": "提案", "style": "accent_red"},
                    {"text": "コンセプト", "style": "default"},
                ]
            },
        )
        report = write_slot_payload(target, payload, required_slots=["trace:S05:title.primary", "trace:S05:footer.brand"])
        assert report["unresolved_required_slots"] == []
        xml = _xml_text(target)
        assert "提案" in xml and "コンセプト" in xml and "D71920" in xml
        assert inspect_template_package(target)["full_slide_raster_count"] == 0


def test_kpi_adapter_never_returns_canonical_actuals_without_evidence() -> None:
    payload = adapt_role("KPI", surface="summary", slide=_slide())
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert "20時間/件" not in payload.slots.values()
    assert payload.diagnostics[0]["fallback"] == "未取得"


def test_estimate_adapter_requires_verified_current_prices() -> None:
    context = SimpleNamespace(estimate=SimpleNamespace(total_label="￥10,500,000"))
    payload = adapt_role("ESTIMATE", context=context, surface="summary", slide=_slide())
    assert payload.failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert "￥10,500,000" not in payload.slots.values()


def test_market_and_roi_adapters_fail_without_current_evidence() -> None:
    market = adapt_role("MARKET_ANALYSIS", surface="detail", slide=_slide())
    roi = adapt_role("ROI_OR_EFFECT", surface="detail", slide=_slide())
    assert market.failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert roi.failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_d20_requires_verified_image_and_never_uses_canonical_photo() -> None:
    payload = adapt_role("CASE_STUDY", surface="detail", context=SimpleNamespace(case_studies=[{"name": "テスト"}]), slide=_slide())
    assert payload.failure_reason == FailureReason.EVIDENCE_IMAGE_REQUIRED.value
    assert payload.source_fields["case_study.image"] == "unbound"
    assert not any(key.endswith(":image.1") for key in payload.slots)


def test_d20_text_does_not_fabricate_metrics_or_quote() -> None:
    payload = adapt_role("CASE_STUDY", surface="detail", context=SimpleNamespace(case_studies=[]), slide=_slide())
    assert payload.renderable is False
    assert all("FAJ" not in str(value) for value in payload.slots.values())
    assert all("約" not in str(value) for value in payload.slots.values())
    assert "FAJ" in payload.prohibited_sample_strings


def test_competition_on_and_off_are_both_fail_closed_without_provenance() -> None:
    off = adapt_role("COMPETITION", surface="conditional", slide=_slide())
    on = adapt_role("COMPETITION", surface="conditional", context=SimpleNamespace(competitor_rows=[{"name": "競合"}]), slide=_slide())
    assert off.failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert on.failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert on.evidence_status["competition.rows"] == "UNKNOWN"


def test_win_probability_requires_explicit_provenance_before_binding() -> None:
    off = adapt_role("WIN_PROBABILITY", surface="conditional", slide=_slide())
    on = adapt_role("WIN_PROBABILITY", surface="conditional", context=SimpleNamespace(win_probability=SimpleNamespace(probability="68%")), slide=_slide())
    assert off.failure_reason == FailureReason.EVIDENCE_REQUIRED.value
    assert on.failure_reason == FailureReason.EVIDENCE_REQUIRED.value


def test_photo_and_crop_relationships_survive_runtime_clone() -> None:
    source = _asset("detail", "CASE_STUDY")
    with tempfile.TemporaryDirectory() as temp_dir:
        target = Path(temp_dir) / "case.pptx"
        clone_report = clone_template_package(source, target, approved_slide_id="D20", required_slots=["trace:D20:title.primary", "trace:D20:footer.brand"])
        source_report = inspect_template_package(source)
        target_report = inspect_template_package(target)
        assert clone_report["media_relationships_preserved"] is True
        assert target_report["image_count"] == source_report["image_count"]
        assert target_report["crop_values"] == source_report["crop_values"]


def test_injected_packages_remain_editable_and_raster_free() -> None:
    for surface, role in (("summary", "COVER"), ("detail", "CLOSING"), ("conditional", "WIN_PROBABILITY")):
        source = _asset(surface, role)
        report = inspect_template_package(source)
        assert report["editable_text_shape_count"] > 0
        assert report["editable_shape_count"] > 0
        assert report["full_slide_raster_count"] == 0


def test_runtime_source_checksums_remain_unchanged_after_adapter_calls() -> None:
    source = _asset("summary", "COVER")
    before = sha256_file(source)
    render_native_role_dry_run("COVER", slide=_slide("確認"), surface="summary")
    assert sha256_file(source) == before


def test_production_dispatcher_is_connected_at_the_existing_dispatch_point() -> None:
    summary = adapter_registry_summary()
    assert summary["production_dispatch_connected"] is True
    assert not (ROOT / "backend" / "app" / "services" / "pptx_parts" / "native_trace_content_adapter.py").resolve().samefile(
        ROOT / "backend" / "app" / "services" / "pptx_parts" / "slides.py"
    )
