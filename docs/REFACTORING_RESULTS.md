# Version 22.1 Refactoring Results

Date: 2026-07-14

## Scope

Version 22.1 was a decomposition and regression-lock sprint. It did not add sales features, AI agents, backend APIs, database tables, migrations, screens, role behavior, workspace behavior, Beautiful.ai behavior, or output contract changes.

## File Size Changes

| Area | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| `frontend/components/AppShell.tsx` | 7,441 | 5,101 | 2,340 |
| `backend/app/repositories.py` | 1,832 | 4 | 1,828 |
| `backend/app/services/pptx_service.py` | 2,184 | 1,088 | 1,096 |

Total reduction in the three target files: 5,264 lines.

## New Internal Structure

```text
frontend/components/app-shell/
  logic.ts
  logic-parts/
    estimates.ts
    hearing.ts
    intake.ts
    outputs.ts
    strategy.ts
    workflow.ts

backend/app/repository_parts/
  analytics.py
  crm.py
  operations.py
  shared.py
  users.py

backend/app/services/pptx_parts/
  content.py
  drawing.py
  models.py
```

## Compatibility Facades

- `backend/app/repositories.py` remains as the import-compatible facade and re-exports repository functions from `repository_parts`.
- `frontend/components/app-shell/logic.ts` remains as the import-compatible facade for AppShell helper logic.
- `backend/app/services/pptx_service.py` remains the public PPTX service entry point. PPTX helper modules are internal only.

## New File Line Counts

| File | Lines |
| --- | ---: |
| `frontend/components/app-shell/logic-parts/estimates.ts` | 297 |
| `frontend/components/app-shell/logic-parts/hearing.ts` | 272 |
| `frontend/components/app-shell/logic-parts/intake.ts` | 383 |
| `frontend/components/app-shell/logic-parts/outputs.ts` | 402 |
| `frontend/components/app-shell/logic-parts/strategy.ts` | 444 |
| `frontend/components/app-shell/logic-parts/workflow.ts` | 296 |
| `backend/app/repository_parts/analytics.py` | 553 |
| `backend/app/repository_parts/crm.py` | 226 |
| `backend/app/repository_parts/operations.py` | 452 |
| `backend/app/repository_parts/shared.py` | 97 |
| `backend/app/repository_parts/users.py` | 394 |
| `backend/app/services/pptx_parts/content.py` | 593 |
| `backend/app/services/pptx_parts/drawing.py` | 236 |
| `backend/app/services/pptx_parts/models.py` | 42 |

All newly added decomposition files are below 800 lines.

## Regression Results

| Check | Result |
| --- | --- |
| `npm.cmd run typecheck` | Passed |
| `npm.cmd run check:unused` | Passed |
| `npm.cmd run build` | Passed |
| `npm.cmd run test:e2e` | Passed, 29 tests |
| `python -m compileall app tests` | Passed |
| `pytest -q` | Passed, 139 tests |
| `pip check` | Passed |

## Build Comparison

| Metric | Baseline | After |
| --- | ---: | ---: |
| Next.js compile time | 5.4s | 4.1s |
| Route `/` size | 3.22 kB | 3.22 kB |
| First Load JS | 106 kB | 106 kB |
| Shared JS | 103 kB | 103 kB |

## Route And Serverless Check

| Item | Count |
| --- | ---: |
| Frontend App Router route handlers | 0 |
| Assumed Vercel Serverless Functions from frontend route handlers | 0 |
| Backend router modules | 22 |

## PPTX Regression Note

Normal PPTX and summary PPTX endpoint tests passed after the split. The checks confirm successful generation and PowerPoint MIME response. A binary diff against a pre-refactor artifact was not possible because no pre-refactor artifact was preserved during this sprint.

## Remaining Large Files

- `frontend/components/AppShell.tsx`: 5,101 lines. Reduced below the 5,500 line target, but still a future decomposition candidate.
- `backend/app/services/pptx_service.py`: 1,088 lines. Reduced by about half, but further slide-level extraction can be done in a later sprint.

## Cloud Status

GitHub Actions, Vercel, and Render were not executed from this local environment. Do not treat cloud deployment as verified until those dashboards are checked manually.
