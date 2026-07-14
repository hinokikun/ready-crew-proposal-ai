# Cloud Deployment Verification

Vercel / Render へ公開したあとに、AI営業秘書が安全に動くか確認するための手順です。
本番確認では顧客本文や生成本文を使わず、必要に応じて `USE_MOCK_AI=true` の環境で実施してください。

## 1. 事前確認

- GitHub Actions が成功している
- Vercel の Deployment が `Ready` になっている
- Render の Service が `Live` になっている
- Render に必要な環境変数が設定されている
- Vercel に `NEXT_PUBLIC_API_URL` が設定されている
- テスト用 admin/member アカウントを用意している
- viewer 権限確認をする場合は、viewer のテストアカウントも用意している

## 2. Health Check

ブラウザまたはコマンドで確認します。

```powershell
Invoke-RestMethod "$env:BACKEND_URL/health"
Invoke-RestMethod "$env:BACKEND_URL/health/live"
Invoke-RestMethod "$env:BACKEND_URL/health/ready"
```

期待値:

- `/health/live` は 200
- `/health/ready` は依存関係が正常なら 200
- `auth_configured` が `true`
- `db_connected` が `true`
- `pptx` が `available`
- `pdf` が `available`
- `DATABASE_URL`、APIキー、パスワード、トークンが返っていない

`/health` が `degraded` の場合は、`db_connected`、`auth_configured`、`ai_api` を確認してください。

## 3. Cloud Smoke Test

公開後の最小確認は `scripts/smoke_test.py` で実行できます。
このテストは提案書生成やPPT/PDF生成を実行しないため、OpenAI費用や顧客データ保存を発生させません。

```powershell
$env:FRONTEND_URL = "https://your-app.vercel.app"
$env:BACKEND_URL = "https://your-backend.onrender.com"
$env:SMOKE_TEST_EMAIL = "admin@example.com"
$env:SMOKE_TEST_PASSWORD = "********"
$env:SMOKE_VIEWER_EMAIL = "viewer@example.com"
$env:SMOKE_VIEWER_PASSWORD = "********"
python scripts/smoke_test.py
```

GitHub Actions では `workflow_dispatch` から手動実行できます。
Secrets:

- `SMOKE_FRONTEND_URL`
- `SMOKE_BACKEND_URL`
- `SMOKE_TEST_EMAIL`
- `SMOKE_TEST_PASSWORD`
- `SMOKE_VIEWER_EMAIL` 任意
- `SMOKE_VIEWER_PASSWORD` 任意

期待される出力例:

```text
PASS Frontend
PASS Backend health
PASS Auth configured
PASS Database connection
PASS Login API
PASS Unauthenticated protected API rejection
PASS Authenticated core API
PASS Viewer generation guard
```

`FAIL` が1つでもあれば失敗です。`SKIP Viewer generation guard` は viewer 用テストアカウント未設定の場合に表示されます。

## 4. 最重要動線

- ログインできる
- 一般ユーザーに管理者メニューが表示されない
- 案件メール貼り付け欄が表示される
- AI Workspace が表示される
- 既存データのCRMが表示できる
- 品質ゲート画面が開く
- 要約PPT / 詳細PPT / 見積PDF のボタンが表示される
- 管理者は監査ログ、利用状況、リリース管理を開ける

本番環境で提案書生成を試す場合は、必ずデモ案件か社内テスト案件のみを使ってください。

## 5. 失敗時の確認先

- Vercel Build Logs
- Render Logs
- GitHub Actions の失敗ジョブ
- `/health` の `status` と `db_connected`
- ブラウザ画面に表示された `request_id`
- Backend の構造化ログに出ている同じ `request_id`

## 6. 完了条件

- GitHub Actions が成功
- Vercel が `Ready`
- Render が `Live`
- `/health/ready` が 200
- Smoke Test が `FAIL 0`
- 管理者と一般ユーザーの権限差が確認できている
- APIキー、DATABASE_URL、パスワードが画面・ログ・レスポンスに出ていない
## Version 18.2 Workspace Isolation Verification

After deploying Render and Vercel:

1. Open Render `/health`.
2. Confirm:
   - `db_connected: true`
   - `migration_ready: true`
   - `migration_current` matches `migration_head`
   - no `DATABASE_URL` or secret values are returned
3. Open Render `/health/ready`; it must return 200 before production traffic.
4. Run the cloud smoke test:

```powershell
python scripts/smoke_test.py
```

Recommended optional environment variables for the smoke test:

- `SMOKE_FORBIDDEN_ORGANIZATION_ID`
- `SMOKE_FORBIDDEN_WORKSPACE_ID`
- `SMOKE_OTHER_WORKSPACE_PROJECT_ID`

These validate that workspace switching and direct ID access are rejected across scope.
