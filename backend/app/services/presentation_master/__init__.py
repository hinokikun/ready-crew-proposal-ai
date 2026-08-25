"""Production-native Presentation Design Master package."""

from .contracts import (
    MASTER_FEATURE_FLAG,
    MASTER_MODE_ENABLED,
    MASTER_MODE_OFF,
    MASTER_MODE_SHADOW,
    MASTER_SOURCE_OF_TRUTH,
    MASTER_SHADOW_FEATURE_FLAG,
    MASTER_VERSION,
    MasterBuildOutput,
    MasterQualityError,
    MasterRoutingDecision,
    MasterUnsupportedInput,
    fallback_category_for_exception,
    resolve_master_runtime_mode,
)
from .grammar import PHASE4C_GRAMMAR_CONTRACT, golden_regression_cases, grammar_contract_summary
from .orchestrator import build_presentation_master
from .qa import route_payload_for_master, validate_master_output
from .renderer_mvp import (
    RENDERER_MVP_FEATURE_FLAG,
    RENDERER_MVP_VERSION,
    RendererMvpBuildOutput,
    RendererMvpIntegrationError,
    build_renderer_mvp_pptx,
    inspect_pptx_bytes,
)

__all__ = [
    "MASTER_FEATURE_FLAG",
    "MASTER_MODE_ENABLED",
    "MASTER_MODE_OFF",
    "MASTER_MODE_SHADOW",
    "MASTER_SOURCE_OF_TRUTH",
    "MASTER_SHADOW_FEATURE_FLAG",
    "MASTER_VERSION",
    "PHASE4C_GRAMMAR_CONTRACT",
    "MasterBuildOutput",
    "MasterQualityError",
    "MasterRoutingDecision",
    "MasterUnsupportedInput",
    "build_presentation_master",
    "fallback_category_for_exception",
    "golden_regression_cases",
    "grammar_contract_summary",
    "route_payload_for_master",
    "resolve_master_runtime_mode",
    "RENDERER_MVP_FEATURE_FLAG",
    "RENDERER_MVP_VERSION",
    "RendererMvpBuildOutput",
    "RendererMvpIntegrationError",
    "build_renderer_mvp_pptx",
    "inspect_pptx_bytes",
    "validate_master_output",
]
