# TROUBLESHOOTING

## Vercel buildでModule not found

- import先ファイルが存在するか確認する
- 大文字小文字が一致しているか確認する
- `frontend/tsconfig.tsbuildinfo` と `.next` を削除して再ビルドする

```powershell
cd frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
Remove-Item -Force tsconfig.tsbuildinfo -ErrorAction SilentlyContinue
npm.cmd run typecheck
npm.cmd run build
```

## Backendが起動しない

- Render LogsでImportErrorを確認する
- `python -m compileall app tests` を実行する
- `DATABASE_URL`、`APP_AUTH_SECRET`、初期管理者の環境変数を確認する
- `/health` が返るか確認する

## pytestが実行できない

Windowsでは次を実行してください。

```powershell
cd backend
.\test_backend.ps1
```

`.venv` が壊れている場合、このスクリプトが再作成します。手動で直す場合は以下です。

```powershell
cd backend
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
```

## auth_configured false

Renderに以下を設定してください。

- `APP_AUTH_SECRET`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`

## PPTX / PDF生成失敗

- `python-pptx` と `reportlab` が `requirements.txt` にあるか確認する
- Renderログでフォント、一時ファイル、権限エラーを確認する
- 一時ファイルは `/tmp` を利用する

## OpenAI API上限

- 時間を置いて再実行する
- 検証時は `USE_MOCK_AI=true` に切り替える
- API利用上限、請求設定、モデル設定を確認する

## DB接続失敗

- `DATABASE_URL` を確認する
- 接続文字列は画面やログに出さない
- SQLiteの場合は `app.db` の書き込み権限を確認する
- PostgreSQLの場合はRender/Supabase/Neonの接続状態を確認する
