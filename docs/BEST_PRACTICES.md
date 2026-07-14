# Best Practice Library

Version 20.0 adds a safe Best Practice Library for proposal optimization.

The library stores reusable patterns learned from approved or generated Presentation Revisions. It is designed to improve future recommendations without saving customer-confidential proposal text.

## Stored Data

Allowed fields:

- Category
- Title
- Pattern summary
- Source type
- Success metric
- Confidence
- Adoption count
- Organization ID
- Workspace ID

Forbidden data:

- Full proposal body text
- Full case emails
- Customer names or private customer information
- Phone numbers and email addresses
- API keys
- Passwords
- Beautiful.ai tokens
- Raw Beautiful.ai response bodies

## Source

Best practices are extracted from safe revision metadata:

- Selected revision actions
- Generated revision status
- Adoption count
- Aggregated optimization metadata

The system stores reusable structure only, such as:

- Successful proposal order
- Successful CTA pattern
- Successful ROI structure
- Successful implementation roadmap pattern
- Frequently useful FAQ additions

## Approval Flow

Best practices are not available to AI recommendations immediately after extraction.

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
- `admin`: approve/reject/archive and audit.
- `viewer`: read only.

Review fields:

- Evidence count
- Evidence period
- Workspace
- Confidential risk
- Quality score
- Prediction flag
- Approval reason
- Rejection reason

## Duplicate Control

Duplicate detection uses safe structural fields:

- Category
- Normalized title
- Tags
- Structure summary
- CTA type
- Slide order pattern

When a duplicate is found, the existing pattern is updated instead of creating many similar records.

## Workspace Separation

Every best practice record is scoped by:

- `organization_id`
- `workspace_id`

Users can only view best practices for their current workspace. Cross-organization access must be rejected by the backend.

## Operations

Recommended flow:

1. Create a proposal.
2. Run Presentation Review.
3. Create and approve a safe Revision.
4. Generate the Revision through Beautiful.ai.
5. Extract safe patterns into the Best Practice Library.
6. Use those patterns in future Proposal Optimization recommendations.

## Human Review

Best practices are recommendations, not automatic truth. A human reviewer should check that the pattern is still appropriate before it is used in customer-facing proposals.
