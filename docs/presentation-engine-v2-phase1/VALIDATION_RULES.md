# Validation Rules

Validation includes schema and semantic checks.

## Severity

- `error`: blocks render readiness
- `warning`: requires review but does not block contract validity
- `info`: informational only

## Error code families

- `PE2-SCHEMA-*`
- `PE2-MESSAGE-*`
- `PE2-VISUAL-*`
- `PE2-LAYOUT-*`
- `PE2-QUALITY-*`
- `PE2-SAFETY-*`

## Main rules

- headline must not be empty
- invalid enum values are rejected
- unsupported blueprint versions are rejected
- duplicate internal IDs are rejected
- placeholder labels such as `Metric 1` and `TBD` are rejected
- visual type and diagram type must be compatible
- comparison slides require comparison items
- timeline and roadmap slides require timeline items
- process slides require process steps
- matrix slides require axis definitions
- table visuals require columns and rows
- metric-oriented slides require metric blocks
- next-action slides require CTA
- safe area must stay inside slide bounds
- extremely small body font is rejected

