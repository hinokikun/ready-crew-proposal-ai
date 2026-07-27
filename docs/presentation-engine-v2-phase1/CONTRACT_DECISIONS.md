# Contract Decisions

## Blueprint version

Supported version:

```text
pe2_slide_blueprint_v1
```

## Required identity fields

- `blueprint_version`
- `blueprint_id`
- `slide_id`
- `slide_index`
- `slide_type`
- `status`

## Required content fields

- `slide_goal`
- `audience`
- `headline`
- `main_message`
- `visual_type`
- `primary_element`

## Renderer boundary

The renderer is not part of Phase 1. Future renderers must accept only validated blueprint JSON and must not infer message, diagram, theme, or layout strategy.

## Enum policy

Internal enum values use lowercase snake_case. Display labels are separate from internal values.

## Null policy

Empty strings may be normalized to `None` only for optional fields. Required text fields must remain non-empty.

