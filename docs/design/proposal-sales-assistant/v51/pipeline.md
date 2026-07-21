# Version 51 Pipeline

## Integration Boundary

The Proposal Preview endpoint converts the Sales Assistant input into the existing `ProposalRequest` model and calls `app.services.openai_service.generate_proposal`.

It does not call `/api/analyze` because that route also handles project persistence and creation history. Version 51 intentionally returns a preview only.

## Reused Inputs

Strategy Brief is preferred for:

- strategy
- story
- persona
- decision maker
- KPI pack
- estimate pack
- priority messages
- risk messages
- required slide types

Sales Assistant Brief is used as supplemental context for:

- meeting goal
- customer pain
- objections
- recommended positioning
- next actions
- human review reasons

## Non-Scope

- PPTX generation
- Beautiful.ai generation
- email sending
- DB save
- creation history
- learning feedback
- dashboard analytics
- new OpenAI integration logic
