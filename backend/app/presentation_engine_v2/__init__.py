"""Presentation Engine 2.0 Phase 1 contract foundation.

This package is intentionally offline and isolated. It defines blueprint
contracts, validation, normalization, fixtures, and evaluation helpers only.
It is not connected to existing proposal generation or PPTX rendering flows.
"""

from .evaluator import EvaluationReport, evaluate_blueprint
from .models import SlideBlueprint
from .normalizers import NormalizationResult, normalize_blueprint_payload
from .schema import slide_blueprint_schema
from .validators import validate_blueprint

__all__ = [
    "EvaluationReport",
    "NormalizationResult",
    "SlideBlueprint",
    "evaluate_blueprint",
    "normalize_blueprint_payload",
    "slide_blueprint_schema",
    "validate_blueprint",
]
