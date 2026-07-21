# API Contract

## GET /api/sales-assistant/status

Admin only.

Response:

```json
{
  "enabled": false,
  "version": "50",
  "requires_admin": true,
  "persistence_enabled": false,
  "external_ai_enabled": false
}
```

## POST /api/sales-assistant/generate

Admin only and feature-flag gated.

Minimum request:

```json
{
  "project_title": "Project title",
  "project_summary": "Project summary",
  "meeting_stage": "preparation",
  "known_requirements": [],
  "known_constraints": [],
  "previous_interactions": [],
  "evidence_items": []
}
```

Response:

```json
{
  "sales_assistant_brief": {},
  "strategy_brief_summary": {},
  "warnings": [],
  "human_review_required": true,
  "human_review_reasons": [],
  "generation_metadata": {}
}
```

## Limits

- Request size: 64 KB
- `project_title`: 200 characters
- `project_summary`: 10,000 characters
- List count limits are enforced per field
- Control characters are removed

## Errors

- Disabled: 404 with `sales_assistant_disabled`
- Too large: 413 with `sales_assistant_request_too_large`
- Invalid input: 422 with `sales_assistant_input_error`
- Generation failure: 500 with `sales_assistant_generation_error`

Error responses do not include stack traces, API keys, tokens, or customer input全文.
