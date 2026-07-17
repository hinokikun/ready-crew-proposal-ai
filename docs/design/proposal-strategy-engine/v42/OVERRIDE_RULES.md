# Override Rules

Status: aligned with offline review utility.

## Changeable Fields

Sales users may change:

- `primary_persona`
- `secondary_personas`
- `decision_maker`
- `story_type`
- `hero_theme`
- `main_message`
- `priority_messages`
- `risk_messages`
- `next_actions`
- `required_slide_types`
- `optional_slide_types`

## Locked Fields

Sales users may not change:

- `schema_version`
- `project_category`
- `secondary_category`
- `primary_pack`
- `secondary_pack`
- `confidence`
- `selection_reasons`
- `assumptions`
- `missing_information`
- `evidence_summary`
- `allowed_terms`
- `conditional_terms`
- `prohibited_terms`

## Reasoning

Editable fields represent presentation direction and human judgment.

Locked fields represent engine evidence, traceability, category guardrails, and schema integrity.

## Rejected Override Behavior

If a locked field is included in overrides, the review report records it under `rejected_overrides`.

The original value remains unchanged.
