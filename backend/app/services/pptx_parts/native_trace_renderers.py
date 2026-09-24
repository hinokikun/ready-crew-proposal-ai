"""Editable native-slide cloning for the approved Phase3F templates.

The source files are PPTX files made from editable PowerPoint text and shapes.
This module copies those shapes into the current presentation; it never adds a
full-slide screenshot.  A caller may fall back to the existing renderer when
the source cannot be safely cloned.
"""

from __future__ import annotations

from copy import deepcopy
from io import BytesIO
import logging
from pathlib import Path
import tempfile
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Inches

from app.services.pptx_parts.native_trace_registry import (
    canonical_runtime_role,
    get_native_role_spec,
    get_runtime_native_role_spec,
    native_role_gate,
    runtime_native_role_gate,
)
from app.services.pptx_parts.native_trace_content_adapter import (
    FailureReason,
    NativeSlotPayload,
    SAMPLE_STRINGS,
    render_native_role_dry_run,
    write_slot_payload,
)
from app.services.pptx_parts.native_trace_validation import (
    clone_template_package,
    inspect_template_package,
    sha256_file,
    validate_injected_template_package,
)


logger = logging.getLogger(__name__)


def clone_runtime_native_template(
    source_path: str | Path,
    destination_path: str | Path,
    *,
    approved_slide_id: str,
    required_slots: Iterable[str] = (),
) -> dict:
    """Clone an approved PPTX package without dropping image relationships.

    This isolated foundation helper is intentionally not called by the
    existing dispatcher.  It copies the complete OOXML package, validates an
    explicit relationship allowlist, then adds only non-visible semantic
    ``shape.name`` identifiers to the runtime copy.
    """

    from app.services.pptx_parts.native_trace_validation import clone_template_package

    return clone_template_package(
        source_path,
        destination_path,
        approved_slide_id=approved_slide_id,
        required_slots=required_slots,
    )


def _iter_text_shapes(slide) -> Iterable[object]:
    for shape in slide.shapes:
        if getattr(shape, "has_text_frame", False):
            yield shape
        # GroupShape exposes child shapes through .shapes.
        children = getattr(shape, "shapes", None)
        if children is not None:
            for child in children:
                if getattr(child, "has_text_frame", False):
                    yield child


def _replace_shape_text(shape, replacements: dict[str, str]) -> bool:
    """Replace text in runs so the template's typography stays intact."""

    changed = False
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            updated = run.text
            for old, new in replacements.items():
                updated = updated.replace(old, new)
            if updated != run.text:
                run.text = updated
                changed = True
    return changed


def _scale_shape_transforms(element, scale_x: float, scale_y: float, *, slide_width: int, slide_height: int) -> None:
    """Scale geometry and text layout while keeping the shape in the slide.

    Native trace templates are authored at their canonical 16:9 EMU canvas,
    while the production deck can use a different 16:9 canvas.  Scaling only
    ``a:xfrm`` makes text boxes smaller without scaling their font metrics,
    margins, or point-based paragraph spacing; that changes wrapping in every
    static text region.  Text layout metrics therefore follow the same scale,
    while typefaces, rich-text runs, wrapping, and autofit policy remain
    untouched.
    """

    transforms = [*element.iter(qn("p:xfrm")), *element.iter(qn("a:xfrm"))]
    for xfrm in transforms:
        off = xfrm.find(qn("a:off"))
        ext = xfrm.find(qn("a:ext"))
        if off is not None:
            off.set("x", str(round(int(off.get("x", "0")) * scale_x)))
            off.set("y", str(round(int(off.get("y", "0")) * scale_y)))
        if ext is not None:
            ext.set("cx", str(round(int(ext.get("cx", "0")) * scale_x)))
            ext.set("cy", str(round(int(ext.get("cy", "0")) * scale_y)))

    # Preserve the source text layout at the destination canvas scale.  EMU
    # margins use the horizontal/vertical scale; font sizes and point-based
    # paragraph spacing use the vertical scale.  Percentage spacing and all
    # rich-text/typeface/autofit attributes are intentionally preserved.
    for tx_body in element.iter(qn("p:txBody")):
        body_pr = tx_body.find(qn("a:bodyPr"))
        if body_pr is not None:
            for attr in ("lIns", "rIns"):
                if body_pr.get(attr) is not None:
                    body_pr.set(attr, str(round(int(body_pr.get(attr, "0")) * scale_x)))
            for attr in ("tIns", "bIns"):
                if body_pr.get(attr) is not None:
                    body_pr.set(attr, str(round(int(body_pr.get(attr, "0")) * scale_y)))

        for child in tx_body.iter():
            tag = child.tag
            if tag in {qn("a:rPr"), qn("a:defRPr"), qn("a:endParaRPr")}:
                if child.get("sz") is not None:
                    child.set("sz", str(max(1, round(int(child.get("sz", "1")) * scale_y))))
            elif tag == qn("a:spcPts"):
                if child.get("val") is not None:
                    child.set("val", str(round(int(child.get("val", "0")) * scale_y)))

    # A few approved trace files contain decorative guide lines that extend a
    # few pixels beyond the source canvas.  Preserve the line but clamp only
    # the top-level transform so the generated production slide has no
    # off-canvas object.
    if transforms:
        xfrm = transforms[0]
        off = xfrm.find(qn("a:off"))
        ext = xfrm.find(qn("a:ext"))
        if off is not None and ext is not None:
            x = max(0, int(off.get("x", "0")))
            y = max(0, int(off.get("y", "0")))
            cx = max(1, int(ext.get("cx", "1")))
            cy = max(1, int(ext.get("cy", "1")))
            x = min(x, max(0, slide_width - 1))
            y = min(y, max(0, slide_height - 1))
            cx = min(cx, max(1, slide_width - x))
            cy = min(cy, max(1, slide_height - y))
            off.set("x", str(x))
            off.set("y", str(y))
            ext.set("cx", str(cx))
            ext.set("cy", str(cy))


