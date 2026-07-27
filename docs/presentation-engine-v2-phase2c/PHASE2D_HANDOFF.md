# Phase 2D Handoff

## Inputs Available for Phase 2D

- `MessageDesignerOutput`
- `SlideMessageDesign`
- headline
- main_message
- supporting_messages
- key_takeaway
- speaker_note_summary
- evidence_alignment_level
- missing_evidence_disclosure
- message_style
- message_tone
- message_confidence
- evaluation_result

## Recommended Next Phase

Phase 2D should decide Slide Intent or Slide Blueprint inputs from message contracts without re-running Deck Planner or Evidence Planner.

## Non-Negotiable Boundary

Phase 2D must not treat missing evidence as confirmed fact. It must preserve disclosures and warnings into downstream contracts.
