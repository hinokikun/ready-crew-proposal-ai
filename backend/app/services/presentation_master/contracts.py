from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MASTER_VERSION = "presentation_design_master_v1"
MASTER_FEATURE_FLAG = "PRESENTATION_DESIGN_AI_MASTER_ENABLED"
MASTER_SHADOW_FEATURE_FLAG = "PRESENTATION_DESIGN_AI_MASTER_SHADOW_ENABLED"
MASTER_SOURCE_OF_TRUTH = "phase4c_human_approved_visual_grammar"
MASTER_MODE_OFF = "off"
MASTER_MODE_SHADOW = "shadow"
MASTER_MODE_ENABLED = "enabled"


@dataclass(frozen=True)
class MasterRoutingDecision:
    supported: bool
    route: str
    reason_code: str = ""
    failure_stage: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "supported": self.supported,
            "route": self.route,
            "reason_code": self.reason_code,
            "failure_stage": self.failure_stage,
        }


@dataclass(frozen=True)
class MasterBuildOutput:
    pptx_bytes: bytes
    quality_report: dict[str, Any]


class MasterUnsupportedInput(ValueError):
    def __init__(self, decision: MasterRoutingDecision):
        self.decision = decision
        self.reason_code = decision.reason_code or "unsupported_input"
        self.failure_stage = decision.failure_stage or "routing"
        super().__init__(self.reason_code)


class MasterQualityError(ValueError):
    def __init__(self, reason_code: str, *, qa_report: dict[str, Any]):
        self.reason_code = reason_code
        self.failure_stage = "qa_blocking"
        self.qa_report = qa_report
        super().__init__(reason_code)


def resolve_master_runtime_mode(*, enabled: bool, shadow_enabled: bool, explicit_shadow: bool = False) -> str:
    if enabled:
        return MASTER_MODE_ENABLED
    if shadow_enabled or explicit_shadow:
        return MASTER_MODE_SHADOW
    return MASTER_MODE_OFF


def fallback_category_for_exception(exc: Exception) -> str:
    reason_code = getattr(exc, "reason_code", "")
    if reason_code in {"summary_deck_uses_legacy", "unsupported_category_uses_legacy"}:
        return "unsupported"
    if isinstance(exc, TimeoutError):
        return "timeout"
    if exc.__class__.__name__ == "MasterQualityError" or reason_code == "master_runtime_qa_blocked":
        return "qa_block"
    if isinstance(exc, (ImportError, ModuleNotFoundError, ValueError, RuntimeError)):
        return "generation_failure"
    return "unexpected_error"
