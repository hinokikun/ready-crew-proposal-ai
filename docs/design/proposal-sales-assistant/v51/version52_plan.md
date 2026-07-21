# Version 52 Candidate Scope

Version 51 stops at Proposal Preview. Version 52 can connect an approved Proposal Preview to output generation after human approval.

Candidate work:

- connect Proposal Preview to PPTX generation
- connect Proposal Preview to Beautiful.ai generation
- decide whether preview results should be saved
- add audit logging for preview-to-output handoff
- define workspace-scoped history behavior

The Version 51 endpoint already marks:

- `persistence_enabled=false`
- `pptx_enabled=false`
- `beautiful_ai_enabled=false`

Those values should remain false until Version 52 explicitly changes the scope.
