# Presentation Engine 2.0 Phase 2C Message Designer

This module is an offline, deterministic foundation for slide-level message design.

## Scope

The Message Designer accepts:

- Proposal Context
- Deck Blueprint
- Evidence Planner Result

It emits message-only contracts for each planned slide:

- headline
- main_message
- supporting_messages
- key_takeaway
- speaker_note_summary
- message_style
- message_confidence
- evidence_alignment_summary
- missing_evidence_disclosure
- warnings
- validation_result

## Explicit Non-Scope

This module does not create or connect:

- Slide Blueprint
- Diagram
- Layout
- Theme
- Typography
- Image
- Chart
- PPTX
- Renderer
- Quality Engine
- Frontend
- Backend API
- Database

## Determinism

The implementation uses rules only and does not call OpenAI, Beautiful.ai, or any runtime proposal generation path.
