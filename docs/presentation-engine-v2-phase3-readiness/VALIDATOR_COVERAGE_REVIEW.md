# Validator Coverage Review

## Existing Coverage

The current Visual Plan validator covers:

- Visual Strategy missing
- Slide Intent contradiction
- Diagram and Chart conflict
- Information Priority contradiction
- Reading Order contradiction
- Evidence unsupported chart or diagram
- Placeholder leakage
- Downstream generation boundary violation
- Duplicate slide reference
- Deck id mismatch
- Unstable slide order
- Overconfident plans with risk flags

## Coverage Status

| Area | Status |
|---|---|
| Minimum requested validators | PASS |
| Contract boundary validators | PASS |
| Evidence-driven chart safety | PASS |
| Cross-slide visual diversity | GAP |
| Audience visual fit | GAP |
| Decision stage visual fit | GAP |
| Table complexity | GAP |
| Unsupported visual claim | GAP |
| Internal label leakage beyond placeholders | GAP |

## Additional Validator Candidates

| ID | Priority | Candidate |
|---|---|---|
| VC-001 | P1 | Rule priority and fallback selected when no visual pattern default exists |
| VC-002 | P1 | Cross-slide duplicate visual pattern overuse |
| VC-003 | P1 | Phase4 required handoff fields present when strategy requires composition |
| VC-004 | P2 | Component count too high |
| VC-005 | P2 | Component count too low |
| VC-006 | P2 | Executive deck visual density too high |
| VC-007 | P2 | Technical deck visual abstraction too high |
| VC-008 | P2 | Chart type and evidence source mismatch |
| VC-009 | P2 | Diagram type and evidence relationship mismatch |
| VC-010 | P2 | Table column count too high |
| VC-011 | P2 | Slide role and visual strategy mismatch |
| VC-012 | P3 | Deck-level visual consistency weak |
| VC-013 | P3 | Image strategy selected without asset plan |
| VC-014 | P3 | Unsupported visual claim in renderer hint |
| VC-015 | P3 | Customer-facing wording naturalness |

## Recommendation

Do not modify validators before Phase 3 starts unless a blocker appears. Add the
P1 validators in the Visual Director Engine test suite.
