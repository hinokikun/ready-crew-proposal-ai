# Feature Flag Activation Path

Flag: `PPTX_APPROVED_NATIVE_RENDERER_ENABLED`

- Source default: `False` in `backend/app/config.py`.
- Current effective state: OFF.
- Local validation override: process-local environment value for a temporary backend process only; no `.env` edit.
- Future server activation: set the same environment variable in the server-side deployment environment. No Frontend dependency and no API field is required.
- Restart: required because application settings are read during backend process initialization.
- OFF behavior: `add_designed_slide` skips the optional native attempt and uses the existing renderer path.
- ON behavior: the optional native dispatcher is attempted only when all role safety gates pass; failures fall back to the existing renderer for the same slide.
- API contract: unchanged for `/api/download-pptx` and `/api/download-summary-pptx`.
- Rollback: set the environment value to `false` and restart. No migration, DB rollback, Frontend rollback, or PDF change is required.

This plan does not change any environment or enable the flag.
