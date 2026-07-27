# Visual Director Guide

## Purpose

Visual Director will be implemented after this contract foundation. Its job is
to transform Slide Intent and upstream contracts into a Visual Plan Contract.

## Inputs Used in Phase 3

- Proposal Context: business context and audience hints
- Deck Blueprint: deck goal, section order, slide order
- Evidence Planner Output: evidence availability and missing evidence warnings
- Message Designer Output: headline, main message, supporting messages, numeric claims
- Slide Intent Output: visual pattern, reading order, information priority

## Output Generated in Phase 3

- Visual Plan Contract

Visual Director must generate only the contract. It must not generate Blueprint
Composer output, Renderer output, PPTX, coordinates, themes, diagrams, or charts.

## Decision Scope

Visual Director may decide:

- visual strategy
- layout strategy
- emphasis strategy
- visual priority
- component candidates
- diagram/chart/image/table/callout/icon strategy
- visual risk flags
- confidence

Visual Director must not decide:

- new proposal claims
- new evidence
- PowerPoint coordinates
- font sizes
- colors
- actual chart data series
- actual diagram geometry
- PPTX files

## Minimum Phase 3 Tests

- every Slide Intent produces one Visual Plan item
- Visual Plan order matches Slide Intent order
- chart without numeric evidence is blocked
- placeholder leakage is blocked
- downstream generation boundary flags are blocked
- reading order and layout contradictions are detected
- comparison intent maps to comparison visual strategy
