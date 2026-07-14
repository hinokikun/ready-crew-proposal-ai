# Organization Management

Version 18.0 adds the foundation for using AI営業秘書 across multiple companies, departments, and internal teams.

## Purpose

Organization is the top-level tenant boundary. Examples:

- Ready Crew
- 株式会社AAA
- 株式会社BBB
- 社内AIチーム
- 営業部
- 制作部

The system keeps each Organization's operational data separated by `organization_id`.

## Default Organization

On startup, the backend seeds:

- Organization: `Ready Crew`
- Workspace: `営業部`

Existing rows are backfilled to this default Organization and Workspace. Existing data is not deleted.

## Permissions

- `admin`: system-wide administrator. Can create Organizations, Workspaces, and memberships.
- `manager`: compatible with Organization administrator operations for review/approval flows, but Organization creation remains admin-only.
- `member`: normal user. Can use the current assigned Organization/Workspace.
- `viewer`: read-only. Cannot generate or edit operational data.

Cross-Organization access attempts are rejected and recorded in the audit log as `organization_cross_access_denied`.

## Scoped Data

The startup migration adds `organization_id` and `workspace_id` to major operational tables, including:

- customers / projects / lifecycle events
- proposal histories and usage logs
- analytics events and sessions
- Knowledge and templates
- Beautiful.ai presentations
- reviews and quality gates
- pilot issues and feedback-related records
- workspace conversations and action queue

## API

- `GET /api/organizations/context`
- `PATCH /api/organizations/context`
- `POST /api/organizations`
- `POST /api/organizations/{organization_id}/workspaces`
- `POST /api/organizations/memberships`

Only safe metadata is returned. Tokens, passwords, API keys, and connection strings are never returned.

## Notes

This version establishes the SaaS separation foundation. Some legacy admin dashboards may still show historical aggregate values until each report is fully scoped in a future hardening sprint.

## Version 18.1 Hardening Notes

- Backend APIs now derive organization/workspace from the authenticated user context.
- Direct ID access for reviews, quality gates, workspace conversations, notifications, prompt experiments, learning, orchestrator queue, pilot issues, and Beautiful.ai is scoped server-side.
- Workspace switching requires active Organization and Workspace membership.
- Frontend workspace switching clears workspace-scoped state so stale CRM, proposal, Quality Gate, and Beautiful.ai data is not shown after switching.
- See `docs/WORKSPACE_ISOLATION_AUDIT.md` and `docs/WORKSPACE_API_AUDIT.md` for the full audit.