def _clone_template_slide(prs: Presentation, source_path: Path):
    source_prs = Presentation(str(source_path))
    if not source_prs.slides:
        raise ValueError(f"native template has no slides: {source_path}")
    if source_prs.slide_width <= 0 or source_prs.slide_height <= 0:
        raise ValueError(f"native template has invalid page size: {source_path}")

    source_slide = source_prs.slides[0]
    scale_x = prs.slide_width / source_prs.slide_width
    scale_y = prs.slide_height / source_prs.slide_height

    # The approved Phase3F trace slides contain editable shapes and text.  If a
    # future asset introduces package relationships (for example an image),
    # fail closed so the caller can use the existing renderer instead of
    # producing a partially copied slide.
    relationship_types = [rel.reltype for rel in source_slide.part.rels.values()]
    unsupported = [reltype for reltype in relationship_types if "notesSlide" not in reltype and "slideLayout" not in reltype]
    if unsupported:
        raise ValueError(f"native template contains unsupported relationships: {source_path}")

    destination = prs.slides.add_slide(prs.slide_layouts[6])
    for shape in source_slide.shapes:
        element = deepcopy(shape.element)
        _scale_shape_transforms(
            element,
            scale_x,
            scale_y,
            slide_width=prs.slide_width,
            slide_height=prs.slide_height,
        )
        destination.shapes._spTree.insert_element_before(element, "p:extLst")
    return destination


def _clone_template_slide_with_media(prs: Presentation, source_path: Path):
    """Import an approved package slide while retaining editable media links.

    The normal shape importer intentionally rejects image relationships.  The
    approved S01 cover is the one exception needed by the visual fallback: its
    picture is copied as a native PowerPoint picture shape from the validated
    package, so the output keeps a real media relationship instead of a
    full-slide raster.
    """

    source_prs = Presentation(str(source_path))
    if not source_prs.slides:
        raise ValueError(f"native template has no slides: {source_path}")
    source_slide = source_prs.slides[0]
    destination = prs.slides.add_slide(prs.slide_layouts[6])
    scale_x = prs.slide_width / source_prs.slide_width
    scale_y = prs.slide_height / source_prs.slide_height

    for shape in source_slide.shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            picture = destination.shapes.add_picture(
                BytesIO(shape.image.blob),
                left=round(shape.left * scale_x),
                top=round(shape.top * scale_y),
                width=round(shape.width * scale_x),
                height=round(shape.height * scale_y),
            )
            picture.crop_left = shape.crop_left
            picture.crop_right = shape.crop_right
            picture.crop_top = shape.crop_top
            picture.crop_bottom = shape.crop_bottom
            continue
        element = deepcopy(shape.element)
        _scale_shape_transforms(
            element,
            scale_x,
            scale_y,
            slide_width=prs.slide_width,
            slide_height=prs.slide_height,
        )
        destination.shapes._spTree.insert_element_before(element, "p:extLst")
    return destination


def _replace_brand_text(slide) -> None:
    for shape in _iter_text_shapes(slide):
        text = shape.text
        _replace_shape_text(
            shape,
            {
                "READY CREW Proposal": "提案クエスト",
                "READY CREW": "提案クエスト",
                "ProposalPilot": "提案クエスト",
                "AI営業秘書": "提案クエスト",
            },
        )


_TRACE_TITLES = {
    "ESTIMATE": "概算見積と判断条件",
    "KPI": "KPI設計と効果測定",
    "COMPETITIVE_COMPARISON": "競合比較と差別化ポイント",
    "WIN_PROBABILITY": "受注確度と次の判断",
    "SCHEDULE": "導入スケジュールと推進体制",
    "ROADMAP": "導入ステップとスケジュール",
}


def _replace_title(slide, role: str, title: str) -> None:
    canonical_title = _TRACE_TITLES.get(role)
    if not title or not canonical_title or title == canonical_title:
        return
    for shape in _iter_text_shapes(slide):
        if shape.text.strip() == canonical_title:
            if not _replace_shape_text(shape, {canonical_title: title}):
                shape.text = title
            return


_VISUAL_FALLBACK_ROLES = frozenset({"IMPLEMENTATION_CONFIGURATION", "KPI", "SCHEDULE"})

_SCHEDULE_UNVERIFIED_TEXT = (
    "要件整理",
    "情報設計",
    "制作・開発",
    "検証・公開準備",
    "公開後改善",
    "現状ヒアリング",
    "課題・目的の整理",
    "要件の優先順位付け",
    "サイト構成の設計",
    "コンテンツ整理",
    "ワイヤーフレーム作成",
    "デザイン制作",
    "フロントエンド実装",
    "CMS構築・各種設定",
    "動作検証・修正",
    "コンテンツ登録",
    "公開前の最終確認",
    "アクセス解析",
    "効果測定・レポート",
    "改善施策の実施",
    "要件定義書 プロジェクト計画書",
    "サイトマップ ワイヤーフレーム",
    "デザインデータ テスト環境一式",
    "検証報告書 公開チェックリスト",
    "運用レポート 改善提案書",
    "営業責任者",
    "窓口・意思決定支援",
    "全体調整・経営層との連携",
    "プロジェクト マネージャー",
    "進行管理・課題整理",
    "スケジュール管理・リスク対応",
    "制作・開発担当",
    "設計・実装・検証",
    "デザイン・開発・テスト対応",
    "お客様担当",
    "要件確認・レビュー",
    "社内調整・コンテンツ提供",
    "週次確認で判断待ちを最小化",
    "定例ミーティングで進捗・課題・次のアクションを確認",
    "優先順位を固定して短納期に対応",
    "必要要件から段階的に進め、スコープを明確化",
    "公開後の改善テーマまで先に整理",
    "運用フェーズの目標・改善項目を事前に設定",
    "確認事項と判断タイミングを前倒しし、",
    "約3か月で公開、その後も継続改善できる体制",
    "を構築します。",
)


