# Future Roadmap

## Phase 3: Visual Director

Purpose:

- Convert Slide Intent Output into Visual Plan Contract.

Expected scope:

- Contract adapter
- Rule engine
- Candidate generation
- Candidate scoring
- Candidate selection
- Fallback strategy
- Visual Plan validation
- Fixtures and golden outputs
- Alpha Integration extension

Release gate:

- Deterministic outputs
- No P0 validator failures
- Golden outputs for representative cases
- No renderer, PPTX, API, DB, or frontend connection

## Phase 4: Blueprint Composer

Purpose:

- Convert Visual Plan Contract into renderer-ready slide blueprint structure.

Expected scope:

- Component hierarchy
- Composition intent
- Density handling
- Safe area and grouping intent
- Renderer-independent blueprint output

Release gate:

- Blueprint output can be validated without PowerPoint rendering.
- Visual Plan semantics are preserved.

## Phase 5: Renderer

Purpose:

- Render validated blueprint output into editable PowerPoint shapes.

Expected scope:

- PowerPoint primitives
- Text boxes, cards, connectors, tables, icons, placeholders
- Layout safety checks
- Editable output guarantee

Release gate:

- Generated PPTX is editable.
- No text overflow in representative fixtures.
- No renderer mutation of message or strategy.

## Phase 6: Version81 Integration

Purpose:

- Connect Presentation Engine 2.0 to existing Version81 flow through a feature
  flag and adapter layer.

Expected scope:

- Feature flag
- Legacy fallback
- Contract adapter
- Regression tests
- Human review gate

Release gate:

- Existing PPTX generation remains unchanged by default.
- New engine can be disabled immediately.

## Production Candidate

Production readiness requires:

- Real proposal validation
- Human visual quality review
- Accessibility review
- Performance review
- Regression against existing ProposalPilot generation
- Rollback plan
