# SECURITY

This document summarizes the production security policy for AI営業秘書.

## Vulnerability reporting

Report vulnerabilities privately to the system owner or internal security contact. Do not publish exploit details in public issues or chat channels.

When reporting, include:

- Affected function or screen
- Safe reproduction steps
- Role / Organization / Workspace
- request_id if available
- Expected and actual result

Do not include secrets, passwords, API keys, tokens, Authorization headers, cookies, DATABASE_URL, real customer text, or generated full proposal text.

## Authentication

- `APP_AUTH_SECRET` is required in production.
- Tokens include role and auth version.
- Disabled users and stale auth versions are rejected.
- Passwords are hashed and never displayed.

## Authorization

- `admin`: full administration.
- `manager`: operational review and management without secret settings.
- `member`: normal proposal work in assigned workspace.
- `viewer`: read-only.

Backend APIs must enforce permissions. Frontend display control is not sufficient.

## Data isolation

Organization and Workspace scope must be enforced for CRM, proposals, Knowledge, Analytics, Beautiful.ai, Review, Quality Gate, Learning, Pilot, Issue, Workspace conversations, and histories.

## Secrets

Never store or display:

- OpenAI API key
- Beautiful.ai API key
- OAuth token or refresh token
- Password
- Authorization header
- DATABASE_URL full value
- Real customer confidential body text
- Full generated proposal text

## External services

Beautiful.ai calls are made only from the Backend. The Frontend receives only safe status, presentation IDs, editor/player URLs, and sanitized diagnostics.

## Logging

Audit logs may include actor, role, organization, workspace, action, target ID, status, request_id, error_type, and safe metadata. They must not include body text, generated full text, passwords, tokens, or API keys.

## Production hardening

- Production CORS must allow only approved Vercel origins.
- Security Headers must remain enabled.
- Maintenance Mode should be used during major incidents.
- `/health` and `/health/ready` should be checked before release.
