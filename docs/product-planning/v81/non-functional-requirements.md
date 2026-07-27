# Non Functional Requirements

| Area | 現状値 | 目標値 | 測定方法 | Release Condition |
|---|---|---|---|---|
| Performance | 未測定、一部E2Eは約20分 | ホーム初期表示を実務許容内 | Lighthouse/Playwright | regressionなし |
| Availability | 未測定 | 業務時間の安定稼働 | health/ready | health正常 |
| Scalability | SQLite/Render運用あり | PostgreSQL移行可能 | load test | DB選定 |
| Reliability | pytest/E2Eあり | 生成失敗時に入力保持 | failure E2E | retry導線 |
| Security | 認証/権限あり | Object Level認可強化 | security tests | secret漏えい0 |
| Privacy | 入力全文ログ禁止方針 | PII分類 | audit | log review |
| Accessibility | 部分対応 | WCAG主要導線 | axe/manual | keyboard操作 |
| Observability | logsあり | job/AI/費用監視 | dashboards | safe logs |
| Maintainability | AppShell巨大 | 機能単位分割 | dependency review | circularなし |
| Testability | 371 pytest, 66 E2E | fixture/golden強化 | CI | all green |
| Portability | Windows中心 | Render/Vercel/Postgres | deployment test | env docs |
| Backup | docsあり | restore rehearsal | runbook | rehearsal |
| Recovery | docsあり | feature flag rollback | UAT | rollback手順 |
| Cost Control | 未測定 | token/API費用記録 | metrics | alert設計 |

