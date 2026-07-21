# ProposalPilot Version49 AI Sales Assistant

Version49 adds an offline AI Sales Assistant contract and deterministic generator. It consumes the existing Version41 Strategy Brief as its primary source and produces a Sales Assistant Brief for meeting preparation, discovery, objection handling, decision-maker support, evidence guidance, next actions, and follow-up drafting.

This package is intentionally not connected to production APIs, Frontend, DB, Migration, PPTX generation, Beautiful.ai, OpenAI, or the existing Proposal generation flow.

## Boundary

- Input: Strategy Brief plus supplemental sales context.
- Output: JSON-serializable Sales Assistant Brief.
- Runtime: deterministic Python code only.
- Side effects: none.
- Network: none.

## Files

- `backend/app/sales_assistant/`: offline contract, generator, evaluator, fixtures.
- `backend/tests/sales_assistant/`: pytest coverage and Golden JSON.
- `docs/design/proposal-sales-assistant/v49/`: design documents.

