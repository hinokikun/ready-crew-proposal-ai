# Version52 Feature Flags

| Flag | Default | Area | API | Admin Only | Dependency |
| --- | --- | --- | --- | --- | --- |
| `USE_MOCK_AI` | `false` | Proposal output | `/api/analyze` | No | Local/test only |
| `MAINTENANCE_MODE` | `false` | generation/output | generation/output APIs | No | Incident operation |
| `PILOT_MODE` | `false` | Pilot panels | Pilot APIs | Admin actions | Pilot user settings |
| `BEAUTIFUL_AI_ENABLED` | `false` | Beautiful.ai | `/api/beautiful-ai/*` | Diagnostics admin-only | API key/config |
| `BEAUTIFUL_AI_MOCK` | `false` | Beautiful.ai diagnostics | `/api/beautiful-ai/*` | Diagnostics admin-only | Beautiful.ai enabled/config |
| `BEAUTIFUL_AI_API_MODE` | `prompt` | Beautiful.ai API mode | Beautiful.ai generation | Diagnostics admin-only | prompt/structured |
| `PRESENTATION_ENGINE_MODE` | `legacy` | Presentation path | PPT generator boundary | No | `legacy` is safe default |
| `SALES_ASSISTANT_ENABLED` | `false` | Sales Assistant API | `/api/sales-assistant/generate` | Yes | Backend admin auth |
| `SALES_ASSISTANT_PROPOSAL_ENABLED` | `false` | Proposal Preview | `/api/sales-assistant/proposal-preview` | Yes | `SALES_ASSISTANT_ENABLED=true` |
| `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED` | `false` | Admin UI | none | UI only | Backend flags must also be enabled |

Production defaults are intentionally conservative.
