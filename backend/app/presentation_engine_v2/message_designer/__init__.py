"""Offline Message Designer for Presentation Engine 2.0 Phase 2C.

This package creates message-level plans only. It does not create Slide
Blueprints, visuals, diagrams, layouts, themes, typography, PPTX output, API
routes, database records, or runtime proposal output.
"""

from .designer import MessageDesigner, design_messages, design_messages_from_payload
from .designer_evaluator import evaluate_message_designer_output, evaluate_slide_message_design
from .designer_models import MessageDesignerInput, MessageDesignerOutput, SlideMessageDesign

__all__ = [
    "MessageDesigner",
    "MessageDesignerInput",
    "MessageDesignerOutput",
    "SlideMessageDesign",
    "design_messages",
    "design_messages_from_payload",
    "evaluate_message_designer_output",
    "evaluate_slide_message_design",
]
