# System Pipeline

## Formal Pipeline

```mermaid
flowchart LR
  A["Proposal Context"] --> B["Deck Planner"]
  B --> C["Deck Blueprint"]
  C --> D["Evidence Planner"]
  D --> E["Evidence Planner Output"]
  E --> F["Message Designer"]
  F --> G["Message Designer Output"]
  G --> H["Slide Intent"]
  H --> I["Slide Intent Output"]
  I --> J["Visual Director - future"]
  J --> K["Visual Plan - future"]
  K --> L["Blueprint Composer - future"]
  L --> M["Slide Blueprint - future"]
  M --> N["Renderer - future"]
  N --> O["PowerPoint - future"]
```

## Module Inputs and Outputs

| Module | Input | Output | Responsibility |
|---|---|---|---|
| Proposal Context | user or fixture input | normalized business context | describe project and customer situation |
| Deck Planner | Proposal Context | Deck Blueprint | decide deck goal, audience, story arc, sections, slide order |
| Evidence Planner | Deck Blueprint, Proposal Context | Evidence Planner Output | decide evidence requirements and missing evidence warnings |
| Message Designer | Context, Deck, Evidence | Message Designer Output | write message fields and evidence disclosure |
| Slide Intent | Context, Deck, Evidence, Message | Slide Intent Output | decide abstract visual intent and reading direction |
| Visual Director | Slide Intent Output | Visual Plan | future module, decides visual expression |
| Blueprint Composer | Visual Plan | Slide Blueprint | future module, creates renderer-ready structure |
| Renderer | Slide Blueprint | PowerPoint | future module, draws only |

## Dependency Prohibition

- Deck Planner must not read Evidence Planner or Message Designer.
- Evidence Planner must not write message text.
- Message Designer must not decide layout, color, font, diagram, chart, or PowerPoint.
- Slide Intent must not generate Slide Blueprint, coordinates, theme, or diagram objects.
- Visual Director must not rewrite strategy or message.
- Blueprint Composer must not invent claims.
- Renderer must not rewrite proposal content.

## Alpha Integration Position

Alpha Integration is not a runtime engine. It is an offline review harness that verifies Deck Planner, Evidence Planner, and Message Designer consistency. It can inform readiness, but should not be inserted into the production rendering path.
