# Version 1.0 Release Notes

Release date: 2026-07-16

## Summary

AI営業秘書 Version 1.0 is the first production-ready release candidate for limited customer rollout. It focuses on stable proposal generation, guided user workflow, output governance, Beautiful.ai integration, role-based operations, auditability, and release readiness.

## Highlights

- Simple 7-step guided proposal workflow for general users
- Proposal generation from pasted project notes, emails, and meeting memos
- Summary PowerPoint, detailed PowerPoint, and estimate PDF output
- Beautiful.ai Prompt API integration with diagnostics and history
- Human-in-the-loop Quality Gate before external submission
- Presentation Review, Revision, and Proposal Optimization support
- Creation history and artifact history
- Admin user management and password reset operations
- Role separation for admin, manager, member, and viewer
- Organization / Workspace isolation
- Audit logs for login, generation, output, settings, and errors
- Maintenance Mode and production runbooks
- Production CORS and Security Headers hardening

## Supported roles

| Role | Main use |
| --- | --- |
| admin | Full administration, user management, diagnostics, audit logs |
| manager | Review and operational oversight without secret settings |
| member | Proposal creation and outputs within assigned workspace |
| viewer | Read-only access |

## Production readiness

Version 25 RC1 audit classified the system as suitable for limited customer rollout after cloud confirmation. Critical release blockers were not found in local verification.

Before production rollout, confirm:

1. GitHub Actions success
2. Vercel Ready
3. Render Live
4. `/health`
5. `/health/ready`
6. admin/member/viewer login
7. Quality Gate
8. PPTX/PDF output
9. Beautiful.ai output
10. Audit logs
11. Organization / Workspace isolation

## Known limitations

- Full SaaS billing is not included.
- SSO/OIDC is not included.
- PostgreSQL production migration is prepared but not mandatory for this release.
- External Gmail/Slack/Calendar OAuth integration is not active.
- Cloud monitoring and SLO reporting should be added before broad SaaS sales.

## Upgrade notes

No destructive DB migration is required for Version 1.0 release preparation. Existing Version 25 RC1 deployments can use the same API and DB contracts.

## Security notes

- API keys must remain in Render environment variables only.
- Beautiful.ai API keys must not be configured in Vercel or `NEXT_PUBLIC_*` variables.
- Passwords, tokens, customer full body text, and generated full text must not be stored in logs.
- Production CORS should allow only the Vercel production domain.
