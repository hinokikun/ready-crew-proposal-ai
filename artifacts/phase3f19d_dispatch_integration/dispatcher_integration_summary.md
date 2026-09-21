# Phase3F-19D Fail-Closed Production Dispatcher Integration

## Integration boundary

The integration is at `backend/app/services/pptx_parts/slides.py:add_designed_slide`. The existing `render_v5_masterpiece_slide` path remains the fallback. `pptx_service.py` supplies the Summary/Detail surface context without changing either API contract.

The dispatch sequence is:

`feature flag` → `approved runtime registry` → `role gate` → `native content adapter` → `text-fit/sample/provenance validation` → `validated runtime package` → `editable slide import` → existing renderer fallback on any failure.

The runtime registry at `backend/app/presentation_assets/native_trace/registry.json` is the authoritative Human approval source for this dispatcher. Unknown or missing roles fail closed.

## Evidence-sensitive behavior

KPI, ESTIMATE, MARKET_ANALYSIS, TARGET_ANALYSIS, ROI_OR_EFFECT, RISK, CASE_STUDY, COMPETITION, WIN_PROBABILITY, and evidence-dependent SCHEDULE remain fallback-only with current data. The adapter’s Phase3F-19C provenance guards are preserved. No Canonical sample values are promoted into customer output.

## Failure isolation

Each native attempt returns a structured trace containing ROLE, NATIVE_REQUESTED, NATIVE_ELIGIBLE, NATIVE_RENDERED, FALLBACK_USED, FAILURE_REASON, HUMAN_APPROVAL_STATUS, PROVENANCE_STATUS, TEXT_FIT_STATUS, and SAMPLE_LEAK_STATUS. Native exceptions are logged and the current slide is rendered with the established renderer; the deck is not failed solely by the optional native path.

## Feature flag

`PPTX_APPROVED_NATIVE_RENDERER_ENABLED` already exists as the single server-side control and defaults to `OFF`. It was not enabled in the environment. With OFF, native dispatch is not requested and the existing renderer remains the only path.

## Validation

- Phase3F-19A foundation: 10/10
- Phase3F-19B adapter: 23/23
- Phase3F-19C evidence binding: 12/12
- Phase3F-19D dispatcher/integration: 22/22
- Combined focused result: 67/67

Validated scenarios include flag OFF, eligible generic role, Human-unapproved role, evidence-sensitive fallback, sample-leak prevention, text-fit failure, missing template, renderer exception, fallback continuation, Summary/Detail compatibility, and runtime template immutability.

## Scope confirmation

API, Frontend, PDF, DB schema, auth, frozen Native Trace source files, and production environment state were not changed. No deployment, stage, commit, or push was performed. This is dispatcher integration only; it is not a production activation or Human Visual PASS declaration.
