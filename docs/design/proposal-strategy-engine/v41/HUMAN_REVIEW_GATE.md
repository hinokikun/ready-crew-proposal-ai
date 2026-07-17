# Human Review Gate

Status: specification and offline evaluator behavior.

## Review Required Conditions

`human_review_required` becomes true when:

- confidence is below threshold
- Generic fallback is selected
- persona is unknown
- category conflict is detected
- budget exists but budget type is unclear
- input is sparse
- prohibited or conflicting category terms appear in the source

## Review Reasons

Reasons are stored in `human_review_reasons`.

Examples:

- `confidence below review threshold`
- `generic fallback selected`
- `persona unknown`
- `category conflict detected`
- `budget exists but budget_type is unclear`
- `input information is sparse`

## Production Rule for Future Versions

If this evaluator is integrated later, human review state should be visible before final PPTX generation.
