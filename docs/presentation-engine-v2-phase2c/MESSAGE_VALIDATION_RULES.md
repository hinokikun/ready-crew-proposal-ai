# Message Validation Rules

## Schema

Pydantic models reject missing required fields, invalid enum values, and extra properties.

## Content Validation

The validator checks:

- required fields
- version mismatch
- headline empty, too long, or noun-only
- main message empty, too long, or duplicated
- support count, length, and duplicates
- weak or ambiguous language
- placeholders and internal labels
- unsupported numeric, ROI, ratio, currency, or period claims
- evidence alignment and missing disclosure

## Error Codes

Codes are namespaced with `PE2-MSG-*`, for example:

- `PE2-MSG-SCHEMA-001`
- `PE2-MSG-HEADLINE-001`
- `PE2-MSG-MAIN-001`
- `PE2-MSG-SUPPORT-001`
- `PE2-MSG-EVIDENCE-001`
- `PE2-MSG-NUMERIC-001`
- `PE2-MSG-PLACEHOLDER-001`

