# Phase 2B Handoff

## Recommended Next Phase

Phase 2B should convert Deck Blueprint planning output into Slide Blueprint skeleton planning while remaining offline.

## Inputs

- `DeckBlueprint`
- `sections`
- `slide_plan`
- `slide_recommendations`
- `story_beats`
- `decision_points`
- `cta_plan`
- `theme_direction`

## Required Boundaries

Phase 2B should still avoid:

- Existing Proposal Generator connection
- PPTX rendering
- Frontend changes
- Backend API routes
- Database persistence
- Migration
- Beautiful.ai connection

## Suggested Goals

1. Create a Deck-to-Slide Planning Adapter.
2. Generate one Slide Blueprint skeleton per `slide_plan` item.
3. Preserve Deck Planner IDs.
4. Keep final headline, body copy, diagram detail, and rendering out of scope unless separately approved.
5. Validate every generated Slide Blueprint with the Phase 1 contract.

## Acceptance Criteria

- Every required slide plan item has a corresponding Slide Blueprint skeleton.
- No rendered PowerPoint is produced.
- No runtime proposal flow is changed.
- Golden Deck Planner outputs remain compatible.

