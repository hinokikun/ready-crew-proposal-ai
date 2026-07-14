# Proposal Optimization Acceptance & Evidence Governance

Version 20.1 hardens the Version 20.0 Proposal Optimization Engine for production-style operation.

This is not a new sales feature. It improves safety, explainability, evidence handling, state transitions, and acceptance criteria around proposal optimization.

## Version 20.0 Audit Result

| Area | Status | Notes |
|---|---|---|
| `proposal_improvement_backlog` | Accepted with 20.1 hardening | Added evidence, estimate, measurement, and transition governance. |
| `proposal_best_practices` | Accepted with 20.1 hardening | Added approval status, quality metadata, duplicate keys, and approval controls. |
| Proposal Optimization API | Accepted with changes | Added transition validation, measurement endpoint, revision-action bridge, and best-practice approval endpoint. |
| Presentation Review integration | Accepted | Uses existing Review/Revision APIs. No duplicate revision system was added. |
| Learning / Analytics integration | Accepted as aggregate metadata | Uses safe counts and rates only. |
| Beautiful.ai Revision metadata | Accepted | Optimization improves structure/story/CTA/ROI/roadmap only; Beautiful.ai remains responsible for design. |
| Organization / Workspace scope | Accepted | All records include `organization_id` and `workspace_id`; API reads and writes are scoped by authenticated user context. |
| Security | Accepted with caution | Full proposal text, customer body text, API keys, tokens, and Beautiful.ai raw responses are not stored. |

## Measured Values vs Estimated Values

Measured values are calculated from observed system data:

- Backlog selection rate
- Manager/admin approval rate
- Revision count
- Generated revision count
- Quality Gate / Review metadata when available
- Recorded measurement results

Estimated values are rule/AI-assisted reference estimates:

- Predicted win-rate delta
- Predicted review count reduction
- Predicted proposal time reduction
- Predicted Quality Gate improvement

Every estimated value includes:

- `is_estimate`
- `confidence`
- `sample_size`
- `evidence_type`
- `calculation_method`
- `generated_at`
- `requires_human_review`

Estimated values must not be displayed as guaranteed outcomes.

## Evidence Types

The engine classifies evidence as:

- `workspace_history`
- `organization_history`
- `approved_knowledge`
- `presentation_review`
- `project_outcome`
- `quality_gate`
- `review_feedback`
- `rule_based`
- `ai_estimate`
- `insufficient_data`

Evidence displays must explain:

- Why the recommendation was generated
- Which safe data category was used
- Sample size
- Evidence period
- Confidence
- Whether the value is an estimate
- Whether human review is required

Customer names, full proposal text, and case email bodies must not be included in evidence displays.

## Sample Size Rule

Default minimum:

```text
OPTIMIZATION_MIN_SAMPLE_SIZE=10
```

When sample size is below the threshold:

- Do not present predicted win-rate impact as a confirmed metric.
- Mark the recommendation as `ai_estimate` or `insufficient_data`.
- Lower confidence.
- Set `requires_human_review=true`.
- Display a low-sample warning.

## Causality Rule

The UI and API wording must not claim causation unless causation was verified.

Allowed:

> Proposals with ROI explanation showed a higher win-rate tendency in the available metadata.

Not allowed:

> Adding ROI slides increased win rate by 12%.

## Backlog Status Flow

Allowed statuses:

- `suggested`
- `selected`
- `approved`
- `in_revision`
- `applied`
- `measured`
- `rejected`
- `archived`

Expected flow:

```text
suggested -> selected -> approved -> in_revision -> applied -> measured
```

Invalid transitions return HTTP 409.

Legacy status mapping:

- `open` -> `suggested`
- `adopted` -> `selected`
- `done` -> `applied`
- `deferred` -> `archived`

## Best Practice Approval Flow

Allowed statuses:

- `draft`
- `pending_review`
- `approved`
- `rejected`
- `archived`

AI may reference only `approved` best practices.

Permissions:

- `member`: view approved best practices only.
- `manager`: approve/reject/archive.
- `admin`: approve/reject/archive and review all.
- `viewer`: read only.

Duplicate detection keys:

- Category
- Normalized title
- Tags
- Structure summary
- CTA type
- Slide order pattern

## Optimization Score Formula

The score uses configurable weights:

```text
optimization_score =
impact * 0.30
+ confidence * 0.25
+ urgency * 0.20
+ historical_adoption * 0.15
- effort * 0.10
```

Environment variables:

- `OPTIMIZATION_WEIGHT_IMPACT`
- `OPTIMIZATION_WEIGHT_CONFIDENCE`
- `OPTIMIZATION_WEIGHT_URGENCY`
- `OPTIMIZATION_WEIGHT_ADOPTION`
- `OPTIMIZATION_WEIGHT_EFFORT`

Weights are normalized in code so the calculation remains stable.

## Permissions

- `viewer`: read only.
- `member`: view recommendations, select improvements, request revision bridge actions.
- `manager`: approve improvements, approve best practices, record measurements.
- `admin`: all manager permissions plus system-scope analytics and configuration.

Backend APIs enforce permission checks. Frontend-only checks are not trusted.

## Production Risks Before Full Rollout

- Predicted effects are estimates and need human review.
- Some analytics remain metadata-based until enough pilot data is collected.
- Cloud verification must be run after deployment; local tests do not prove Vercel/Render state.
- Real Beautiful.ai behavior must be checked with a safe test presentation before customer use.
