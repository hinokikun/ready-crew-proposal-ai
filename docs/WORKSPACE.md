# Workspace Management

Workspace is the working area inside an Organization.

Examples:

- 営業
- 制作
- AIチーム
- 管理

## Current Workspace

After login, the frontend displays the current Organization and Workspace near the top of the home screen.

Users can switch only to Workspaces they are allowed to access.

## Workspace Switching

The UI calls:

```http
GET /api/organizations/context
PATCH /api/organizations/context
```

Switching updates the user's `current_organization_id` and `current_workspace_id`.

After switching, CRM, projects, Knowledge, Beautiful.ai, and analytics-related writes use the selected context.

## Data Separation

The following flows are scoped to the current Workspace:

- CRM project creation and CRM listing
- project lifecycle events
- proposal generation history and usage logs
- Knowledge entry creation, search, best practices, and templates
- Beautiful.ai presentation creation and listing
- analytics event/session recording
- Organization/Workspace analytics breakdown
- review approval and review revision history
- Quality Gate completion / bypass state
- AI Workspace conversations and work logs
- AI notifications
- Orchestrator queue actions
- Prompt Studio versions and experiments
- Learning improvements
- Pilot issue management

## Beautiful.ai

Beautiful.ai presentation records include:

- `organization_id`
- `workspace_id`

The same `project_id` in another Workspace does not return presentations from the previous Workspace.

## Analytics

The admin Product Analytics response includes:

- Organization usage count
- Workspace usage count
- project count
- average win probability as a practical win-rate indicator

## Operational Notes

- Organization and Workspace IDs are internal IDs. Do not expose database URLs, tokens, or API keys.
- If a user cannot see expected projects, confirm their Workspace switcher selection first.
- If admin creates a new Organization, assign users to the desired Workspace before pilot use.
- If an old SQLite database still has `quality_gates.project_id UNIQUE`, follow `docs/ORGANIZATION_MIGRATION.md` before running multiple workspaces with overlapping project IDs.