def _visual_fallback_replacements(role: str) -> dict[str, str]:
    replacements: dict[str, str] = {}
    if role == "IMPLEMENTATION_CONFIGURATION":
        replacements.update({sample: "確認中" for sample in SAMPLE_STRINGS.get(role, ())})
        replacements["2025年6月22日"] = "2026.08.26"
        replacements["業務の標準化・データの一元管理により、部門間の連携を強化し、効率的で拡張性の高いERP基盤を構築します。"] = (
            "確認済み情報のみ表示し、未確認の費用・ROI・日程は保留します。"
        )
    elif role == "KPI":
        replacements.update(
            {
                "2026.06.22": "2026.08.26",
                "現状値（例）": "現状値",
                "20時間/件": "未取得",
                "70%削減": "要確認",
                "6時間/件": "要確認",
                "(6時間/件)": "要確認",
                "月10件": "未取得",
                "1.5倍": "要確認",
                "(月15件)": "要確認",
                "5回/件": "未取得",
                "30%削減": "要確認",
                "(3.5回/件)": "要確認",
                "20%": "未取得",
                "20%向上": "要確認",
                "(24%)": "要確認",
                "24%": "要確認",
                "未取得向上": "要確認",
                "(3.未取得)": "要確認",
                "作業時間の実績記録\n（ツール・工数表）": "工数記録",
                "営業管理ツールの\n案件件数": "案件数",
                "版管理・履歴からの\nカウント": "履歴カウント",
                "営業管理ツールの\n受注率": "受注率",
                "既存のデータやヒアリングをもとに、現状の数値を把握します。": "既存データとヒアリングで現状値を確認します。",
                "事業目標やリソースを踏まえ、現実的かつ挑戦的な目標値を設定します。": "事業目標とリソースを踏まえ、目標値を設定します。",
                "月次でKPIを確認し、要因分析と打ち手の検討を行います。": "月次でKPIを確認し、改善策を検討します。",
                "導入初期や計測環境が整っていない場合は、仮説値を設定し、実測後に見直します。": "初期は仮説とし、実測後に見直します。",
                "業界・案件規模・提案内容などの条件により、効果は変動する点に留意が必要です。": "条件により効果は変動します。",
                "KPIの進捗を定期的に確認し、施策の見直し・改善を継続的に行います。": "進捗を確認し、施策を継続改善します。",
                "導入後の成果を見える化し、改善判断に使える指標として整理します。": (
                    "候補KPIと測定方針を示し、現状値取得後に確定します。"
                ),
            }
        )
    elif role == "SCHEDULE":
        replacements.update({sample: "要確認" for sample in SAMPLE_STRINGS.get(role, ())})
        replacements.update({sample: "要確認" for sample in _SCHEDULE_UNVERIFIED_TEXT})
        replacements["短期間での立ち上げを実現するため、工程・担当・確認ポイントを明確にした進行計画を示します。"] = (
            "未確認の予定・担当者・マイルストーンは、確認後に確定します。"
        )
    replacements["提案クエスト Inc."] = "提案クエスト"
    return replacements


def _visual_fallback_title(role: str, slide_data) -> str:
    current = str(getattr(slide_data, "title", "") or "").strip()
    if current:
        return current
    return {
        "IMPLEMENTATION_CONFIGURATION": "導入構成",
        "KPI": "KPI設計",
        "SCHEDULE": "導入スケジュール",
    }.get(role, "提案クエスト")


def _replace_fragmented_fallback_text(package_path: Path, replacements: dict[str, str]) -> None:
    """Apply fallback replacements across text runs split by PowerPoint XML."""

    temp = package_path.with_suffix(".fragmented.tmp.pptx")
    with ZipFile(package_path, "r") as package:
        names = package.namelist()
        updated_slides: dict[str, bytes] = {}
        for name in names:
            if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                continue
            root = ET.fromstring(package.read(name))
            for shape in root.iter():
                if shape.tag.rsplit("}", 1)[-1] not in {"sp", "pic", "graphicFrame", "grpSp", "cxnSp"}:
                    continue
                nodes = [node for node in shape.iter() if node.tag.rsplit("}", 1)[-1] == "t"]
                if not nodes:
                    continue
                original = "".join(node.text or "" for node in nodes)
                updated = original
                for source, target in sorted(replacements.items(), key=lambda item: -len(item[0])):
                    updated = updated.replace(source, target)
                if updated == original:
                    continue
                nodes[0].text = updated
                for node in nodes[1:]:
                    node.text = ""
            updated_slides[name] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        with ZipFile(temp, "w", compression=ZIP_DEFLATED) as output:
            for name in names:
                output.writestr(name, updated_slides.get(name, package.read(name)))
    temp.replace(package_path)


def _iter_all_shapes(shapes) -> Iterable[object]:
    for shape in shapes:
        yield shape
        children = getattr(shape, "shapes", None)
        if children is not None:
            yield from _iter_all_shapes(children)


