# Ready Crew Proposal AI 管理者向け運用手順

この文書は、社内研修課題提出版を安全に運用するための管理者向け手順です。環境変数の実値、パスワード、APIキー、シークレットは記載しません。

## 1. VercelとRenderの構成

- Frontend: VercelでNext.jsアプリを配信します。
- Backend: RenderでFastAPIアプリを配信します。
- Frontendは `NEXT_PUBLIC_API_BASE_URL` でBackend URLを参照します。

## 2. FrontendとBackendの接続

1. Vercelの環境変数 `NEXT_PUBLIC_API_BASE_URL` がRender Backend URLを指していることを確認します。
2. Backendの `/health` と `/health/ready` を確認します。
3. ログイン後、Beautiful.ai診断またはシステム診断でBackend疎通を確認します。

## 3. 必要な環境変数名

| 区分 | 変数名 | 用途 |
| --- | --- | --- |
| Backend | `APP_AUTH_SECRET` | 認証トークン署名 |
| Backend | `INITIAL_ADMIN_EMAIL` | 初期管理者作成用メールアドレス |
| Backend | `INITIAL_ADMIN_PASSWORD` | 初期管理者作成用パスワード |
| Backend | `OPENAI_API_KEY` | OpenAI利用 |
| Backend | `BEAUTIFUL_AI_API_KEY` | Beautiful.ai利用 |
| Backend | `BEAUTIFUL_AI_ENABLED` | Beautiful.ai有効化 |
| Backend | `BEAUTIFUL_AI_API_MODE` | Prompt API / Structured API切替 |
| Backend | `DATABASE_URL` | PostgreSQL等のDB接続先 |
| Frontend | `NEXT_PUBLIC_API_BASE_URL` | Backend URL |

## 4. DB migration方法

1. 本番DBのバックアップを取得します。
2. Render Shellまたは安全な管理端末でAlembicの現在Revisionを確認します。
3. `20260722_2500_training_metrics.py`、`20260722_5000_proposal_agent_memory.py`、`20260722_7100_training_submission_rc.py` の順で適用できる状態を確認します。
4. 最新までupgradeします。
5. `/health/ready` で `migration_ready` を確認します。

## 5. Render再デプロイ方法

1. GitHubへ反映後、Render Eventsで新しいDeployが開始されたことを確認します。
2. Deploy live後に `/health` と `/health/ready` を確認します。
3. Application logsで起動エラー、DB接続エラー、Migrationエラーがないか確認します。

## 6. Vercel再デプロイ方法

1. Vercel Deploymentsで最新commitがProductionに反映されていることを確認します。
2. Build logsにエラーがないことを確認します。
3. 公開URLをCtrl+F5で更新します。

## 7. 初期管理者作成

Backend起動時、`INITIAL_ADMIN_EMAIL` と `INITIAL_ADMIN_PASSWORD` が設定され、該当ユーザーが存在しない場合のみ、adminロールの初期管理者が作成されます。既存ユーザーのパスワードは上書きされません。

## 8. ログの確認方法

- Render Application logsでBackendエラーを確認します。
- 管理画面の監査ログでログイン、出力、診断、デモデータ投入を確認します。
- APIキーやパスワードがログへ出ないことを確認します。

## 9. 障害時の切り分け

| 症状 | 確認先 |
| --- | --- |
| ログイン不可 | 初期管理者、ユーザー有効状態、APP_AUTH_SECRET |
| Backend未接続 | VercelのAPI Base URL、Render起動状態 |
| Beautiful.ai不可 | Beautiful.ai診断、API Key、API Mode、提出前チェック |
| CSV不可 | 認証、Role、Workspace、CSVレスポンス |
| 業務改善レポート保存不可 | 入力値、使用前時間、品質範囲、DB migration |

## 10. バックアップ方針

本番DB変更前に必ずバックアップを取得します。SQLiteを使う場合はDBファイルのコピー、PostgreSQLを使う場合はDBサービス標準のバックアップまたはdumpを利用します。

## 11. SQLiteを本番利用する場合の注意

Renderの一時ファイル領域にSQLite DBを置くと、再デプロイやインスタンス再作成でデータが失われる可能性があります。本番や継続的な研修運用では、永続ディスクまたはPostgreSQLを推奨します。

## 12. PostgreSQL移行推奨事項

- `DATABASE_URL` をPostgreSQLに切り替えます。
- 事前に空DBでAlembic upgradeを検証します。
- 既存SQLiteデータを移行する場合は、個人情報とデモデータを分けて扱います。
- 移行後にログイン、作成履歴、業務改善レポート、CSV、Beautiful.aiを確認します。
