# Known Issues

## Release Blockers

None as of Version 2.2 production release preparation.

## Operational Constraints

| Area | Constraint | Recommended Action |
|---|---|---|
| Final customer submission | AI output is customer-ready by automated checks, but customer names, facts, numbers, and contractual conditions still require human confirmation. | Sales user performs final review before sending. |
| Database | SQLite is suitable for local development. Render's default filesystem is not durable for production SQLite. | Use PostgreSQL or a persistent disk. |
| Beautiful.ai | Availability depends on external API, workspace, and returned URL fields. | Keep PowerPoint download as fallback. |
| OpenAI | Latency and quality can vary by model, prompt, and input quality. | Monitor generation time and keep `USE_MOCK_AI` available for demos. |
| Rendering | LibreOffice rendering can differ from Microsoft PowerPoint in small font and layout details. | Confirm representative customer decks in PowerPoint before official rollout. |
| Feature flags | Frontend flags are display helpers. Backend flags and roles are authoritative. | Manage flags in Backend environment variables. |
| Large input | Very large pasted text can increase generation time or hit request limits. | Ask users to paste relevant meeting notes and requirements only. |
| External URLs | Beautiful.ai edit/view URLs must come from API response. | Do not construct Beautiful.ai URLs from presentation IDs. |

## Human Review Items

- Customer name and proposal target are correct.
- KPI current value, target value, measurement timing, and owner are realistic.
- ROI assumptions and estimate scope are aligned with the customer.
- Schedule and implementation scope are feasible.
- Security, operations, and integration risks are explained.
- No internal notes or mock values remain in the proposal.

## Monitoring Items

- Backend health and ready status.
- Login failures and role errors.
- Proposal generation errors.
- Customer Ready NOT_READY / REVIEW_REQUIRED rates.
- PPTX/PDF download failures.
- Beautiful.ai API errors and missing URL responses.
- Database connection errors.
- Average generation time.

## Deferred Improvements

- Persistent production storage policy for generated files.
- Automated production dashboard for Customer Ready and proposal generation metrics.
- Formal Microsoft PowerPoint rendering comparison in a Windows Office automation environment.
- Expanded support playbook for customer-specific deployment variations.
