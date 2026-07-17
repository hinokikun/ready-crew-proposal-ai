# Feature Flag

## Environment Variable

```text
PRESENTATION_ENGINE_MODE=legacy
```

Supported values:

| Value | Behavior |
|---|---|
| `legacy` | Existing PPTX generation path. Strategy Engine is not called. |
| `strategy_v1` | Requires approved Strategy Brief Review Report, converts it to Presentation Context, then calls PPTX generation. |

## Default Behavior

Default is `legacy`.

Invalid values are treated as `legacy`.

## Why Legacy Is Default

The production app already has an accepted proposal generation flow. Version 44 is a controlled bridge, not a forced migration.

Existing users must not see behavior changes unless an operator explicitly enables `strategy_v1` and provides approved review data.

## Strategy Mode Preconditions

`strategy_v1` can run only when:

- Strategy Brief exists.
- Human Review status is `approved` or `approved_with_changes`.
- Review Report is passed to the PPTX request.
- Presentation Context can be generated.

If the approved review report is missing, generation is blocked instead of silently bypassing review.

## Safe Rollback

Set:

```text
PRESENTATION_ENGINE_MODE=legacy
```

No database rollback is required because Version 44 adds no schema changes.
