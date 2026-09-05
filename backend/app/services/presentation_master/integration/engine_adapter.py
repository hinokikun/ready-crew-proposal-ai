from __future__ import annotations

import hashlib
import logging
from time import perf_counter
from typing import Any

from app.models import PptxDownloadRequest
from app.services.presentation_master.composition import compose_from_selection
from app.services.presentation_master.definitions import MASTER_REGISTRY
from app.services.presentation_master.renderer_integration import build_renderer_integration_spec
from app.services.presentation_master.renderer_mvp import RendererMvpNativeRenderer, inspect_pptx_bytes
from app.services.presentation_master.renderer_structural_bridge import build_renderer_structural_contract, validate_renderer_structural_contract
from app.services.presentation_master.selection import select_master, suitability_metadata
from app.services.presentation_master.upstream_adapter import composition_items_for_master

from .models import AdapterStatus, FallbackStage, Pmv3RenderResult, ProductionAdapterInput, ProductionPmv3AdapterResult
from .production_request_adapter import build_adapter_input
from .semantic_input_adapter import prepare_semantics


logger = logging.getLogger(__name__)

_PRESELECTION_EVENT = "presentation_master_preselection_snapshot"
_SELECTION_DIAGNOSTICS_EVENT = "presentation_master_selection_diagnostics"
_BOUNDED_MASTERS = frozenset(f"M{i}" for i in range(45, 55))
_BOUNDED_GROUPS = frozenset(
    group.group_id for definition in MASTER_REGISTRY.all() for group in definition.information_groups
)
_BOUNDED_RELATIONSHIPS = frozenset(
    relationship.relationship_type for definition in MASTER_REGISTRY.all() for relationship in definition.relationships
)
_BOUNDED_SIGNALS = frozenset(
    signal
    for master_id in _BOUNDED_MASTERS
    for signal in suitability_metadata(master_id).positive_signals
)
_BOUNDED_EVIDENCE_STATES = frozenset({"missing", "provided", "confirmed", "source_backed", "unverified"})
_BOUNDED_MISSING_KEYS = _BOUNDED_SIGNALS | {f"group:{group}" for group in _BOUNDED_GROUPS} | {
    "decision_context_unclear",
    "kpi_values_missing",
    "evidence_item_binding_missing",
    "stage_items_missing",
    "low_confidence",
}
_BOUNDED_PROVENANCE_KEYS = frozenset({"DIRECT", "SAFE_DERIVED", "EXISTING_SUPPLEMENT", "UNRESOLVED"})
_BOUNDED_DECISION_CONTEXTS = frozenset(
    context for master_id in _BOUNDED_MASTERS for context in suitability_metadata(master_id).decision_contexts
)
_BOUNDED_CANDIDATE_STATES = frozenset({"CONFIRMED", "CORRECTED", "UNCONFIRMED", "REJECTED", "UNRESOLVED"})


def _bounded_keys(values: Any, allowed: frozenset[str], *, limit: int = 64) -> tuple[str, ...]:
    if not isinstance(values, (set, frozenset, tuple, list)):
        return ()
    return tuple(sorted(value for value in values if isinstance(value, str) and value in allowed)[:limit])


def _correlation_id(adapter_input: ProductionAdapterInput, request_id: str | None) -> str:
    value = getattr(adapter_input.payload, "candidate_boundary_correlation_id", None)
    if isinstance(value, str) and value:
        return value[:64]
    if request_id:
        return hashlib.sha256(request_id.encode()).hexdigest()[:16]
    return "missing"


def _candidate_state_counts(candidate_set: Any) -> dict[str, int]:
    counts = {"confirmed": 0, "corrected": 0, "unconfirmed": 0, "rejected": 0, "unresolved": 0, "unresolved_critical": 0}
    candidates = tuple(getattr(candidate_set, "candidates", ())) if candidate_set is not None else ()
    for candidate in candidates:
        state = getattr(getattr(candidate, "review_state", None), "value", getattr(candidate, "review_state", None))
        if isinstance(state, str):
            key = state.lower()
            if key in counts:
                counts[key] += 1
    critical = getattr(candidate_set, "unresolved_critical", None) if candidate_set is not None else None
    if callable(critical):
        counts["unresolved_critical"] = min(max(len(tuple(critical())), 0), 100000)
    return counts