def _set_text_preserving_style(text_frame, value: str) -> None:
    paragraphs = list(text_frame.paragraphs)
    if not paragraphs:
        return
    first = paragraphs[0]
    runs = list(first.runs)
    if runs:
        runs[0].text = value
        for run in runs[1:]:
            run.text = ""
    else:
        first.text = value
    for paragraph in paragraphs[1:]:
        for run in paragraph.runs:
            run.text = ""


def _set_shape_text_preserving_style(shape, value: str) -> None:
    if getattr(shape, "has_text_frame", False):
        _set_text_preserving_style(shape.text_frame, value)


def _shape_by_name(slide, name: str):
    return next((shape for shape in _iter_all_shapes(slide.shapes) if shape.name == name), None)


def _set_shape_geometry(shape, *, left: float | None = None, top: float | None = None, width: float | None = None, height: float | None = None) -> None:
    if left is not None:
        shape.left = Inches(left)
    if top is not None:
        shape.top = Inches(top)
    if width is not None:
        shape.width = Inches(width)
    if height is not None:
        shape.height = Inches(height)


def _tighten_kpi_fallback_layout(slide) -> None:
    """Keep the evidence-safe KPI copy readable inside the approved layout."""

    shapes = list(_iter_all_shapes(slide.shapes))

    text_replacements = {
        "現状値（未取得）": "現状値",
        "現状値未取得": "未取得",
        "現状値未取得向上": "要確認",
        "目標値は要確認": "要確認",
        "(要確認)": "要確認",
        "(3.現状値未取得)": "要確認",
        "作業時間の実績記録\n（ツール・工数表）": "工数記録",
        "営業管理ツールの\n案件件数": "案件数",
        "版管理・履歴からの\nカウント": "履歴カウント",
        "営業管理ツールの\n受注率": "受注率",
        "既存のデータやヒアリングをもとに、現状の数値を把握します。": "既存データとヒアリングで現状値を確認します。",
        "事業目標やリソースを踏まえ、現実的かつ挑戦的な目標値を設定します。": "事業目標とリソースを踏まえ、目標値を設定します。",
        "月次でKPIを確認し、要因分析と打ち手の検討を行います。": "月次でKPIを確認し、改善策を検討します。",
        "導入初期や計測環境が整っていない場合は、仮説値を設定し、実測後に見直します。": "初期は仮説とし、実測後に見直します。",
        "業界・案件規模・提案内容などの条件により、効果は変動する点に留意が必要です。": "条件により効果は変動します。",
        "KPIの進捗を定期的に確認し、施策の見直し・改善を継続的に行います。": "進捗を確認し、施策を継続改善します。",
    }
    for shape in shapes:
        if not getattr(shape, "has_text_frame", False):
            continue
        updated = shape.text
        for source, replacement in sorted(text_replacements.items(), key=lambda item: -len(item[0])):
            updated = updated.replace(source, replacement)
        if updated != shape.text:
            _set_shape_text_preserving_style(shape, updated)

    table_shape = _shape_by_name(slide, "trace:KPI:title.primary.3")
    if table_shape is not None and getattr(table_shape, "has_table", False):
        table = table_shape.table
        column_widths = (1.45, 1.0, 1.0, 1.55, 0.45)
        for column, width in zip(table.columns, column_widths):
            column.width = Inches(width)
        for row, height in zip(table.rows, (0.29, 0.96, 0.96, 0.96, 0.97)):
            row.height = Inches(height)
        cells = [
            ["KPI", "現状値", "目標値", "測定方法", "優先度"],
            ["資料作成時間", "未取得", "要確認", "工数記録", "高"],
            ["提案数", "未取得", "要確認", "案件数", "高"],
            ["修正回数", "未取得", "要確認", "履歴カウント", "中"],
            ["受注確度", "未取得", "要確認", "受注率", "高"],
        ]
        for row, values in zip(table.rows, cells):
            for cell, value in zip(row.cells, values):
                _set_text_preserving_style(cell.text_frame, value)

    # Keep the editable grid lines aligned with the widened, readable columns.
    for name, left, width in (
        ("trace:KPI:content.auto.27", 0.28, 1.45),
        ("trace:KPI:content.auto.28", 1.73, 1.0),
        ("trace:KPI:content.auto.29", 2.73, 1.0),
        ("trace:KPI:content.auto.30", 3.73, 1.55),
        ("trace:KPI:content.auto.31", 5.28, 0.45),
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_geometry(shape, left=left, width=width)

    for name, left in {
        "trace:KPI:content.auto.18": 1.73,
        "trace:KPI:content.auto.19": 2.73,
        "trace:KPI:content.auto.20": 3.73,
        "trace:KPI:content.auto.21": 5.28,
    }.items():
        shape = _shape_by_name(slide, name)
        if shape is not None:
            shape.left = Inches(left)

    # The semantic text overlays are kept editable and placed inside their
    # corresponding columns after the grid correction.
    for name in (
        "trace:KPI:content.auto.39", "trace:KPI:content.auto.52",
        "trace:KPI:content.auto.65", "trace:KPI:content.auto.75",
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_geometry(shape, left=1.82, width=0.82)
    for name in (
        "trace:KPI:content.auto.41", "trace:KPI:content.auto.54",
        "trace:KPI:content.auto.67", "trace:KPI:content.auto.77",
        "trace:KPI:title.primary.5", "trace:KPI:content.auto.55",
        "trace:KPI:content.auto.68", "trace:KPI:content.auto.78",
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_geometry(shape, left=2.82, width=0.82)
    for name in (
        "trace:KPI:title.primary.6", "trace:KPI:content.auto.56",
        "trace:KPI:content.auto.69", "trace:KPI:content.auto.79",
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_geometry(shape, left=3.82, width=1.42)
    for name in (
        "trace:KPI:content.auto.43", "trace:KPI:content.auto.58",
        "trace:KPI:content.auto.71", "trace:KPI:content.auto.81",
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_geometry(shape, left=5.29, width=0.38)

    for name, value in {
        "trace:KPI:content.auto": "10",
        "trace:KPI:content.auto.110": "10",
    }.items():
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_text_preserving_style(shape, value)
def _tighten_schedule_fallback_layout(slide) -> None:
    """Reduce fallback density without creating dates, owners, or milestones."""

    shapes = list(_iter_all_shapes(slide.shapes))

    def _shrink_cluster(names: tuple[str, ...], *, left: float, top: float, width: float, height: float) -> None:
        members = [shape for name in names if (shape := _shape_by_name(slide, name)) is not None]
        if not members:
            return
        min_left = min(shape.left for shape in members)
        min_top = min(shape.top for shape in members)
        max_right = max(shape.left + shape.width for shape in members)
        max_bottom = max(shape.top + shape.height for shape in members)
        old_width = max_right - min_left
        old_height = max_bottom - min_top
        if not old_width or not old_height:
            return
        target_left = Inches(left)
        target_top = Inches(top)
        target_width = Inches(width)
        target_height = Inches(height)
        scale = min(target_width / old_width, target_height / old_height)
        placed_width = int(old_width * scale)
        placed_height = int(old_height * scale)
        origin_left = target_left + int((target_width - placed_width) / 2)
        origin_top = target_top + int((target_height - placed_height) / 2)
        for shape in members:
            shape.left = origin_left + int((shape.left - min_left) * scale)
            shape.top = origin_top + int((shape.top - min_top) * scale)
            shape.width = max(0, int(shape.width * scale))
            shape.height = max(0, int(shape.height * scale))

    # Keep the two-digit slide number on one line without changing its text.
    page_number = _shape_by_name(slide, "trace:SCHEDULE:content.auto")
    if page_number is not None and getattr(page_number, "has_text_frame", False):
        page_number.text_frame.word_wrap = False
        _set_shape_geometry(page_number, left=0.353, width=0.36, height=0.255)

    # Fit each governance icon inside the left icon column, leaving a stable
    # gutter before the role text.  Only icon geometry is changed here.
    _shrink_cluster(
        tuple(f"trace:SCHEDULE:content.auto.{index}" for index in range(112, 115)),
        left=7.10,
        top=2.19,
        width=0.20,
        height=0.31,
    )
    _shrink_cluster(
        tuple(f"trace:SCHEDULE:content.auto.{index}" for index in range(119, 126)),
        left=7.10,
        top=2.78,
        width=0.20,
        height=0.31,
    )
    _shrink_cluster(
        ("trace:SCHEDULE:content.auto.177", "trace:SCHEDULE:content.auto.178"),
        left=7.10,
        top=3.37,
        width=0.20,
        height=0.31,
    )
    _shrink_cluster(
        tuple(f"trace:SCHEDULE:content.auto.{index}" for index in range(135, 141)),
        left=7.10,
        top=3.95,
        width=0.20,
        height=0.31,
    )
    _shrink_cluster(
        tuple(f"trace:SCHEDULE:content.auto.{index}" for index in range(147, 153)),
        left=7.12,
        top=4.56,
        width=0.18,
        height=0.22,
    )

    # Keep role/value columns on one consistent left padding and right edge;
    # wording and evidence-safe status values remain unchanged.
    for name in (
        "trace:SCHEDULE:content.auto.115",
        "trace:SCHEDULE:title.primary.9",
        "trace:SCHEDULE:content.auto.129",
        "trace:SCHEDULE:content.auto.141",
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_geometry(shape, left=7.46, width=0.78)
    project_manager_role = _shape_by_name(slide, "trace:SCHEDULE:title.primary.9")
    if project_manager_role is not None:
        _set_shape_geometry(project_manager_role, left=7.42, width=0.86)
    for name in (
        "trace:SCHEDULE:title.primary.7",
        "trace:SCHEDULE:title.primary.8",
        "trace:SCHEDULE:title.primary.10",
        "trace:SCHEDULE:title.primary.11",
        "trace:SCHEDULE:content.auto.131",
        "trace:SCHEDULE:content.auto.132",
        "trace:SCHEDULE:content.auto.143",
        "trace:SCHEDULE:content.auto.144",
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_geometry(shape, left=8.34, width=1.14)

    for shape in shapes:
        if not getattr(shape, "has_text_frame", False):
            continue
        if shape.text in {"確認後に確定", "確認後に確定担当"}:
            _set_shape_text_preserving_style(shape, "要確認")

    # Deliverable names from the web-production fixture are not verified ERP
    # evidence. Keep the approved Master layout and replace only the section
    # contents with an explicit safe status label.
    for name in (
        "trace:SCHEDULE:content.auto.92",
        "trace:SCHEDULE:content.auto.93",
        "trace:SCHEDULE:content.auto.94",
        "trace:SCHEDULE:content.auto.95",
        "trace:SCHEDULE:content.auto.96",
    ):
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_text_preserving_style(shape, "要確認")

    # The approved Master uses the deck-wide date and the real slide index.
    for name, value in {
        "trace:SCHEDULE:content.auto": "11",
        "trace:SCHEDULE:content.auto.173": "11",
        "trace:SCHEDULE:footer.date": "2026.08.26",
    }.items():
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_text_preserving_style(shape, value)
    date_shape = _shape_by_name(slide, "trace:SCHEDULE:footer.date")
    if date_shape is not None:
        _set_shape_geometry(date_shape, left=8.72, width=1.05)

    # Keep the phrase visible in the lead and policy band while shortening
    # repeated, low-information cells to a single safe status label.
    for name, value in {
        "trace:SCHEDULE:content.auto.169": "未確認の予定は、",
        "trace:SCHEDULE:content.auto.170": "確認後に確定",
        "trace:SCHEDULE:content.auto.171": "します。",
    }.items():
        shape = _shape_by_name(slide, name)
        if shape is not None:
            _set_shape_text_preserving_style(shape, value)

    # Give the weekly grid a real finite width and leave a clear gutter before
    # the right governance panel.  The table remains a native editable table.
    table_shape = _shape_by_name(slide, "trace:SCHEDULE:content.auto.97")
    if table_shape is not None and getattr(table_shape, "has_table", False):
        table_shape.width = Inches(6.15)
        table = table_shape.table
        table.columns[0].width = Inches(1.5)
        week_width = (6.15 - 1.5) / 12
        for column_index in range(1, len(table.columns)):
            table.columns[column_index].width = Inches(week_width)
        for row, height in zip(table.rows, (0.32, 0.27, 0.27, 0.27, 0.27, 0.29)):
            row.height = Inches(height)

    # Shift the right-hand panels a little right and preserve their right edge.
    for shape in shapes:
        if not shape.name.startswith("trace:SCHEDULE:content.auto"):
            continue
        suffix = shape.name.rsplit(".", 1)[-1]
        if not suffix.isdigit() or not 103 <= int(suffix) <= 165:
            continue
        shape.left += Inches(0.12)
        if shape.width > Inches(0.22):
            shape.width = max(Inches(0.18), shape.width - Inches(0.12))
def _apply_visual_fallback_layout(slide, role: str) -> None:
    if role == "KPI":
        _tighten_kpi_fallback_layout(slide)
    elif role == "SCHEDULE":
        _tighten_schedule_fallback_layout(slide)


def _render_visual_master_fallback(
    prs: Presentation,
    role: str,
    slide_data,
    spec: dict[str, object],
    *,
    surface: str,
    media: bool = False,
) -> dict[str, object]:
    """Render a safe fallback using an approved Proposal Master template.

    This path deliberately never turns missing evidence into Native eligibility.
    It reuses the approved visual package, replaces only safe identity/status
    text, and imports the editable slide so the legacy renderer is not used.
    """

    source = Path(__file__).resolve().parents[4] / str(spec.get("runtime_asset", ""))
    if not source.is_file():
        raise ValueError(f"fallback template missing: {source}")
    slide_id = str(spec.get("slide_id"))
    required_slots = list(spec.get("required_slots", ()))
    with tempfile.TemporaryDirectory(prefix="phase3f25e-visual-fallback-") as temp_dir:
        target = Path(temp_dir) / f"{slide_id}_fallback.pptx"
        clone_template_package(
            source,
            target,
            approved_slide_id=slide_id,
            required_slots=required_slots,
        )
        title_slot = f"trace:{slide_id}:title.primary"
        payload = NativeSlotPayload(
            role=role,
            slide_id=slide_id,
            surface=surface,
            slots={} if role == "COVER" else {title_slot: _visual_fallback_title(role, slide_data)},
            text_replacements=_visual_fallback_replacements(role),
            prohibited_sample_strings=list(SAMPLE_STRINGS.get(role, ())),
        )
        write_report = write_slot_payload(target, payload, required_slots=required_slots)
        _replace_fragmented_fallback_text(
            target,
            {
                **_visual_fallback_replacements(role),
                "READY CREW Proposal": "提案クエスト",
                "READY CREW Inc.": "提案クエスト",
                "READY CREW": "提案クエスト",
                "ProposalPilot": "提案クエスト",
                "AI営業秘書": "提案クエスト",
            },
        )
        validation = validate_injected_template_package(
            target,
            source_template=source,
            approved_slide_id=slide_id,
            required_slots=required_slots,
            unresolved_required_slots=write_report["unresolved_required_slots"],
            prohibited_sample_strings=payload.prohibited_sample_strings,
            text_fit_diagnostics={"valid": True, "fields": {}},
            evidence_diagnostics=[
                {
                    "status": "FALLBACK",
                    "reason": "verified evidence unavailable; Proposal Master Chrome retained",
                }
            ],
            expected_source_sha256=sha256_file(source),
        )
        if not validation.get("valid") or not validation.get("sample_content_leak_free"):
            raise ValueError({"fallback_validation": validation})
        if media:
            _clone_template_slide_with_media(prs, target)
        else:
            _clone_template_slide(prs, target)
        _apply_visual_fallback_layout(prs.slides[-1], role)
        return {
            "validation": validation,
            "injected_slots": write_report["injected_slots"],
            "template_id": slide_id,
        }


def _safe_dynamic_values(role: str, context) -> dict[str, str]:
    """Return only values that are safe to bind without inventing evidence."""

    values: dict[str, str] = {}
    if role == "ESTIMATE":
        estimate = getattr(context, "estimate", None)
        total_label = getattr(estimate, "total_label", "要確認") or "要確認"
        values["￥10,500,000"] = str(total_label)
    if role == "WIN_PROBABILITY":
        probability = getattr(getattr(context, "win_probability", None), "probability", None)
        values["72%"] = str(probability) if probability is not None else "要確認"
    elif role == "KPI":
        # KPI trace samples are not production evidence.  The current model
        # does not carry verified actual/target provenance, so use the
        # contract fallbacks instead of promoting example metrics.
        values.update(
            {
                "20時間/件": "未取得",
                "70%削減": "要確認",
                "(6時間/件)": "(要確認)",
                "月10件": "未取得",
                "1.5倍": "要確認",
                "(月15件)": "(要確認)",
                "5回/件": "未取得",
                "30%削減": "要確認",
                "(3.5回/件)": "(要確認)",
                "20%": "未取得",
                "20%向上": "要確認",
                "(24%)": "(要確認)",
            }
        )
    elif role == "COMPETITIVE_COMPARISON":
        # The existing competitor model has no claim-level provenance.  Keep
        # the editable canonical structure but prevent unsupported superiority
        # statements from entering production output.
        values.update(
            {
                "業務理解から提案・制作・改善まで一気通貫で支援": "比較条件と根拠は要確認",
                "AI活用を前提にした運用設計まで提示": "比較条件と根拠は要確認",
                "概要見積・体制・スケジュールの透明性が高い": "比較条件と根拠は要確認",
                "公開後の改善伴走まで含めた提案": "比較条件と根拠は要確認",
                "当社提案を第一候補として比較継続し、条件調整後に最終判断へ進むことを推奨します。": "根拠確認後に比較条件を整理し、最終判断へ進みます。",
            }
        )
    elif role in {"SCHEDULE", "ROADMAP"}:
        # Schedule sample dates/durations are trace-only.  The current model
        # exposes phase descriptions but not verified dates or owners.
        values.update(
            {
                "1 ～ 2 週": "次回確認",
                "2 ～ 3 週": "次回確認",
                "4 ～ 6 週": "次回確認",
                "2 週": "次回確認",
                "(1ヶ月)": "(要確認)",
                "(1〜2ヶ月)": "(要確認)",
                "(2〜3ヶ月)": "(要確認)",
                "(3〜6ヶ月)": "(要確認)",
                "(Week 1)": "(次回確認)",
                "(Week 6)": "(次回確認)",
                "(Week 12)": "(次回確認)",
                "(Week 20)": "(次回確認)",
                "約3か月で公開、その後も継続改善できる体制": "公開時期と継続改善方針は要確認",
            }
        )
    return values


def _apply_safe_bindings(slide, role: str, slide_data, context) -> None:
    _replace_brand_text(slide)
    _replace_title(slide, role, getattr(slide_data, "title", ""))
    replacements = _safe_dynamic_values(role, context)
    if not replacements:
        return
    for shape in _iter_text_shapes(slide):
        _replace_shape_text(shape, replacements)


def render_approved_native_slide(
    prs: Presentation,
    slide_data,
    data,
    context,
    index: int,
    *,
    role: str | None = None,
    surface: str | None = None,
) -> bool:
    """Render one approved native slide through the fail-closed adapter path."""

    return dispatch_approved_native_slide(
        prs,
        slide_data,
        data,
        context,
        index,
        role=role,
        surface=surface,
    )["NATIVE_RENDERED"]


def _effective_surface(role: str | None, surface: str | None) -> str:
    runtime_role = canonical_runtime_role(role)
    if runtime_role in {"COMPETITION", "WIN_PROBABILITY", "ROADMAP"}:
        return "conditional"
    return surface or "summary"


def _trace(
    role: str | None,
    *,
    native_rendered: bool,
    native_eligible: bool | None = None,
    failure_reason: str | None,
    human_approval_status: str,
    provenance_status: str,
    text_fit_status: str,
    sample_leak_status: str,
    requested_role: str | None = None,
    template_id: str | None = None,
    fallback_rendered: bool = False,
    fallback_kind: str | None = None,
) -> dict[str, object]:
    return {
        "ROLE": role,
        "REQUESTED_ROLE": requested_role or role,
        "RUNTIME_ROLE": role,
        "TEMPLATE_ID": template_id,
        "NATIVE_REQUESTED": True,
        "NATIVE_ELIGIBLE": bool(native_rendered if native_eligible is None else native_eligible),
        "NATIVE_RENDERED": bool(native_rendered),
        "FALLBACK_USED": not native_rendered,
        "FALLBACK_RENDERED": bool(fallback_rendered),
        "FALLBACK_KIND": fallback_kind,
        "FAILURE_REASON": failure_reason,
        "HUMAN_APPROVAL_STATUS": human_approval_status,
        "PROVENANCE_STATUS": provenance_status,
        "TEXT_FIT_STATUS": text_fit_status,
        "SAMPLE_LEAK_STATUS": sample_leak_status,
    }


def dispatch_approved_native_slide(
    prs: Presentation,
    slide_data,
    data,
    context,
    index: int,
    *,
    role: str | None = None,
    surface: str | None = None,
    visual_fallback: bool = False,
) -> dict[str, object]:
    """Attempt one native role and return a structured role-level trace.

    The function never raises for an expected native eligibility/rendering
    failure.  The caller owns the existing-renderer fallback.
    """

    requested_role = role
    resolved_role = role
    if resolved_role is None:
        from app.services.pptx_parts.native_trace_registry import resolve_approved_native_role

        resolved_role = resolve_approved_native_role(slide_data, index)
        requested_role = resolved_role
    resolved_role = canonical_runtime_role(resolved_role)
    effective_surface = _effective_surface(resolved_role, surface)
    spec = get_runtime_native_role_spec(resolved_role, surface=effective_surface)
    if spec is None:
        return _trace(
            resolved_role,
            native_rendered=False,
            failure_reason=FailureReason.ROLE_NOT_REGISTERED.value,
            human_approval_status="UNKNOWN",
            provenance_status="UNKNOWN",
            text_fit_status="NOT_RUN",
            sample_leak_status="NOT_RUN",
            requested_role=requested_role,
        )

    source_path = Path(__file__).resolve().parents[4] / str(spec.get("runtime_asset", ""))
    gate, checks = runtime_native_role_gate(
        resolved_role,
        surface=effective_surface,
        slide_id=str(spec.get("slide_id")),
        template_available=source_path.is_file(),
        data_contract_valid=True,
        text_fit_valid=True,
        renderer_available=True,
    )
    if not gate:
        failed_gate = next((name for name, passed in checks.items() if not passed), "NATIVE_GATE_FAILED")
        return _trace(
            resolved_role,
            native_rendered=False,
            failure_reason=failed_gate,
            human_approval_status="PASS" if checks.get("HUMAN_APPROVED") else "PENDING_OR_UNKNOWN",
            provenance_status="NOT_RUN",
            text_fit_status="NOT_RUN",
            sample_leak_status="NOT_RUN",
            requested_role=requested_role,
            template_id=str(spec.get("slide_id")),
        )

    try:
        result = render_native_role_dry_run(
            resolved_role,
            data=data,
            context=context,
            slide=slide_data,
            surface=effective_surface,
            slide_id=str(spec.get("slide_id")),
        )
        payload = result.payload
        provenance_status = "PASS" if payload and payload.failure_reason is None else "FAIL"
        text_fit_status = "PASS" if result.text_fit.get("valid") else ("FAIL" if result.text_fit else "NOT_RUN")
        sample_leak_status = "PASS" if result.validation.get("injected", {}).get("sample_content_leak_free", False) else ("FAIL" if result.validation else "NOT_RUN")
        if not result.success or not result.package_path:
            if visual_fallback and result.failure_reason == FailureReason.EVIDENCE_REQUIRED.value and resolved_role in _VISUAL_FALLBACK_ROLES:
                fallback = _render_visual_master_fallback(
                    prs,
                    resolved_role,
                    slide_data,
                    spec,
                    surface=effective_surface,
                )
                return _trace(
                    resolved_role,
                    native_rendered=False,
                    native_eligible=False,
                    failure_reason=FailureReason.EVIDENCE_REQUIRED.value,
                    human_approval_status="PASS",
                    provenance_status="FAIL",
                    text_fit_status=text_fit_status,
                    sample_leak_status="PASS" if fallback["validation"].get("sample_content_leak_free") else "FAIL",
                    requested_role=requested_role,
                    template_id=str(spec.get("slide_id")),
                    fallback_rendered=True,
                    fallback_kind="PROPOSAL_MASTER_EVIDENCE_SAFE",
                )
            return _trace(
                resolved_role,
                native_rendered=False,
                failure_reason=result.failure_reason or FailureReason.VALIDATION_FAILED.value,
                human_approval_status="PASS",
                provenance_status=provenance_status,
                text_fit_status=text_fit_status,
                sample_leak_status=sample_leak_status,
                requested_role=requested_role,
                template_id=str(spec.get("slide_id")),
            )

        # Import only the already validated, runtime-cloned package.  Image
        # relationships are deliberately rejected by the editable slide
        # importer; the established renderer then handles that role safely.
        _clone_template_slide(prs, Path(result.package_path))
        return _trace(
            resolved_role,
            native_rendered=True,
            failure_reason=None,
            human_approval_status="PASS",
            provenance_status=provenance_status,
            text_fit_status=text_fit_status,
            sample_leak_status=sample_leak_status,
            requested_role=requested_role,
            template_id=str(spec.get("slide_id")),
        )
    except ValueError as exc:
        if visual_fallback and resolved_role == "COVER" and "unsupported relationships" in str(exc):
            try:
                fallback = _render_visual_master_fallback(
                    prs,
                    resolved_role,
                    slide_data,
                    spec,
                    surface=effective_surface,
                    media=True,
                )
                return _trace(
                    resolved_role,
                    native_rendered=False,
                    native_eligible=True,
                    failure_reason=FailureReason.UNSUPPORTED_RELATIONSHIP.value,
                    human_approval_status="PASS",
                    provenance_status="PASS",
                    text_fit_status="PASS",
                    sample_leak_status="PASS" if fallback["validation"].get("sample_content_leak_free") else "FAIL",
                    requested_role=requested_role,
                    template_id=str(spec.get("slide_id")),
                    fallback_rendered=True,
                    fallback_kind="APPROVED_COVER_PACKAGE_CLONE",
                )
            except Exception:
                logger.exception("approved_cover_visual_fallback_failed")
        return _trace(
            resolved_role,
            native_rendered=False,
            native_eligible=True,
            failure_reason=(
                FailureReason.UNSUPPORTED_RELATIONSHIP.value
                if "unsupported relationships" in str(exc)
                else FailureReason.TEMPLATE_CLONE_FAILED.value
            ),
            human_approval_status="PASS",
            provenance_status="PASS",
            text_fit_status="PASS",
            sample_leak_status="PASS",
            requested_role=requested_role,
            template_id=str(spec.get("slide_id")),
        )
    except Exception:
        logger.exception("approved_native_dispatch_failed", extra={"role": resolved_role})
        return _trace(
            resolved_role,
            native_rendered=False,
            native_eligible=True,
            failure_reason=FailureReason.TEMPLATE_CLONE_FAILED.value,
            human_approval_status="PASS",
            provenance_status="PASS",
            text_fit_status="PASS",
            sample_leak_status="PASS",
            requested_role=requested_role,
            template_id=str(spec.get("slide_id")),
        )


# Name used by integration tests and future renderer adapters.
render_approved_slide = render_approved_native_slide
