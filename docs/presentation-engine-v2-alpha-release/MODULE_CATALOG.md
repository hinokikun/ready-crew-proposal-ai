# Module Catalog

## Implemented Alpha Modules

| Module | Path | Status | Responsibility | Runtime Connected |
|---|---|---|---|---|
| Slide Blueprint Foundation | `backend/app/presentation_engine_v2/` | Implemented | Single-slide typed blueprint contract, normalizer, validator, evaluator, schema, fixtures, golden data. | No |
| Deck Blueprint Foundation | `backend/app/presentation_engine_v2/deck_*` | Implemented | Deck-level purpose, audience, story arc, sections, slide order, CTA, validation. | No |
| Deck Planner | `backend/app/presentation_engine_v2/deck_planner/` | Implemented | Converts Proposal Context into Deck Blueprint offline. | No |
| Evidence Planner | `backend/app/presentation_engine_v2/evidence_planner/` | Implemented | Defines required and optional evidence per slide. | No |
| Message Designer | `backend/app/presentation_engine_v2/message_designer/` | Implemented | Creates headline, main message, support points, evidence usage, and disclosures offline. | No |
| Slide Intent | `backend/app/presentation_engine_v2/slide_intent/` | Implemented | Converts messages into abstract slide intent, visual pattern, reading order, and candidate visual type. | No |
| Alpha Integration | `backend/app/presentation_engine_v2/alpha_integration/` | Implemented | Offline cross-module validation, evaluation, and reporting. | No |
| Visual Plan Contract | `backend/app/presentation_engine_v2/visual_plan_contract/` | Contract only | Defines Phase 3 Visual Plan input/output models, enums, schema, rules, and validators. | No |

## Supporting Test Modules

| Test Area | Path |
|---|---|
| Slide Blueprint Foundation | `backend/tests/presentation_engine_v2/test_contract_foundation.py` |
| Deck Blueprint Foundation | `backend/tests/presentation_engine_v2/deck/test_deck_blueprint_foundation.py` |
| Deck Planner | `backend/tests/presentation_engine_v2/deck_planner/test_deck_planner_offline_engine.py` |
| Evidence Planner | `backend/tests/presentation_engine_v2/evidence_planner/test_evidence_planner_foundation.py` |
| Message Designer | `backend/tests/presentation_engine_v2/message_designer/test_message_designer_foundation.py` |
| Slide Intent | `backend/tests/presentation_engine_v2/slide_intent/test_slide_intent_foundation.py` |
| Alpha Integration | `backend/tests/presentation_engine_v2/alpha_integration/test_alpha_integration_review.py` |

## Not Implemented as Modules

- Visual Director Engine
- Blueprint Composer
- Renderer
- Runtime adapter to Version81
- API layer
- Frontend UI
