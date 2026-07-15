# Workspace Isolation Audit

Version 18.1 hardening audit for Organization / Workspace isolation.

## Scope Model

The backend must derive scope from the authenticated user. Frontend supplied
organization/workspace IDs are treated only as switch requests, not as trusted
authorization data.

Common request context fields:

- `user_id`
- `role`
- `organization_id`
- `workspace_id`
- `membership_role`
- `request_id`

Implemented common helpers:

- `backend/app/context.py`
- `backend/app/dependencies/context.py`
- `backend/app/scoping/service.py`

## Table Classification

| Table | Category | Required Scope | Current Handling | Owner Check |
|---|---|---:|---|---|
| `organizations` | organization master | global + active | `is_active` added | system/admin only |
| `workspaces` | workspace master | `organization_id` | `is_active` added | membership check |
| `workspace_memberships` | membership | `organization_id`, `workspace_id`, `user_id` | role includes viewer | active org/workspace |
| `users` | user | user/global | current user lookup | auth token |
| `customers` | workspace data | `organization_id`, `workspace_id` | existing context columns | scoped repository |
| `projects` | workspace data | `organization_id`, `workspace_id` | existing context columns | scoped repository |
| `proposal_reviews` | workspace data | `organization_id`, `workspace_id` | list/detail/update scoped | project/review scope |
| `proposal_review_revisions` | workspace data | `organization_id`, `workspace_id` | revision list scoped | review scope |
| `presentation_reviews` | workspace data | `organization_id`, `workspace_id` | review/list scoped | project scope |
| `presentation_revisions` | workspace data | `organization_id`, `workspace_id` | revision/list/generate scoped | review/revision scope |
| `presentation_revision_history` | workspace data | `organization_id`, `workspace_id` | compare scoped | revision scope |
| `proposal_improvement_backlog` | workspace data | `organization_id`, `workspace_id` | recommendation/list/update scoped | backlog scope |
| `proposal_best_practices` | workspace data | `organization_id`, `workspace_id` | list/extract scoped | current context |
| `quality_gates` | workspace data | `organization_id`, `workspace_id` | get/save/complete/bypass scoped | project scope |
| `workspace_conversations` | workspace data | `organization_id`, `workspace_id` | save/list/detail scoped | project scope |
| `workspace_work_logs` | workspace data | `organization_id`, `workspace_id` | save/list/detail scoped | project scope |
| `proposal_knowledge` | workspace data | `organization_id`, `workspace_id` plus approval | approved-only search already enforced | repository scope |
| `proposal_templates` | workspace data | `organization_id`, `workspace_id` | context columns present | admin review needed |
| `prompt_versions` | scoped config | `scope_type`, `scope_id`, org/workspace | list/create/route scoped | admin/manager |
| `experiments` | scoped config | `scope_type`, `scope_id`, org/workspace | list/create/judge scoped | admin/manager |
| `prompt_experiment_metrics` | analytics | `organization_id`, `workspace_id` | metric insert/analytics scoped | current context |
| `learning_runs` | analytics/config | `organization_id`, `workspace_id` | run/list scoped | current context |
| `learning_improvements` | analytics/config | `organization_id`, `workspace_id` | list/update scoped | current context |
| `ai_notifications` | user/workspace | `user_id`, `organization_id`, `workspace_id` | list/update scoped | notification owner |
| `action_queue` | workspace data | `organization_id`, `workspace_id` | queue/run/retry scoped | project scope |
| `beautiful_ai_presentations` | workspace data | `organization_id`, `workspace_id` | existing service scoped | quality gate scope |
| `pilot_issues` | workspace operations | `organization_id`, `workspace_id` | list/create/update scoped | admin/manager |
| `feedback_entries` | workspace operations | `organization_id`, `workspace_id` | used by feedback-to-issue scoped | current context |
| `analytics_events` | analytics | `organization_id`, `workspace_id` | context columns present | dashboard scoping pending |
| `analytics_sessions` | analytics | `organization_id`, `workspace_id` | context columns present | dashboard scoping pending |
| `audit_logs` | audit | actor + target scope | scope fields available | no secret body |
| `integration_settings` | integration config | org/workspace | context columns present | admin/manager |
| `external_intake_items` | intake | org/workspace | context columns present | approval flow |
| `release_records` | release | org/workspace/system | context columns present | admin/manager |

## Fixed in 18.1

- Review and review revision reads/writes now include current organization/workspace.
- Quality Gate reads/writes now include current organization/workspace.
- Beautiful.ai creation checks the scoped Quality Gate.
- Workspace conversation and work log persistence now includes organization/workspace.
- Prompt Version and Experiment list/create/route/analytics now use current scope or `system`.
- Learning analysis now uses current workspace data only.
- Orchestrator queue list/run/retry/analytics now uses current workspace.
- AI notifications now use current user and workspace scope.
- Pilot issue management now uses current workspace.
- Workspace switching requires active organization/workspace membership and resets frontend workspace-scoped state.

## Known Migration Notes

- Older SQLite databases may still have `quality_gates.project_id UNIQUE`.
  New databases no longer create that unique constraint. Existing production
  databases should be migrated with an explicit table rebuild before allowing
  duplicate `project_id` across workspaces.
- Some legacy analytics dashboard aggregations remain global for system-admin
  views. Workspace-level dashboards should pass user/context explicitly before
  production multi-tenant rollout.

## Version 18.2 Acceptance Updates

- Admin aggregation APIs now accept explicit `scope=workspace|organization|system`.
- Default scope is `workspace`.
- `organization` scope is limited to admin/manager.
- `system` scope is limited to admin.
- Usage, audit, product analytics, pilot summary, trial report, and improvement dashboard expose scope metadata.
- CSV exports include Organization / Workspace labels.
- Local browser cache for proposal history, pilot checklist, AI Workspace cache, local CRM-style storage, and local usage logs is scoped by user / organization / workspace.
- `/health` and `/health/ready` include migration readiness fields.
- Formal Alembic revision `20260713_1820_workspace_isolation_acceptance` migrates legacy Quality Gate uniqueness to `(organization_id, workspace_id, project_id)`.

Remaining production verification:

- Run the cloud smoke test with a forbidden workspace ID and other-workspace project ID.
- Confirm Vercel and Render are on the same commit before accepting production traffic.

## Version 20.1 Optimization Evidence Scope

- Backlog recommendation, evidence, prediction, measurement, and approval fields are scoped by organization/workspace.
- Best Practice approval and duplicate control are scoped by organization/workspace.
- Members and viewers must not see pending Best Practices from another workspace.
- Backend rejects direct access by `backlog_id` or `best_practice_id` when the item belongs to a different workspace.
