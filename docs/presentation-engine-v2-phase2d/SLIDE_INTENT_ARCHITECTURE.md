# Slide Intent Architecture

```mermaid
flowchart LR
  A["Proposal Context"] --> E["Slide Intent Engine"]
  B["Deck Blueprint"] --> E
  C["Evidence Planner Output"] --> E
  D["Message Designer Output"] --> E
  E --> F["Slide Intent Output"]
  F --> G["Validator"]
  F --> H["Evaluator"]
  F -. "future only" .-> I["Phase 3 Visual Director"]
```

## Responsibility

Slide Intent decides what the viewer should understand from each slide and what abstract visual direction can support that message.

## Boundary

The engine emits abstract candidates only. It does not decide coordinates, shape geometry, fonts, colors, theme tokens, diagrams, charts, or PowerPoint elements.
