# Version 22.1 Refactoring Baseline

Date: 2026-07-14

This file records the state captured before the Version 22.1 large-file decomposition. The refactor was limited to internal structure. No UI, API route, DB schema, role, workspace, Beautiful.ai behavior, or output contract changes were intended.

## Baseline File Sizes

| File | Lines Before |
| --- | ---: |
| `frontend/components/AppShell.tsx` | 7,441 |
| `backend/app/repositories.py` | 1,832 |
| `backend/app/services/pptx_service.py` | 2,184 |

## Baseline Checks

| Check | Result |
| --- | --- |
| `npm.cmd run typecheck` | Passed |
| `npm.cmd run check:unused` | Passed |
| `npm.cmd run build` | Passed |
| `npm.cmd run test:e2e` | Passed, 29 tests |
| `python -m compileall backend/app backend/tests` | Passed |
| `pytest -q` | Passed, 139 tests |
| `pip check` | Passed |
| `git diff --check` | Passed with CRLF warnings only |

## Baseline Build

| Metric | Value |
| --- | ---: |
| Next.js compile time | 5.4s |
| Route `/` size | 3.22 kB |
| First Load JS | 106 kB |
| Shared JS | 103 kB |

## Route And Function Counts

| Item | Count |
| --- | ---: |
| Frontend App Router route handlers | 0 |
| Assumed Vercel Serverless Functions from frontend route handlers | 0 |
| Backend router modules | 22 |

Backend routers at baseline:

`analytics`, `auth`, `beautiful_ai`, `briefing`, `feedback`, `integrations`, `knowledge`, `learning`, `logs`, `notifications`, `orchestrator`, `organizations`, `pilot`, `presentation_review`, `projects`, `prompts`, `proposal_optimization`, `quality_gates`, `releases`, `reviews`, `users`, `workspace`.