def _emit_preselection_snapshot(selection_input: Any, provenance: Any, adapter_input: ProductionAdapterInput, request_id: str | None) -> None:
    try:
        content_counts = getattr(selection_input, "content_counts", {})
        bounded_counts = {
            key: min(max(int(value), 0), 100000)
            for key, value in content_counts.items()
            if isinstance(key, str) and key in _BOUNDED_GROUPS and isinstance(value, int) and value >= 0
        }
        groups = _bounded_keys(getattr(selection_input, "available_groups", ()), _BOUNDED_GROUPS)
        fields = {
            "correlation_id": _correlation_id(adapter_input, request_id),
            "decision_context": (
                selection_input.decision_context
                if selection_input.decision_context in _BOUNDED_DECISION_CONTEXTS
                else ("empty" if not selection_input.decision_context else "unknown")
            ),
            "semantic_signal_keys": _bounded_keys(getattr(selection_input, "semantic_signals", ()), _BOUNDED_SIGNALS),
            "available_group_keys": groups,
            "group_counts": bounded_counts,
            "relationship_type_keys": _bounded_keys(getattr(selection_input, "relationship_types", ()), _BOUNDED_RELATIONSHIPS),
            "relationship_count": min(len(getattr(selection_input, "relationship_types", ())), 64),
            "content_counts": bounded_counts,
            "evidence_state_keys": _bounded_keys(getattr(selection_input, "evidence_states", ()), _BOUNDED_EVIDENCE_STATES),
            "source_binding_count": min(len(getattr(adapter_input, "source_bindings", ())), 100000),
            "unresolved_requirement_keys": _bounded_keys(getattr(selection_input, "missing_information", ()), _BOUNDED_MISSING_KEYS),
            "provenance_counts": {
                str(key): min(max(int(value), 0), 100000)
                for key, value in (provenance.items() if isinstance(provenance, dict) else ())
                if isinstance(key, str) and key in _BOUNDED_PROVENANCE_KEYS and isinstance(value, int) and value >= 0
            },
            "candidate_state_counts": _candidate_state_counts(getattr(adapter_input, "semantic_candidates", None)),
        }
        logger.info(_PRESELECTION_EVENT, extra=fields)
    except Exception:
        return


def _emit_selection_diagnostics(selection: Any, adapter_input: ProductionAdapterInput, request_id: str | None) -> None:
    try:
        diagnostics = []
        for rank, candidate in enumerate(getattr(selection, "ranked_candidates", ())[:10], start=1):
            master_id = getattr(candidate, "master_id", None)
            if master_id not in _BOUNDED_MASTERS:
                continue
            diagnostics.append(
                {
                    "master_id": master_id,
                    "rank": rank,
                    "score": int(getattr(candidate, "score", 0)),
                    "missing_keys": _bounded_keys(getattr(candidate, "missing_signals", ()), _BOUNDED_MISSING_KEYS),
                    "missing_groups": tuple(
                        sorted(
                            key[6:]
                            for key in getattr(candidate, "missing_signals", ())
                            if isinstance(key, str) and key.startswith("group:") and key[6:] in _BOUNDED_GROUPS
                        )
                    ),
                    "unsupported_topology": "unavailable",
                    "cardinality": getattr(candidate, "dimension_scores", {}).get("cardinality", "unavailable"),
                    "eligible": bool(getattr(candidate, "eligible", False)),
                }
            )
        logger.info(
            _SELECTION_DIAGNOSTICS_EVENT,
            extra={"correlation_id": _correlation_id(adapter_input, request_id), "masters": tuple(diagnostics)},
        )
    except Exception:
        return


_INVALID_INPUT_REASONS = frozenset(
    {
        "PRODUCTION_REQUEST_INVALID",
        "CONFIRMATION_TRANSPORT_INVALID",
        "SEMANTIC_SUPPLY_INVALID",
        "SEMANTIC_PREPARATION_INVALID",
        "MASTER_SELECTION_INVALID",
        "COMPOSITION_INVALID",
        "RENDER_PREPARATION_INVALID",
        "ADAPTER_VALIDATION_ERROR",
    }
)
_SEMANTIC_SUPPLY_INVALID_REASONS = frozenset(
    {
        "NO_CANDIDATES",
        "REVIEWED_BUT_AUTHORITY_NOT_ADMISSIBLE",
        "ADMISSIBILITY_STATE_UNCLASSIFIED",
    }
)
_BOUNDED_RESOLUTION_STATUSES = frozenset({"RESOLVED", "PARTIALLY_RESOLVED", "UNRESOLVED", "CONFLICT", "REVIEW_REQUIRED"})
_BOUNDED_REQUIREMENT_IDS = frozenset(
    {
        "kpi:value",
        "kpi:threshold",
        "stage:explicit_items",
        "responsibility:owner",
        "relationship:direction",
        "evidence_item_binding_missing",
        "kpi_values_missing",
        "stage_items_missing",
        "decision_context_unclear",
        "low_confidence",
        "conflict:duplicate_item_id",
        "conflict:multiple_owners",
    }
)
_BOUNDED_CONFLICT_TYPES = frozenset({"metric", "accountable_owner", "semantic_item_identity", "responsible_owner"})


