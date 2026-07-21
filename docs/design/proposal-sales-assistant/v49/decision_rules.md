# Decision Rules

Version49 does not create a new category or proposal analysis engine. It only reads Strategy Brief decisions.

## Reused Strategy Brief fields

- `project_category`
- `primary_persona`
- `decision_maker`
- `primary_strategy`
- `story_type`
- `primary_pack`
- `kpi_pack`
- `estimate_pack`
- `confidence`
- `evidence_summary`
- `allowed_terms`
- `conditional_terms`
- `prohibited_terms`
- `human_review_required`

## Human review propagation

Human review is required when:

- the source Strategy Brief requires review;
- confidence is below the review threshold;
- budget, schedule, evidence, client, or summary information is missing;
- source input contains terms prohibited by the selected strategy scope.

