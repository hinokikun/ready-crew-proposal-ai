# AI営業秘書 / AI Workspace

AI営業秘書は、案件メールや議事録を貼り付けるだけで、AI Workspace、提案書作成、PPT/PDF出力、CRM、レビュー、品質ゲート、ナレッジ、Analyticsを一つの画面で扱う社内向け営業支援ツールです。

Version 14.2では新機能を追加せず、正式リリース候補としてテスト、CI、運用手順、セキュリティ確認を安定化しています。

## 最初に使う画面

一般ユーザーの初期画面は、日々の営業作業に必要な項目だけに絞っています。

- 今日のAIブリーフィング
- AI通知
- 案件メール貼り付け
- AI Workspace
- 要約PPTダウンロード

CRM、管理者機能、Prompt Studio、外部連携、Analyticsなどは詳細メニューまたは管理者メニューに格納しています。

## 構成

- Frontend: Next.js / Vercel
- Backend: FastAPI / Render
- DB: SQLite対応、PostgreSQL移行準備済み
- AI: OpenAI API、または `USE_MOCK_AI=true` のモック動作

## ローカル起動

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm install
copy .env.example .env.local
npm.cmd run dev
```

## 確認コマンド

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
```

Backend:

```powershell
cd backend
.\test_backend.ps1
```

`test_backend.ps1` は壊れた `.venv` を再作成し、テスト用SQLite DBを使って `pytest` を実行します。本番用の `app.db` は使いません。

## 必須環境変数

Backend / Render:

- `APP_AUTH_SECRET`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `OPENAI_API_KEY`
- `USE_MOCK_AI`
- `DATABASE_URL`
- `CORS_ORIGINS`

Frontend / Vercel:

- `NEXT_PUBLIC_API_URL`

APIキー、パスワード、DB接続文字列はコードへ書かず、`.env`、`.env.local`、Vercel、Renderの環境変数で管理してください。

## ドキュメント

- [環境構築](docs/SETUP.md)
- [運用手順](docs/OPERATIONS.md)
- [セキュリティ方針](docs/SECURITY.md)
- [トラブル対応](docs/TROUBLESHOOTING.md)
- [構成・DB・API](docs/ARCHITECTURE.md)
- [リリース手順](docs/RELEASE.md)
- [Version 14.1 Production Release Audit](docs/RELEASE_AUDIT.md)

## Testing

Windowsローカル、Playwright、pytest、GitHub Actionsの詳しい確認手順は [docs/TESTING.md](docs/TESTING.md) を参照してください。

## Cloud Deployment Verification

Vercel / Render 公開後の確認手順は以下を参照してください。

- [Cloud Deployment Verification](docs/DEPLOYMENT_VERIFICATION.md): `/health`、手動Smoke Test、公開後チェックリスト
- [Backup and Restore](docs/BACKUP_RESTORE.md): SQLite / PostgreSQL のバックアップ・リストア方針
- [Incident Response](docs/INCIDENT_RESPONSE.md): 障害時の確認先、復旧、ロールバック手順

公開後の最小確認は次のスクリプトで実行できます。提案書生成やPPT/PDF生成は実行しないため、OpenAI費用や顧客データ保存を発生させません。

```powershell
$env:FRONTEND_URL = "https://your-app.vercel.app"
$env:BACKEND_URL = "https://your-backend.onrender.com"
$env:SMOKE_TEST_EMAIL = "admin@example.com"
$env:SMOKE_TEST_PASSWORD = "********"
python scripts/smoke_test.py
```

GitHub Actions の `Cloud deployment smoke test` は手動実行専用です。通常のpull requestではクラウド環境へアクセスしません。

## Pilot Mode（社内試験導入）

社内試験導入時は、RenderのBackend環境変数に以下を設定します。

```text
PILOT_MODE=true
PILOT_START_DATE=2026-07-11
PILOT_END_DATE=2026-07-25
PILOT_MAX_USERS=5
MAINTENANCE_MODE=false
```

Pilot Mode中は、admin以外では「Pilot対象」に設定されたユーザーだけがログインできます。重大な問題がある場合は `MAINTENANCE_MODE=true` にすると、新規提案書作成、PPT/PDF新規作成、Orchestrator新規実行を停止できます。ログイン、履歴確認、CRM閲覧、管理者メニュー、ヘルスチェックは継続できます。

クラウド確認用のGitHub Secrets:

```text
SMOKE_FRONTEND_URL
SMOKE_BACKEND_URL
SMOKE_TEST_EMAIL
SMOKE_TEST_PASSWORD
SMOKE_VIEWER_EMAIL
SMOKE_VIEWER_PASSWORD
SMOKE_DISABLED_EMAIL
SMOKE_DISABLED_PASSWORD
SMOKE_EXPECT_PILOT_MODE
```

Pilot運用資料:

- [Pilot Launch Plan](docs/PILOT_PLAN.md)
- [Pilot Admin Guide](docs/PILOT_ADMIN_GUIDE.md)
- [Pilot User Guide](docs/PILOT_USER_GUIDE.md)

## Beautiful.ai連携

Beautiful.aiは追加のプレゼンテーション出力として利用できます。既存の要約PPT、詳細PPT、見積PDFはそのまま残ります。

Render Backendに設定する環境変数:

```text
BEAUTIFUL_AI_ENABLED=false
BEAUTIFUL_AI_API_KEY=
BEAUTIFUL_AI_BASE_URL=https://www.beautiful.ai/api/v1
BEAUTIFUL_AI_DEFAULT_THEME_ID=
BEAUTIFUL_AI_TIMEOUT_SECONDS=120
BEAUTIFUL_AI_MOCK=false
```

社内検証では `BEAUTIFUL_AI_ENABLED=true` と `BEAUTIFUL_AI_MOCK=true` を設定すると、実APIを呼ばずに動作確認できます。APIキーはFrontend/Vercelへ設定しないでください。

詳細: [Beautiful.ai連携](docs/BEAUTIFUL_AI_INTEGRATION.md)
## Beautiful.ai 本番接続確認手順

Beautiful.aiが本番環境で表示・動作するかは、画面上の「Beautiful.ai接続確認」カードで確認できます。VercelのFrontend Build Version、RenderのCurrent backend version、`/api/beautiful-ai/status` の到達状態、Route foundを比較してください。

詳細手順: [Beautiful.ai Production Verification](docs/BEAUTIFUL_AI_PRODUCTION_VERIFICATION.md)
