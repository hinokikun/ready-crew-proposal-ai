# Migration Plan

## Goal

Enable Strategy Engine integration without changing the default user experience.

## Phase 1: Keep Legacy Default

- Deploy Version 44 with `PRESENTATION_ENGINE_MODE=legacy`.
- Confirm existing PPTX, summary PPTX, PDF, and Beautiful.ai flows.
- Confirm logs show `engine_mode=legacy`.

## Phase 2: Internal Strategy Test

- Generate Strategy Brief from fixtures.
- Run Human Review.
- Approve the review report.
- Submit PPTX generation with `strategy_review_report`.
- Confirm Presentation Context is generated.
- Confirm PPTX generation succeeds.

## Phase 3: Limited Operator Toggle

Only after internal approval:

```text
PRESENTATION_ENGINE_MODE=strategy_v1
```

Use test users and non-customer data first.

## Verification

Required checks:

- Legacy mode does not call Strategy Adapter.
- Strategy mode rejects missing Review Report.
- Strategy mode rejects rejected and re-evaluate reports.
- Strategy mode generates Presentation Context from approved reports.
- PPTX generation succeeds in both modes.
- No customer input body is logged.

## Rollback

Set:

```text
PRESENTATION_ENGINE_MODE=legacy
```

Then redeploy or restart the backend.

No data rollback is needed.

## Future Work

Version 44 does not add a frontend review screen or persistence for Strategy Review Reports. A future version should connect the Human Review workflow to the application UI before enabling `strategy_v1` for general users.
