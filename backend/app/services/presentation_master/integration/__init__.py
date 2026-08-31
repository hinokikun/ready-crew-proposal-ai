"""Offline-only Production-to-Presentation-Master adapter contracts."""

from .engine_adapter import prepare_pmv3, render_pmv3
from .models import (
    AdapterStatus,
    FallbackStage,
    ProductionAdapterInput,
    ProductionPmv3AdapterResult,
    Pmv3RenderResult,
    ProvenanceClass,
)
from .production_request_adapter import build_adapter_input, PRODUCTION_REQUEST_MAPPING
from .semantic_supply_adapter import ProductionSemanticSupply, SemanticAvailability, SemanticSupplyField, inspect_production_semantic_supply
from .semantic_confirmation_transport import SemanticConfirmationTransportError, apply_semantic_confirmation_state
from .shadow_integration import ShadowController, ShadowJob, ShadowResult, ShadowEligibility, eligible_for_shadow, is_sampled
from .shadow_candidate_binding import ShadowCandidateBinding, bind_shadow_candidates
from .shadow_process_isolation import ProcessShadowController, ProcessShadowJob, ShadowProcessWorkload
from .candidate_state_bridge import (
    CandidateStateBridgeError,
    ProductionShadowCandidateContext,
    build_candidate_state_bridge,
    candidate_set_from_dict,
)
from .production_semantic_contract import (
    ProductionSemanticCandidate,
    ProductionSemanticCandidateSet,
    SemanticAuthority,
    SemanticItemType,
    SemanticReviewState,
    confirm_candidate,
    correct_candidate,
    reject_candidate,
    extract_explicit_candidates,
    propose_candidates_from_analysis,
    candidate_set_to_dict,
)
from .semantic_supply_adapter import build_semantic_envelope_from_confirmed_candidates

__all__ = [
    "AdapterStatus",
    "FallbackStage",
    "ProductionAdapterInput",
    "ProductionPmv3AdapterResult",
    "Pmv3RenderResult",
    "ProvenanceClass",
    "PRODUCTION_REQUEST_MAPPING",
    "build_adapter_input",
    "prepare_pmv3",
    "render_pmv3",
    "ProductionSemanticSupply",
    "SemanticAvailability",
    "SemanticSupplyField",
    "inspect_production_semantic_supply",
    "SemanticConfirmationTransportError",
    "apply_semantic_confirmation_state",
    "ShadowController",
    "ShadowJob",
    "ShadowResult",
    "ShadowEligibility",
    "eligible_for_shadow",
    "is_sampled",
    "ShadowCandidateBinding",
    "bind_shadow_candidates",
    "ProcessShadowController",
    "ProcessShadowJob",
    "ShadowProcessWorkload",
    "CandidateStateBridgeError",
    "ProductionShadowCandidateContext",
    "build_candidate_state_bridge",
    "candidate_set_from_dict",
    "ProductionSemanticCandidate",
    "ProductionSemanticCandidateSet",
    "SemanticAuthority",
    "SemanticItemType",
    "SemanticReviewState",
    "confirm_candidate",
    "correct_candidate",
    "reject_candidate",
    "extract_explicit_candidates",
    "propose_candidates_from_analysis",
    "candidate_set_to_dict",
    "build_semantic_envelope_from_confirmed_candidates",
]
