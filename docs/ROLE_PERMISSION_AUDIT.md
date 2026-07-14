# Role Permission Audit

This document records the backend permission model. Frontend visibility is only a convenience; backend APIs must enforce permissions.

## Roles

| Role | Purpose | Allowed scope |
| --- | --- | --- |
| `admin` | System administrator | workspace, organization, system |
| `manager` | Organization / review manager | workspace, organization |
| `member` | Standard user | workspace |
| `viewer` | Read-only user | workspace read-only |

## Version 18.2 Scope Permission Rules

- `workspace` scope is the default and smallest scope.
- `organization` scope is limited to `admin` and `manager`.
- `system` scope is limited to `admin` and must be explicitly requested.
- `member` and `viewer` must not receive cross-workspace aggregation data.
- Admin-only screens should still default to current workspace unless the user explicitly selects organization or system scope.
- Backend APIs enforce these rules; frontend display controls are not treated as authorization.

## API Areas

| Area | Required role | Notes |
| --- | --- | --- |
| Auth | any authenticated user | token role and `auth_version` are checked |
| Users | admin | user creation, activation, role changes |
| Logs / Audit | admin / manager for scoped operational logs | audit logs are not shown to general users |
| Proposal generation | admin / member | viewer cannot generate |
| Beautiful.ai creation | admin / member | quality gate must permit download/export |
| CRM / Projects | scoped user access | cross-workspace direct IDs return 403 or 404 |
| Review approval | admin / manager | member can request review, not approve |
| Quality Gate | admin / member for completion; admin for bypass | bypass reason required |
| Knowledge approval | admin / manager | AI can only use approved knowledge |
| Analytics / dashboards | admin / manager | system scope admin only |
| Pilot / operations | admin / manager depending endpoint | destructive pilot actions are admin only |
| Orchestrator queue monitor | admin / manager | queue actions are scoped |
| Integrations | admin / manager for settings/review | tokens and API keys are not stored |

## Audit Log Policy

Store:

- actor user id
- actor role
- organization id
- workspace id
- action
- target type
- target id
- request id
- status
- timestamp

Do not store:

- passwords
- tokens
- API keys
- customer body text
- generated proposal text
- external OAuth credentials
