# Presentation Revision

Version 19.1 treats Beautiful.ai updates as revisions instead of directly editing a presentation in place.

## Revision Model

Each generated presentation can have revision history:

- Proposal v1
- Proposal v2
- Proposal v3

The revision stores metadata and safe summaries only.

## Tables

- `presentation_reviews`: review score and improvement summary.
- `presentation_revisions`: revision number, score, slide count deltas, status, approval state, selected actions, sanitized outline, and Beautiful.ai presentation ID/URLs.
- `presentation_revision_history`: safe add/delete/modify summary between revisions, before/after summaries, reason, and human action.

## Beautiful.ai Flow

The app does not redraw PowerPoint slides itself for the revision loop.

1. AI Presentation Review checks the proposal structure.
2. The user selects improvement actions.
3. The user creates a draft revision candidate.
4. A manager/admin approves the revision.
5. Beautiful.ai receives the revised structure for regeneration.
6. The revision is stored as a new version with a new presentation ID.

This keeps Beautiful.ai responsible for presentation design quality.

Existing Beautiful.ai presentations are never overwritten. Revision titles include the Proposal version.

## Diff Display

The UI compares two revisions and displays:

- Added items
- Removed items
- Modified items
- Before/after summary
- Reason
- Human action

The diff is intentionally summary-based. It must not expose full slide body text or customer confidential text.

## Approval

Admin and manager roles can approve a revision. Member users can create review and revision candidates but cannot approve revisions.

Viewer users can read timeline information only.

Beautiful.ai regeneration is restricted to manager/admin after approval.

## Analytics

Presentation Analytics summarizes:

- Average review score
- Review count
- Improvement count
- Revision count
- Added slide count
- Removed slide count
- Improvement adoption rate
- Beautiful.ai revision success rate
- Approval rate
- Unresolved issue count
- Generation failure count

## Production Checklist

Before enabling real Beautiful.ai production revision usage:

- Confirm `BEAUTIFUL_AI_ENABLED` and `BEAUTIFUL_AI_MOCK` settings.
- Confirm the real Beautiful.ai presentation ID is returned and saved.
- Confirm no API token is stored in presentation revision tables.
- Confirm revision approval permissions with admin, manager, member, and viewer users.
- Confirm `PRESENTATION_MAX_REVISIONS` prevents loops after the configured limit.
