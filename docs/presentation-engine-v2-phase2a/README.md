# Presentation Engine 2.0 Phase 2A

## Deck Planner Offline Engine

Phase 2A adds an offline Deck Planner that converts Proposal Context into a Deck Blueprint.

This phase stops at deck-level planning. It does not create Slide Blueprints, PowerPoint files, diagrams, colors, coordinates, fonts, or body copy.

## Scope

- Input: Proposal Context
- Output: Deck Planner Result and Deck Blueprint
- Mode: deterministic offline rules
- Runtime connection: none

## Explicitly Not Connected

- Existing Proposal Generator
- PPTX generation
- Frontend
- Backend API
- Database
- Migration
- Presentation Designer
- Renderer
- Quality Engine
- Beautiful.ai

## Main Files

- `backend/app/presentation_engine_v2/deck_planner/planner.py`
- `backend/app/presentation_engine_v2/deck_planner/planner_models.py`
- `backend/app/presentation_engine_v2/deck_planner/planner_rules.py`
- `backend/app/presentation_engine_v2/deck_planner/planner_evaluator.py`
- `backend/tests/presentation_engine_v2/deck_planner/test_deck_planner_offline_engine.py`

