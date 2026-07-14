# Organization / Workspace Migration Guide

This document captures the production migration policy for Version 18.x.

## Current State

The application still supports SQLite for local and pilot operation. Most
business tables have `organization_id` and `workspace_id` columns that are
created on startup if missing.

Default backfill:

- Organization: `Ready Crew`
- Workspace: `営業部`
- Existing rows: `organization_id = 1`, `workspace_id = 1`

## Version 18.2 Formal Migration

Version 18.2 adds this Alembic revision:

- `backend/alembic/versions/20260713_1820_workspace_isolation_acceptance.py`

This revision backfills missing context values to the default Organization / Workspace, adds scoped indexes, adds prompt and experiment scope fields, adds audit trace fields, and migrates legacy SQLite Quality Gate uniqueness from `project_id` to `(organization_id, workspace_id, project_id)`.

The migration must not print or store customer body text, generated proposal text, API keys, tokens, or passwords.

## Why a Formal Migration Is Needed

Startup column creation is safe for pilot use, but production multi-tenant
operation should move to an explicit migration tool such as Alembic.

Required production migration tasks:

1. Create `organizations`, `workspaces`, and `workspace_memberships`.
2. Backfill existing records to the default organization/workspace.
3. Add `organization_id` and `workspace_id` to all workspace-scoped tables.
4. Add indexes on common scope filters.
5. Rebuild tables that still have old single-column uniqueness constraints.
6. Validate row counts before and after migration.
7. Run isolation tests before enabling multiple organizations.

## SQLite Notes

SQLite cannot drop a unique constraint in place. For old databases where
`quality_gates.project_id` is still unique, rebuild the table:

1. Create `quality_gates_new` without `project_id UNIQUE`.
2. Copy rows from `quality_gates`.
3. Drop the old table after verifying counts.
4. Rename `quality_gates_new` to `quality_gates`.
5. Recreate indexes.

Do not delete `app.db` in production. Back it up first.

For legacy SQLite databases, the final Quality Gate uniqueness must be:

```text
UNIQUE (organization_id, workspace_id, project_id)
```

Validate key row counts before and after migration:

```sql
SELECT COUNT(*) FROM quality_gates;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM proposal_reviews;
SELECT COUNT(*) FROM proposal_knowledge;
SELECT COUNT(*) FROM analytics_events;
SELECT COUNT(*) FROM audit_logs;
```

## PostgreSQL Readiness

`DATABASE_URL` should be usable with either:

- `sqlite:///app.db`
- `postgresql://...`

Before production PostgreSQL migration:

- Use Render PostgreSQL, Supabase, or Neon.
- Add Alembic revision files.
- Replace startup DDL with migration execution in deployment runbooks.
- Add FK constraints where existing data quality allows it.
- Keep `DATABASE_URL` out of UI, logs, and documentation screenshots.

## Recommended Alembic Plan

1. Add Alembic config under `backend/migrations`.
2. Generate baseline revision from current schema.
3. Add a revision for organization/workspace columns and indexes.
4. Add a revision for Prompt scope columns.
5. Add a revision for removing legacy SQLite-only uniqueness constraints.
6. Test on empty SQLite, existing SQLite copy, and PostgreSQL staging.

## Readiness Gates

Do not enable multiple external organizations until all are true:

- Existing data backfill succeeded.
- Scope indexes exist.
- Cross-organization IDOR tests pass.
- Quality Gate uniqueness migration completed.
- `/health` returns `db_connected: true`.
- Backups and rollback steps are documented.

## Production Startup Policy

For production, set:

```text
AUTO_SCHEMA_PATCH=false
```

Production schema changes should be applied by Alembic, not by startup auto-ALTER. If the schema is not ready, `/health/ready` should return degraded status or `503`.

Use startup schema patching only for local development and tests.

## Version 18.2 Production Runbook

1. Enable Maintenance Mode.
2. Back up the database.
3. Verify that the backup can be restored.
4. Run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
```

5. Confirm `/health/ready` returns `migration_ready: true`.
6. Run `scripts/smoke_test.py` against the cloud backend.
7. Confirm scoped dashboards with `scope=workspace` and, for system admin only, `scope=system`.
8. Disable Maintenance Mode.
