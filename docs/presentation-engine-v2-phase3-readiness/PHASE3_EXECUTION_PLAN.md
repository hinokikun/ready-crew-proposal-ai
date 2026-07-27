# Phase3 Execution Plan

## Recommended Implementation Style

Use option C first:

`candidate generation + ranking`

This gives the best balance between deterministic behavior, explainability,
fixture coverage, and future AI extensibility.

## Alternatives Compared

| Option | Strength | Weakness | Recommendation |
|---|---|---|---|
| A. Pure rule-based | Simple and deterministic. | Can be rigid and repetitive. | Good for baseline only. |
| B. Scoring rule-based | Explainable and testable. | May still miss creative alternatives. | Good foundation. |
| C. Candidate generation + ranking | Explainable and extensible. | More tests needed. | Recommended. |
| D. Future hybrid with AI | Flexible and expressive. | Harder to test and audit. | Later only. |

## Execution Steps

1. Add `visual_director/` module without connecting runtime.
2. Build contract adapter from upstream outputs.
3. Generate visual candidates per slide from Slide Intent.
4. Score candidates with deterministic dimensions.
5. Select one primary candidate and optional alternatives.
6. Normalize to Visual Plan Contract.
7. Run Visual Plan validators.
8. Add evaluator for sales-readiness and Phase4-readiness.
9. Add fixtures and golden outputs.
10. Extend Alpha Integration offline harness.
11. Document Phase4 handoff gaps.

## Stop Conditions

Stop Phase3 if:

- Visual Plan Contract cannot represent selected output.
- Slide Intent to Visual Plan mapping becomes ambiguous for core fixtures.
- Visual Director needs coordinates, theme, PPTX, or renderer knowledge.
- External AI becomes necessary for basic deterministic output.

## Completion Criteria

- All core fixture cases produce valid Visual Plan Contract.
- No P0 validator failures.
- Golden outputs are deterministic.
- Phase4 handoff review has no blocking gap.
