# Visual Plan Contract Foundation

This package defines the Phase 3 preparation contract for Presentation Engine 2.0.

It does not implement Visual Director, Blueprint Composer, Renderer, Theme Engine,
PowerPoint generation, API endpoints, database storage, OpenAI calls, or
Beautiful.ai integration.

## Inputs

- Proposal Context
- Deck Blueprint
- Evidence Planner Output
- Message Designer Output
- Slide Intent Output

## Output

- Visual Plan Contract

The contract contains slide-level visual strategy, layout strategy, emphasis
strategy, visual priority, component candidates, diagram/chart/image/table/
callout/icon strategies, risk flags, and confidence.

## Boundary

The contract must stay renderer-agnostic. It must not contain coordinates, font
sizes, colors, theme tokens, generated diagrams, generated charts, or PPTX
artifacts.

## Validation

Validators check:

- missing Visual Strategy
- contradiction with Slide Intent
- Diagram and Chart conflicts
- information priority contradictions
- reading order contradictions
- unsupported evidence-driven visuals
- placeholder leakage
- downstream generation boundary violations
