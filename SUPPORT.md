# Support

## Support scope

This project is prepared for controlled production rollout. Support covers:

- Login and account access
- Proposal generation
- Quality Gate
- PPTX / PDF output
- Beautiful.ai output
- Creation history
- Admin user management
- Organization / Workspace access
- Audit log and operational checks

## Before contacting support

Please collect:

- Date and time
- User role
- Organization
- Workspace
- Screen name
- Operation performed
- Error message
- request_id, if shown
- Browser and screen width

Do not send:

- Passwords
- API keys
- Tokens
- Authorization headers
- Real customer confidential text
- Full generated proposal body

## Useful self-checks

1. Refresh the page.
2. Confirm you are using the correct login mode.
3. Confirm Maintenance Mode is not active.
4. Ask an admin to check `/health` and `/health/ready`.
5. For Beautiful.ai, ask an admin to check the diagnostics panel.
6. If output generation fails, try the alternative PPTX/PDF output.

## Escalation

Critical issues:

- Login unavailable for all users
- Backend unavailable
- DB connection failure
- Organization / Workspace data exposure
- viewer can generate or edit
- Secrets appear in logs or UI

For critical issues, enable Maintenance Mode and follow the incident runbook.