def _semantic_supply_invalid_reason(candidate_set: Any) -> str:
    candidates = tuple(getattr(candidate_set, "candidates", ()))
    if not candidates:
        return "NO_CANDIDATES"
    if all(
        getattr(candidate, "review_state", None).value in {"CONFIRMED", "CORRECTED"}
        and getattr(candidate, "authority", None).value not in {"USER_EXPLICIT", "SYSTEM_EXTRACTED", "EXTERNAL_VERIFIED"}
        for candidate in candidates
    ):
        return "REVIEWED_BUT_AUTHORITY_NOT_ADMISSIBLE"
    return "ADMISSIBILITY_STATE_UNCLASSIFIED"


def _fallback(status: AdapterStatus, stage: FallbackStage, reason: str, **kwargs: Any) -> ProductionPmv3AdapterResult:
    return ProductionPmv3AdapterResult(
        status=status,
        semantic_readiness=status.value,
        fallback_required=True,
        fallback_reason=reason,
        fallback_stage=stage,
        **kwargs,
    )


def _resolution_diagnostics(resolution: Any) -> dict[str, Any]:
    """Expose only bounded fields already present on the frozen resolution result."""
    diagnostics: dict[str, Any] = {"resolution_diagnostic_status": "AVAILABLE"}
    try:
        status = getattr(getattr(resolution, "status", None), "value", None)
        if status in _BOUNDED_RESOLUTION_STATUSES:
            diagnostics["resolution_status"] = status
            diagnostics["resolution_status_requires_review"] = status in {"PARTIALLY_RESOLVED", "UNRESOLVED", "CONFLICT", "REVIEW_REQUIRED"}

        unresolved = tuple(getattr(resolution, "unresolved_requirement_ids", ()))
        diagnostics["unresolved_requirement_count"] = min(max(len(unresolved), 0), 64)
        diagnostics["resolution_has_unresolved_requirements"] = bool(unresolved)
        safe_unresolved = tuple(
            item for item in unresolved
            if isinstance(item, str) and item in _BOUNDED_REQUIREMENT_IDS
        )
        if safe_unresolved:
            diagnostics["unresolved_requirements"] = safe_unresolved[:16]

        conflicts = tuple(getattr(resolution, "conflicts", ()))
        diagnostics["conflict_count"] = min(max(len(conflicts), 0), 64)
        diagnostics["resolution_has_conflicts"] = bool(conflicts)
        safe_conflict_types = tuple(
            role for role in sorted(
                {
                    getattr(conflict, "semantic_role", None)
                    for conflict in conflicts
                    if isinstance(getattr(conflict, "semantic_role", None), str)
                    and getattr(conflict, "semantic_role", None) in _BOUNDED_CONFLICT_TYPES
                }
            )
        )
        if safe_conflict_types:
            diagnostics["conflict_types"] = safe_conflict_types[:16]
        elif conflicts:
            diagnostics["conflict_types"] = ("UNAVAILABLE",)
    except Exception:
        return {"resolution_diagnostic_status": "UNAVAILABLE"}
    return diagnostics


