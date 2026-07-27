# Validation Rules

The validator checks:

- slide type is set
- slide intent is set
- reading order is stable
- diagram and chart are not both used as competing primary candidates
- chart is not selected when evidence is missing
- chart is not selected without numeric claims
- comparison visual has comparison basis
- timeline / roadmap has time sequence
- hierarchy has layer basis
- checklist has enough items
- image-dominant visual does not assume external image evidence
- information density is not excessive or insufficient
- internal labels or TODO text are not present
- offline boundary is preserved
- high confidence is not used when evidence is missing

Errors block downstream use. Warnings are review items for Phase 3.
