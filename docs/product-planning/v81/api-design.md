# API Design

## Future Proposal APIs

| Method | Path | Purpose | Role | Request | Response | Status |
|---|---|---|---|---|---|---|
| POST | `/api/proposals` | Proposal draft作成 | member+ | ProposalBrief | Proposal | new |
| GET | `/api/proposals` | 一覧 | member+ | query | list | new |
| GET | `/api/proposals/{id}` | 詳細 | member+ | none | ProposalDetail | new |
| PATCH | `/api/proposals/{id}` | metadata更新 | member+ | patch | Proposal | new |
| POST | `/api/proposals/{id}/versions` | Version作成 | member+ | ProposalVersion | version | new |
| GET | `/api/proposals/{id}/versions/{version}` | Version取得 | member+ | none | version | new |
| POST | `/api/proposals/{id}/story` | Story生成 | member+ | ProposalBrief | StoryPlan | new |
| PATCH | `/api/proposals/{id}/slides/{slide_id}` | Slide編集 | member+ | SlidePatch | SlidePlan | new |
| POST | `/api/proposals/{id}/quality` | 品質評価 | member+ | version_id | QualityReport | new |
| POST | `/api/proposals/{id}/exports/pptx` | PPTX生成 | member+ | ExportRequest | GenerationJob/Artifact | extend |
| POST | `/api/proposals/{id}/exports/pdf` | PDF生成 | member+ | ExportRequest | GenerationJob/Artifact | extend |
| POST | `/api/proposals/{id}/exports/beautiful-ai` | Beautiful.ai | member+ | ExportRequest | Artifact | extend |

## Error Model

```json
{
  "error_type": "INPUT_REQUIRED",
  "message": "案件名を入力してください。",
  "request_id": "req_xxx",
  "status": 400,
  "details": {}
}
```

秘密情報と入力全文は`details`へ含めない。

## Long Running Generation

同期API維持:

- 長所: 実装が簡単、既存互換。
- 短所: timeout、再試行、進捗が弱い。

Job方式:

- 長所: 進捗、再試行、キャンセル、監視が可能。
- 短所: DB tableとpolling/SSEが必要。

推奨: Version83でJob方式を追加し、既存同期APIは互換として残す。

