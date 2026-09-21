"""Foundation validation and runtime-copy helpers for approved native traces.

This module operates on the OOXML package directly.  It intentionally does
not re-save a presentation through a high-level library: copying the package
as-is preserves image relationships, crop rectangles, custom geometry, and
the approved editable shapes.  The only runtime-copy mutation performed here
is the addition of non-visible semantic names to ``p:cNvPr`` elements.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
import shutil
from tempfile import NamedTemporaryFile
from typing import Any, Iterable
from zipfile import ZIP_DEFLATED, ZipFile, is_zipfile
import xml.etree.ElementTree as ET


NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}

ALLOWED_RELATIONSHIP_TYPES = frozenset(
    {
        f"{NS['r']}/image",
        f"{NS['r']}/notesSlide",
        f"{NS['r']}/slideLayout",
        f"{NS['r']}/hyperlink",
        f"{NS['r']}/chart",
        f"{NS['r']}/media",
        f"{NS['r']}/oleObject",
    }
)

_EMU_PER_INCH = 914400
_SLIDE_XML_RE = re.compile(r"^ppt/slides/slide(\d+)\.xml$")
_REL_XML_RE = re.compile(r"^ppt/slides/_rels/slide(\d+)\.xml\.rels$")


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _iter_descendants(element: ET.Element, local_name: str) -> Iterable[ET.Element]:
    for child in element.iter():
        if _local_name(child.tag) == local_name:
            yield child


def _safe_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _slide_dimensions(root: ET.Element) -> tuple[int, int]:
    slide_size = next((node for node in root.iter() if _local_name(node.tag) == "sldSz"), None)
    if slide_size is None:
        return 0, 0
    return _safe_int(slide_size.attrib.get("cx")) or 0, _safe_int(slide_size.attrib.get("cy")) or 0


def _resolve_target(package_path: str, target: str) -> str:
    base = Path(package_path).parent
    # Targets in slide relationship parts are relative to ppt/slides/.
    if package_path.startswith("ppt/slides/"):
        base = Path("ppt/slides")
    normalized = (base / target).as_posix()
    parts: list[str] = []
    for part in normalized.split("/"):
        if part in {"", "."}:
            continue
        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


def _shape_transform(shape: ET.Element) -> tuple[int, int, int, int]:
    xfrm = next((node for node in shape.iter() if _local_name(node.tag) == "xfrm"), None)
    if xfrm is None:
        return 0, 0, 0, 0
    off = next((node for node in xfrm if _local_name(node.tag) == "off"), None)
    ext = next((node for node in xfrm if _local_name(node.tag) == "ext"), None)
    if off is None or ext is None:
        return 0, 0, 0, 0
    return (
        _safe_int(off.attrib.get("x")) or 0,
        _safe_int(off.attrib.get("y")) or 0,
        _safe_int(ext.attrib.get("cx")) or 0,
        _safe_int(ext.attrib.get("cy")) or 0,
    )


def _shape_elements(slide_root: ET.Element) -> Iterable[ET.Element]:
    tree = next((node for node in slide_root.iter() if _local_name(node.tag) == "spTree"), None)
    if tree is None:
        return
    for child in list(tree):
        if _local_name(child.tag) in {"sp", "pic", "graphicFrame", "grpSp", "cxnSp"}:
            yield child


def _text_of_shape(shape: ET.Element) -> str:
    return "".join(node.text or "" for node in _iter_descendants(shape, "t"))


def _shape_kind(shape: ET.Element) -> str:
    return _local_name(shape.tag)


def _relationship_report(zip_file: ZipFile, slide_number: int) -> dict[str, Any]:
    rel_path = f"ppt/slides/_rels/slide{slide_number}.xml.rels"
    if rel_path not in zip_file.namelist():
        return {"types": [], "unsupported": [], "missing_targets": [], "image_relationships": []}
    root = ET.fromstring(zip_file.read(rel_path))
    types: list[str] = []
    unsupported: list[str] = []
    missing_targets: list[str] = []
    image_relationships: list[dict[str, Any]] = []
    for rel in root:
        rel_type = rel.attrib.get("Type", "")
        target = rel.attrib.get("Target", "")
        types.append(rel_type)
        if rel_type not in ALLOWED_RELATIONSHIP_TYPES:
            unsupported.append(rel_type)
        target_path = _resolve_target(rel_path, target)
        if not rel.attrib.get("TargetMode") and target_path not in zip_file.namelist():
            missing_targets.append(target_path)
        if rel_type == f"{NS['r']}/image":
            image_relationships.append({"id": rel.attrib.get("Id"), "target": target_path})
    return {
        "types": sorted(types),
        "unsupported": sorted(set(unsupported)),
        "missing_targets": sorted(set(missing_targets)),
        "image_relationships": image_relationships,
    }


def _package_slide_numbers(zip_file: ZipFile) -> list[int]:
    numbers: list[int] = []
    for name in zip_file.namelist():
        match = _SLIDE_XML_RE.match(name)
        if match:
            numbers.append(int(match.group(1)))
    return sorted(numbers)


def inspect_template_package(path: str | Path) -> dict[str, Any]:
    """Return package, editability, media, geometry, and relationship facts."""

    source = Path(path)
    report: dict[str, Any] = {
        "path": str(source),
        "exists": source.is_file(),
        "package_valid": False,
        "slide_count": 0,
        "slide_size_emu": [0, 0],
        "text_count": 0,
        "editable_shape_count": 0,
        "editable_text_shape_count": 0,
        "image_count": 0,
        "media_count": 0,
        "media_files": [],
        "crop_rect_count": 0,
        "crop_values": [],
        "full_slide_raster_count": 0,
        "unexpected_media": [],
        "relationship_types": [],
        "unsupported_relationships": [],
        "missing_relationship_targets": [],
        "semantic_slots": [],
        "duplicate_semantic_slots": [],
        "font_families": [],
        "errors": [],
    }
    if not source.is_file():
        report["errors"].append("template_missing")
        return report
    if not is_zipfile(source):
        report["errors"].append("not_a_zip_package")
        return report

    try:
        with ZipFile(source) as package:
            names = set(package.namelist())
            if "[Content_Types].xml" not in names or "ppt/presentation.xml" not in names:
                report["errors"].append("missing_presentation_parts")
                return report
            presentation_root = ET.fromstring(package.read("ppt/presentation.xml"))
            report["slide_size_emu"] = list(_slide_dimensions(presentation_root))
            slide_numbers = _package_slide_numbers(package)
            report["slide_count"] = len(slide_numbers)
            media_files = sorted(name for name in names if name.startswith("ppt/media/"))
            report["media_files"] = media_files
            report["media_count"] = len(media_files)
            referenced_media: set[str] = set()
            relationship_types: set[str] = set()
            unsupported: set[str] = set()
            missing_targets: set[str] = set()
            for slide_number in slide_numbers:
                slide_path = f"ppt/slides/slide{slide_number}.xml"
                slide_root = ET.fromstring(package.read(slide_path))
                slide_w, slide_h = report["slide_size_emu"]
                for shape in _shape_elements(slide_root):
                    kind = _shape_kind(shape)
                    text = _text_of_shape(shape)
                    if text:
                        report["editable_text_shape_count"] += 1
                        report["text_count"] += len(list(_iter_descendants(shape, "t")))
                    if kind in {"sp", "pic", "graphicFrame", "grpSp", "cxnSp"}:
                        report["editable_shape_count"] += 1
                    if kind == "pic":
                        report["image_count"] += 1
                        x, y, cx, cy = _shape_transform(shape)
                        if slide_w and slide_h and x == 0 and y == 0 and cx == slide_w and cy == slide_h:
                            report["full_slide_raster_count"] += 1
                    for crop in _iter_descendants(shape, "srcRect"):
                        report["crop_rect_count"] += 1
                        report["crop_values"].append(dict(crop.attrib))
                    for c_nv_pr in _iter_descendants(shape, "cNvPr"):
                        name = c_nv_pr.attrib.get("name", "")
                        if name.startswith("trace:"):
                            report["semantic_slots"].append(name)
                rel_report = _relationship_report(package, slide_number)
                relationship_types.update(rel_report["types"])
                unsupported.update(rel_report["unsupported"])
                missing_targets.update(rel_report["missing_targets"])
                referenced_media.update(item["target"] for item in rel_report["image_relationships"])
            report["relationship_types"] = sorted(relationship_types)
            report["unsupported_relationships"] = sorted(unsupported)
            report["missing_relationship_targets"] = sorted(missing_targets)
            report["unexpected_media"] = sorted(set(media_files) - referenced_media)
            counts: dict[str, int] = {}
            for slot in report["semantic_slots"]:
                counts[slot] = counts.get(slot, 0) + 1
            report["duplicate_semantic_slots"] = sorted(slot for slot, count in counts.items() if count > 1)
            font_families: set[str] = set()
            for name in names:
                if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                    xml = package.read(name).decode("utf-8", errors="ignore")
                    font_families.update(re.findall(r"(?:typeface|font)=[\"']([^\"']+)[\"']", xml))
            report["font_families"] = sorted(font_families)
            report["package_valid"] = not report["errors"]
    except (OSError, ET.ParseError, ValueError, KeyError, RuntimeError) as exc:
        report["errors"].append(f"package_read_error:{type(exc).__name__}:{exc}")
    return report


def validate_template_package(
    path: str | Path,
    *,
    approved_slide_id: str | None = None,
    required_slots: Iterable[str] = (),
    source_path: str | Path | None = None,
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    report = inspect_template_package(path)
    required = sorted(set(required_slots))
    present = set(report.get("semantic_slots", []))
    report["approved_slide_id"] = approved_slide_id
    report["required_slots"] = required
    report["missing_required_slots"] = sorted(slot for slot in required if slot not in present)
    report["source_frozen_unchanged"] = None
    report["source_sha256"] = sha256_file(path) if report.get("exists") else None
    if source_path is not None and Path(source_path).is_file():
        source_hash = sha256_file(source_path)
        report["source_sha256"] = source_hash
        report["runtime_sha256"] = sha256_file(path) if report.get("exists") else None
        report["source_frozen_unchanged"] = True
        if expected_source_sha256 and source_hash != expected_source_sha256:
            report["source_frozen_unchanged"] = False
            report["errors"].append("frozen_source_checksum_mismatch")
    else:
        report["runtime_sha256"] = sha256_file(path) if report.get("exists") else None
    report["valid"] = bool(
        report.get("package_valid")
        and report.get("slide_count") == 1
        and not report.get("unsupported_relationships")
        and not report.get("missing_relationship_targets")
        and not report.get("missing_required_slots")
        and report.get("full_slide_raster_count") == 0
        and report.get("editable_shape_count", 0) > 0
        and report.get("editable_text_shape_count", 0) > 0
        and not report.get("duplicate_semantic_slots")
    )
    return report


def require_valid_template_package(path: str | Path, **kwargs: Any) -> dict[str, Any]:
    report = validate_template_package(path, **kwargs)
    if not report["valid"]:
        raise ValueError({"template": str(path), "diagnostic": report})
    return report


def _slotify_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:32] if text else ""


def _shape_slot(text: str, kind: str, y: int, slide_h: int, slide_id: str, counters: dict[str, int]) -> str:
    normalized = text.replace(" ", "")
    if kind == "pic":
        base = "image.1"
    elif "AIで、提案をもっと速く、もっと強く" in normalized:
        base = "header.tagline"
    elif "THINKTOGETHER,CREATETHENEXT" in normalized:
        base = "header.message"
    elif "人とテクノロジーで、より良い社会をつくる" in normalized:
        base = "footer.tagline.jp"
    elif "Think Together, Create the Next." in text:
        base = "footer.tagline.en"
    elif re.search(r"20\d{2}\.\d{2}\.\d{2}", normalized):
        base = "footer.date"
    elif "提案クエスト" in normalized or normalized in {"提案", "クエスト"}:
        if y > slide_h * 0.78:
            base = "footer.brand"
        elif y < slide_h * 0.25:
            base = "header.brand"
        else:
            base = "title.primary"
    elif y < slide_h * 0.42 and len(normalized) >= 7:
        base = "title.primary"
    elif y < slide_h * 0.55 and len(normalized) >= 16:
        base = "lead"
    else:
        base = "content.auto"
    count = counters.get(base, 0) + 1
    counters[base] = count
    return base if count == 1 else f"{base}.{count}"


def annotate_semantic_slots(path: str | Path, slide_id: str) -> dict[str, Any]:
    """Add stable, non-visible ``shape.name`` identifiers to a runtime copy."""

    source = Path(path)
    with ZipFile(source, "r") as package:
        names = package.namelist()
        slide_paths = [name for name in names if _SLIDE_XML_RE.match(name)]
        if len(slide_paths) != 1:
            raise ValueError(f"runtime template must contain exactly one slide: {source}")
        slide_path = slide_paths[0]
        root = ET.fromstring(package.read(slide_path))
        dimensions = _slide_dimensions(ET.fromstring(package.read("ppt/presentation.xml")))
        counters: dict[str, int] = {}
        assigned: list[str] = []
        for shape in _shape_elements(root):
            c_nv_pr = next((node for node in _iter_descendants(shape, "cNvPr")), None)
            if c_nv_pr is None:
                continue
            text = _text_of_shape(shape)
            _, y, _, _ = _shape_transform(shape)
            logical = _shape_slot(text, _shape_kind(shape), y, dimensions[1], slide_id, counters)
            name = f"trace:{slide_id}:{logical}"
            c_nv_pr.set("name", name)
            assigned.append(name)
        updated_slide = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        with NamedTemporaryFile(delete=False, suffix=".pptx") as temp:
            temp_path = Path(temp.name)
        try:
            with ZipFile(temp_path, "w", compression=ZIP_DEFLATED) as output:
                for name in names:
                    payload = updated_slide if name == slide_path else package.read(name)
                    output.writestr(name, payload)
            shutil.move(temp_path, source)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    return {"path": str(source), "slide_id": slide_id, "assigned_slots": assigned, "slot_count": len(assigned)}


def clone_template_package(
    source_path: str | Path,
    destination_path: str | Path,
    *,
    approved_slide_id: str,
    required_slots: Iterable[str] = (),
) -> dict[str, Any]:
    """Copy a full PPTX package, preserving image/media relationships."""

    source = Path(source_path)
    destination = Path(destination_path)
    source_report = inspect_template_package(source)
    if source_report["unsupported_relationships"]:
        raise ValueError({"template": str(source), "diagnostic": source_report})
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    runtime_sha_before_normalization = sha256_file(destination)
    annotate_semantic_slots(destination, approved_slide_id)
    report = validate_template_package(
        destination,
        approved_slide_id=approved_slide_id,
        required_slots=required_slots,
        source_path=source,
        expected_source_sha256=source_report.get("source_sha256"),
    )
    report["runtime_sha256_before_normalization"] = runtime_sha_before_normalization
    report["runtime_sha256_after_normalization"] = sha256_file(destination)
    report["media_relationships_preserved"] = (
        report.get("image_count", 0) == source_report.get("image_count", 0)
        and report.get("crop_rect_count", 0) == source_report.get("crop_rect_count", 0)
        and not report.get("missing_relationship_targets")
    )
    if not report["valid"]:
        raise ValueError({"template": str(destination), "diagnostic": report})
    return report


def _shape_bounds_by_name(path: str | Path) -> dict[str, tuple[int, int, int, int]]:
    """Return non-visible shape geometry keyed by the semantic shape name."""

    bounds: dict[str, tuple[int, int, int, int]] = {}
    with ZipFile(path, "r") as package:
        for slide_path in sorted(name for name in package.namelist() if _SLIDE_XML_RE.match(name)):
            root = ET.fromstring(package.read(slide_path))
            for shape in _shape_elements(root):
                c_nv_pr = next((node for node in _iter_descendants(shape, "cNvPr")), None)
                if c_nv_pr is None or not c_nv_pr.attrib.get("name", "").startswith("trace:"):
                    continue
                bounds[c_nv_pr.attrib["name"]] = _shape_transform(shape)
    return bounds


def _package_text(path: str | Path) -> str:
    with ZipFile(path, "r") as package:
        return "\n".join(
            package.read(name).decode("utf-8", errors="ignore")
            for name in package.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )


def validate_injected_template_package(
    path: str | Path,
    *,
    source_template: str | Path | None = None,
    approved_slide_id: str | None = None,
    required_slots: Iterable[str] = (),
    unresolved_required_slots: Iterable[str] = (),
    prohibited_sample_strings: Iterable[str] = (),
    text_fit_diagnostics: dict[str, Any] | None = None,
    evidence_diagnostics: Iterable[dict[str, Any]] = (),
    expected_source_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate a cloned template after content injection.

    This is intentionally stricter than the foundation package check.  It
    verifies that injection did not alter geometry or image relationships and
    that known Canonical/sample strings did not survive in evidence-sensitive
    roles.
    """

    report = validate_template_package(
        path,
        approved_slide_id=approved_slide_id,
        required_slots=required_slots,
        source_path=source_template,
        expected_source_sha256=expected_source_sha256,
    )
    report["unresolved_required_slots"] = sorted(set(unresolved_required_slots))
    prohibited = sorted({value for value in prohibited_sample_strings if value})
    package_text = _package_text(path) if report.get("exists") else ""
    report["prohibited_sample_strings"] = prohibited
    report["prohibited_sample_strings_found"] = [value for value in prohibited if value in package_text]
    report["sample_content_leak_free"] = not report["prohibited_sample_strings_found"]
    report["text_fit"] = text_fit_diagnostics or {"valid": True, "fields": {}}
    report["text_fit_valid"] = bool(report["text_fit"].get("valid", False))
    report["evidence_diagnostics"] = list(evidence_diagnostics)
    fit_fields = report["text_fit"].get("fields", {}).values()
    report["font_size_minimum_valid"] = all(
        float(field.get("font_size", 0)) >= float(field.get("minimum_font_size", 0))
        for field in fit_fields
    )
    report["shape_bounds_unchanged"] = None
    report["image_relationships_preserved"] = None
    if source_template is not None and Path(source_template).is_file() and report.get("exists"):
        source_bounds = _shape_bounds_by_name(source_template)
        injected_bounds = _shape_bounds_by_name(path)
        report["shape_bounds_unchanged"] = source_bounds == injected_bounds
        source_inspection = inspect_template_package(source_template)
        report["image_relationships_preserved"] = (
            source_inspection.get("image_count") == report.get("image_count")
            and source_inspection.get("crop_rect_count") == report.get("crop_rect_count")
            and source_inspection.get("crop_values") == report.get("crop_values")
            and not report.get("missing_relationship_targets")
        )
    report["valid"] = bool(
        report.get("valid")
        and not report["unresolved_required_slots"]
        and report.get("sample_content_leak_free")
        and report.get("text_fit_valid")
        and report.get("font_size_minimum_valid")
        and report.get("shape_bounds_unchanged") is not False
        and report.get("image_relationships_preserved") is not False
    )
    return report
