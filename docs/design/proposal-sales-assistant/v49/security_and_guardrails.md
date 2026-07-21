# Security and Guardrails

## No secret handling

The offline generator does not accept credentials and does not log or persist output.

## No unsupported assertions

When evidence is missing, the output uses:

- confirmation required
- insufficient information
- hypothesis

## Term Guard

Generated guarded sections are checked against Strategy Brief prohibited terms:

- talk track
- objection handling
- decision maker support
- follow-up email
- next actions

When a prohibited term appears, the generator replaces it with a safe placeholder and marks human review as required.

