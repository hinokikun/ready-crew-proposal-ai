# AppShell Decomposition

Version 22.1 decomposed `frontend/components/AppShell.tsx` without changing the visible UI or user flow.

## AppShell Responsibilities

`AppShell.tsx` still owns the screen composition and state wiring for:

- authentication and current user state
- organization and workspace display
- dashboard and Sales Copilot entry points
- proposal intake, analysis, strategy, hearing, estimates, and outputs
- AI Workspace display
- Quality Gate and review states
- Beautiful.ai status and presentation actions
- Presentation Review and Proposal Optimization panels
- CRM, Knowledge, Analytics, Prompt Studio, Pilot, Release, and admin panels
- loading, error, maintenance, and UAT display states

## Extraction Policy

The refactor moved pure logic and static workflow helpers out of `AppShell.tsx`. It did not move JSX sections or change DOM labels, CSS classes, routes, role checks, or API payloads.

## New Structure

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
```

`logic.ts` is a compatibility facade that re-exports the same helper surface used by `AppShell.tsx`.

## Line Count Result

| File | Lines |
| --- | ---: |
| `AppShell.tsx` before | 7,441 |
| `AppShell.tsx` after | 5,101 |
| `logic-parts/estimates.ts` | 297 |
| `logic-parts/hearing.ts` | 272 |
| `logic-parts/intake.ts` | 383 |
| `logic-parts/outputs.ts` | 402 |
| `logic-parts/strategy.ts` | 444 |
| `logic-parts/workflow.ts` | 296 |

All new frontend logic files are below 800 lines.
