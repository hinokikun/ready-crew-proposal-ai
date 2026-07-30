# Administrator Guide

## Purpose

This guide is for administrators who operate Ready Crew Proposal AI in production.

## Responsibilities

- Manage production environment variables.
- Maintain user accounts and roles.
- Confirm Backend, Frontend, OpenAI, and Beautiful.ai status.
- Monitor logs and errors.
- Manage backups and restore procedures.
- Run release smoke tests.
- Handle incidents and rollback.

## Environment Setup

### Backend

1. Deploy Backend to Render.
2. Set production environment variables.
3. Use PostgreSQL for production data.
4. Confirm `/health` and `/health/ready`.
5. Login with the initial admin account.

### Frontend

1. Deploy Frontend to Vercel.
2. Set `NEXT_PUBLIC_API_URL` to the Render Backend URL.
3. Confirm the app can login and call Backend APIs.

## Initial Admin

Set these variables for the first production deployment:

- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `APP_AUTH_SECRET`
- `DATABASE_URL`

The Backend creates the admin only if the email does not already exist. Existing users are not overwritten.

After first login:

1. Create personal admin accounts if needed.
2. Create member or viewer users.
3. Store credentials outside the repository.
4. Rotate the initial password if it was shared during setup.

## Updates

Before updating production:

1. Review release notes.
2. Run Backend pytest.
3. Run Frontend typecheck, build, and E2E.
4. Confirm Markdown links.
5. Confirm no secrets are in the diff.
6. Confirm rollback target is available.

After updating:

1. Confirm `/health/ready`.
2. Confirm login.
3. Generate a small proposal.
4. Download PowerPoint and PDF.
5. Test Beautiful.ai if enabled.
6. Review logs for errors.

## Logs

Check Render logs for:

- Startup errors
- Database connection errors
- Authentication errors
- OpenAI errors
- Beautiful.ai API errors
- PPTX/PDF generation errors
- Customer Ready blocked events

Do not log:

- Passwords
- API keys
- Bearer tokens
- Database credentials
- Full customer confidential text unless explicitly required by approved operations policy

## Backup

Recommended production backup:

1. Use PostgreSQL managed backups.
2. Export database before major release changes.
3. Keep generated proposal files only according to internal retention rules.
4. Record restore test results.

If SQLite is used with a persistent disk:

1. Stop write traffic or enable maintenance mode.
2. Copy the database file from the persistent disk.
3. Verify the backup file is readable.
4. Resume service.

Do not delete production data during backup.

## Incident Response

### Login Failure

1. Confirm Backend `/health/ready`.
2. Confirm `DATABASE_URL`.
3. Confirm user exists and is active.
4. Confirm role is correct.
5. Check Render logs for authentication errors.

### Proposal Generation Failure

1. Check OpenAI settings.
2. Confirm `USE_MOCK_AI=false` is intentional.
3. Check request size and timeout.
4. Ask user to retry with shorter input if needed.

### PowerPoint or PDF Failure

1. Confirm Backend logs.
2. Confirm generated proposal data exists.
3. Try a small sample proposal.
4. If all exports fail, enable maintenance mode until resolved.

### Beautiful.ai Failure

1. Check `BEAUTIFUL_AI_ENABLED`.
2. Check `BEAUTIFUL_AI_API_KEY`.
3. Run Beautiful.ai diagnostics.
4. Confirm returned URL is `editor_url` or `player_url`.
5. If Beautiful.ai is unavailable, instruct users to use PowerPoint download.

### Database Failure

1. Set `MAINTENANCE_MODE=true` if data writes are unsafe.
2. Check Render PostgreSQL status.
3. Restore from the latest known good backup if needed.
4. Confirm login and proposal history.

## Feature Flags

Keep optional features disabled unless verified:

| Flag | Default | Production Note |
|---|---|---|
| `USE_MOCK_AI` | `false` | Use `true` only for demos without real AI. |
| `BEAUTIFUL_AI_ENABLED` | `false` | Enable only with a valid API key. |
| `SALES_ASSISTANT_ENABLED` | `false` | Admin-only feature. |
| `SALES_ASSISTANT_PROPOSAL_ENABLED` | `false` | Requires Sales Assistant. |
| `PROPOSAL_EXPORT_ENABLED` | `false` | Requires approved export workflow. |
| `MAINTENANCE_MODE` | `false` | Use during incidents. |

## Rollback

1. Enable maintenance mode if users are affected.
2. Roll back Backend on Render to the previous successful deployment.
3. Roll back Frontend on Vercel to the previous successful deployment.
4. Confirm `/health/ready`.
5. Run smoke tests.
6. Disable maintenance mode after confirmation.

## Production Smoke Test

- Admin login
- Member login
- User management visible only to admin
- New proposal generation
- Customer Ready display
- Quality Report display
- PPTX download
- PDF estimate download
- Beautiful.ai creation if enabled
- History display
- Audit log update

## Release Documents

- [Production Deployment Guide](../deployment/PRODUCTION_DEPLOYMENT.md)
- [Version 2.2 Release Notes](../releases/VERSION_2.2_RELEASE.md)
- [Known Issues](../../KNOWN_ISSUES.md)
- [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)
