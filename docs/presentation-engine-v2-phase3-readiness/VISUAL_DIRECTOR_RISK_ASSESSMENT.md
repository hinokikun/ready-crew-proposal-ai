# Visual Director Risk Assessment

| risk_id | description | likelihood | impact | severity | affected_stage | mitigation | phase3_blocking | phase4_blocking |
|---|---|---|---|---|---|---|---|---|
| R-001 | Candidate ranking is underdefined. | Medium | High | High | Phase3 | Implement deterministic scoring and tie-breaks. | No | No |
| R-002 | Blueprint Composer may need more composition metadata. | High | High | High | Phase4 | Track Phase4 handoff gaps and add versioned extension later. | No | Yes |
| R-003 | Audience-specific visuals may be too generic. | Medium | Medium | Medium | Phase3 | Add audience-fit tests for executive and technical cases. | No | No |
| R-004 | Evidence gaps may still result in visually persuasive but unsupported plans. | Medium | High | High | Phase3 | Keep chart/diagram blockers and risk flags visible. | No | No |
| R-005 | Cross-slide visual rhythm may repeat. | Medium | Medium | Medium | Phase3 | Add diversity evaluator after first engine pass. | No | No |
| R-006 | Long Japanese messages may exceed assumed density. | Medium | Medium | Medium | Phase3 | Include long Japanese fixtures and density tests. | No | No |
| R-007 | Short decks may lack enough visual variety. | Medium | Low | Low | Phase3 | Add short-deck fixture coverage. | No | No |
| R-008 | Multi-audience decks may select a compromise visual that fits nobody. | Medium | Medium | Medium | Phase3 | Use primary audience as default and flag secondary audience tradeoffs. | No | No |
| R-009 | Diagram and chart responsibilities may leak into Visual Director. | Low | High | Medium | Phase3 | Keep boundary flags and test no coordinates/objects are generated. | No | No |
| R-010 | Version81 integration may need adapters. | Medium | Medium | Medium | Future | Keep Presentation Engine 2.0 offline until approved. | No | No |

## Maximum Risk

The largest risk is Phase4 handoff under-specification. It does not block Phase3,
but it can slow Blueprint Composer if left untreated.

## Risk Recommendation

Implement Phase3 in a way that produces auditable reasons and explicit fallback
visuals. Do not optimize for visual richness before correctness and traceability.
