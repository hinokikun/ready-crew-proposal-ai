# Boundary Guide

## Main Rule

Each module must decide only one layer of the proposal.

## Boundaries

| Module | Boundary |
|---|---|
| Deck Planner | does not decide visual design |
| Evidence Planner | does not write proposal message |
| Message Designer | does not decide layout |
| Slide Intent | does not decide coordinates, fonts, colors, theme, or final diagrams |
| Visual Director | must not generate PowerPoint |
| Blueprint Composer | must not decide sales strategy |
| Renderer | must not rewrite content |

## Examples

Deck Planner may say: "The deck needs a competitor comparison slide."

Evidence Planner may say: "This slide requires competitor comparison evidence."

Message Designer may say: "We should compare value and implementation risk, not only price."

Slide Intent may say: "This should be seen as a comparison with left-to-right reading order."

Visual Director may say: "Use a two-axis comparison matrix."

Blueprint Composer may say: "Create four editable cards and a two-axis grid."

Renderer may say: "Draw these shapes at these positions."

## Blocker Conditions

Stop implementation and review architecture if:

- a module needs to read a downstream output
- renderer needs to invent content
- Slide Intent needs coordinates
- Message Designer needs theme or layout
- evidence gaps are hidden
- fake numbers are introduced
