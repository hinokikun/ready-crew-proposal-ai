# OPERATIONS

## 日次運用

- `/health` でBackend、DB、AI API、PPTX、PDFの状態を確認する
- 管理者メニューで利用状況、エラー、フィードバック、監査ログを確認する
- Review / Quality Gate が未完了の案件を確認する
- 外部連携候補は承認後に案件化する

## 権限

- `admin`: 全機能、ユーザー管理、監査ログ、リリース管理、Prompt Studio
- `manager`: レビュー、リリース承認、一部管理ダッシュボード
- `member`: 通常作業、提案書作成、PPT/PDF、レビュー依頼
- `viewer`: 閲覧のみ。生成、編集、承認は不可

Backend API側でも権限を確認します。Frontendの表示制御だけに依存しません。

## 管理者メニュー分類

管理者メニューは初期状態では折りたたみ、次のカテゴリに整理します。

- 運用管理: ユーザー管理、監査ログ、リリース管理、運用準備チェック
- 改善分析: Product Analytics、Learning Dashboard、Prompt Studio、改善提案
- ナレッジ管理: Knowledge、テンプレート、承認待ち
- 外部連携: Integration、Dry Run、Connector Readiness
- 案件管理: CRM、Project Lifecycle、Review、Quality Gate
- AI実験/Prompt管理: Prompt Version、Experiment、Rollback

## 最重要動線の手動E2Eチェック

リリース前に、少なくとも次を手動確認してください。

- ログインできる
- 案件メールを貼り付けできる
- AI Workspaceが進行する
- 提案書を作成できる
- 提出前品質ゲートを確認できる
- 要約PPTをダウンロードできる
- 詳細PPTをダウンロードできる
- 見積PDFをダウンロードできる
- 上司レビューを依頼できる
- CRMに保存される
- AI通知が表示される
- 管理者メニューを閲覧できる

## エラー時の画面確認

以下の状態で、画面全体が落ちず、日本語で次の行動が表示されることを確認してください。

- Backend未接続
- 認証期限切れ
- OpenAI API上限
- PPT生成失敗
- PDF生成失敗
- 権限不足
- DB接続失敗

## バックアップ

SQLite利用時は `backend/app.db` を定期バックアップしてください。Render無料環境では永続化が保証されない場合があります。正式運用ではRender PostgreSQL、Supabase、Neonなどを推奨します。
# RC1 Operations Checklist

正式運用前に以下を確認してください。

## 毎回のリリース前

1. DBバックアップを取得する。
2. `python -m alembic upgrade head` を実行する。
3. Backendをデプロイする。
4. `/health/ready` が `status: ok` であることを確認する。
5. Frontendをデプロイする。
6. Cloud Smoke Testを実行する。
7. ログイン、案件メール貼り付け、提案書作成、要約PPT、詳細PPT、見積PDFを確認する。
8. 監査ログにログイン・生成・Maintenance操作が残ることを確認する。
9. 異常時はRollback判断を行う。

## Maintenance Mode

- 環境変数 `MAINTENANCE_MODE=true` が最優先です。
- 環境変数で有効化されている場合、画面から解除できません。
- 画面から有効化した場合も、Backendで新規生成系APIを503拒否します。

## Rate Limit運用

環境変数で調整できます。

- `RATE_LIMIT_LOGIN_LIMIT`
- `RATE_LIMIT_LOGIN_WINDOW_SECONDS`
- `RATE_LIMIT_GENERATION_LIMIT`
- `RATE_LIMIT_GENERATION_WINDOW_SECONDS`
- `RATE_LIMIT_ADMIN_LIMIT`
- `RATE_LIMIT_ADMIN_WINDOW_SECONDS`

過剰な429が出る場合は、利用者数と操作頻度を確認してから値を調整してください。
