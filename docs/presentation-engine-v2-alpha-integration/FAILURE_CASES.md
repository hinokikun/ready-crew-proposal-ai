# Failure Cases

Failure fixtures intentionally include:

- Missing Proposal Context
- Empty integration case ID
- Version mismatch
- Extra property
- Empty project summary
- Proposal Context extra property
- Too many problems
- Too many expected outcomes
- Case name too long
- Too many review tags
- Too many available evidence entries
- Too many constraints
- Invalid language
- Budget range too long
- Non-object Proposal Context

These are schema and input failures. Cross-module runtime failures are tested by mutating generated outputs in unit tests.

