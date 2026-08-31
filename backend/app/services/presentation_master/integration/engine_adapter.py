from __future__ import annotations

from time import perf_counter
from typing import Any

from app.models import PptxDownloadRequest
from app.services.presentation_master.composition import compose_from_selection
from app.services.presentation_master.definitions import MASTER_REGISTRY
from app.services.presentation_master.renderer_integration import build_renderer_integration_spec
from app.services.presentation_master.renderer_mvp import RendererMvpNativeRenderer, inspect_pptx_bytes
from app.services.presentation_master.renderer_structural_bridge import build_renderer_structural_contract, validate_renderer_structural_contract
from app.services.presentation_master.selection import select_master
from app.services.presentation_master.upstream_adapter import composition_items_for_master

from .models import AdapterStatus, FallbackStage, Pmv3RenderResult, ProductionAdapterInput, ProductionPmv3AdapterResult
from .production_request_adapter import build_adapter_input
from .semantic_input_adapter import prepare_semantics


def _fallback(status: AdapterStatus, stage: FallbackStage, reason: str, **kwargs: Any) -> ProductionPmv3AdapterResult:
    return ProductionPmv3AdapterResult(
        status=status,
        semantic_readiness=status.value,
        fallback_required=True,
        fallback_reason=reason,
        fallback_stage=stage,
        **kwargs,
    )


def prepare_pmv3(
    source: ProductionAdapterInput | PptxDownloadRequest,
    *,
    strategy_brief: Any | None = None,
    semantic_envelope: Any | None = None,
    source_bindings: tuple[Any, ...] = (),
    semantic_candidates: Any | None = None,
) -> ProductionPmv3AdapterResult:
    try:
        adapter_input = source if isinstance(source, ProductionAdapterInput) else build_adapter_input(
            source,
            strategy_brief=strategy_brief,
            semantic_envelope=semantic_envelope,
            source_bindings=source_bindings,
            semantic_candidates=semantic_candidates,
        )
        envelope, resolution, provenance, early_status, reason = prepare_semantics(adapter_input)
        if early_status is not None:
            return _fallback(early_status, FallbackStage.SEMANTIC_ADAPTER, reason, provenance_summary=provenance)
        selection_input = resolution.merged_envelope.to_selection_input()
        selection = select_master(selection_input)
        if selection.state == "no_match":
            return _fallback(AdapterStatus.NO_MATCH, FallbackStage.MASTER_SELECTION, selection.selection_reason, selection=selection, provenance_summary=provenance)
        if selection.state == "review_required":
            return _fallback(AdapterStatus.REVIEW_REQUIRED, FallbackStage.MASTER_SELECTION, selection.selection_reason, selection=selection, selected_master_id=selection.selected_master_id, provenance_summary=provenance)
        items = composition_items_for_master(resolution.merged_envelope, selection.selected_master_id)
        composition = compose_from_selection(selection_input, items)
        if composition.composition is None or composition.state == "INVALID":
            return _fallback(AdapterStatus.NOT_READY, FallbackStage.COMPOSITION, "Composition is invalid.", selection=selection, selected_master_id=selection.selected_master_id, composition_readiness=composition.state, provenance_summary=provenance)
        if composition.state in {"DEGRADED", "REVIEW_REQUIRED"}:
            return _fallback(AdapterStatus.REVIEW_REQUIRED, FallbackStage.COMPOSITION, "Composition requires review.", selection=selection, selected_master_id=selection.selected_master_id, composition_readiness=composition.state, provenance_summary=provenance)
        definition = MASTER_REGISTRY.get(selection.selected_master_id)
        spec = build_renderer_integration_spec(composition.composition, definition)
        contract = build_renderer_structural_contract(spec)
        issues = validate_renderer_structural_contract(contract)
        if issues:
            return _fallback(AdapterStatus.NOT_READY, FallbackStage.RENDER_PREP, "Renderer structural preparation failed.", selection=selection, selected_master_id=selection.selected_master_id, composition_readiness=composition.state, provenance_summary=provenance, diagnostics={"issue_count": len(issues)})
        binding_ready = bool(adapter_input.source_bindings)
        return ProductionPmv3AdapterResult(
            status=AdapterStatus.READY_WITH_VALID_BINDINGS if binding_ready else AdapterStatus.READY,
            semantic_readiness="RESOLVED",
            selection=selection,
            selected_master_id=selection.selected_master_id,
            composition_readiness=composition.state,
            renderer_spec=contract,
            provenance_summary=provenance,
            diagnostics={"renderer_preparation": "PASS", "structural_issue_count": 0},
        )
    except (TypeError, ValueError) as exc:
        return _fallback(AdapterStatus.INVALID_INPUT, FallbackStage.INPUT_ADAPTER, exc.__class__.__name__)
    except Exception as exc:
        return _fallback(AdapterStatus.ADAPTER_ERROR, FallbackStage.SEMANTIC_ADAPTER, exc.__class__.__name__)


def render_pmv3(prepared: ProductionPmv3AdapterResult) -> Pmv3RenderResult:
    if prepared.status not in {AdapterStatus.READY, AdapterStatus.READY_WITH_VALID_BINDINGS} or not prepared.renderer_spec or not prepared.selected_master_id:
        raise ValueError("PMV3 render requires a ready prepared adapter result")
    started = perf_counter()
    pptx_bytes, render_report = RendererMvpNativeRenderer().render_deck_to_bytes(prepared.renderer_spec)
    audit = inspect_pptx_bytes(pptx_bytes)
    if pptx_bytes[:2] != b"PK" or not audit.get("page_count"):
        raise ValueError("PMV3 renderer returned an invalid PPTX")
    return Pmv3RenderResult(
        pptx_bytes=pptx_bytes,
        selected_master_id=prepared.selected_master_id,
        readiness=prepared.status,
        slide_count=int(audit["page_count"]),
        validation_status="PASS",
        renderer_duration_ms=round((perf_counter() - started) * 1000),
        rasterization_ratio=float(audit.get("rasterization_ratio", 0.0)),
        clipping_count=int(audit.get("clipping_count", 0)),
        overflow_count=int(audit.get("overflow_count", 0)),
        off_canvas_count=int(audit.get("off_canvas_count", 0)),
    )
