from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from app.models import PptxDownloadRequest, SemanticConfirmationTransportItem

from .production_semantic_contract import ProductionSemanticCandidateSet
from .semantic_confirmation_transport import apply_semantic_confirmation_state


@dataclass(frozen=True)
class ShadowCandidateBinding:
    """Minimal request-scoped binding; no request, response, or primary bytes."""

    request_id: str
    detailed: bool
    candidates: ProductionSemanticCandidateSet
    confirmation_state: tuple[SemanticConfirmationTransportItem, ...]
    relationships: tuple[Any, ...] = ()


def bind_shadow_candidates(
    payload: PptxDownloadRequest,
    *,
    request_id: str | None,
    candidates: ProductionSemanticCandidateSet | None,
    confirmation_state: Iterable[SemanticConfirmationTransportItem | dict[str, Any]] | None = None,
) -> ShadowCandidateBinding | None:
    """Resolve the authoritative candidate set without reconstructing semantics."""
    if not isinstance(payload, PptxDownloadRequest) or payload.summary:
        return None
    if not request_id or candidates is None or confirmation_state is None:
        return None
    state = tuple(
        item if isinstance(item, SemanticConfirmationTransportItem) else SemanticConfirmationTransportItem.parse_obj(item)
        for item in confirmation_state
    )
    transported = apply_semantic_confirmation_state(candidates, state)
    return ShadowCandidateBinding(
        request_id=request_id,
        detailed=True,
        candidates=transported,
        confirmation_state=state,
    )


__all__ = ["ShadowCandidateBinding", "bind_shadow_candidates"]
