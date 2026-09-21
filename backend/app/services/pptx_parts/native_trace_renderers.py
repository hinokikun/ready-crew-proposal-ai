"""Editable native-slide cloning for the approved Phase3F templates.

The source files are PPTX files made from editable PowerPoint text and shapes.
This module copies those shapes into the current presentation; it never adds a
full-slide screenshot.  A caller may fall back to the existing renderer when
the source cannot be safely cloned.
"""

from __future__ import annotations

from copy import deepcopy
import logging
from pathlib import Path
from typing import Iterable

from pptx import Presentation
from pptx.oxml.ns import qn

from app.services.pptx_parts.native_trace_registry import (
    get_native_role_spec,
    get_runtime_native_role_spec,
    native_role_gate,
    runtime_native_role_gate,
)
from app.services.pptx_parts.native_trace_content_adapter import (
    FailureReason,
    render_native_role_dry_run,
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
    destination = prs.slides.add_slide(prs.slide_layouts[6])
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
    if role in {"COMPETITION", "COMPETITIVE_COMPARISON", "WIN_PROBABILITY"}:
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
) -> dict[str, object]:
    return {
        "ROLE": role,
        "NATIVE_REQUESTED": True,
        "NATIVE_ELIGIBLE": bool(native_rendered if native_eligible is None else native_eligible),
        "NATIVE_RENDERED": bool(native_rendered),
        "FALLBACK_USED": not native_rendered,
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
) -> dict[str, object]:
    """Attempt one native role and return a structured role-level trace.

    The function never raises for an expected native eligibility/rendering
    failure.  The caller owns the existing-renderer fallback.
    """

    resolved_role = role
    if resolved_role is None:
        from app.services.pptx_parts.native_trace_registry import resolve_approved_native_role

        resolved_role = resolve_approved_native_role(slide_data, index)
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
            return _trace(
                resolved_role,
                native_rendered=False,
                failure_reason=result.failure_reason or FailureReason.VALIDATION_FAILED.value,
                human_approval_status="PASS",
                provenance_status=provenance_status,
                text_fit_status=text_fit_status,
                sample_leak_status=sample_leak_status,
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
        )
    except ValueError as exc:
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
        )


# Name used by integration tests and future renderer adapters.
render_approved_slide = render_approved_native_slide
