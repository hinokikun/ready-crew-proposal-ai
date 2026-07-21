# UAT Result Template

ProposalPilot Release Candidateの社内UAT結果を記録するためのテンプレートです。実顧客情報、APIキー、Password、Token、個人情報、顧客本文全文は記載しないでください。

## 基本情報

| 項目 | 記入 |
| --- | --- |
| UAT ID |  |
| 実施日 |  |
| 実施者 |  |
| 環境 | local / Render + Vercel / other |
| Frontend Version |  |
| Backend Version |  |
| Browser |  |
| Role | admin / manager / member / viewer |
| Organization |  |
| Workspace |  |

## Feature Flag

| Flag | 値 |
| --- | --- |
| SALES_ASSISTANT_ENABLED |  |
| SALES_ASSISTANT_PROPOSAL_ENABLED |  |
| PROPOSAL_EXPORT_ENABLED |  |
| NEXT_PUBLIC_SALES_ASSISTANT_ENABLED |  |
| NEXT_PUBLIC_PROPOSAL_EXPORT_ENABLED |  |
| BEAUTIFUL_AI_ENABLED |  |
| USE_MOCK_AI |  |

## 確認結果

| No | 項目 | 結果 | コメント |
| --- | --- | --- | --- |
| 1 | ログイン | OK / Partial / NG |  |
| 2 | Sales Assistant | OK / Partial / NG |  |
| 3 | Proposal Preview | OK / Partial / NG |  |
| 4 | Human Review | OK / Partial / NG |  |
| 5 | PowerPoint Export | OK / Partial / NG |  |
| 6 | PPTX Download | OK / Partial / NG |  |
| 7 | Beautiful.ai | OK / Partial / NG / N/A |  |
| 8 | 権限 | OK / Partial / NG |  |
| 9 | 既存7ステップUI | OK / Partial / NG |  |
| 10 | モバイル表示 | OK / Partial / NG |  |

## 指標

| 指標 | 値 |
| --- | --- |
| 重大障害件数 |  |
| Major件数 |  |
| Minor件数 |  |
| 改善要望件数 |  |
| Export成功率 |  |
| Human Review承認率 |  |
| PPTXダウンロード成功率 |  |
| Beautiful.ai成功率 |  |

## 判定

- 総合判定: Go / Conditional Go / No-Go
- 判定理由:
- 次Versionへ回す項目:

## 添付

- Screenshot:
- Browser Console:
- Backend log summary:
- issue_backlog ID:
