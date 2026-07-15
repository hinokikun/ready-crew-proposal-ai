# Version 25.0 Production Runbook

## 毎日確認すること

1. Render が Live であること。
2. Vercel が Ready であること。
3. `/health` と `/health/ready` を確認すること。
4. 管理者ダッシュボードで直近エラーと Beautiful.ai 診断を確認すること。
5. 監査ログに権限外アクセスや連続失敗がないこと。

## 障害時の初動

1. 画面の日本語エラーと `request_id` を控えます。
2. Role、Organization、Workspace、操作内容を控えます。
3. Render Logs で同じ `request_id` を検索します。
4. Beautiful.ai 失敗時は管理者診断の直近20件を確認します。
5. 重大障害の場合は Maintenance Mode を有効化します。

## 重大障害の例

- ログイン不能
- Backend 全体停止
- DB 接続不能
- Organization / Workspace 越境
- viewer が生成できる
- PPTX / PDF が連続失敗
- Beautiful.ai が連続失敗
- 秘密情報がログへ出た疑い

## Maintenance Mode で止めるもの

- 新規提案書作成
- PPTX / PDF 新規生成
- Beautiful.ai 新規生成
- Orchestrator 新規実行

## Maintenance Mode 中も使えるもの

- ログイン
- CRM 閲覧
- 作成履歴
- 監査ログ
- 管理者診断
- `/health`
- `/health/ready`

## 復旧確認

1. `/health/ready` が `status: ok`
2. admin / member / viewer のログイン確認
3. Quality Gate 確認
4. 要約PPTX、詳細PPTX、見積PDF の安全なテスト出力
5. Beautiful.ai の接続テスト
6. 監査ログに復旧操作が残っていること

## 共有禁止情報

- API キー
- Password
- Token
- Authorization header
- DATABASE_URL
- 実顧客名
- 実メール本文
- 生成本文全文
