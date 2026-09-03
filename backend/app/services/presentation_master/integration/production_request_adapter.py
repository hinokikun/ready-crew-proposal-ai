from __future__ import annotations

from typing import Any

from app.models import PptxDownloadRequest

from .models import ProductionAdapterInput, ProvenanceClass
from .semantic_confirmation_transport import apply_semantic_confirmation_state


PRODUCTION_REQUEST_MAPPING: dict[str, ProvenanceClass | None] = {
    "project_summary": ProvenanceClass.DIRECT,
    "customer_company": ProvenanceClass.DIRECT,
    "business_issue": ProvenanceClass.DIRECT,
    "proposal_direction": ProvenanceClass.DIRECT,
    "budget": ProvenanceClass.DIRECT,
    "deadline": ProvenanceClass.DIRECT,
    "timeline": ProvenanceClass.DIRECT,
    "decision_maker": None,
    "kpi": None,
    "kpi_threshold": None,
    "stages": None,
    "responsibilities": None,
    "evidence": None,
    "constraints": ProvenanceClass.DIRECT,
    "story": ProvenanceClass.EXISTING_SUPPLEMENT,
    "strategy": ProvenanceClass.EXISTING_SUPPLEMENT,
    "audience": ProvenanceClass.SAFE_DERIVED,
    "category": ProvenanceClass.SAFE_DERIVED,
}


def build_adapter_input(
    payload: PptxDownloadRequest,
    *,
    strategy_brief: Any | None = None,
    semantic_envelope: Any | None = None,
    source_bindings: tuple[Any, ...] = (),
    semantic_candidates: Any | None = None,
    semantic_relationships: tuple[Any, ...] = (),
    source_metadata: dict[str, str] | None = None,
) -> ProductionAdapterInput:
    if not isinstance(payload, PptxDownloadRequest):
        raise TypeError("Production adapter requires PptxDownloadRequest")
    resolved_candidates = semantic_candidates
    if resolved_candidates is not None and payload.semantic_confirmation_state is not None:
        resolved_candidates = apply_semantic_confirmation_state(resolved_candidates, payload.semantic_confirmation_state)
    return ProductionAdapterInput(
        payload=payload,
        strategy_brief=strategy_brief,
        semantic_envelope=semantic_envelope,
        source_bindings=tuple(source_bindings),
        semantic_candidates=resolved_candidates,
        semantic_relationships=tuple(semantic_relationships),
        source_metadata=dict(source_metadata or {}),
    )
