# Dependency Map

```mermaid
flowchart TD
  V81["V81 Design Foundation"] --> V82["V82 Proposal Studio"]
  V82 --> V83["V83 Save + Jobs"]
  V83 --> V84["V84 Knowledge AI"]
  V83 --> V85["V85 Proposal OS Core"]
  V85 --> V86["V86 Collaboration"]
  V86 --> V87["V87 Governance"]
  V85 --> V88["V88 Integrations"]
  V87 --> V89["V89 Scale"]
  V88 --> V89
  V89 --> V90["V90 External RC"]
```

## Critical Dependencies

- Proposal Studio requires ProposalVersion and SlidePlan.
- Job progress requires GenerationJob.
- Knowledge AI requires strict Workspace/Organization scoping.
- Collaboration requires object-level permissions.
- External RC requires observability and rollback.

