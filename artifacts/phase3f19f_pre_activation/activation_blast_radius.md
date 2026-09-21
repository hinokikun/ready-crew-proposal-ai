# Activation Blast Radius

## Changes when the flag is ON

- Summary and Detail still use the existing role sequence and conditional generation rules.
- A role may use the approved Native renderer only when Human approval, template availability, contract, adapter, provenance, sample-leak, text-fit, and renderer gates all pass.
- `PROPOSAL_SUMMARY` is the first intended runtime role after its explicit Human Visual PASS.
- Evidence-sensitive roles with missing verified data continue through the existing renderer and are not omitted.
- A Native exception falls back for the same slide and does not abort the deck.

## Does not change

- `/api/download-pptx` and `/api/download-summary-pptx` request/response contracts.
- Auth, permissions, history logging, Quality Gate, Summary 11-slide contract, Detail conditional behavior, and download filenames.
- PDF generation, Frontend behavior, DB schema/data, Backend business data model, and Beautiful.ai paths.
- Frozen Native templates and Canonical sources.

The user-visible change is limited to eligible approved Native slide rendering. Blocked or failed roles retain the current renderer output.
