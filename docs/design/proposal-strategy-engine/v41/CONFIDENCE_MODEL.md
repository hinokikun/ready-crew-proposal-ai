# Confidence Model

Status: deterministic heuristic, not statistical model.

## Meaning

`confidence` represents strength of evidence for the selected Strategy Brief.

It does not represent:

- win probability
- ROI probability
- project success probability
- AI model confidence

## Positive Signals

Confidence increases when:

- project category is clear
- persona is explicit or strongly inferred
- current problem and proposed solution are both present
- deliverables, integrations, KPI, budget, or schedule are provided
- primary and secondary categories form a known compound pattern

## Negative Signals

Confidence decreases when:

- input is sparse
- category signals conflict
- persona is unknown
- budget exists but budget type is unclear
- prohibited or conflicting category terms appear
- important evidence is missing

## Human Review Threshold

Human review is required when confidence is below `0.62`.

The threshold is conservative because Version 41 is not connected to production and must be validated before implementation.
