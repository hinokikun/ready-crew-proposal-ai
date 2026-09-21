# Phase3F-22D rollback plan

## Single control

Set `PPTX_APPROVED_NATIVE_RENDERER_ENABLED=OFF` in the runtime environment and restart the backend process if the environment requires restart for configuration reload.

## Expected result

The dispatcher will not request approved Native rendering. Existing renderer behavior resumes for Summary and Detail, including all evidence-sensitive roles. No database migration, API change, Frontend change, PDF change, or template mutation is required.

## Trigger conditions

- Any runtime visual regression or Human Review block.
- Any provenance, completeness, sample-leak, or text-fit regression.
- Any Native exception that is not isolated as designed.
- Any slide omission, duplicate, blank slide, clipping, overflow, or invalid PPTX package.
- Any API/auth/permission regression.

## Verification after rollback

1. Confirm effective flag state is OFF.
2. Generate one Summary and one Detail deck in a controlled local context.
3. Confirm existing renderer trace is used and required slides remain present.
4. Confirm no Native template files, DB state, or request/response contracts were changed.

The source default remains OFF before and after this checkpoint.
