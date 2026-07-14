# Presentation Review

Version 19.1 stabilizes the AI Presentation Review step after proposal generation in AI Workspace. The goal is to help users notice weak points, choose only the improvements they want, and create an approved Beautiful.ai revision as a separate presentation.

## What It Reviews

The reviewer evaluates generated proposal slide structure and metadata, not the full slide body text.

- Missing slides
- Duplicate slides
- Logical gaps
- Weak persuasion
- Missing numbers
- Missing ROI
- Weak competitor comparison
- Missing risk explanation
- Missing implementation schedule
- Missing CTA
- Missing summary

## Scores

Each review returns 1.0 to 5.0 scores for:

- Story
- Persuasion
- Issue understanding
- ROI
- Competitor comparison
- Implementation plan
- Design
- Risk
- CTA
- Summary

Each score includes a short reason, evidence summary, confidence, and a `requires_human_review` flag. The UI shows these as star-style score rows and an average score.

## Improvement Candidates

The reviewer returns short selectable improvement actions such as:

- Add slide
- Delete candidate
- Merge candidate
- Heading improvement
- Copy improvement
- Chart addition
- Number addition
- Case study addition
- FAQ addition
- Implementation roadmap addition
- ROI addition
- Price comparison addition
- Competitor comparison addition
- Q&A addition

The app does not automatically send these actions to Beautiful.ai. A user must select actions and create a draft revision first.

## Security Policy

The backend stores only structured review data:

- Scores
- Issue categories
- Short improvement summaries
- Slide counts
- Revision numbers
- Approval state
- Beautiful.ai presentation ID
- Editor/player URLs for generated revisions
- Revision status and approval metadata

The backend must not store:

- Full proposal body text
- Full slide text
- Customer confidential information
- API keys
- Beautiful.ai tokens
- Passwords

## Organization / Workspace Isolation

Presentation reviews are scoped by `organization_id` and `workspace_id`. A user can only read and write reviews in their current organization/workspace context.

## Learning Engine Integration

The Learning Engine receives only aggregated metrics:

- Review count
- Average review score
- Review issue count
- Revision count
- Improvement adoption rate
- Beautiful.ai revision success rate
- Approval rate
- Unresolved issue count
- Added slide count
- Removed slide count

It does not receive or persist customer text or full proposal content.

## Human Confirmation

Before production use, confirm:

- Scores match the expected proposal quality criteria.
- Improvement candidates do not expose confidential information.
- Beautiful.ai real API revision flow works with the current production account.
- Workspace isolation is verified with at least two organizations.
- v1 and v2 are separate Beautiful.ai presentation IDs.
- `PRESENTATION_MAX_REVISIONS` is configured if the default of 3 is not appropriate.
