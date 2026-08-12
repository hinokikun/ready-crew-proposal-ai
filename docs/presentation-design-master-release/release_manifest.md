# Presentation Design Master Release Manifest

## Version

Presentation Design Master v1

## Commit hash

To be filled after release commit.

## Feature Flag

- Name: `PRESENTATION_DESIGN_AI_MASTER_ENABLED`
- Default: `false`
- Unset behavior: disabled

## Production entry

`/api/download-pptx` calls `build_pptx_bytes_for_engine()`.

When the master flag is enabled, the integration layer requests `presentation_design_master_v1`.
When disabled, the existing production PPTX generation path is preserved.

## Fallback

Master generation failures fall back to the existing production generator. No database rollback or migration is required.

Logged fields:

- `requested_version`
- `actual_version`
- `shadow_enabled`
- `shadow_success`
- `fallback_used`
- `fallback_reason`

## Runtime files

- `backend/app/config.py`
- `backend/app/services/presentation_engine_integration.py`
- Existing tracked `backend/app/presentation_director/`
- Existing tracked `backend/app/presentation_design_ai/`
- Existing tracked `backend/app/presentation_composer/`

No runtime dependency is taken on `artifacts/`.

## Tests

- `backend/tests/test_presentation_master_integration.py`
- Existing V10.1 and strategy integration tests
- Backend full pytest before commit
- `compileall`
- `pip check`
- `git diff --check`
- `git diff --cached --check`

## Rollback

Set `PRESENTATION_DESIGN_AI_MASTER_ENABLED=false`.

No DB migration, tag rollback, or deployment rollback is required for feature disablement.

## Known limitations

- Some visual regions remain flattened for visual fidelity.
- Title Fidelity is approved with limitations, not pixel-perfect.
- Fontconfig cache warnings appeared during local artifact generation, but generation completed.
- Production flag `true` has not been verified in the live production environment.
- Production deployment smoke test has not been executed.
