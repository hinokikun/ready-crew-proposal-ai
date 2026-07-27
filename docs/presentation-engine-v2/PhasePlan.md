# Phase Plan

This phase plan expands the roadmap into execution-ready checkpoints.

---

## Phase 1: Blueprint Contract

| Item | Detail |
|---|---|
| Purpose | Create the renderer-independent contract |
| Deliverables | JSON schema, examples, validation rules |
| Risks | Schema becomes too generic or too renderer-specific |
| Tests | Valid and invalid blueprint fixtures |
| Completion | Blueprint can describe 10 representative proposal slides |

## Phase 2: Slide Intent AI

| Item | Detail |
|---|---|
| Purpose | Decide each slide's communication job |
| Deliverables | Intent taxonomy, classifier contract, confidence rules |
| Risks | Intent becomes a renamed slide type |
| Tests | Problem, ROI, comparison, CTA, roadmap cases |
| Completion | One primary intent per slide or split recommendation |

## Phase 3: Message Designer AI

| Item | Detail |
|---|---|
| Purpose | Turn raw content into a clear message |
| Deliverables | Headline rewrite, keep/cut/emphasize, evidence model |
| Risks | Losing important nuance |
| Tests | Human readability, evidence preservation, no invented facts |
| Completion | Slide message is clear in 10 seconds |

## Phase 4: Visual Director AI

| Item | Detail |
|---|---|
| Purpose | Select visual expression |
| Deliverables | Visual type rules and examples |
| Risks | Overusing one visual type |
| Tests | Visual selection fixtures |
| Completion | Visual choice explains why it beats bullets |

## Phase 5: Hierarchy, Typography, White Space

| Item | Detail |
|---|---|
| Purpose | Make slides readable and persuasive |
| Deliverables | Hierarchy model, typography tokens, density rules |
| Risks | Rule conflicts with theme |
| Tests | Font floor, density, split recommendations |
| Completion | No slide needs tiny body text |

## Phase 6: Diagram Composer

| Item | Detail |
|---|---|
| Purpose | Design editable diagrams |
| Deliverables | Diagram schema, node/edge models, examples |
| Risks | Diagrams become too complex |
| Tests | Process, matrix, roadmap, KPI dashboard validation |
| Completion | Diagram definitions are renderer-safe |

## Phase 7: Theme Engine

| Item | Detail |
|---|---|
| Purpose | Match deck design to audience and proposal strategy |
| Deliverables | Theme tokens and selection rules |
| Risks | Decorative themes weaken clarity |
| Tests | Theme selection fixtures |
| Completion | Theme supports message and audience |

## Phase 8: Renderer Integration

| Item | Detail |
|---|---|
| Purpose | Render Blueprint into editable PPTX |
| Deliverables | Renderer adapter and fallback policy |
| Risks | Renderer changes message or numbers |
| Tests | PPTX openability, numeric integrity, overlap, clipping |
| Completion | Renderer accepts Blueprint without strategy inference |

## Phase 9: Human Review and Release Gate

| Item | Detail |
|---|---|
| Purpose | Ensure proposal-grade quality |
| Deliverables | Human rubric, quality report, acceptance criteria |
| Risks | Automated score hides visual issues |
| Tests | Human review of representative decks |
| Completion | Decks pass reviewer threshold before release |

