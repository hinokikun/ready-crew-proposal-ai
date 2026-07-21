# Feature Flag Matrix

| Flag | Default | 対象 | 必要条件 |
| --- | --- | --- | --- |
| `SALES_ASSISTANT_ENABLED` | false | Sales Assistant生成 | admin |
| `SALES_ASSISTANT_PROPOSAL_ENABLED` | false | Proposal Preview | Sales Assistant enabled、admin |
| `PROPOSAL_EXPORT_ENABLED` | false | PowerPoint/Beautiful.ai Export | Proposal Preview enabled、admin |
| `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED` | false | Frontend表示 | backend flagと併用 |
| `BEAUTIFUL_AI_ENABLED` | false | Beautiful.ai実生成 | Beautiful.ai設定 |
| `USE_MOCK_AI` | false | Mock生成 | 本番では原則false |

Version54では`PROPOSAL_EXPORT_ENABLED`がfalseの場合、Export APIとダウンロードAPIはいずれも利用できない。
