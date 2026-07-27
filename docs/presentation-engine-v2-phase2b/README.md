# Presentation Engine 2.0 Phase 2B

## Evidence Planner Foundation

Phase 2B adds an offline Evidence Planner. It receives a Deck Blueprint and Proposal Context, then creates evidence requirements for each planned slide.

## Scope

- Input: Deck Blueprint and Proposal Context
- Output: Evidence Planner Result
- Mode: deterministic offline rules
- Runtime connection: none

## Explicitly Out of Scope

- Headline generation
- Main message generation
- Body text generation
- Slide Blueprint generation
- PPTX generation
- Renderer connection
- Existing Proposal Generator connection
- Frontend changes
- Backend API routes
- Database changes
- Migration

## Primary Module

`backend/app/presentation_engine_v2/evidence_planner/`

