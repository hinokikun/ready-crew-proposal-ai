# Version52 Monitoring Design

Monitoring is not implemented in Version52. The following signals should be added in a later release.

## API

- `/api/sales-assistant/generate` request count
- `/api/sales-assistant/generate` error rate
- `/api/sales-assistant/proposal-preview` request count
- `/api/sales-assistant/proposal-preview` error rate
- p95 latency by endpoint

## Quality

- Human Review required count
- Human Review reason distribution
- Proposal Preview retry count
- Feature Flag enabled sessions

## Safety

- 401/403 count
- 413 large input count
- 422 validation count
- 500 internal error count
- redacted error samples

## Business

- Proposal Preview generated count
- Preview-to-output conversion rate after Version52
- fallback to legacy proposal generation
