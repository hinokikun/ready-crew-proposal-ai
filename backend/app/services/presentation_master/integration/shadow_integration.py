"""Single public Shadow controller facade.

The execution implementation lives in ``shadow_process_isolation``. This
module intentionally contains no executor or renderer execution of its own.
"""

from dataclasses import dataclass
from .shadow_process_isolation import ProcessShadowController, ProcessShadowJob, ShadowProcessWorkload

ShadowResult = dict[str, object]


@dataclass(frozen=True)
class ShadowEligibility:
    eligible: bool
    reason: str = "NOT_ELIGIBLE"

ShadowController = ProcessShadowController
ShadowJob = ProcessShadowJob

is_sampled = ProcessShadowController.is_sampled
eligible_for_shadow = ProcessShadowController.eligibility

__all__ = [
    "ShadowController",
    "ShadowJob",
    "ShadowProcessWorkload",
    "ShadowResult",
    "ProcessShadowController",
    "eligible_for_shadow",
    "is_sampled",
    "ShadowEligibility",
]
