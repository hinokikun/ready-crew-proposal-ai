# Visual Plan Contract

## Purpose

The Visual Plan Contract is the formal handoff from Slide Intent to future
Blueprint Composer. It tells downstream modules how a slide should be visually
handled without drawing it.

## Input

Visual Director Input contains:

- Proposal Context
- Deck Blueprint
- Evidence Planner Output
- Message Designer Output
- Slide Intent Output

## Output

Visual Plan Contract contains:

- `visual_plan`
- `visual_strategy`
- `layout_strategy`
- `emphasis_strategy`
- `visual_priority`
- `component_candidates`
- `diagram_strategy`
- `chart_strategy`
- `image_strategy`
- `table_strategy`
- `callout_strategy`
- `icon_strategy`
- `risk_flags`
- `confidence`

## Slide-Level Item

Each slide has one `VisualPlanItem`.

Required slide-level fields include:

- `visual_plan_id`
- `deck_id`
- `slide_blueprint_id`
- `source_intent_id`
- `slide_order`
- visual strategy fields
- component candidates
- strategy plans
- source intent metadata
- evidence references
- boundary flags

## Not Included

The contract must not include:

- coordinates
- font sizes
- color tokens
- shape IDs
- generated diagrams
- generated charts
- PPTX paths
- runtime connections

These belong to later phases.
