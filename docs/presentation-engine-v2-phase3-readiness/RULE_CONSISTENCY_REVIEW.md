# Rule Consistency Review

## Reviewed Rule Area

Reviewed static rules in `visual_plan_contract/rules.py`.

## Current Strengths

- Slide Intent visual patterns map to Visual Strategy and Layout Strategy.
- Reading order compatibility is explicitly checked per layout.
- Chart strategies have numeric evidence requirements.
- Diagram and Chart conflicts are listed.
- Placeholder tokens are blocked by validator rules.
- Fallback helper exists for unknown visual patterns.

## Rule Conflict Count

| Type | Count | Notes |
|---|---:|---|
| Blocking rule conflict found | 0 | No direct contradiction blocks implementation. |
| Rule coverage gap | 7 | Several advanced decisions are not yet encoded. |
| Fallback exists | 1 | Unknown pattern returns empty defaults and should be handled by engine fallback. |

## Rule Gaps

| ID | Priority | Gap | Recommended Action |
|---|---|---|---|
| RG-001 | P1 | No explicit rule priority order. | Add rule resolution order in Visual Director implementation. |
| RG-002 | P1 | Multiple visual candidates are not ranked. | Add candidate scoring and deterministic tie-breaks. |
| RG-003 | P2 | Timeline rules do not require timeline evidence directly. | Add time-sequence validation in engine tests. |
| RG-004 | P2 | Comparison rules do not require comparison basis directly. | Add comparison basis validation against evidence/message. |
| RG-005 | P2 | Table rules do not evaluate column count or density. | Add table complexity validator. |
| RG-006 | P2 | Audience-specific visual rules are not encoded. | Add audience-fit scoring. |
| RG-007 | P3 | Deck-level visual repetition rules are absent. | Add cross-slide diversity evaluator later. |

## Recommendation

Start Phase 3 with rule-based selection plus scoring. Avoid external AI until
the deterministic rules and tie-breaks are stable.
