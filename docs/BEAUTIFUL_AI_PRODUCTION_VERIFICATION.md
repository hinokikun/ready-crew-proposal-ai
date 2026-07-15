# Beautiful.ai Production Verification

このドキュメントは、Beautiful.ai 連携を本番環境で確認するための手順と、実際に確認できた結果だけを記録する場所です。

重要:

- 確認していないGitHub / Vercel / Render / Beautiful.ai実APIの状態を「成功」と記録しないでください。
- APIキー、Authorizationヘッダー、顧客本文、生成本文、外部APIレスポンス全文は記録しないでください。
- Beautiful.aiが失敗しても、既存の要約PPTX、詳細PPTX、見積PDFは利用できる状態を維持してください。

## 1. Git確認

確認項目:

- 現在ブランチ
- 最新commit
- `git status --short`
- 未コミット変更
- `git diff --check`
- GitHubへpush済みか

ユーザーの未コミット変更を削除、巻き戻し、上書きしないでください。

## 2. GitHub Actions確認

最新commitに対して以下が成功していることをGitHub画面で確認してください。

- Backend pytest
- Frontend build
- Lint and syntax checks
- Frontend Playwright E2E

Cloud deployment smoke test が手動実行専用の場合は、未実行を失敗扱いにしないでください。

## 3. Vercel確認

確認項目:

- 最新DeploymentがReady
- Productionへ反映済み
- commitがGitHub最新commitと一致
- Serverless Functions上限エラーが出ていない
- Root Directoryが `frontend`
- Frontend Build Versionが最新
- Beautiful.ai接続確認カードが表示される

Vercelに設定しないもの:

- `BEAUTIFUL_AI_API_KEY`
- `OPENAI_API_KEY`
- `DATABASE_URL`
- Backendの秘密情報

Vercelに必要な基本設定:

```text
NEXT_PUBLIC_API_URL=<Render Backend URL>
```

## 4. Render確認

確認URL:

```text
GET {Render Backend URL}/health
```

確認項目:

- 最新DeployがLive
- `/health` がHTTP 200
- `git.commit_short` がGitHub最新commitと一致
- `db_connected=true`
- `beautiful_ai.route_registered=true`
- `routes.beautiful_ai_status_registered=true`
- `maintenance_mode=false`

`/health` にAPIキーや接続文字列などの秘密情報を出さないでください。

## 5. Beautiful.ai環境変数確認

Renderに設定する前提:

```text
BEAUTIFUL_AI_ENABLED=true
BEAUTIFUL_AI_MOCK=false
BEAUTIFUL_AI_API_KEY=<real API key>
BEAUTIFUL_AI_BASE_URL=https://www.beautiful.ai/api/v1
BEAUTIFUL_AI_TIMEOUT_SECONDS=120
```

必要に応じて設定:

```text
BEAUTIFUL_AI_DEFAULT_THEME_ID=minimal
BEAUTIFUL_AI_WORKSPACE_ID=
BEAUTIFUL_AI_FOLDER_ID=
```

空文字の `themeId` は外部APIへ送信しないでください。APIキーの値は画面、ログ、レスポンス、テスト、ドキュメントへ出さないでください。

## 6. Beautiful.ai Status API確認

ログイン済みadminまたはmemberで確認します。

```text
GET /api/beautiful-ai/status
```

期待値:

- `enabled=true`
- `configured=true`
- `mock=false`
- `api_reachable=true`
- `route_found=true`
- `backend_version` が最新

注意:

- `api_reachable` はReady Crew Backendのstatus APIへ到達できた意味です。
- Beautiful.ai外部APIで実プレゼン生成に成功した意味ではありません。
- 401はログイン期限切れ、403は権限不足、404はRender未反映として扱います。

## 7. Quality Gate確認

同一 `project_id` に対して確認します。

```text
GET /api/quality-gates/{project_id}
```

次のいずれかがtrueなら解除済みです。

- `completed`
- `bypassed`
- `download_unlocked`

確認項目:

- FrontendとBackendで同じ `project_id` を使用
- Quality Gate完了後に再取得
- ページ再読み込み後も状態復元
- 古い案件IDを参照しない
- memberでも正常に利用可能
- viewerは利用不可

## 8. Beautiful.aiボタン有効条件

本番画面で以下を確認します。

