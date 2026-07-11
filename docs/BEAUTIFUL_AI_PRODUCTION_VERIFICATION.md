# Beautiful.ai Production Verification

Version 17.3では、画面上に「Beautiful.ai接続確認」カードを表示します。ここでVercelのFrontend、RenderのBackend、Beautiful.ai status APIの状態を同時に確認できます。

## Beautiful.aiボタンの表示条件

Beautiful.aiの作成ボタンは、提案書作成後の出力エリアに表示されます。

- `result` が存在する: 提案書作成が完了している
- `/api/beautiful-ai/status` を取得できている
- `BEAUTIFUL_AI_ENABLED=true`
- `BEAUTIFUL_AI_API_KEY` が設定済み、または `BEAUTIFUL_AI_MOCK=true`
- ログインユーザーが `admin` または `member`
- 提出前品質ゲートが完了、またはadminがバイパス済み
- Maintenance Modeで新規生成が停止されていない

未設定・404・権限エラーの場合も、ボタンは無効状態で表示し、理由を「Beautiful.ai接続確認」カードと出力エリアに表示します。

## Frontend表示条件の追跡

`frontend/components/AppShell.tsx` では次の順に判定します。

1. ログイン後に `refreshAccountData()` を実行
2. `refreshBeautifulAiVerification()` が `/health` と `/api/beautiful-ai/status` を取得
3. `beautifulAiStatus.enabled` が `true` の場合、Beautiful.ai作成ボタンを有効化
4. `canDownloadMainOutputs` が `true` の場合、品質ゲート通過済みとして作成可能
5. `isMaintenanceMode` が `false` の場合、新規作成可能

`enabled=false` やstatus API失敗時も、ボタンは無効状態で表示されます。

## Vercel確認

1. Vercelの最新Deploymentが成功していることを確認します。
2. 画面の「Beautiful.ai接続確認」で `Frontend Build Version`、`Git Commit`、`Build Time` を確認します。
3. GitHubの最新コミットと画面上のFrontend commitが一致するか確認します。

## Render確認

1. Renderの最新Deployが成功していることを確認します。
2. `https://<your-render-backend>.onrender.com/health` を開きます。
3. `git.commit_short` がGitHubの最新コミットと一致することを確認します。
4. `beautiful_ai.route_registered` が `true` であることを確認します。
5. `routes.beautiful_ai_status` が `/api/beautiful-ai/status` であることを確認します。

## Beautiful.ai status確認

正しいURL:

```text
https://<your-render-backend>.onrender.com/api/beautiful-ai/status
```

ログイン済みのFrontendからは自動で取得します。HTTPステータス別の意味は以下です。

- `200`: status APIに到達しています
- `401`: ログイン期限切れの可能性があります
- `403`: ログインユーザーの権限を確認してください
- `404`: RenderがBeautiful.ai router入りの最新コミットを動かしていない可能性があります
- `500`: Renderログを確認してください

## GitHub確認

1. GitHub ActionsのBackend pytest / Frontend buildが成功していることを確認します。
2. `backend/app/routers/beautiful_ai.py` が存在することを確認します。
3. `backend/app/main.py` に `beautiful_ai_router` が `include_router` されていることを確認します。
4. `/openapi.json` または `/docs` に `/api/beautiful-ai/status` が表示されることを確認します。
