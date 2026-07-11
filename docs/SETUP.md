# SETUP

## ローカル環境

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm.cmd run dev
```

## WindowsでBackendテストを実行する

推奨コマンド:

```powershell
cd backend
.\test_backend.ps1
```

このスクリプトは次を自動で行います。

- `py -3.13`、`py -3`、`python`、`python3` の順に利用可能なPythonを探す
- `.venv` が壊れている場合は削除して作り直す
- `pip install -r requirements.txt` を実行する
- `DATABASE_URL` を `test-local.db` に切り替える
- `USE_MOCK_AI=true` でpytestを実行する

テストでは本番用の `backend/app.db` を使いません。

## `.venv` が壊れた場合の手動復旧

`python -m pytest` や `.venv\Scripts\python.exe` が起動しない場合は、以下で作り直してください。

```powershell
cd backend
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
```

Python 3.13がない場合は `py -3` または `python` に置き換えてください。

## 環境変数

Backend:

- `APP_AUTH_SECRET`: 認証用の十分に長い秘密文字列
- `INITIAL_ADMIN_EMAIL`: 初期管理者メール
- `INITIAL_ADMIN_PASSWORD`: 初期管理者パスワード
- `OPENAI_API_KEY`: OpenAI APIキー
- `USE_MOCK_AI`: APIキーなしで確認する場合は `true`
- `DATABASE_URL`: 未設定時は `sqlite:///app.db`
- `CORS_ORIGINS`: Vercel URLとローカルURLをカンマ区切りで設定

Frontend:

- `NEXT_PUBLIC_API_URL`: Render Backend URL

## Vercel

- Root Directory: `frontend`
- Build Command: `npm run build`
- Environment Variables: `NEXT_PUBLIC_API_URL`

## Render

- `render.yaml` はリポジトリ直下に配置
- Root Directory: `backend`
- Build Command: `pip install --upgrade pip && pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variables: Backend用の環境変数をRender Secretsへ設定

## SQLite / PostgreSQL方針

開発・試験導入ではSQLiteを利用できます。正式運用ではRender PostgreSQL、Supabase、Neonなどへの移行を推奨します。`DATABASE_URL` は画面やログへ表示しないでください。
