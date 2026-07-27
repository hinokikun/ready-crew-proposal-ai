# Pipeline Architecture

## Flow

1. Read `AlphaIntegrationCase`.
2. Run Phase 2A Deck Planner.
3. Validate Deck Blueprint.
4. Run Phase 2B Evidence Planner.
5. Validate Evidence Planner Output.
6. Run Phase 2C Message Designer.
7. Validate Message Designer Output.
8. Run cross-module validation.
9. Evaluate the full pipeline.
10. Generate human-readable review summary.

## Design Principle

Alpha Integration uses existing offline modules as black-box dependencies. It does not rewrite their planning rules or alter their contracts.

