# Contract Catalog

## Core Contracts

| Contract | Owner | Purpose |
|---|---|---|
| `SlideBlueprint` | Slide Blueprint Foundation | Represents one slide contract without rendering PowerPoint. |
| `DeckBlueprint` | Deck Blueprint Foundation | Represents deck goal, audience, section order, slide plan, story arc, and CTA. |
| `ProposalContext` | Deck Planner | Input business context for offline planning. |
| `DeckPlannerResult` | Deck Planner | Deck Planner output containing context, deck blueprint, decisions, recommendations, warnings, and evaluation. |
| `EvidencePlanningInput` | Evidence Planner | Input pairing Deck Blueprint and Proposal Context. |
| `EvidencePlannerResult` | Evidence Planner | Evidence requirements, missing evidence warnings, and evidence evaluation per slide. |
| `MessageDesignerInput` | Message Designer | Input combining Proposal Context, Deck Blueprint, and Evidence Planner output. |
| `MessageDesignerOutput` | Message Designer | Slide message designs, evidence usage, unsupported claims, missing evidence disclosures, and evaluation. |
| `SlideIntentInput` | Slide Intent | Input combining Proposal Context, Deck Blueprint, Evidence, and Message outputs. |
| `SlideIntentOutput` | Slide Intent | Slide-level intent, visual pattern candidate, diagram/chart candidate, reading order, and density. |
| `VisualDirectorInput` | Visual Plan Contract | Future Phase 3 input contract for Visual Director. |
| `VisualPlanContract` | Visual Plan Contract | Future Phase 3 output contract for visual strategy and component candidates. |

## Alpha Integration Contracts

| Contract | Purpose |
|---|---|
| `integration-case-input.schema.json` | Defines one offline integration review case input. |
| `integration-case-output.schema.json` | Defines one integration review output. |
| `integration-evaluation.schema.json` | Defines integration scoring output. |
| `cross-module-validation.schema.json` | Defines cross-module validation result. |
| `phase2d-readiness.schema.json` | Defines Phase 2D readiness result. |

## Schema Artifacts

| Directory | Artifacts |
|---|---|
| `docs/presentation-engine-v2-contracts/` | Slide Blueprint schema, example, invalid examples. |
| `docs/presentation-engine-v2-deck-contracts/` | Deck Blueprint schema, example, invalid examples, slide reference contract. |
| `docs/presentation-engine-v2-phase2a/` | Proposal Context schema and Deck Planner result schema. |
| `docs/presentation-engine-v2-phase2b/` | Evidence Planner input and result schemas. |
| `docs/presentation-engine-v2-message-contracts/` | Message Designer input/output and slide message schemas. |
| `docs/presentation-engine-v2-phase2d/contracts/` | Slide Intent input/output schemas, example, invalid example. |
| `docs/presentation-engine-v2-alpha-integration/contracts/` | Alpha Integration schema set. |

## Contract Rule

Alpha contracts are versioned and should be treated as append-only unless a new
versioned adapter is introduced.
