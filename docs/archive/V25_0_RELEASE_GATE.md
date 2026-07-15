# Version 25.0 Release Gate

## 目的

正式版公開前に、技術確認・セキュリティ確認・UAT 確認を同じ基準で判定します。

## Gate A: Code Quality

- `python -m compileall app tests`
- `python -m pytest -q`
- `python -m pip check`
- `npm.cmd run typecheck`
- `npm.cmd run check:unused`
- `npm.cmd run build`
- `npm.cmd run test:e2e`
- `git diff --check`

すべて成功が必要です。

## Gate B: Security

- production CORS が Vercel 本番 URL のみを許可すること。
- `localhost` と `*` が production で許可されないこと。
- API キー、Password、Token、DATABASE_URL が画面・ログ・DB に平文保存されないこと。
- Security Headers が `/health` と `/api` に付与されること。
- admin / manager / member / viewer の API 権限が Backend で拒否されること。

## Gate C: Cloud

- GitHub Actions が最新 commit で成功
- Vercel Deployment が Ready
- Render Deploy が Live
- `/health` が確認可能
- `/health/ready` が `status: ok`
- Frontend / Backend commit の不一致警告がないこと

## Gate D: Product

- AI 提案書生成
- 要約PPTX
- 詳細PPTX
- 見積PDF
- Beautiful.ai
- Presentation Review
- Proposal Optimization
- Quality Gate
- 作成履歴
- 監査ログ

## 公開判定

| 判定 | 条件 |
| --- | --- |
| Go | Gate A-D がすべて合格 |
| Conditional Go | Cloud または UAT に軽微な未確認があるが重大項目は合格 |
| No Go | 権限漏れ、データ越境、ログイン不可、出力不可、Health 異常のいずれか |

## No Go 時の対応

1. 新規公開を止めます。
2. 原因を `request_id` とともに記録します。
3. `git revert <problem_commit>` で戻します。
4. force push は使用しません。
5. 修正後に Gate A から再実行します。
