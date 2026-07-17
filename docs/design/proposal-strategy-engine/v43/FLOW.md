# Version 43 Flow

Status: Bridge Layer flow only.

## Flow

```mermaid
flowchart LR
  A["案件入力"] --> B["Strategy Engine"]
  B --> C["Strategy Brief"]
  C --> D["Human Review"]
  D --> E{"Review Result"}
  E -->|"approved"| F["Strategy Brief Adapter"]
  E -->|"approved_with_changes"| F
  E -->|"rejected"| G["Stop"]
  E -->|"re_evaluate_required"| H["Re-evaluate"]
  F --> I["Presentation Context"]
  I -. "Version 43 does not connect" .-> J["Presentation Engine"]
```

## Version 43 Stop Point

Version 43 stops after Presentation Context generation.

It does not call Presentation Engine or PPTX generation.

## Version 44 Candidate

Future integration may allow:

```text
Approved Presentation Context
-> Presentation Engine input
-> PPTX generation
```

Only after human approval and regression testing.
