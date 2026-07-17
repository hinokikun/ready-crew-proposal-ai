# Version 44 Presentation Engine Integration

Status: feature-flagged bridge. Legacy Engine remains the default.

Version 44 connects an approved Strategy Brief Review Report to the existing PPTX generation entry point through Presentation Context.

## What Changed

- Added `PRESENTATION_ENGINE_MODE`.
- Added a small integration layer between approved review reports and PPTX generation.
- Allowed PPTX generation to receive `PresentationContext` as an optional input.
- Preserved legacy behavior when the feature flag is unset.

## What Did Not Change

- No frontend change.
- No database or migration change.
- No Beautiful.ai change.
- No OpenAI change.
- No default behavior change for existing users.
- No replacement of the existing PPTX generator.

## Default

```text
PRESENTATION_ENGINE_MODE=legacy
```

If the variable is missing or invalid, the system falls back to `legacy`.

## Strategy Mode Boundary

`strategy_v1` requires an approved human review report before Presentation Context can be generated.

Rejected or re-evaluation reports are blocked.

## Files

| File | Purpose |
|---|---|
| `FEATURE_FLAG.md` | Engine mode configuration and rollout rules. |
| `ENGINE_SEQUENCE.md` | Legacy and strategy sequence diagrams. |
| `INTEGRATION_GUIDE.md` | Integration boundary and developer notes. |
| `MIGRATION_PLAN.md` | Safe rollout, rollback, and verification plan. |
