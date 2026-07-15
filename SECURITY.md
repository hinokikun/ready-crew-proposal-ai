# Security Policy

## Supported version

| Version | Status |
| --- | --- |
| 1.0.x | Supported for controlled production rollout |

## Reporting a vulnerability

Please report security issues privately to the project administrator or responsible internal security contact.

Include only the minimum necessary information:

- Affected area
- Steps to reproduce using safe test data
- Expected result
- Actual result
- Role, Organization, Workspace, and request_id if available
- Screenshots with secrets and customer information removed

Do not include:

- API keys
- Passwords
- Tokens
- Authorization headers
- Cookies
- DATABASE_URL
- Real customer names or email bodies
- Full generated proposal text

## Security principles

- Backend enforces permissions; Frontend hiding is not sufficient.
- Organization and Workspace isolation must be preserved.
- Passwords are hashed and never displayed.
- API keys are stored only in server-side environment variables.
- Beautiful.ai API keys must never be exposed to Vercel or `NEXT_PUBLIC_*` variables.
- Audit logs must avoid confidential body text and secrets.
- Production CORS must allow only approved frontend origins.
- Security Headers must remain enabled for Backend API and health endpoints.

## Incident response

For suspected production incidents, follow `docs/INCIDENT_RESPONSE.md` and `docs/V25_0_RUNBOOK.md`.
