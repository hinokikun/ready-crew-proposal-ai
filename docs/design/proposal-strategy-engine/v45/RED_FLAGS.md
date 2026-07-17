# Red Flags

Red flags identify issues that score alone may hide.

| Code | Severity | Meaning |
|---|---|---|
| `evidence_insufficient` | high | Evidence is missing or only inferred. |
| `kpi_missing` | high | KPI pack or KPI slide coverage is missing. |
| `risk_missing` | medium | Risk messages are missing. |
| `story_inconsistent` | high | Strategy Brief story differs from Presentation Context. |
| `review_not_approved` | critical | Human Review is not approved. |
| `cta_missing` | medium | Next actions are missing. |

## Handling

Critical:

- Do not pass to presentation generation.
- Return to Human Review.

High:

- Correct the Strategy Brief, review result, or Presentation Context before generation.

Medium:

- Sales reviewer can approve only with clear reason.
