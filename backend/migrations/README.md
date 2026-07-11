# Database Migration Notes

This project currently keeps SQLite as the default database and prepares the schema for a future PostgreSQL/Alembic migration.

## Current Database Targets

- Default local/Render setting: `sqlite:///app.db`
- Future production setting: `postgresql://...` or `postgresql+psycopg://...`

Do not commit `.env`, `app.db`, database dumps, or connection strings.

## Current Tables

- `users`
- `customers`
- `projects`
- `proposal_histories`
- `meeting_memos`
- `usage_logs`
- `audit_logs`
- `feedback_entries`
- `analytics_sessions`
- `analytics_events`
- `analytics_errors`
- `release_notes`
- `release_records`
- `proposal_knowledge`
- `proposal_templates`
- `workspace_conversations`
- `workspace_work_logs`
- `proposal_reviews`
- `proposal_review_revisions`
- `quality_gates`

`proposal_reviews` stores the human approval workflow for AI Workspace outputs. It keeps project metadata, status, short reviewer comments, reviewer IDs, and timestamps only. Do not store proposal body text or customer confidential text in this table.
`proposal_review_revisions` stores the feedback-loop history: previous/next status, short reviewer comment, AI improvement policy, diff summary, timestamp, and executing user ID. It must not store full proposal text or customer confidential text.
`quality_gates` stores the human pre-submission checklist state for a project. It keeps checklist labels, completion flags, admin bypass status, short bypass reason, user ID, and timestamps only. Do not store proposal body text, customer confidential text, API keys, or passwords in this table.
`release_records` stores release management metadata: version, status, release date, summary, changes, rollout checklist, known issues, rollback memo, released user ID, and timestamps only. Do not store API keys, environment variables, customer information, or generated proposal text in this table.

## Current Compatibility Columns

`proposal_knowledge` has these Version 8.1 quality-control columns:

- `approval_status`
- `quality_score`
- `confidential_risk`
- `confidential_flags`
- `source_type`
- `source_note`

The current application adds missing columns at startup for SQLite compatibility. This is intentionally conservative and avoids destructive schema changes.

## Initialization Flow

The startup flow is:

1. `create_tables()`
2. `add_missing_columns()`
3. `ensure_initial_admin()`
4. `seed_default_templates()`

Router files must not contain database initialization logic.

## Future Alembic Migration Plan

1. Add Alembic as a backend dependency.
2. Generate a baseline revision from the current table list.
3. Mark existing SQLite databases as the baseline only after a backup.
4. Move `add_missing_columns()` changes into explicit Alembic revisions.
5. For PostgreSQL, create a fresh database and run all revisions from the baseline.
6. Keep sensitive fields out of migrations and seed data.

## PostgreSQL Notes

When moving to PostgreSQL:

- Use `DATABASE_URL=postgresql://...` or `DATABASE_URL=postgresql+psycopg://...`.
- The app normalizes `postgresql://` to the SQLAlchemy psycopg driver URL.
- Use managed PostgreSQL services such as Render PostgreSQL, Supabase, or Neon.
- Run migrations before enabling production traffic.

## Backup Before Migration

SQLite:

```powershell
Copy-Item backend\app.db backend\backup\app_yyyyMMdd_HHmm.db
```

PostgreSQL:

Use the provider backup feature or `pg_dump`. Do not store dumps in Git.
