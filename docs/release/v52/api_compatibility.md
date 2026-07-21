# Version52 API Compatibility

## Version41

`StrategyBrief` schema version remains `strategy_brief_v1`.

## Version49

`SalesAssistantBrief` generator version remains `v49_offline_deterministic`.

## Version50

`GET /api/sales-assistant/status` remains compatible and adds the optional `proposal_preview_enabled` field.

`POST /api/sales-assistant/generate` remains compatible and adds the full `strategy_brief` object for downstream reuse.

## Version51

`POST /api/sales-assistant/proposal-preview` is a new admin-only endpoint behind `SALES_ASSISTANT_PROPOSAL_ENABLED`.

## Breaking Change Review

- Existing proposal generation endpoint is not changed.
- Existing PPTX and PDF paths are not changed.
- Existing Beautiful.ai paths are not changed.
- Existing Sales Assistant response keys remain present.
- Added fields are additive.
