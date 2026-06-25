# Ready Crew Proposal AI

Ready Crew の案件概要から、Web制作会社向けの営業提案書を自動生成するWebサービスです。

Frontend は Next.js、Backend は FastAPI、AI は OpenAI API を利用します。  
Vercel + Render にデプロイすると、`https://xxxxxxxx.vercel.app` のようなURLから誰でも利用できます。

## 主な機能

- 提案書生成
- 競合分析支援
- 見積AI
- ヒアリングシート生成
- ヒアリング結果の議事録整理
- Markdown出力
- 通常版PowerPoint出力
- 要約PowerPoint出力
- 見積書PDF出力
- 生成履歴のローカル保存

## ディレクトリ構成

```text
ready-crew-proposal-ai/
├─ backend/
│  ├─ app/
│  ├─ .env.example
│  └─ requirements.txt
├─ frontend/
│  ├─ app/
│  ├─ lib/
│  ├─ types/
│  ├─ .env.example
│  └─ package.json
├─ render.yaml
├─ .gitignore
└─ README.md
```

## ローカル起動

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

APIキーなしで動作確認する場合は、`backend/.env` の `USE_MOCK_AI=true` のまま使います。  
OpenAI API を使う場合は、`OPENAI_API_KEY` を入れて `USE_MOCK_AI=false` にします。

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm.cmd run dev
```

`frontend/.env.local` は以下です。

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

ブラウザで開きます。

```text
http://localhost:3000
```

## 環境変数

### Frontend / Vercel

Vercel の Environment Variables に設定します。

```env
NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com
```

`NEXT_PUBLIC_API_URL` は、Render にデプロイした Backend のURLです。

### Backend / Render

Render の Environment Variables または Secrets に設定します。

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
USE_MOCK_AI=false
CORS_ORIGINS=https://your-vercel-app.vercel.app
CORS_ORIGIN_REGEX=^https://.*\.vercel\.app$
REQUEST_TIMEOUT_SECONDS=60
TMPDIR=/tmp
TEMP=/tmp
TMP=/tmp
```

`OPENAI_API_KEY` はコードやGitHubに保存しません。Render の Secret として登録します。

## GitHubへアップロードする方法

1. GitHubで新しいリポジトリを作成します。
2. この `ready-crew-proposal-ai` フォルダをリポジトリとして使います。
3. 以下を実行します。

```powershell
git init
git add .
git commit -m "Initial deploy ready version"
git branch -M main
git remote add origin https://github.com/YOUR_NAME/YOUR_REPOSITORY.git
git push -u origin main
```

`.env` と `.env.local` は `.gitignore` に入っているため、GitHubへアップロードされません。

## Render登録・Backendデプロイ方法

1. Render に登録します。
2. GitHubアカウントを連携します。
3. Render の Dashboard で `New +` を押します。
4. `Blueprint` を選択します。
5. GitHubリポジトリを選択します。
6. `render.yaml` が読み込まれます。
7. `OPENAI_API_KEY` を Secret として入力します。
8. 作成すると Backend がデプロイされます。

Render の起動設定は `render.yaml` に入っています。

```yaml
buildCommand: pip install --upgrade pip && pip install -r requirements.txt
startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
healthCheckPath: /health
```

デプロイ後、以下にアクセスして確認します。

```text
https://your-render-backend.onrender.com/health
```

`{"status":"ok"}` が表示されればOKです。

## Vercel登録・Frontendデプロイ方法

1. Vercel に登録します。
2. GitHubアカウントを連携します。
3. `Add New Project` を押します。
4. GitHubリポジトリを選択します。
5. Root Directory に `frontend` を指定します。
6. Framework Preset は `Next.js` を選択します。
7. Environment Variables に以下を追加します。

```env
NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com
```

8. `Deploy` を押します。

デプロイ後、以下のようなURLが発行されます。

```text
https://your-vercel-app.vercel.app
```

## CORS設定

Vercel のURLが決まったら、Render の Backend 環境変数を更新します。

```env
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

プレビューURLも許可したい場合は、以下を設定します。

```env
CORS_ORIGIN_REGEX=^https://.*\.vercel\.app$
```

更新後、Render で Backend を再デプロイします。

## デプロイ順序

おすすめの順序です。

1. GitHubへpush
2. RenderでBackendをデプロイ
3. RenderのURLをコピー
4. VercelでFrontendをデプロイ
5. Vercelに `NEXT_PUBLIC_API_URL` を設定
6. VercelのURLをコピー
7. Renderに `CORS_ORIGINS` を設定
8. RenderとVercelを再デプロイ

## 更新方法

コードを修正したら、GitHubへpushします。

```powershell
git add .
git commit -m "Update proposal AI"
git push
```

Vercel と Render は GitHub 連携により自動で再デプロイされます。  
環境変数を変更した場合は、各サービスの管理画面から手動で再デプロイしてください。

## 独自ドメイン設定方法

### Frontend

1. Vercel の対象プロジェクトを開きます。
2. `Settings` → `Domains` を開きます。
3. 使いたいドメインを追加します。
4. 表示されたDNSレコードを、ドメイン管理サービス側に設定します。
5. 反映後、独自ドメインで画面を開けるようになります。

独自ドメインを使う場合は、Render の `CORS_ORIGINS` にも追加します。

```env
CORS_ORIGINS=https://your-domain.com,https://your-vercel-app.vercel.app
```

### Backend

Backendにも独自ドメインを使う場合は、Render の `Settings` → `Custom Domains` から追加します。  
その場合は、Vercel の `NEXT_PUBLIC_API_URL` を Backend の独自ドメインに変更します。

## PowerPoint・PDF生成について

通常版PowerPoint、要約PowerPoint、見積書PDFは Backend で生成します。  
Frontend は生成APIを呼び出し、ファイルをダウンロードするだけです。

生成データはメモリ上で作成して返却します。クラウド環境で一時領域が必要になった場合も、Render では `/tmp` を使う設定にしています。

## 本番動作確認

Vercel の公開URLで以下を確認します。

1. サンプル入力を押す
2. 提案書初稿を生成する
3. Markdown結果が表示される
4. 競合分析が表示される
5. 見積AIが表示される
6. ヒアリングシートが表示される
7. 通常版PowerPointをダウンロードする
8. 要約PowerPointをダウンロードする
9. 見積書PDFをダウンロードする

## よくあるトラブル

### FrontendからBackendに接続できない

Vercel の `NEXT_PUBLIC_API_URL` が Render のURLになっているか確認します。  
Render の `CORS_ORIGINS` に Vercel のURLが入っているか確認します。

### PowerPointやPDFが失敗する

Render のログを確認します。  
`OPENAI_API_KEY`、`USE_MOCK_AI`、`REQUEST_TIMEOUT_SECONDS` を確認します。

### ローカル画面のCSSが反映されない

Frontend を止めて、`.next` を消してから再起動します。

```powershell
Remove-Item -Recurse -Force .next
npm.cmd run dev
```

## セキュリティ注意

- `OPENAI_API_KEY` はGitHubへpushしません。
- `.env` と `.env.local` はGit管理対象外です。
- 誰でも使える公開URLにする場合、OpenAI API の利用料金が発生します。
- 実運用では、ログイン、利用回数制限、IP制限、レート制限の追加を推奨します。
