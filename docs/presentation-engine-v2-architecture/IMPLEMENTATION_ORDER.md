# Implementation Order

## Current Completed Foundation

1. Phase 1: Slide Blueprint Contract Foundation
2. Phase 1.5: Deck Blueprint Foundation
3. Phase 2A: Deck Planner Offline Engine
4. Phase 2B: Evidence Planner Foundation
5. Phase 2C: Message Designer Foundation
6. Phase 2D: Slide Intent Foundation
7. Alpha Integration Review

## Recommended Future Order

### Phase 3: Visual Director

Purpose: convert Slide Intent into a visual plan.

Dependency: Slide Intent Output.

### Phase 4: Blueprint Composer

Purpose: convert visual plan into renderer-ready editable Slide Blueprint.

Dependency: Visual Plan Contract.

### Phase 5: Renderer

Purpose: draw editable PowerPoint shapes from Slide Blueprint.

Dependency: Rendering Blueprint Contract.

### Phase 6: Version81 Integration

Purpose: connect Presentation Engine 2.0 behind feature flags.

Dependency: stable renderer and regression tests.

## Risk Control

Do not connect to the production proposal flow until each phase has:

- schema
- validator
- evaluator
- fixture
- golden output
- offline regression tests
- known limitation document
