# Contract Gap Analysis

## Source of Truth

| Data | Source of Truth |
|---|---|
| Business context | Proposal Context |
| Deck goal, section order, slide order | Deck Blueprint |
| Evidence availability and gaps | Evidence Planner Output |
| Headline and message content | Message Designer Output |
| Visual pattern, reading order, information priority | Slide Intent Output |
| Visual strategy for downstream composition | Visual Plan Contract |

## Contract Gaps

| ID | Priority | Gap | Impact | Recommended Action | Blocking |
|---|---|---|---|---|---|
| CG-001 | P1 | Visual Plan has no formal `preferred_composition` field. | Blueprint Composer may infer composition inconsistently. | Add in Phase 3 or Phase 4 contract extension if needed. | No |
| CG-002 | P1 | Deck-level visual consistency is represented lightly. | Cross-slide visual rhythm may be weak. | Add deck-level diversity and consistency metadata in Visual Director output. | No |
| CG-003 | P1 | Audience-specific visual adaptation is not explicit. | Executive and technical decks may look too similar. | Add audience-fit scoring in Visual Director implementation. | No |
| CG-004 | P1 | Fallback visual is not explicit per slide. | Phase 4 may not know what to do when evidence is missing. | Add fallback strategy during Phase 3 implementation. | No |
| CG-005 | P1 | Phase4 handoff fields are not fully enumerated in the contract. | Blueprint Composer may need additional metadata. | Treat as Phase4 handoff backlog, not a contract blocker. | No |
| CG-006 | P2 | Component count range is implicit. | Renderer load and slide density may drift. | Add max/min component rules in Visual Director. | No |
| CG-007 | P2 | Table complexity is lightly modeled. | Dense estimate/risk tables may be hard to compose. | Add table complexity validator. | No |
| CG-008 | P2 | Image crop intent is not modeled. | Future image placeholders may be too vague. | Keep out of Phase 3 unless image-heavy layouts are required. | No |
| CG-009 | P2 | Accessibility intent is absent. | Color and reading accessibility must be added later. | Add as Phase4/Renderer quality rule. | No |

## P0 Result

No P0 contract blocker was found.

## Recommendation

Do not change existing contracts before Phase 3. Implement Visual Director using
the current contract and record Phase4 handoff gaps as versioned extensions.
