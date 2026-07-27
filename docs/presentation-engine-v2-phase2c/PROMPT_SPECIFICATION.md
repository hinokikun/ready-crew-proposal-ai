# Prompt Specification

Phase 2C does not call an LLM. This file records the future prompt boundary.

## System Prompt Summary

The model must generate only message fields and evidence alignment metadata. It must not generate Slide Blueprint, diagram, layout, theme, typography, chart, image, coordinates, PPTX, API, or DB output.

## Developer Prompt Summary

Use Proposal Context, Deck Blueprint, and Evidence Planner output. Any numeric, ROI, ratio, currency, or period claim must be backed by explicit evidence IDs. If evidence is missing, disclose it and lower confidence.

## Temperature

`0`

## Failure Recovery

- Retry invalid fields only.
- Drop forbidden output keys.
- Remove unsupported numeric claims.
- Add missing evidence disclosure when evidence is missing.

