"""Phase 2D Slide Intent Foundation."""

from .intent_enums import (
    ChartCandidate,
    DiagramCandidate,
    InformationDensity,
    IntentConfidence,
    LayoutConstraint,
    ReadingOrder,
    SlideIntentType,
    SlideType,
    ValidationSeverity,
    VisualPattern,
)
from .intent_evaluator import evaluate_slide_intent_design, evaluate_slide_intent_output
from .intent_models import (
    SlideIntentDesign,
    SlideIntentInput,
    SlideIntentOutput,
    SUPPORTED_SLIDE_INTENT_OUTPUT_VERSION,
    SUPPORTED_SLIDE_INTENT_VERSION,
)
from .intent_validators import validate_slide_intent_design, validate_slide_intent_output
from .slide_intent import (
    SlideIntentEngine,
    SlideIntentInputError,
    design_slide_intents,
    design_slide_intents_from_payload,
)

__all__ = [
    "ChartCandidate",
    "DiagramCandidate",
    "InformationDensity",
    "IntentConfidence",
    "LayoutConstraint",
    "ReadingOrder",
    "SUPPORTED_SLIDE_INTENT_OUTPUT_VERSION",
    "SUPPORTED_SLIDE_INTENT_VERSION",
    "SlideIntentDesign",
    "SlideIntentEngine",
    "SlideIntentInput",
    "SlideIntentInputError",
    "SlideIntentOutput",
    "SlideIntentType",
    "SlideType",
    "ValidationSeverity",
    "VisualPattern",
    "design_slide_intents",
    "design_slide_intents_from_payload",
    "evaluate_slide_intent_design",
    "evaluate_slide_intent_output",
    "validate_slide_intent_design",
    "validate_slide_intent_output",
]
