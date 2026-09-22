# Phase3F-19E Integration Smoke Test

## Results

- Flag OFF Summary: PASS, 11 slides.
- Flag OFF Detail: PASS, 25 slides.
- Flag ON Summary: PASS, 11 slides.
- Flag ON eligible native role: `PROPOSAL_SUMMARY` rendered natively with adapter, provenance, sample-leak, and text-fit checks passing.
- Blocked roles: 10/10 remained fail-closed and used the existing renderer: KPI, ESTIMATE, MARKET_ANALYSIS, TARGET_ANALYSIS, ROI_OR_EFFECT, RISK, CASE_STUDY, COMPETITION, WIN_PROBABILITY, and SCHEDULE.
- Long-text Detail: PASS, 25 slides rendered; no blank output, clipping, off-canvas, or unhandled overflow finding was detected by the machine checks.
- Controlled native exception: PASS; the affected slide fell back and deck generation continued.

## Structural and visual machine checks

- All generated PPTX packages opened as valid ZIP packages.
- All generated decks remained 16:9.
- Full-slide raster detected: 0.
- Clipping findings: 0.
- Overflow findings: 0.
- Off-canvas findings: 0.
- Collision findings: 0.
- Rendered PNGs: 75, all 1600x900 and non-blank.

Automated checks do not constitute Human Visual PASS.

## Immutability and flag reset

- Frozen Native Trace sources: unchanged.
- Canonical sources: unchanged.
- Fixture files: unchanged.
- Environment flag persistence: none.
- Effective flag after smoke: OFF.
- Deployment, Render/Vercel, stage, commit, and push: not performed.

## API-level smoke completion

Phase3F-19E-A completed the previously pending local API checks only. The existing integrated backend was started on port 8001 with the Native Renderer flag process-local and OFF, using a temporary SQLite database. `/api/download-summary-pptx` returned HTTP 200 and a valid 11-slide PPTX; `/api/download-pptx` returned HTTP 200 and a valid 13-slide PPTX. Both responses preserved the existing PPTX MIME type, returned non-zero bytes, and included Content-Disposition filenames. Existing admin authentication was used successfully; auth, permission, request schema, and response schema were unchanged. The backend was stopped after validation, the temporary database was removed, and port 8001 is closed. No deployed endpoint was contacted.

## Human review package

The native-rendered `PROPOSAL_SUMMARY` slide has a Canonical side-by-side comparison and manifest under `human_review/`. Human Visual PASS is not self-declared.

## Handoff status

Machine smoke, the API smoke, and the Human Review package are ready for the next phase. Human Visual PASS remains a separate review decision and is not self-declared here.
