# Proposal Optimization Engine

Version 20.0 adds a Proposal Optimization Engine that connects Presentation Review, Learning, Analytics, Beautiful.ai Revision metadata, and outcome signals.

The purpose is not to add a new sales AI employee. It is a continuous improvement layer that answers:

- Which proposal should be improved next?
- Which improvement is likely to have the highest impact?
- Which revision actions should be considered before Beautiful.ai regeneration?

## Inputs

The engine uses safe metadata only:

- Presentation Review scores and structured actions
- Revision status and selected action summaries
- Beautiful.ai revision success/failure metadata
- Learning aggregate metrics
- Analytics aggregate metrics
- Project outcome categories when available

It does not use or store full proposal text, full case emails, API keys, passwords, Beautiful.ai tokens, or raw Beautiful.ai responses.

## Output

The engine returns:

- Recommended improvements TOP5
- Priority
- Impact
- Confidence
- Expected improvement
- Effort
- Predicted win-rate delta
- Explanation
- Estimated simulation values

Simulation values are estimates and must be shown as estimates in the UI.

## Version 20.1 Evidence Governance

Each recommendation now separates measured values from estimated values.

Estimated values include:

- `is_estimate`
- `confidence`
- `sample_size`
- `evidence_type`
- `calculation_method`
- `generated_at`
- `requires_human_review`

The default minimum sample size is `OPTIMIZATION_MIN_SAMPLE_SIZE=10`.
When the sample size is below this threshold, the recommendation is treated as low-confidence and requires human review.

The engine must describe findings as tendencies or reference estimates, not as guaranteed causation.

## Permissions

- `member`: view and select recommendations.
- `manager`: approve recommendations.
- `admin`: approve and manage settings.
- `viewer`: view only.

Backend APIs enforce these permissions.

## Workspace Scope

All optimization records include:

- `organization_id`
- `workspace_id`

Users cannot read or update backlog items from another organization/workspace.

## Beautiful.ai Flow

The Optimization Engine improves only:

- Structure
- Story
- Headings
- CTA
- ROI
- Implementation plan

It does not generate visual design. Beautiful.ai remains responsible for presentation design quality.
