# Normalization Rules

The normalizer performs safe normalization only.

Allowed:

- trim leading and trailing whitespace
- collapse repeated spaces
- normalize line endings
- remove empty list items
- remove duplicate primitive list items
- normalize enum display labels to lowercase snake_case values
- normalize hex colors to `#RRGGBB`
- generate deterministic IDs when IDs are missing
- add default blueprint version
- add default empty diagram definition

Forbidden:

- rewrite business meaning
- fill missing content with AI
- invent numbers
- generate a headline
- change visual type without explicit input
- change customer-facing claims

The result keeps both the original and normalized payload for comparison.

