# Proposal Strategy Engine

Version: 40.0
Status: Design only. No production implementation.
Product: ProposalPilot / AI営業秘書

## Purpose

ProposalPilot has design specifications for Premium Visual System, Presentation Pack, Category Pack, and Pack Selection Rules. Those assets define how a proposal should look.

Proposal Strategy Engine defines what the proposal should say, in what order, and for whom.

The engine runs before Presentation Engine:

```text
Project information
-> Proposal Strategy Engine
-> Presentation Pack selection
-> Presentation Engine
-> PPTX / PDF / Beautiful.ai prompt
```

## Scope

This directory contains design documents only. It does not change:

- backend
- frontend
- API
- database
- migrations
- Beautiful.ai
- existing proposal generation logic
- production PPTX generation logic
- V39 Presentation Pack artifacts

## Documents

| File | Purpose |
|---|---|
| `PROPOSAL_STRATEGY_ENGINE.md` | Five-layer strategy engine design. |
| `PERSONA_PACKS.md` | Persona-specific priorities, dislikes, decision points, and narrative order. |
| `STORY_PACKS.md` | Reusable eight-page story patterns. |
| `DECISION_RULES.md` | Rules for selecting strategy, story, persona, and presentation pack. |
| `ARCHITECTURE.md` | System boundaries, data contracts, and Presentation Engine connection. |
| `FLOW_DIAGRAMS.md` | Mermaid diagrams for the engine, layers, and decision flow. |

## Design Principle

Presentation Engine should not decide business strategy. It should receive a structured `Strategy Brief` and render it using the selected Presentation Pack.

Proposal Strategy Engine should not decide visual layout. It should decide:

- audience
- proposal objective
- priority message
- story pattern
- risk framing
- KPI framing
- next action
- prohibited terms

## Human Approval Gate

This design must be reviewed before implementation. Production integration should only start after humans approve:

- layer responsibility
- persona definitions
- story packs
- decision rules
- Presentation Engine contract
- category and persona fallback behavior
