from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.models import PptxDownloadRequest


class AdapterStatus(str, Enum):
    READY = "READY"
    READY_WITH_VALID_BINDINGS = "READY_WITH_VALID_BINDINGS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_READY = "NOT_READY"
    NO_MATCH = "NO_MATCH"
    INVALID_INPUT = "INVALID_INPUT"
    ADAPTER_ERROR = "ADAPTER_ERROR"


class FallbackStage(str, Enum):
    INPUT_ADAPTER = "INPUT_ADAPTER"
    SEMANTIC_ADAPTER = "SEMANTIC_ADAPTER"
    SEMANTIC_RESOLUTION = "SEMANTIC_RESOLUTION"
    MASTER_SELECTION = "MASTER_SELECTION"
    COMPOSITION = "COMPOSITION"
    RENDER_PREP = "RENDER_PREP"


class ProvenanceClass(str, Enum):
    DIRECT = "DIRECT"
    SAFE_DERIVED = "SAFE_DERIVED"
    EXISTING_SUPPLEMENT = "EXISTING_SUPPLEMENT"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ProductionAdapterInput:
    payload: PptxDownloadRequest
    strategy_brief: Any | None = None
    semantic_envelope: Any | None = None
    source_bindings: tuple[Any, ...] = ()
    semantic_candidates: Any | None = None
    semantic_relationships: tuple[Any, ...] = ()
    source_metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProductionPmv3AdapterResult:
    status: AdapterStatus
    semantic_readiness: str
    selection: Any | None = None
    selected_master_id: str | None = None
    composition_readiness: str = "NOT_READY"
    fallback_required: bool = False
    fallback_reason: str = ""
    fallback_stage: FallbackStage | None = None
    renderer_spec: dict[str, Any] | None = None
    provenance_summary: dict[str, int] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Pmv3RenderResult:
    pptx_bytes: bytes
    selected_master_id: str
    readiness: AdapterStatus
    slide_count: int
    validation_status: str
    renderer_duration_ms: int
    rasterization_ratio: float = 0.0
    clipping_count: int = 0
    overflow_count: int = 0
    off_canvas_count: int = 0
    fallback_required: bool = False
    fallback_reason: str = ""
