# Rule Evaluator

Status: deterministic offline evaluator.

## Evaluation Order

1. Normalize input.
2. Extract category signals.
3. Decide primary and secondary category.
4. Decide persona.
5. Decide strategy.
6. Decide story.
7. Decide presentation pack.
8. Decide KPI pack.
9. Decide estimate pack.
10. Apply term guard.
11. Calculate confidence.
12. Apply human review gate.
13. Produce Strategy Brief.

## Category Evaluation

The evaluator uses rule-based keyword signals based on Version 39.3 Pack Selection Rules.

Single weak keywords should not produce high confidence. Sparse input falls back to Generic Consulting and requires human review.

## Persona Evaluation

Explicit `audience_hint` has priority.

If no hint is provided, the evaluator infers persona from stakeholder and problem terms. If confidence is weak, `unknown` is allowed.

## Strategy Evaluation

Strategy is selected from category, persona, and problem signals.

Examples:

- OCR and inspection -> quality improvement
- RPA and repetitive work -> operational improvement
- Web and customer journey -> customer experience
- executive and investment terms -> ROI

## Output Traceability

`selection_reasons` must explain why a category, persona, strategy, and pack were selected.
