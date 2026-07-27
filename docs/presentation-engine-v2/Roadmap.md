# Roadmap

Presentation Engine 2.0 should be implemented in 9 phases.

---

## Phase Overview

| Phase | Name | Purpose |
|---:|---|---|
| 1 | Contract and Blueprint | Define schema and validation |
| 2 | Slide Intent AI | Classify slide purpose |
| 3 | Message Designer AI | Design headline, message, evidence, cuts |
| 4 | Visual Director AI | Select best visual expression |
| 5 | Hierarchy and Typography | Design hierarchy, type, and gaze path |
| 6 | Diagram Composer | Generate editable diagram definitions |
| 7 | Theme Engine | Apply audience-aware themes |
| 8 | Renderer Integration | Connect blueprint to PPTX renderer |
| 9 | Quality Evaluation and Human Review | Validate output and review workflow |

---

## Phase 1: Contract and Blueprint

- Purpose: Define Blueprint JSON.
- Outcome: Schema, examples, validators.
- Risk: Overly broad schema.
- Test: Golden blueprint fixtures.
- Done: Renderer-independent schema accepted.

## Phase 2: Slide Intent AI

- Purpose: Identify slide goal.
- Outcome: Intent map.
- Risk: Keyword-only classification.
- Test: Intent fixture cases.
- Done: Each slide has one clear intent.

## Phase 3: Message Designer AI

- Purpose: Design message before layout.
- Outcome: Headline, main message, keep/cut/emphasize.
- Risk: Over-compression.
- Test: Human-readable message review.
- Done: Slide is understandable in 10 seconds.

## Phase 4: Visual Director AI

- Purpose: Choose expression form.
- Outcome: Visual plan.
- Risk: Overusing cards or KPI dashboards.
- Test: Visual type selection fixtures.
- Done: Visual supports the message.

## Phase 5: Hierarchy and Typography

- Purpose: Define visual hierarchy and type scale.
- Outcome: Hierarchy and typography tokens.
- Risk: Too rigid for varied slides.
- Test: Font floor and hierarchy validation.
- Done: Each slide has clear Level 1 element.

## Phase 6: Diagram Composer

- Purpose: Create editable diagram definitions.
- Outcome: Nodes, edges, matrices, dashboards.
- Risk: Complex diagrams become unreadable.
- Test: Diagram schema validation.
- Done: Diagram is editable and label-safe.

## Phase 7: Theme Engine

- Purpose: Apply design language.
- Outcome: Theme tokens.
- Risk: Theme overrides message clarity.
- Test: Theme fixture comparison.
- Done: Theme fits audience and strategy.

## Phase 8: Renderer Integration

- Purpose: Render Blueprint into PPTX.
- Outcome: Editable deck.
- Risk: Renderer reinterprets content.
- Test: Numeric, clipping, overlap, editable shape tests.
- Done: Renderer uses Blueprint only.

## Phase 9: Quality Evaluation and Human Review

- Purpose: Validate consulting-grade quality.
- Outcome: Quality report and review gates.
- Risk: Automated score misses visual judgment.
- Test: Human review rubric and regression deck set.
- Done: Release candidate deck passes human gate.

