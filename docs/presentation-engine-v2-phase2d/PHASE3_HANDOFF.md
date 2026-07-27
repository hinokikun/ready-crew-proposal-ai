# Phase 3 Handoff

Phase 3 can consume Slide Intent Output as the input to Visual Director.

## Recommended Inputs to Phase 3

- `slide_intent`
- `slide_type`
- `information_priority`
- `reading_order`
- `visual_pattern_candidate`
- `diagram_candidate`
- `chart_candidate`
- `layout_constraint`
- `rendering_hint`
- `intent_confidence`
- `warnings`
- `validation_result`

## Phase 3 Must Not Re-decide

Visual Director should not re-run story strategy or message design. It should use the Phase 2D intent as the abstraction layer between message and visual expression.

## Phase 3 Must Decide

- concrete visual composition
- diagram structure
- chart structure
- layout blueprint
- visual hierarchy
- theme and typography tokens

## Go Criteria

- Phase 2D pytest passes
- Presentation Engine v2 pytest passes
- no API / DB / Frontend / PPTX changes
- normal fixtures validate
- failure fixtures fail safely
