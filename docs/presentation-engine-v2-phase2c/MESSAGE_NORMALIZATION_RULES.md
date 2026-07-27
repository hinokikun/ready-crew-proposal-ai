# Message Normalization Rules

Normalization is intentionally safe and must not rewrite meaning.

## Allowed

- Trim surrounding whitespace
- Collapse repeated whitespace
- Normalize enum labels
- Remove duplicate supporting messages
- Remove duplicate evidence IDs
- Add deterministic input fingerprint
- Add deterministic message ID

## Forbidden

- Rewrite headline meaning
- Add evidence
- Add numbers
- Change slide goal
- Change message style without rule basis
- Summarize or paraphrase for meaning

