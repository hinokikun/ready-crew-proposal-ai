from __future__ import annotations

from typing import Any

from app.services.presentation_master.semantic_enrichment import enrich_semantic_envelope
from app.services.presentation_master.semantic_resolution import resolve_semantic_inputs
from app.services.presentation_master.semantic_supplement import ProposalSemanticSupplement
from app.services.presentation_master.source_binding import BindingState, validate_source_bindings
from app.services.presentation_master.upstream_adapter import adapt_strategy_brief

from .models import AdapterStatus, FallbackStage, ProductionAdapterInput, ProductionPmv3AdapterResult, ProvenanceClass
from .semantic_supply_adapter import build_semantic_envelope_from_confirmed_candidates


def _provenance_summary(envelope: Any) -> dict[str, int]:
    summary = {item.value: 0 for item in ProvenanceClass}
    for item in getattr(envelope, "items", ()):
        level = getattr(getattr(item, "derivation_level", None), "value", "")
        if level in {"DIRECT", "NORMALIZED"}:
            summary[ProvenanceClass.DIRECT.value] += 1
        elif level == "DERIVED":
            summary[ProvenanceClass.SAFE_DERIVED.value] += 1
        else:
            summary[ProvenanceClass.UNRESOLVED.value] += 1
    summary[ProvenanceClass.UNRESOLVED.value] += len(getattr(envelope, "unresolved_gaps", ()))
    return summary


def prepare_semantics(source: ProductionAdapterInput) -> tuple[Any, Any | None, dict[str, int], AdapterStatus | None, str]:
    if source.semantic_envelope is not None:
        envelope = source.semantic_envelope
    elif source.semantic_candidates is not None:
        if source.semantic_candidates.unresolved_critical():
            return None, None, {}, AdapterStatus.REVIEW_REQUIRED, "Critical semantic candidates require explicit confirmation."
        envelope = build_semantic_envelope_from_confirmed_candidates(source.semantic_candidates)
    elif source.strategy_brief is not None:
        envelope = adapt_strategy_brief(source.strategy_brief)
    else:
        return None, None, {}, AdapterStatus.NOT_READY, "StrategyBrief or explicit semantic envelope is required."

    binding_result = validate_source_bindings(source.source_bindings) if source.source_bindings else None
    if binding_result is not None and binding_result.state in {BindingState.INVALID, BindingState.CONFLICT}:
        return envelope, None, _provenance_summary(envelope), AdapterStatus.REVIEW_REQUIRED, "Source bindings are invalid or conflicting."
    enrichment = enrich_semantic_envelope(envelope)
    supplement = binding_result.supplement if binding_result is not None else ProposalSemanticSupplement()
    resolution = resolve_semantic_inputs(enrichment, supplement)
    # The frozen resolver uses UNRESOLVED for an envelope with no resolver
    # requirements. That is distinct from an unresolved requirement: allow
    # selection when there are no unresolved IDs or conflicts, and preserve
    # review status when concrete gaps remain.
    if resolution.unresolved_requirement_ids or resolution.conflicts or resolution.status.value in {"CONFLICT", "REVIEW_REQUIRED"}:
        return envelope, resolution, _provenance_summary(resolution.merged_envelope), AdapterStatus.REVIEW_REQUIRED, f"Semantic resolution is {resolution.status.value}."
    return resolution.merged_envelope, resolution, _provenance_summary(resolution.merged_envelope), None, ""