- Proposal Ready: true
- Role Allowed: true
- Quality Gate: true
- Status API: true
- Route Found: true
- Enabled: true
- Configured: true
- Maintenance: false
- Other Output Busy: false

以下はボタン無効条件にしません。

- member利用時の `Admin=false`
- `Mock=false`
- `last_success_at` が空
- Build Time不一致
- version表示の一時的な不一致

必須条件がそろったら「Beautiful.aiで提案書を作成」が有効になります。

## 9. Beautiful.ai実API生成テスト

実Beautiful.ai APIへの生成は1回だけ行います。顧客情報を含まない接続確認用データを使ってください。

テストタイトル:

```text
[CONNECTION TEST] Beautiful.ai Integration
```

送信する内容:

- title
- language
- preserveExactText
- slides

設定がある場合のみ送信:

- workspaceId
- folderId
- themeId
- themeOptions

送信禁止:

- APIキーをJSON本文へ含めること
- 顧客メール全文
- 電話番号
- パスワード
- 不要な個人情報

成功条件:

- 外部API HTTP 2xx
- `presentation_id` 取得
- `editor_url` 取得
- `player_url` 取得、または公式仕様上任意であることを確認
- DB保存成功
- 「Beautiful.aiで編集」表示
- 「プレゼンテーションを表示」表示
- `editor_url` が開く
- 同じ `project_id` で重複生成されない
- APIキーがFrontend、DB、ログ、レスポンスへ出ない

## 10. レスポンス解析

安全に解析する形式:

直接:

- `presentationId`
- `editorUrl`
- `playerUrl`
- `status`
- `title`

`data` 階層:

- `data.presentationId`
- `data.editorUrl`
- `data.playerUrl`
- `data.status`
- `data.title`

保存時は以下へ正規化します。

- `presentation_id`
- `editor_url`
- `player_url`
- `status`
- `title`

`presentation_id` または `editor_url` が欠ける場合は、成功扱いにしないでください。レスポンス全文をログや画面へ出さないでください。

## 11. エラー分類

- 400: `beautiful_ai_bad_request`
- 401: `beautiful_ai_invalid_api_key`
- 403: `beautiful_ai_access_not_enabled`
- 404: `beautiful_ai_endpoint_not_found`
- 429: `beautiful_ai_rate_limit`
- timeout: `beautiful_ai_timeout`
- 500系: `beautiful_ai_service_error`

Ready Crew内部APIの404と、Beautiful.ai外部APIの404を区別してください。Frontendには安全な日本語メッセージとrequest_idだけを表示し、外部APIの生エラー本文は表示しないでください。

## 12. 二重生成防止

確認項目:

- ボタン押下後に無効化
- 処理中は再押下不可
- 同じ `project_id` の成功済みレコードがあれば既存結果を返す
- ページ再読み込みでも重複生成しない
- 失敗後のみ再試行可能
- `finally` でbusy状態を解除
- 429の場合に連打させない

## 13. フォールバック確認

Beautiful.aiが失敗しても以下を維持してください。

- 要約PPTX
- 詳細PPTX
- 見積PDF
- 提案書生成結果
- Quality Gate状態
- フィードバック入力

Beautiful.ai失敗で既存成果物を削除しないでください。

## 14. セキュリティ確認

確認項目:

- `BEAUTIFUL_AI_API_KEY` はRenderのみ
- Vercelには設定しない
- `NEXT_PUBLIC_*` に秘密情報なし
- Frontend bundleにAPIキーなし
- Git差分にAPIキーなし
- Git履歴にAPIキーなし
- DBにAPIキーなし
- 監査ログにAPIキーなし
- Render LogsにAuthorizationなし
- editor_url/player_url全文をログ保存しない

過去に露出したAPIキーは再利用しないでください。

## 15. ローカル確認コマンド

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

共通:

```powershell
git diff --check
git status --short
```

## 16. Version 17.3.6 Go-Live Verification Record

確認日時: 2026-07-13

ローカルで確認できた内容だけを記録します。GitHub Actions、Vercel、Render、Beautiful.ai実API生成は、このCodex環境から本番画面・本番APIキーへアクセスできないため未確認です。未確認項目は成功扱いにしません。

### Git

- Branch: `main`
- Local commit: `4f18150be95c5d08ecb1ad4ab0302023ac2d0b05`
- Working tree before verification: clean
- `git diff --check`: 成功

