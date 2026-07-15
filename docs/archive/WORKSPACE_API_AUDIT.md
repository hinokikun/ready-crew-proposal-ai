# Workspace API Audit

Version 18.1 API scope audit.

## Scope Categories

- `system`: system-wide endpoint. Only system admin should use it.
- `organization`: organization-level endpoint.
- `workspace`: workspace-level business data endpoint.
- `user`: current-user endpoint.
- `public`: no authenticated business data.

## API Audit

| Router | Endpoint Area | Scope | 18.1 Status |
|---|---|---|---|
| `auth` | login/me/logout | user | current user only |
| `users` | user list/create/update | system / organization | admin path; org role labels added in UI docs |
| `organizations` | context/list/switch/create/add-member | organization/workspace | switch checks membership + active org/workspace |
| `projects` | CRM/customer/project | workspace | repository already context-aware from 18.0; review child reads still require scoped child queries |
| `reviews` | review request/list/update/revisions | workspace | scoped in 18.1 |
| `quality_gates` | gate get/save/complete/bypass | workspace | scoped in 18.1 |
| `workspace` | AI Workspace conversations/logs/summary | workspace | scoped in 18.1 |
| `knowledge` | knowledge/templates/search | workspace/system | approved-only search retained; current repository scoping retained |
| `analytics` | product analytics/release notes | workspace/system | event storage scoped; dashboard aggregation still needs explicit workspace mode for non-system views |
| `learning` | learning run/dashboard/status | workspace | scoped in 18.1 |
| `prompts` | Prompt Studio, experiments, metrics | workspace/system | `scope_type` / `scope_id` added; list/create/route scoped |
| `pilot` | dashboard/issues/maintenance/end | workspace/system | Issue management scoped; dashboard remains admin operational aggregate |
| `notifications` | notification center/read/archive | user + workspace | scoped in 18.1 |
| `integrations` | settings/intake/dry-run | workspace | context columns present; approval flow retained |
| `orchestrator` | queue/start/run/retry/analytics | workspace | scoped in 18.1 |
| `releases` | release management | system/org | admin/manager only |
| `feedback` | proposal feedback | workspace | storage already context-enabled; feedback-to-issue scoped |
| `logs` | usage/audit logs | system/org | admin visibility only |
| `beautiful_ai` | status/create/list/open | workspace | presentation and quality gate scoped |
| `briefing` | Today's briefing | workspace | should use CRM/current user context |

## Direct ID Access Rules

The following IDs must be checked against the current organization/workspace
before returning or mutating data:

- `project_id`
- `review_id`
- `quality_gate_id` or quality-gate `project_id`
- `presentation_id`
- `knowledge_id`
- `experiment_id`
- `notification_id`
- `issue_id`
- `conversation_id`
- `action_id`

18.1 applied this rule to Reviews, Quality Gates, Workspace conversations,
Beautiful.ai, Prompt/Experiment, Learning, Notifications, Orchestrator, and
Pilot Issues.

## Safe Failure Behavior

Cross-organization or cross-workspace access should return a generic `404` or
`403` without leaking object names, body text, customer names, or generated
content. Audit logs should record action names and target IDs only.

## Version 18.2 Aggregation Scope Contract

Aggregation endpoints must use the smallest scope by default:

- `scope=workspace`: current workspace only
- `scope=organization`: current organization only, admin/manager
- `scope=system`: all organizations, admin only

Frontend scope values are never trusted directly. The backend resolves the final scope from the authenticated user and current membership.

Updated areas:

- `/api/logs`
- `/api/logs/audit`
- `/api/logs/usage-dashboard`
- `/api/logs/usage-dashboard.csv`
- `/api/logs/trial-report`
- `/api/logs/improvement-dashboard`
- `/api/analytics/dashboard`
- `/api/analytics/errors/{error_id}`
- `/api/pilot/dashboard`
- `/api/pilot/end`

System-wide data must not be returned unless the caller explicitly requests `scope=system` and has system admin rights.
