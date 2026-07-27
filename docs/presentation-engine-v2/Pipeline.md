# Pipeline

Presentation Engine 2.0 introduces a message-first pipeline.

---

## Full Flow

```mermaid
sequenceDiagram
  participant User as User
  participant Strategy as Sales Strategy AI
  participant Story as Story Engine
  participant Intent as Slide Intent AI
  participant Message as Message Designer AI
  participant Visual as Visual Director AI
  participant Hierarchy as Hierarchy Engine
  participant Theme as Theme Engine
  participant Blueprint as Rendering Blueprint
  participant Renderer as PowerPoint Renderer

  User->>Strategy: Project brief
  Strategy->>Story: Sales Strategy Brief
  Story->>Intent: Story outline
  Intent->>Message: Slide goals
  Message->>Visual: Main message and evidence
  Visual->>Hierarchy: Visual type and content density
  Hierarchy->>Theme: Hierarchy plan
  Theme->>Blueprint: Theme tokens
  Blueprint->>Renderer: Rendering Blueprint JSON
  Renderer-->>User: Editable PPTX
```

---

## Step Details

| Step | Input | Output | Key Decision |
|---|---|---|---|
| Sales Strategy AI | Project brief | Sales Strategy Brief | Who to persuade and why |
| Story Engine | Strategy Brief | Story Outline | Proposal sequence |
| Slide Intent AI | Story Outline | Slide Intent Map | Purpose of each slide |
| Message Designer AI | Intent Map | Message Plan | What to say, cut, emphasize |
| Visual Director AI | Message Plan | Visual Plan | Best visual form |
| Hierarchy Engine | Visual Plan | Hierarchy Plan | What the eye sees first |
| Theme Engine | Strategy, Audience, Hierarchy | Theme Tokens | Design language |
| Rendering Blueprint | All plans | Blueprint JSON | Renderer contract |
| PowerPoint Renderer | Blueprint JSON | PPTX | Editable rendering |

---

## Failure Handling

| Failure | Behavior |
|---|---|
| Missing evidence | Mark as confirmation item |
| Too much content | White Space Optimizer splits or compresses |
| No clear visual | Use message-first minimal layout |
| Unsupported diagram | Use safe editable fallback |
| Risk of numeric change | Stop and require review |
| Low confidence | Human review required |

---

## Human Review Gate

Human review should happen before rendering when:

- Main message is inferred from weak evidence.
- ROI, schedule, price, or success rate is not provided.
- Diagram contains assumptions.
- Slide has legal, financial, security, or executive approval implications.
- Confidence is below the configured threshold.

