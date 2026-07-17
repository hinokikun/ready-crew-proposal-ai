# Engine Sequence

## Legacy Mode

```mermaid
sequenceDiagram
    participant User
    participant API as PPTX API
    participant Legacy as Legacy PPTX Generator

    User->>API: Download PPTX request
    API->>Legacy: Build PPTX from existing payload
    Legacy-->>API: PPTX bytes
    API-->>User: PPTX download
```

Legacy mode does not call Strategy Engine, Human Review, Strategy Adapter, or Presentation Context generation.

## Strategy v1 Mode

```mermaid
sequenceDiagram
    participant User
    participant Strategy as Strategy Engine
    participant Review as Human Review
    participant Adapter as Strategy Brief Adapter
    participant API as PPTX API
    participant Presentation as Presentation Engine

    User->>Strategy: Proposal input
    Strategy-->>Review: Strategy Brief
    Review-->>API: Approved Review Report
    API->>Adapter: Convert approved report
    Adapter-->>API: Presentation Context
    API->>Presentation: Existing PPTX payload + Presentation Context
    Presentation-->>API: PPTX bytes
    API-->>User: PPTX download
```

Presentation Engine receives only Presentation Context. It must not receive Strategy Brief directly.

## Logging

The bridge logs:

- Engine Mode
- Strategy Version
- Presentation Context Version
- Presentation Pack
- Story
- Persona

It does not log full customer input, prompt text, API keys, or authorization tokens.
