# Phase3F-19C Evidence-Sensitive Role Binding Review

## Scope

This review inspected the current Production request and PPTX context flow. It did not connect the native dispatcher, enable the feature flag, change API/Frontend/PDF behavior, change the database, or modify frozen Native Trace assets.

## Actual finding

The current context contains user-entered project text, hearing text, competitor identity fields, a budget range, derived target/KPI/competitor/schedule rows, heuristic estimate lines, generated risk/ROI narrative, parsed case-study text, and a generated/unproven `WinProbability` object. It does not carry field-level evidence/provenance for the factual values required by the approved evidence-sensitive layouts.

The optional `semantic_candidates` transport is the only current boundary that can carry source field, authority, review state, source reference, and admissibility metadata. `build_pptx_context` does not currently copy that transport into `PptxContext`; therefore it does not unlock any evidence-sensitive role in the ordinary current flow.

## Role result

| Role | Result | Current reason |
|---|---|---|
| KPI | `KPI_EVIDENCE_REQUIRED` | KPI defaults/targets are generated or derived; no actual measurement evidence is bound |
| ESTIMATE | `ESTIMATE_EVIDENCE_REQUIRED` | heuristic min/max lines and budget range only; no quantity/unit/unit-price provenance |
| MARKET_ANALYSIS | `MARKET_EVIDENCE_REQUIRED` | no research evidence field in `PptxContext` |
| TARGET_ANALYSIS | `TARGET_EVIDENCE_REQUIRED` | generated/profile target rows, not customer-specific evidence |
| ROI_OR_EFFECT | `ROI_EVIDENCE_REQUIRED` | no verified investment/effect inputs or calculation basis |
| RISK | `RISK_EVIDENCE_REQUIRED` | generic narrative only; no structured owner/likelihood/impact/status |
| CASE_STUDY | `CASE_STUDY_EVIDENCE_IMAGE_REQUIRED` | case text may exist, but image provenance and permission are absent |
| COMPETITION | `COMPETITION_EVIDENCE_REQUIRED` | competitor scores are keyword heuristics; no criterion-level source/date |
| WIN_PROBABILITY | `WIN_PROBABILITY_EVIDENCE_REQUIRED` | rank/probability object is generated or unproven; rank cannot produce a percentage |

`SCHEDULE` remains blocked for factual dates, owners, and milestones for the same reason, although it is adjacent to the nine-role evidence-sensitive review set.

## Adapter decision

The isolated adapter now performs provenance checks against the existing semantic-candidate transport when it is supplied to the adapter. It accepts only confirmed/corrected trusted candidates or explicit user-provided evidence according to role policy. It rejects generated-only candidates, rank-only probability, unsupported competitor claims, budget-only estimate detail, and case studies without a permitted verified image. No dispatcher is connected and no new upstream input field was added.

## Validation

- Phase3F-19A focused tests: 10/10 passed.
- Phase3F-19B focused tests: 23/23 passed after the stricter provenance contract was applied.
- Phase3F-19C focused tests: 12/12 passed.
- Combined focused result: 45/45 passed.
- Sample-content leak found: no.
- Unsupported inference: current generated/heuristic values were detected and remain blocked; none were upgraded to verified.

## Readiness

No evidence-sensitive role is unlocked by the current ordinary Production data path. The system is ready for Phase3F-19D dispatcher integration only as a fail-closed integration: the dispatcher must preserve these gates and must not enable a native role until its evidence contract is satisfied.
