# Workspace Isolation Acceptance Plan

Version 18.2 finalizes the acceptance criteria for Organization / Workspace isolation before production rollout.

## Scope Definitions

| Scope | Meaning | Allowed roles | Default |
| --- | --- | --- | --- |
| `workspace` | Current selected workspace only | admin, manager, member, viewer where endpoint role permits | Yes |
| `organization` | Current selected organization across its workspaces | admin, manager | No |
| `system` | All organizations | admin only | No |

Frontend-provided `scope` is a request only. Backend resolves it from the authenticated user and current membership. If a user asks for a scope they cannot use, the API returns `403`.

## Remaining Items Extracted From 18.1 Audits

| Item | Target API/Table | Current state before 18.2 | Risk | Fix policy | Test policy | Completion criteria |
| --- | --- | --- | --- | --- | --- | --- |
| Analytics dashboard aggregation scope | `/api/analytics/dashboard`, `analytics_*` | Event storage had context, dashboard could aggregate globally | Cross-workspace usage/error visibility | Add explicit `scope` and backend enforcement | A/A1, A/A2, B/B1 scoped counts | Workspace default returns only current workspace |
| Usage dashboard scope | `/api/logs/usage-dashboard`, CSV | Admin aggregate was global | Admin sees unrelated organization data by default | Add `scope`, default workspace, CSV scope labels | scoped API + CSV smoke | CSV includes selected Organization/Workspace labels |
| Trial / improvement reports | `/api/logs/trial-report`, `/api/logs/improvement-dashboard` | Report could use global counts | Pilot/report leakage | Pass resolved scope into report builders | report scope test | Report includes scope metadata |
| Pilot dashboard scope | `/api/pilot/dashboard` | Operational counts were global | Pilot issues/feedback mixed across workspaces | Scope event/issue/feedback counts | pilot scoped dashboard test | Summary counts follow requested allowed scope |
| Quality Gate legacy unique | `quality_gates` | Old SQLite could have `project_id UNIQUE` | Same project key impossible across workspaces | Alembic table rebuild for SQLite; scoped unique index | legacy DB migration test | unique `(organization_id, workspace_id, project_id)` exists |
| Startup schema patching | `AUTO_SCHEMA_PATCH` / `/health/ready` | Startup ALTER allowed in pilot/dev | Production schema drift | `AUTO_SCHEMA_PATCH=false` disables auto patch; readiness checks migration | health readiness test | `/health/ready` is degraded if migration is not ready |
| Audit log scope | `audit_logs` | Context columns existed, actor role/request id incomplete | Weak traceability | Store actor role, org, workspace, request id metadata | audit log field test | Logs expose no secret/body data |
| Local browser cache | `localStorage` | Some keys were global/user-only | Workspace stale data after switching | Add user/org/workspace to workspace-dependent keys | frontend type/build + manual switch check | Switching workspace does not load previous history |
| Smoke test org checks | `scripts/smoke_test.py` | Cloud smoke did not validate workspace isolation | Cloud deploy may pass without tenant checks | Add current context, allowed/disallowed switch, IDOR env checks | smoke test dry run | Read-only by default; optional disallowed IDs are rejected |

## Admin Aggregation Classification

| Aggregation | Default scope | Organization scope | System scope |
| --- | --- | --- | --- |
| Usage Dashboard | `workspace` | admin/manager | admin |
| Product Analytics | `workspace` | admin/manager | admin |
| Pilot Dashboard | `workspace` | admin/manager | admin |
| Learning Dashboard | `workspace` | admin/manager | admin |
| Improvement Dashboard | `workspace` | admin/manager | admin |
| Trial Report | `workspace` | admin/manager | admin |
| Operation Readiness | system health, no customer content | admin/manager | admin |
| Notification Analytics | `workspace` | admin/manager | admin |
| Orchestrator Analytics | `workspace` | admin/manager | admin |
| Project Lifecycle Analytics | `workspace` | admin/manager | admin |
| Feedback aggregation | `workspace` | admin/manager | admin |
| Error aggregation | `workspace` | admin/manager | admin |

## Acceptance Tests

1. Create Organization A / Workspace A1, Organization A / Workspace A2, Organization B / Workspace B1.
2. Add at least one user, project, review, quality gate, knowledge entry, notification, analytics event, Beautiful.ai record, pilot issue, orchestrator action, and workspace conversation in each workspace.
3. Confirm A1 member can only see A1 data.
4. Confirm A2 member can only see A2 data.
5. Confirm B1 member can only see B1 data.
6. Confirm organization manager can see A1/A2 with `scope=organization`, but cannot see B1.
7. Confirm system admin can see all data only when explicitly requesting `scope=system`.
8. Confirm direct ID access across workspace returns `403` or `404` without names, counts, or body text.
9. Confirm CSV/Markdown exports include only the requested allowed scope and show scope labels.
10. Confirm `/health/ready` reports `migration_ready=true` before production traffic.

## Human Pre-Production Checklist

1. Enable Maintenance Mode.
2. Back up the database.
3. Verify the backup can be restored.
4. Run `alembic upgrade head`.
5. Confirm migration revision and `/health/ready`.
6. Run the cloud smoke test.
7. Review audit logs for denied cross-scope attempts.
8. Disable Maintenance Mode.
