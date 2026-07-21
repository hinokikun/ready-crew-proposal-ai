# Version52 Performance Review

Measurement date: 2026-07-19 JST

Environment:

- Local TestClient
- SQLite temporary DB
- `USE_MOCK_AI=true`
- 5 repeated iterations
- no external OpenAI call
- no Beautiful.ai call

## Results

| Item | Average | Max |
| --- | ---: | ---: |
| Sales Assistant generation | 10.08 ms | 13.51 ms |
| Proposal Preview generation | 18.04 ms | 18.66 ms |
| large input rejection | 5.06 ms | n/a |

## Notes

These are local Mock AI measurements. Production OpenAI latency, Render cold starts, Vercel network latency, and database latency must be measured separately.

## Performance Risks

- Proposal Preview calls the existing Proposal Generator and may be slower when real OpenAI is enabled.
- Consecutive admin generation should remain rate-limited.
- Very large inputs are rejected before generation.
