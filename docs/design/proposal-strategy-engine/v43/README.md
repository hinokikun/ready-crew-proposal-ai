# Version 43 Strategy Brief Adapter

Status: Bridge Layer only. Production PPTX generation is unchanged.

Version 43 adds an adapter that converts an approved Strategy Brief review report into a Presentation Context.

## Boundary

Version 43 does not change:

- PPT generation logic
- frontend
- database
- migrations
- Beautiful.ai
- OpenAI
- existing Presentation Pack assets

## Rule

Presentation Engine should receive `PresentationContext`, not `StrategyBrief`.

Only these review states can create Presentation Context:

- `approved`
- `approved_with_changes`

These states cannot create Presentation Context:

- `rejected`
- `re_evaluate_required`

## Files

| File | Purpose |
|---|---|
| `ADAPTER_SPEC.md` | Adapter responsibility and behavior. |
| `PRESENTATION_CONTEXT.md` | Context schema and field descriptions. |
| `FLOW.md` | Human review to Presentation Context flow. |