def prepare_pmv3(
    source: ProductionAdapterInput | PptxDownloadRequest,
    *,
    strategy_brief: Any | None = None,
    semantic_envelope: Any | None = None,
    source_bindings: tuple[Any, ...] = (),
    semantic_candidates: Any | None = None,
    semantic_relationships: tuple[Any, ...] = (),
) -> ProductionPmv3AdapterResult:
    try:
        try:
            adapter_input = source if isinstance(source, ProductionAdapterInput) else build_adapter_input(
                source,
                strategy_brief=strategy_brief,
                semantic_envelope=semantic_envelope,
                source_bindings=source_bindings,
                semantic_candidates=semantic_candidates,
                semantic_relationships=semantic_relationships,
            )
        except (TypeError, ValueError):
            reason = (
                "CONFIRMATION_TRANSPORT_INVALID"
                if isinstance(source, PptxDownloadRequest)
                and semantic_candidates is not None
                and source.semantic_confirmation_state is not None
                else "PRODUCTION_REQUEST_INVALID"
            )
            return _fallback(
                AdapterStatus.INVALID_INPUT,
                FallbackStage.INPUT_ADAPTER,
                "Invalid Production adapter input.",
                diagnostics={"invalid_input_reason": reason},
            )
        if (
            adapter_input.semantic_candidates is not None
            and not adapter_input.semantic_candidates.admissible()
            and not adapter_input.semantic_candidates.unresolved_critical()
        ):
            semantic_supply_invalid_reason = _semantic_supply_invalid_reason(adapter_input.semantic_candidates)
            return _fallback(
                AdapterStatus.INVALID_INPUT,
                FallbackStage.SEMANTIC_ADAPTER,
                "Confirmed semantic candidates are required.",
                diagnostics={
                    "invalid_input_reason": "SEMANTIC_SUPPLY_INVALID",
                    "semantic_supply_invalid_reason": semantic_supply_invalid_reason
                    if semantic_supply_invalid_reason in _SEMANTIC_SUPPLY_INVALID_REASONS
                    else "ADMISSIBILITY_STATE_UNCLASSIFIED",
                },
            )
        try:
            envelope, resolution, provenance, early_status, reason = prepare_semantics(adapter_input)
        except (TypeError, ValueError):
            return _fallback(
                AdapterStatus.INVALID_INPUT,
                FallbackStage.SEMANTIC_ADAPTER,
                "Invalid semantic preparation input.",
                diagnostics={"invalid_input_reason": "SEMANTIC_PREPARATION_INVALID"},
            )
        if early_status is not None:
            diagnostics = _resolution_diagnostics(resolution) if resolution is not None else {"resolution_diagnostic_status": "UNAVAILABLE"}
            return _fallback(early_status, FallbackStage.SEMANTIC_ADAPTER, reason, provenance_summary=provenance, diagnostics=diagnostics)
        selection_input = resolution.merged_envelope.to_selection_input()
        _emit_preselection_snapshot(selection_input, provenance, adapter_input, None)
        try:
            selection = select_master(selection_input)
        except (TypeError, ValueError):
            return _fallback(
                AdapterStatus.INVALID_INPUT,
                FallbackStage.MASTER_SELECTION,
                "Invalid master selection input.",
                diagnostics={"invalid_input_reason": "MASTER_SELECTION_INVALID"},
            )
        _emit_selection_diagnostics(selection, adapter_input, None)
        if selection.state == "no_match":
            return _fallback(AdapterStatus.NO_MATCH, FallbackStage.MASTER_SELECTION, selection.selection_reason, selection=selection, provenance_summary=provenance)
        if selection.state == "review_required":
            return _fallback(AdapterStatus.REVIEW_REQUIRED, FallbackStage.MASTER_SELECTION, selection.selection_reason, selection=selection, selected_master_id=selection.selected_master_id, provenance_summary=provenance)
        try:
            items = composition_items_for_master(resolution.merged_envelope, selection.selected_master_id)
            composition = compose_from_selection(selection_input, items)
        except (TypeError, ValueError):
            return _fallback(
                AdapterStatus.INVALID_INPUT,
                FallbackStage.COMPOSITION,
                "Invalid composition input.",
                diagnostics={"invalid_input_reason": "COMPOSITION_INVALID"},
            )
        if composition.composition is None or composition.state == "INVALID":
            return _fallback(AdapterStatus.NOT_READY, FallbackStage.COMPOSITION, "Composition is invalid.", selection=selection, selected_master_id=selection.selected_master_id, composition_readiness=composition.state, provenance_summary=provenance)
        if composition.state in {"DEGRADED", "REVIEW_REQUIRED"}:
            return _fallback(AdapterStatus.REVIEW_REQUIRED, FallbackStage.COMPOSITION, "Composition requires review.", selection=selection, selected_master_id=selection.selected_master_id, composition_readiness=composition.state, provenance_summary=provenance)
        try:
            definition = MASTER_REGISTRY.get(selection.selected_master_id)
            spec = build_renderer_integration_spec(composition.composition, definition)
            contract = build_renderer_structural_contract(spec)
            issues = validate_renderer_structural_contract(contract)
        except (TypeError, ValueError):
            return _fallback(
                AdapterStatus.INVALID_INPUT,
                FallbackStage.RENDER_PREP,
                "Invalid renderer preparation input.",
                diagnostics={"invalid_input_reason": "RENDER_PREPARATION_INVALID"},
            )
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
    except (TypeError, ValueError):
        return _fallback(
            AdapterStatus.INVALID_INPUT,
            FallbackStage.INPUT_ADAPTER,
            "Invalid adapter validation input.",
            diagnostics={"invalid_input_reason": "ADAPTER_VALIDATION_ERROR"},
        )
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
