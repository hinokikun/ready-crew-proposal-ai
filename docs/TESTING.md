# テスト実行ガイド

AI営業秘書 / AI Workspace の修正後に、WindowsローカルとGitHub Actionsで同じ確認を行うための手順です。

## Frontend

PowerShellで実行します。

```powershell
cd frontend
npm.cmd ci
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

初回だけPlaywrightのブラウザが必要です。ブラウザ不足で失敗した場合は次を実行してください。

```powershell
cd frontend
npx.cmd playwright install chromium
```

npmのキャッシュ権限で失敗する場合は、プロジェクト内キャッシュを使います。

```powershell
cd frontend
$env:npm_config_cache = "$PWD\.npm-cache"
npm.cmd ci
```

`npm.cmd run test:e2e` は `frontend/scripts/run-e2e.mjs` からNext.js dev serverを起動し、テスト後に停止します。すでに `http://127.0.0.1:3000` が起動している場合は既存サーバーを再利用します。

## Backend

PowerShellで実行します。

```powershell
cd backend
.\test_backend.ps1
```

個別に実行する場合は次の通りです。

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL = "sqlite:///test-app.db"
$env:USE_MOCK_AI = "true"
$env:OPENAI_API_KEY = "test-key"
$env:APP_AUTH_SECRET = "test-secret"
$env:INITIAL_ADMIN_EMAIL = "admin@example.com"
$env:INITIAL_ADMIN_PASSWORD = "test-password"
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
```

pytestの一時フォルダは `backend/.pytest-tmp` に固定しています。Windowsの既定Tempフォルダに権限がない環境でも、プロジェクト内でテストできます。

## Broken .venv の再作成

`.venv` が壊れている、またはPythonのバージョンが合わない場合は削除して作り直します。

```powershell
cd backend
Remove-Item -Recurse -Force .venv
.\test_backend.ps1
```

`test_backend.ps1` は `py -3.13`、`py -3`、`python`、`python3`、Codex同梱Pythonの順で利用可能なPythonを探します。

## テストDB

テストでは本番用の `app.db` を使いません。

- `test_backend.ps1`: `backend/test-local.db`
- 手動実行例: `backend/test-app.db`
- pytest fixture: 各テストの一時SQLite

不要になったテストDBは削除して問題ありません。

```powershell
cd backend
Remove-Item -Force test-app.db, test-local.db -ErrorAction SilentlyContinue
```

## よくあるエラー

- `Module not found`: import先のファイル名と大文字小文字を確認してください。Vercel/Linuxでは大文字小文字違いも失敗します。
- `.next cache` 破損: `cd frontend; Remove-Item -Recurse -Force .next; npm.cmd run build`
- Playwright browser missing: `cd frontend; npx.cmd playwright install chromium`
- Port 3000 in use: 既存サーバーを止めるか、`PLAYWRIGHT_BASE_URL` を既存URLに合わせてください。
- npm cache permission: `$env:npm_config_cache="$PWD\.npm-cache"` を設定してください。
- Broken `.venv`: `backend/.venv` を削除して `backend/test_backend.ps1` を再実行してください。
- DATABASE_URL未設定: BackendはSQLiteの `app.db` にフォールバックします。テスト時は必ずテスト用 `DATABASE_URL` を指定してください。

## GitHub Actions

`.github/workflows/test.yml` で以下を自動実行します。

- `backend-test`: Python 3.13、依存インストール、`python -m compileall app tests`、`python -m pytest`
- `frontend-build`: Node.js 24、`npm ci`、`npm run build`
- `frontend-e2e`: Playwright Chromiumをインストールし、`npm run test:e2e`
- `lint-check`: `git diff --check`、Backend構文チェック、Frontend typecheck、未使用importチェック

Actionsが失敗した場合は、GitHubのActionsタブから失敗したjobを開き、最初の赤いステップのログを確認してください。Playwright失敗時は `playwright-report` artifact がアップロードされます。

## Cloud Smoke Test

公開後のVercel / Renderを確認する場合だけ、手動でCloud Smoke Testを実行します。
通常のpull requestでは実行しません。

ローカル実行:

```powershell
$env:FRONTEND_URL = "https://your-app.vercel.app"
$env:BACKEND_URL = "https://your-backend.onrender.com"
$env:SMOKE_TEST_EMAIL = "admin@example.com"
$env:SMOKE_TEST_PASSWORD = "********"
$env:SMOKE_VIEWER_EMAIL = "viewer@example.com"
$env:SMOKE_VIEWER_PASSWORD = "********"
python scripts/smoke_test.py
```

GitHub Actionsで実行する場合は、`Test` workflowを `workflow_dispatch` で手動実行します。
必要なSecrets:

- `SMOKE_FRONTEND_URL`
- `SMOKE_BACKEND_URL`
- `SMOKE_TEST_EMAIL`
- `SMOKE_TEST_PASSWORD`
- `SMOKE_VIEWER_EMAIL` 任意
- `SMOKE_VIEWER_PASSWORD` 任意

このSmoke Testは提案書生成、PPTX生成、PDF生成を実行しません。
OpenAI費用や顧客データ保存を避けるため、ログイン、ヘルスチェック、保護API、viewerの生成拒否だけを確認します。
# Version 22.1 Regression Lock

Run these commands before production deployment.

## Frontend

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

Expected Version 22.1 local result:

- typecheck: passed
- unused import check: passed
- build: passed
- Playwright: 29 passed

## Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Expected Version 22.1 local result:

- compileall: passed
- pytest: 139 passed
- pip check: passed

## Common

```powershell
git diff --check
git status --short
```

`git diff --check` may print CRLF warnings for existing files on Windows. Treat whitespace errors as blockers.

## PPTX Regression

The current automated regression covers:

- normal PowerPoint download endpoint
- summary PowerPoint download endpoint
- estimate PDF endpoint
- authentication and role-protected generation paths

For production acceptance, also open a generated PPTX manually and check slide count, title text, footer, page size, and nonblank slides.
# Version 22.2 PPTX Regression Tests

PPTX生成の内部分割後は、以下を必ず実行する。

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_generation_outputs.py tests\test_pptx_structure_regression.py -q
```

構造snapshot:

- `backend/tests/snapshots/detailed_pptx_structure.json`
- `backend/tests/snapshots/summary_pptx_structure.json`

任意の視覚確認:

```powershell
python scripts/render_pptx_preview.py path\to\proposal.pptx --out outputs\pptx-preview
python scripts/compare_pptx_previews.py expected.pdf actual.pdf
```

LibreOffice / soffice がない環境では視覚比較は未実行として扱う。
