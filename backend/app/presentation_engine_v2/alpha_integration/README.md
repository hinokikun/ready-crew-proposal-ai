# Alpha Integration Review

Offline integration runner for Presentation Engine 2.0.

## Pipeline

`Proposal Context -> Deck Planner -> Evidence Planner -> Message Designer -> Cross-module Validation -> Evaluation -> Human Review Markdown`

## Scope

This package is review-only. It does not connect to existing Proposal generation, Version81 runtime, PPTX rendering, APIs, DB, Frontend, OpenAI, or Beautiful.ai.

## Public Helpers

- `run_alpha_integration(case)`
- `run_alpha_integration_from_payload(payload)`
- `run_alpha_integration_markdown(case)`
- `valid_alpha_integration_cases()`
- `golden_alpha_integration_outputs()`
