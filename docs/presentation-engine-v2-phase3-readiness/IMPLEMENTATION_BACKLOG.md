# Implementation Backlog

| ID | Priority | Issue | Impact | Reproduction Condition | Target Contract | Root Cause Candidate | Recommended Action | Files To Change Candidate | Breaking Change | Estimate | Stop Phase3 | Affects Phase4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B-001 | P1 | Add rule priority order. | Avoid inconsistent decisions. | Multiple rules apply. | Visual Plan | Rules are maps, not ordered decision pipeline. | Add ordered selector flow. | `visual_director/selectors.py` | No | Medium | No | No |
| B-002 | P1 | Add candidate scoring. | Support explainable ranking. | Multiple visual options are valid. | Visual Plan | No scorer yet. | Add deterministic scorer. | `visual_director/scorers.py` | No | Medium | No | No |
| B-003 | P1 | Add fallback visual strategy. | Prevent blocked output for unknown patterns. | Unknown or weak Slide Intent. | Visual Plan | Fallback currently empty defaults. | Add safe message-first fallback. | `visual_director/rules.py` | No | Small | No | Yes |
| B-004 | P1 | Add Phase4 handoff metadata. | Reduce Blueprint Composer ambiguity. | Any handoff to Phase4. | Visual Plan | Composer needs more composition intent. | Add versioned extension after Phase3 MVP if required. | `visual_plan_contract/models.py` later | Possible | No | No | Yes |
| B-005 | P1 | Add golden tests for invalid examples. | Ensure schema/validator examples fail correctly. | Invalid example payloads. | Visual Plan | Examples are helper-only. | Add unit tests in Phase3. | `tests/presentation_engine_v2/visual_director/` | No | Small | No | No |
| B-006 | P2 | Add audience-fit scoring. | Better executive and technical visuals. | Audience-specific decks. | Input/Visual Plan | Audience not first-class in visual rules. | Add scoring dimension. | `visual_director/scorers.py` | No | Medium | No | No |
| B-007 | P2 | Add cross-slide diversity checks. | Avoid repeated visual patterns. | Decks with 8+ slides. | Visual Plan | Only item-level validation exists. | Add deck-level evaluator. | `visual_director/evaluator.py` | No | Medium | No | Yes |
| B-008 | P2 | Add table complexity validator. | Avoid dense tables. | Pricing/risk/evidence tables. | Visual Plan | Table only has max rows hint. | Add rows/columns scoring. | `visual_director/validators.py` | No | Small | No | Yes |
| B-009 | P2 | Add long Japanese fixture. | Validate real content density. | Japanese proposal messages. | All upstream | Unicode length and wrapping not visually tested. | Add fixture cases. | `fixtures/` | No | Small | No | No |
| B-010 | P3 | Add accessibility intent. | Future renderer quality. | Theme/renderer stages. | Future | Out of current scope. | Add in Phase4/Renderer. | Future | No | Medium | No | Yes |

## Backlog Summary

- P0: 0
- P1: 5
- P2: 4
- P3: 1 listed here, with more future hardening in Known Limitations
