# Version 51 API Contract

## Status

`GET /api/sales-assistant/status`

Adds:

```json
{
  "proposal_preview_enabled": false
}
```

The value is controlled by `SALES_ASSISTANT_PROPOSAL_ENABLED`.

## Generate

`POST /api/sales-assistant/generate`

Still returns the Version 49 Sales Assistant Brief and now also returns the full Version 41 `strategy_brief` so the next step can reuse the same strategy without re-implementing strategy selection.

## Proposal Preview

`POST /api/sales-assistant/proposal-preview`

Admin-only. Requires both `SALES_ASSISTANT_ENABLED=true` and `SALES_ASSISTANT_PROPOSAL_ENABLED=true`.

Request:

```json
{
  "source_request": {},
  "sales_assistant_brief": {},
  "strategy_brief": {}
}
```

Response:

```json
{
  "proposal_preview": {
    "proposal_summary": "",
    "issues": [],
    "proposal_story": "",
    "proposal_policy": "",
    "slide_outline": [],
    "kpis": [],
    "estimate_summary": "",
    "deck_title": "",
    "client_name": "",
    "human_review_required": true,
    "human_review_reasons": [],
    "source_versions": {}
  },
  "proposal_response": {},
  "human_review_required": true,
  "human_review_reasons": [],
  "generation_metadata": {
    "persistence_enabled": false,
    "pptx_enabled": false,
    "beautiful_ai_enabled": false
  }
}
```

No DB persistence is performed by this endpoint.
