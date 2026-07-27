# Input Readiness Review

## Visual Director Input

Visual Director Input is defined as:

- Proposal Context
- Deck Blueprint
- Evidence Planner Output
- Message Designer Output
- Slide Intent Output

## Readiness Checklist

| Check | Status | Notes |
|---|---|---|
| Required information exists | PASS | Business, deck, evidence, message, and intent contracts are available. |
| Source of truth is clear | PASS | Each data domain has one upstream owner. |
| Duplicate data is manageable | PASS | Some overlap exists, but ownership is documented. |
| Slide ID references are consistent | PASS | `slide_blueprint_id` is carried across modules. |
| Section ID references are consistent | PASS | Deck and evidence contracts preserve section references. |
| Evidence ID references are consistent | PASS | Evidence ids are used by Message Designer and Visual Plan. |
| Message ID references are consistent | PASS | Slide Intent references Message Designer output. |
| Version management is possible | PASS | Version strings exist in each contract layer. |
| Input fingerprint can be created | PASS | Existing modules expose fingerprints or source fields; Visual Plan has `input_fingerprint`. |
| Missing data behavior is defined | PARTIAL | Evidence gaps are represented; visual fallback rules need Phase3 implementation. |
| Slide-level and deck-level data are separated | PASS | Deck Blueprint and slide-level outputs are distinct. |

## Findings

Visual Director has enough input to make deterministic visual decisions. The
main limitation is not input availability, but how the future engine should
rank alternatives when multiple visuals are valid.

## Recommendation

Use Slide Intent Output as the immediate input anchor. Do not let Visual Director
read raw Proposal Context first and bypass upstream contracts.
