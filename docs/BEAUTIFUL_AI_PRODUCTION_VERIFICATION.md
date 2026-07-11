# Beautiful.ai Production Verification

Version 17.3.3 は、新機能追加ではなく、Vercel Hobby でのデプロイ成功と Beautiful.ai 連携の本番確認を目的とします。

## 1. Vercel Hobby Serverless Functions 確認

Vercel の Root Directory は `frontend` に設定してください。

Vercel Functions として数えられる候補が残っていないことを確認します。

```powershell
cd ready-crew-proposal-ai

if (Test-Path frontend\api) {
  Get-ChildItem frontend\api -Recurse -File
} else {
  "frontend/api は存在しません"
}

(Get-ChildItem frontend\app -Recurse -File -Include route.ts,route.js -ErrorAction SilentlyContinue | Measure-Object).Count

if (Test-Path frontend\pages\api) {
  (Get-ChildItem frontend\pages\api -Recurse -File | Measure-Object).Count
} else {
  0
}
```

期待値:

- `frontend/api`: 存在しない
- `frontend/app/**/route.ts`: 0
- `frontend/app/**/route.js`: 0
- `frontend/pages/api`: 0
- Serverless Function 想定件数: 0

`frontend/client-api/` はクライアント側のAPIヘルパー置き場です。Vercel Functions ではありません。

## 2. import 残り確認

旧パスが残っていないことを確認します。

```powershell
rg -n "@/api/|\.\./api|\./api|frontend/api" frontend -g "!node_modules/**" -g "!.next/**" -g "!test-results/**"
```

期待値: ヒットなし

`frontend/lib/api.ts` は既存コード向けの再export口として維持します。各APIヘルパーの実体は `frontend/client-api/` を参照します。

## 3. Vercel 設定

Vercel 側では次を確認してください。

- Root Directory: `frontend`
- Framework Preset: `Next.js`
- Build Command: `npm run build`
- Output Directory: 未指定
- `NEXT_PUBLIC_API_URL`: Render Backend URL
- `BEAUTIFUL_AI_API_KEY`: Vercel には設定しない

Beautiful.ai APIキーは Backend(Render) 側だけに設定します。

## 4. Render /health 確認

Render Backend の `/health` を開き、以下を確認してください。

```text
https://<your-render-backend>.onrender.com/health
```

確認項目:

- `status`
- `git.commit`
- `git.commit_short`
- `git.branch`
- `beautiful_ai.route_registered`
- `routes.beautiful_ai_status_registered`
- `mock_ai`
- `db_connected`

Frontend の `Frontend Build Version` と Render の `git.commit_short` が一致するか確認してください。

Frontend と Backend を別々のコミットからデプロイしている場合は、不一致でも異常とは限りません。その場合は、同じ GitHub push 由来のデプロイか、Vercel と Render のデプロイ履歴で確認してください。

## 5. Beautiful.ai Status Card 確認

本番画面の Beautiful.ai 接続確認カードで以下を確認してください。

- Enabled
- Mock
- Configured
- API reachable
- Route found
- Backend version
- Frontend Build Version
- Build Time
- Version sync

期待値:

- `Enabled`: `true`
- `Mock`: `false`
- `Configured`: `true`
- `Route found`: `true`
- `API reachable`: status API が正常応答したこと

`API reachable` は Beautiful.ai 外部APIで実際にスライド生成できたことではなく、Ready Crew Backend の status API が疎通したことを意味します。

## 6. Beautiful.ai ボタン表示条件

画面上で `Beautiful.aiで提案書を作成` が有効になる主な条件です。

- 提案書作成済み
- ログインユーザーが `admin` または `member`
- Maintenance Mode が無効
- 提出前品質ゲートが完了済み
- `/api/beautiful-ai/status` の取得成功
- `BEAUTIFUL_AI_ENABLED=true`
- `BEAUTIFUL_AI_API_KEY` 設定済み、または `BEAUTIFUL_AI_MOCK=true`

無効の場合は、UIに無効理由を表示します。既存の要約PPTX、詳細PPTX、見積PDFは引き続き利用できます。

## 7. Beautiful.ai 実API接続テスト

本番で1回だけ接続テストを行う場合の条件です。

- `BEAUTIFUL_AI_ENABLED=true`
- `BEAUTIFUL_AI_MOCK=false`
- Render に `BEAUTIFUL_AI_API_KEY` 設定済み
- admin ユーザー
- Maintenance Mode 無効
- 提出前品質ゲート完了済み

テスト用タイトル:

```text
[CONNECTION TEST] Beautiful.ai Integration
```

テストには実顧客情報を使わないでください。

成功条件:

- HTTP 2xx
- `presentation_id` を取得
- `editor_url` を取得
- `player_url` を取得、または公式仕様上任意であることを確認
- DB保存成功
- `Beautiful.aiで編集` ボタン表示
- `プレゼンテーションを表示` ボタン表示
- `editor_url` が開ける

失敗時は既存の要約PPTX、詳細PPTX、見積PDFの出力が利用できることを確認してください。

## 8. Beautiful.ai 失敗時の切り分け

- `400`: 送信JSONとBeautiful.ai仕様の不一致
- `401`: Beautiful.ai APIキー無効
- `403`: Beautiful.ai API利用権限またはプラン不足
- `404`: Beautiful.ai外部エンドポイント不一致
- `429`: Beautiful.ai利用上限
- `timeout`: 処理時間超過
- `500`系: Beautiful.ai側、またはレスポンス解析失敗

Ready Crew Backend の `/api/beautiful-ai/status` が `404` の場合は、Render が最新コミットをデプロイしているか、`/health` の `route_registered` を確認してください。

APIキー、Authorizationヘッダー、外部APIレスポンス全文はログや画面へ出さないでください。

## 9. ローカル確認

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

## 10. GitHub push 手順

push 前に `.env.local`、`.next`、`node_modules`、`test-results`、`playwright-report` が含まれていないことを確認してください。

```powershell
git status --short
git add frontend/client-api frontend/lib/api.ts frontend/lib/beautifulAi.ts docs/BEAUTIFUL_AI_PRODUCTION_VERIFICATION.md
git add -u frontend/api
git status --short
git commit -m "Fix Vercel Hobby serverless function limit"
git push origin main
```

`git add .` を使う場合も、秘密情報や生成物が含まれていないことを必ず確認してください。

## 11. Vercel デプロイ後の成功条件

- Deployment Status が `Ready`
- Production に反映
- Serverless Functions 上限エラーが出ない
- Build Logs で `next build` 成功
- Deployment URL が最新Deploymentを指す
- 画面の Frontend Build Version が最新commitと一致
- Beautiful.ai 接続確認カードが表示される

実際のVercel画面やRender画面を確認できていない場合は、成功と記録しないでください。
