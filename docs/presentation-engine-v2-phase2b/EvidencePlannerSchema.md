# Evidence Planner Schema

## Schemas

- `evidence-planning-input.schema.json`
- `evidence-planner-result.schema.json`

## Input Contract

The input contains:

- `deck_blueprint`
- `proposal_context`

## Result Contract

The result contains:

- `deck_id`
- `deck_blueprint_version`
- `slide_evidence`
- `evaluation_result`
- `warnings`
- generation boundary flags

## Boundary Flags

The following must remain `false` in Phase 2B:

- `generated_headlines`
- `generated_main_messages`
- `generated_body_text`
- `generated_slide_blueprints`
- `connected_to_runtime`

