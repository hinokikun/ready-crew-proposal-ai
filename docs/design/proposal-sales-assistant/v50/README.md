# Version 50 AI Sales Assistant UI & Feature-Flagged API

Version 50 adds an admin-only interface and feature-flagged API for the Version 49 offline AI Sales Assistant generator.

This version does not connect the Sales Assistant to proposal generation, PPTX generation, Beautiful.ai, email, OpenAI, persistence, or history storage.

## Scope

- Backend API guarded by `SALES_ASSISTANT_ENABLED`
- Admin-only access enforced by backend role checks
- Admin UI guarded by `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED`
- Input form for sales context
- Sales Assistant Brief display
- Copy buttons for operational use
- JSON view for admin verification
- Human Review warnings
- Term Guard and missing information display

## Explicit Non-Scope

- DB save
- Migration
- History save
- Proposal generation integration
- PPTX integration
- Beautiful.ai integration
- Email sending
- OpenAI or external AI calls

## Files

- `architecture.md`
- `api_contract.md`
- `frontend_ui.md`
- `feature_flag.md`
- `security.md`
- `testing.md`
- `integration_plan.md`
