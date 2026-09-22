# Minimal Post-Activation Validation Plan

Run only after the explicit runtime Human Visual PASS and GO decision.

1. Confirm effective flag ON in the isolated activation environment and source default still OFF.
2. Generate one Summary deck; verify 11 slides and role order.
3. Generate one representative Detail deck; verify conditional roles and no duplicates/omissions.
4. Verify `PROPOSAL_SUMMARY` uses the approved S02 Native template and the adapter passes.
5. Verify one evidence-sensitive blocked role uses the existing renderer.
6. Verify `/api/download-summary-pptx` and `/api/download-pptx` return valid non-zero PPTX responses.
7. Verify sample leak count is 0.
8. Verify clipping, overflow, off-canvas, collision, and full-slide raster findings are 0.
9. Verify flag state and environment persistence after restart.
10. Perform one Human Visual spot-check of the runtime Native slide using the 19E-B three-way package.

Do not rerun the full 19E suite unless one of these focused checks fails or a source/template hash changes.
