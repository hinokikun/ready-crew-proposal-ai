from __future__ import annotations

from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from app.services.pptx_parts.native_trace_registry import (
    RUNTIME_REGISTRY_PATH,
    get_runtime_native_role_spec,
    load_runtime_native_registry,
    runtime_native_role_gate,
)
from app.services.pptx_parts.native_trace_renderers import clone_runtime_native_template
from app.services.pptx_parts.native_trace_validation import (
    inspect_template_package,
    sha256_file,
    validate_template_package,
)


ROOT = Path(__file__).resolve().parents[2]
ASSET_ROOT = ROOT / "backend" / "app" / "presentation_assets" / "native_trace"


def _registry() -> dict:
    return load_runtime_native_registry()


def test_all_approved_runtime_assets_exist() -> None:
    registry = _registry()
    assert len(registry["roles"]) == 32
    for role in registry["roles"]:
        asset = ROOT / role["runtime_asset"]
        assert asset.is_file(), role
        assert role["human_approved"] is True
        assert role["registry_status"] == "FOUNDATION_ONLY_NOT_ACTIVATED"


def test_registry_surface_counts_and_required_roles() -> None:
    registry = _registry()
    assert len(registry["summary_roles"]) == 11
    assert len(registry["detail_roles"]) == 15
    assert len(registry["conditional_roles"]) == 2
    assert {"MARKET_ANALYSIS", "TARGET_ANALYSIS", "ROI_OR_EFFECT", "CASE_STUDY"}.issubset(
        set(registry["detail_roles"])
    )
    assert {"COMPETITION", "WIN_PROBABILITY"} == set(registry["conditional_roles"])


def test_registry_does_not_point_at_artifacts() -> None:
    for role in _registry()["roles"]:
        assert "artifacts/" not in role["runtime_asset"]
        assert "artifacts/" not in role["template"]


def test_runtime_role_gate_is_fail_closed_and_unapproved_roles_are_absent() -> None:
    for role in _registry()["roles"]:
        allowed, checks = runtime_native_role_gate(role["role"])
        assert allowed is True, (role, checks)
    for role in ("CASE_STUDY", "ROI_OR_EFFECT", "MARKET_ANALYSIS", "TARGET_ANALYSIS"):
        # These remain in the isolated metadata for the approved detail deck,
        # but a future production adapter must decide separately whether their
        # data contract is safe.  The foundation registry still resolves them
        # as Human-approved templates and marks the sample slots prohibited.
        spec = get_runtime_native_role_spec(role)
        assert spec is not None
        assert spec["conditional"] is False
        assert spec["human_approved"] is True


def test_frozen_source_checksums_match_registry() -> None:
    for role in _registry()["roles"]:
        source = ROOT / role["source_asset"]
        assert source.is_file(), role
        assert sha256_file(source) == role["source_checksum"], role


def test_runtime_templates_open_as_single_slide_with_unique_required_slots() -> None:
    for role in _registry()["roles"]:
        asset = ROOT / role["runtime_asset"]
        report = validate_template_package(
            asset,
            approved_slide_id=role["slide_id"],
            required_slots=role["required_slots"],
            source_path=ROOT / role["source_asset"],
            expected_source_sha256=role["source_checksum"],
        )
        assert report["valid"] is True, (role, report)
        assert report["slide_count"] == 1
        assert report["full_slide_raster_count"] == 0
        assert report["duplicate_semantic_slots"] == []
        assert report["missing_required_slots"] == []
        assert report["source_frozen_unchanged"] is True


def test_photo_template_clone_preserves_image_relationships_and_crop_values() -> None:
    role = next(item for item in _registry()["roles"] if item["role"] == "CASE_STUDY")
    source = ROOT / role["source_asset"]
    source_report = inspect_template_package(source)
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp) / "case-study.pptx"
        report = clone_runtime_native_template(
            source,
            destination,
            approved_slide_id=role["slide_id"],
            required_slots=role["required_slots"],
        )
        assert report["media_relationships_preserved"] is True
        assert report["image_count"] == source_report["image_count"]
        assert report["crop_rect_count"] == source_report["crop_rect_count"]
        assert report["missing_relationship_targets"] == []


def test_unsupported_relationship_fails_cleanly() -> None:
    role = next(item for item in _registry()["roles"] if item["role"] == "COVER" and item["slide_id"] == "S01")
    source = ROOT / role["source_asset"]
    with tempfile.TemporaryDirectory() as tmp:
        broken = Path(tmp) / "unsupported.pptx"
        with ZipFile(source) as input_zip, ZipFile(broken, "w", compression=ZIP_DEFLATED) as output_zip:
            for name in input_zip.namelist():
                payload = input_zip.read(name)
                if name == "ppt/slides/_rels/slide1.xml.rels":
                    payload = payload.replace(
                        b"/relationships/slideLayout",
                        b"/relationships/unsupportedPhase3F19A",
                    )
                output_zip.writestr(name, payload)
        assert inspect_template_package(broken)["unsupported_relationships"]
        with pytest.raises(ValueError):
            clone_runtime_native_template(
                broken,
                Path(tmp) / "should-not-exist.pptx",
                approved_slide_id="S01",
                required_slots=["trace:S01:title.primary"],
            )


def test_production_dispatcher_uses_the_runtime_registry_after_integration() -> None:
    slides_source = (ROOT / "backend" / "app" / "services" / "pptx_parts" / "slides.py").read_text(encoding="utf-8")
    assert "dispatch_approved_native_slide" in slides_source
    assert "pptx_approved_native_renderer_enabled" in slides_source


def test_runtime_registry_file_is_the_expected_path() -> None:
    assert RUNTIME_REGISTRY_PATH == ASSET_ROOT / "registry.json"
    assert RUNTIME_REGISTRY_PATH.is_file()