GitHubへpush済みか、GitHub最新commitと一致しているかは本環境では未確認です。

### Local Frontend Verification

- `npm.cmd run typecheck`: 成功
- `npm.cmd run check:unused`: 成功
- `npm.cmd run build`: 成功
- `npm.cmd run test:e2e`: 成功、23件 passed

Playwrightで確認したBeautiful.ai関連:

- Beautiful.ai未設定時も既存PPTX導線を維持
- Beautiful.ai作成後に編集リンクを表示
- Beautiful.ai 429時も既存PPTXを利用可能
- 品質ゲート未完了ではBeautiful.ai作成ボタンを無効化
- Beautiful.ai Status CardでEnabled/Mockを表示
- status 404時にRender未反映メッセージを表示
- Frontend/Backendバージョン不一致を検出
- member利用時の `Admin=false` をブロック扱いにしない
- `Mock=false` をブロック扱いにしない

### Local Backend Verification

- `.\.venv\Scripts\python.exe -m compileall app tests`: 成功
- `.\.venv\Scripts\python.exe -m pytest -q`: 成功
- `.\.venv\Scripts\python.exe -m pip check`: 成功

Beautiful.ai backendテストで確認している内容:

- status APIでAPIキーを返さない
- mock成功時に同一project_idの重複生成を防止
- memberがreal API modeでも作成可能
- Quality Gate未完了では作成不可
- viewerは作成不可
- Maintenance Mode中は作成不可
- 400/401/403/404/429/500系の安全なerror_type分類
- `data.presentationId` / `data.editorUrl` / `data.playerUrl` 形式のレスポンス解析
- APIキーがレスポンス、保存レコード、監査ログへ出ないこと

### Production Cloud Verification

以下は本環境では未確認です。実画面で確認後に結果を追記してください。

- GitHub Actions: 未確認
- Vercel Deployment Ready: 未確認
- Vercel Production反映: 未確認
- Vercel commitとGitHub最新commit一致: 未確認
- Render Deploy Live: 未確認
- Render `/health` HTTP 200: 未確認
- Render `/health` の `git.commit_short`: 未確認
- Render `/health` の `db_connected=true`: 未確認
- Render `/health` の `beautiful_ai.route_registered=true`: 未確認
- Render `/health` の `routes.beautiful_ai_status_registered=true`: 未確認
- Render `/health` の `maintenance_mode=false`: 未確認

### Beautiful.ai Production Status Verification

以下は本環境では未確認です。ログイン済みadminまたはmemberで本番画面から確認してください。

- `GET /api/beautiful-ai/status`: 未確認
- `enabled=true`: 未確認
- `configured=true`: 未確認
- `mock=false`: 未確認
- `api_reachable=true`: 未確認
- `route_found=true`: 未確認
- `backend_version` 最新: 未確認

注意: `api_reachable` はReady Crew Backendのstatus APIへ到達できた意味であり、Beautiful.ai外部APIで実プレゼン生成に成功した意味ではありません。

### Beautiful.ai Real API Generation Test

本環境では実Beautiful.ai API生成を実行していません。理由は、本番Render環境の `BEAUTIFUL_AI_API_KEY` とログイン済み本番セッションへアクセスできないためです。

実施する場合は、顧客情報を含まない以下のテストタイトルで1回だけ実行してください。

```text
[CONNECTION TEST] Beautiful.ai Integration
```

成功として記録できる条件:

- 外部API HTTP 2xx
- `presentation_id` 取得
- `editor_url` 取得
- `player_url` 取得、または公式仕様上任意であることを確認
- DB保存成功
- 「Beautiful.aiで編集」表示
- 「プレゼンテーションを表示」表示
- `editor_url` が開く
- 同じproject_idで重複生成されない
- APIキーがFrontend、DB、ログ、レスポンスへ出ない

### Production Go-Live Judgment

ローカル品質ゲートは通過しています。

本番Go-Live可否は、以下の未確認項目を人が確認した後に判断してください。

- GitHub Actions success
- Vercel Ready / Production反映
- Render Live / `/health` 正常
- Beautiful.ai Status API正常
- Quality Gate完了後にBeautiful.aiボタン有効
- 実Beautiful.ai API生成1回成功
- APIキー漏えいなし
