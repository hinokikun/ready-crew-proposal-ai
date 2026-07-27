# Planner Architecture

## Purpose

The Deck Planner decides what kind of proposal deck should be created before any slide-level design starts.

## Pipeline

```mermaid
flowchart TD
    A["Proposal Context"] --> B["Context Normalization"]
    B --> C["Category Rule"]
    C --> D["Audience Rule"]
    D --> E["Decision Stage Rule"]
    E --> F["Story Arc Rule"]
    F --> G["Deck Length Rule"]
    G --> H["Section Rule"]
    H --> I["Slide Plan Skeleton"]
    I --> J["Deck Blueprint"]
    J --> K["Offline Planner Evaluation"]
```

## Boundary

The planner creates section and slide-plan skeletons only. Slide Blueprint generation is reserved for later phases.

## Determinism

The same Proposal Context produces the same deck ID, section order, slide order, and golden output.

